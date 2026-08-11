#!/usr/bin/env bash
#
# install.sh — installer for flowctl (github.com/acme/flowctl)
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh?$(date +%s)" | bash
#
# Flags (pass after `--` when piping, or `bash -s -- <flags>`):
#   --version VERSION   install a specific version instead of latest
#   --dest DIR          install directory (default: $HOME/.local/bin, env FLOWCTL_INSTALL_DIR)
#   --daemon            also register flowctl as a background sync service (systemd --user
#                        on Linux, launchd LaunchAgent on macOS) that starts on login
#   --offline TARBALL   install from a local tarball, no network calls at all
#   --easy-mode         append the install dir to your shell rc if it's not already on PATH
#   --force             reinstall even if the target version is already present
#   --quiet             errors only
#   --no-color          disable ANSI color output
#   --no-gum            disable gum styling even if gum is installed
#   --no-verify         skip SHA256 checksum and Sigstore signature verification
#   --uninstall          remove the binary, completions, and any registered service
#   -h, --help          show this help and exit
#
# Env vars honored: FLOWCTL_VERSION, FLOWCTL_INSTALL_DIR, HTTPS_PROXY, HTTP_PROXY, NO_PROXY,
#                    NO_COLOR
#
set -euo pipefail
umask 022

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="flowctl"
BINARY_NAME="flowctl"
FALLBACK_VERSION="0.1.0"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/\.github/workflows/release\.ya?ml@refs/tags/v.*\$"
SYSTEMD_UNIT_PATH="$HOME/.config/systemd/user/${BINARY_NAME}.service"
LAUNCHD_LABEL="com.${OWNER}.${BINARY_NAME}"
LAUNCHD_PLIST_PATH="$HOME/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"
LOCKFILE="${TMPDIR:-/tmp}/${BINARY_NAME}-install.lock"

# ---------------------------------------------------------------------------
# state / defaults
# ---------------------------------------------------------------------------
ACTION="install"
VERSION="${FLOWCTL_VERSION:-}"
DEST="${FLOWCTL_INSTALL_DIR:-$HOME/.local/bin}"
QUIET=0
FORCE=0
NO_GUM=0
NO_VERIFY=0
DAEMON=0
EASY_MODE=0
OFFLINE_TARBALL=""
FROM_SOURCE=0
EXPECTED_SHA=""
TMP=""
LOCK_MODE=""
LOCK_DIR=""

HAS_GUM=0
command -v gum >/dev/null 2>&1 && HAS_GUM=1

# ---------------------------------------------------------------------------
# output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR + non-TTY; err
# is never gated by --quiet
# ---------------------------------------------------------------------------
_log() {
  local level="$1" color="$2" sym="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ] && [ -t 1 ]; then
    gum style --foreground "$color" "$sym $*"
  elif [ -z "${NO_COLOR:-}" ] && [ -t 1 ]; then
    printf '\033[%sm%s\033[0m %s\n' "$color" "$sym" "$*"
  else
    printf '%s %s\n' "$sym" "$*"
  fi
}
info() { _log info 39 '->' "$@"; }
ok()   { _log ok   42 '✓'  "$@"; }
warn() { _log warn 214 '⚠' "$@"; }
err()  { _log err  196 '✗' "$@"; }

draw_box() {
  local title="$1"; shift
  local lines=("$@") line width=${#title}
  for line in "${lines[@]}"; do (( ${#line} > width )) && width=${#line}; done
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ] && [ -t 1 ]; then
    { printf '%s\n' "$title"; printf '%s\n' "${lines[@]}"; } \
      | gum style --border rounded --padding "0 1" --border-foreground 39
    return
  fi
  local border; border=$(printf -- '-%.0s' $(seq 1 $((width + 2))))
  printf '+%s+\n' "$border"
  printf '| %-*s |\n' "$width" "$title"
  printf '+%s+\n' "$border"
  for line in "${lines[@]}"; do printf '| %-*s |\n' "$width" "$line"; done
  printf '+%s+\n' "$border"
}

cleanup() {
  local ec=$?
  [ -n "$TMP" ] && [ -d "$TMP" ] && rm -rf "$TMP"
  [ -n "$LOCK_DIR" ] && [ -d "$LOCK_DIR" ] && rm -rf "$LOCK_DIR"
  exit "$ec"
}
trap cleanup EXIT
TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")

# ---------------------------------------------------------------------------
# flags
# ---------------------------------------------------------------------------
print_help() {
  sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --dest) DEST="$2"; shift 2 ;;
      --daemon) DAEMON=1; shift ;;
      --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --force) FORCE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) export NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --uninstall) ACTION="uninstall"; shift ;;
      -h|--help) print_help; exit 0 ;;
      *) err "unknown flag: $1"; print_help; exit 1 ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# platform + proxy
# ---------------------------------------------------------------------------
detect_os() { OS=$(uname -s | tr 'A-Z' 'a-z'); }

detect_platform() {
  detect_os
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — systemd --user services may need 'systemctl --user' support enabled in wsl.conf"
  fi
}

PROXY_ARGS=()
setup_proxy() {
  if [ -n "${HTTPS_PROXY:-}" ]; then PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

# ---------------------------------------------------------------------------
# version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. flag/env
  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml) || true
  fi
  if [ -z "$VERSION" ] && [ -f package.json ]; then
    VERSION=$(grep -m1 '"version"' package.json | sed -E 's/.*"([0-9][^"]*)".*/\1/') || true
  fi
  [ -n "$VERSION" ] && return 0                                              # 2. manifest
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0                                              # 3. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"                           # 4. redirect  5. hardcoded
}

# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
nearest_existing_dir() {
  local d="$1"
  while [ ! -d "$d" ]; do d=$(dirname "$d"); done
  printf '%s' "$d"
}

preflight() {
  local base avail
  base=$(nearest_existing_dir "$DEST")
  avail=$(df -Pk "$base" 2>/dev/null | awk 'NR==2{print $4}') || true
  if [ -n "$avail" ] && [ "$avail" -lt 51200 ] 2>/dev/null; then
    err "less than 50MB free at $base"; exit 1
  fi
  mkdir -p "$DEST" 2>/dev/null || true
  [ -w "$DEST" ] || { err "$DEST is not writable"; exit 1; }

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || { err "no network reachability (GitHub unreachable); use --offline <tarball> for an airgapped install"; exit 1; }
  fi
}

# ---------------------------------------------------------------------------
# atomic lock — flock-first, mkdir-spinlock fallback, stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    flock -w "$w" 9 || return 1
    LOCK_MODE=flock
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then return 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_MODE=mkdir
  LOCK_DIR="$d"
  return 0
}

# ---------------------------------------------------------------------------
# checksum + sigstore — missing tool = warn+continue; tool present + bad
# signature = hard fail
# ---------------------------------------------------------------------------
fetch_expected_sha() {
  local url="$1" base fname sha line
  EXPECTED_SHA=""
  sha=$(curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" 2>/dev/null | awk '{print $1}') || true
  if [ -n "$sha" ]; then EXPECTED_SHA="$sha"; return 0; fi
  base="${url%/*}"; fname="${url##*/}"
  line=$(curl -fsSL "${PROXY_ARGS[@]}" "${base}/checksums.txt" 2>/dev/null | grep -F "$fname" | head -1) || true
  [ -n "$line" ] && EXPECTED_SHA=$(awk '{print $1}' <<<"$line")
}

verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then
    a=$(sha256sum "$1" | cut -d' ' -f1) || true
  elif command -v shasum >/dev/null 2>&1; then
    a=$(shasum -a 256 "$1" | cut -d' ' -f1) || true
  else
    warn "no SHA256 tool found; skipping checksum verification"
    return 0
  fi
  if [ "$a" = "$2" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $a)"; return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null \
    || { warn "no Sigstore bundle published for this artifact; skipping"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "signature verified"; return 0
  else
    err "Sigstore verification FAILED"; return 1
  fi
}

# ---------------------------------------------------------------------------
# extract / install / build-from-source
# ---------------------------------------------------------------------------
extract_and_install() {
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" || { err "extraction failed"; return 1; } ;;
    *.tar.xz)       tar -xJf "$1" -C "$TMP" || { err "extraction failed"; return 1; } ;;
    *.zip)          unzip -q "$1" -d "$TMP" || { err "extraction failed"; return 1; } ;;
    *) err "unknown archive format: $1"; return 1 ;;
  esac
  local bin; bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME" || { err "failed to install binary"; return 1; }
  ok "installed $BINARY_NAME $VERSION -> $DEST/$BINARY_NAME"
}

install_rustup() {
  warn "cargo not found; installing a minimal rustup toolchain"
  curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal
  # shellcheck disable=SC1090
  source "$HOME/.cargo/env"
}

build_from_source() {
  command -v cargo >/dev/null 2>&1 || install_rustup
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  install -m 0755 "$src/target/release/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source -> $DEST/$BINARY_NAME"
}

already_installed_at_version() {
  [ -x "$DEST/$BINARY_NAME" ] || return 1
  local cur; cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
  [ "$cur" = "$VERSION" ]
}

download_and_install() {
  if [ "$FROM_SOURCE" = 1 ]; then build_from_source; return; fi
  local url
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      if [ "$NO_VERIFY" = 1 ]; then
        warn "--no-verify set; skipping checksum and signature verification"
      else
        fetch_expected_sha "$url"
        if [ -n "$EXPECTED_SHA" ]; then
          verify_checksum "$TMP/artifact.tar.gz" "$EXPECTED_SHA" || { rm -f "$TMP/artifact.tar.gz"; continue; }
        else
          warn "no published checksum for this artifact; skipping checksum check"
        fi
        verify_sigstore "$TMP/artifact.tar.gz" "${url}.sigstore" \
          || { rm -f "$TMP/artifact.tar.gz"; err "aborting on failed signature verification (use --no-verify to bypass)"; exit 1; }
      fi
      extract_and_install "$TMP/artifact.tar.gz" && return 0
    fi
  done
  warn "no working prebuilt artifact for $TARGET; building from source"
  build_from_source
}

verify_and_install_offline() {
  local tarball="$1"
  [ -f "$tarball" ] || { err "offline tarball not found: $tarball"; exit 1; }
  if [ "$NO_VERIFY" != 1 ]; then
    if [ -f "${tarball}.sha256" ]; then
      EXPECTED_SHA=$(awk '{print $1}' "${tarball}.sha256")
      verify_checksum "$tarball" "$EXPECTED_SHA" || exit 1
    else
      warn "no .sha256 sidecar next to offline tarball; skipping checksum (pass --no-verify to silence)"
    fi
  fi
  extract_and_install "$tarball" || exit 1
}

# ---------------------------------------------------------------------------
# completions + PATH
# ---------------------------------------------------------------------------
install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_DATA_HOME:-$HOME/.local/share}/fish/vendor_completions.d"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null \
    && ok "bash completions -> $bash_dir/$BINARY_NAME" || warn "bash completions skipped"
  "$DEST/$BINARY_NAME" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null \
    && ok "zsh completions -> $zsh_dir/_$BINARY_NAME" || warn "zsh completions skipped"
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null \
    && ok "fish completions -> $fish_dir/$BINARY_NAME.fish" || warn "fish completions skipped"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *)
      if [ "$EASY_MODE" = 1 ]; then
        local rc="$HOME/.bashrc"
        [ -n "${ZSH_VERSION:-}" ] || [ "$(basename "${SHELL:-}")" = zsh ] && rc="$HOME/.zshrc"
        if ! grep -qF "$DEST" "$rc" 2>/dev/null; then
          printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
          ok "added $DEST to PATH in $rc (restart your shell, or run: export PATH=\"$DEST:\$PATH\")"
        fi
      else
        warn "$DEST is not on your PATH"
        info "add to your shell rc: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

# ---------------------------------------------------------------------------
# background sync daemon — systemd --user on Linux, launchd on macOS
# ---------------------------------------------------------------------------
install_daemon_linux() {
  mkdir -p "$(dirname "$SYSTEMD_UNIT_PATH")"
  cat > "$SYSTEMD_UNIT_PATH" <<EOF
[Unit]
Description=flowctl background sync daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DEST/$BINARY_NAME daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload 2>/dev/null || true
    if systemctl --user enable --now "${BINARY_NAME}.service" 2>/dev/null; then
      ok "systemd --user service enabled and started"
    else
      warn "service file written but could not be started; retry with: systemctl --user enable --now ${BINARY_NAME}.service"
    fi
    if command -v loginctl >/dev/null 2>&1; then
      loginctl enable-linger "$USER" 2>/dev/null \
        || warn "could not enable-linger for $USER; the service may not start until you log in"
    fi
  else
    warn "systemctl not found; unit file written to $SYSTEMD_UNIT_PATH but not activated"
  fi
}

install_daemon_macos() {
  mkdir -p "$(dirname "$LAUNCHD_PLIST_PATH")" "$HOME/Library/Logs"
  cat > "$LAUNCHD_PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>${DEST}/${BINARY_NAME}</string><string>daemon</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>${HOME}/Library/Logs/${BINARY_NAME}.log</string>
  <key>StandardErrorPath</key><string>${HOME}/Library/Logs/${BINARY_NAME}.err.log</string>
</dict>
</plist>
EOF
  launchctl unload "$LAUNCHD_PLIST_PATH" >/dev/null 2>&1 || true
  if launchctl load -w "$LAUNCHD_PLIST_PATH" 2>/dev/null; then
    ok "launchd agent loaded"
  else
    warn "plist written but could not be loaded; retry with: launchctl load -w $LAUNCHD_PLIST_PATH"
  fi
}

install_daemon() {
  [ "$DAEMON" = 1 ] || return 0
  case "$OS" in
    linux)  install_daemon_linux ;;
    darwin) install_daemon_macos ;;
    *) warn "no background-service support for $OS; skipping --daemon registration" ;;
  esac
}

# ---------------------------------------------------------------------------
# uninstall — must succeed and report success whether or not --daemon was
# ever used
# ---------------------------------------------------------------------------
uninstall() {
  detect_os
  info "uninstalling $BINARY_NAME"
  local had_error=0

  if [ -f "$DEST/$BINARY_NAME" ]; then
    rm -f "$DEST/$BINARY_NAME" && ok "removed binary $DEST/$BINARY_NAME" || { err "failed to remove binary"; had_error=1; }
  else
    info "binary not found at $DEST/$BINARY_NAME (already removed?)"
  fi

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_DATA_HOME:-$HOME/.local/share}/fish/vendor_completions.d"
  rm -f "$bash_dir/$BINARY_NAME" "$zsh_dir/_$BINARY_NAME" "$fish_dir/$BINARY_NAME.fish"
  ok "removed shell completions (if present)"

  case "$OS" in
    linux)
      if [ -f "$SYSTEMD_UNIT_PATH" ]; then
        if command -v systemctl >/dev/null 2>&1; then
          systemctl --user disable --now "${BINARY_NAME}.service" 2>/dev/null || true
          systemctl --user daemon-reload 2>/dev/null || true
        fi
        rm -f "$SYSTEMD_UNIT_PATH" && ok "removed systemd --user service" || { warn "could not remove $SYSTEMD_UNIT_PATH"; had_error=1; }
      else
        info "no systemd service was registered; nothing to remove"
      fi
      ;;
    darwin)
      if [ -f "$LAUNCHD_PLIST_PATH" ]; then
        launchctl unload "$LAUNCHD_PLIST_PATH" >/dev/null 2>&1 || true
        rm -f "$LAUNCHD_PLIST_PATH" && ok "removed launchd agent" || { warn "could not remove $LAUNCHD_PLIST_PATH"; had_error=1; }
      else
        info "no launchd agent was registered; nothing to remove"
      fi
      ;;
    *)
      info "no service manager for $OS; nothing to remove"
      ;;
  esac

  if [ "$had_error" = 1 ]; then
    err "uninstall finished with errors"
    exit 1
  fi
  ok "$BINARY_NAME fully uninstalled"
  exit 0
}

# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------
print_summary() {
  local svc="not requested (use --daemon to enable)"
  if [ "$DAEMON" = 1 ]; then
    case "$OS" in
      linux)  svc="systemd --user: $SYSTEMD_UNIT_PATH" ;;
      darwin) svc="launchd: $LAUNCHD_PLIST_PATH" ;;
      *)      svc="not supported on $OS" ;;
    esac
  fi
  draw_box "flowctl $VERSION installed" \
    "binary:      $DEST/$BINARY_NAME" \
    "completions: bash/zsh/fish (XDG data dirs)" \
    "daemon:      $svc"
}

print_uninstall_instructions() {
  info "to uninstall: re-run this script with --uninstall"
  info "  curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)\" | bash -s -- --uninstall"
  info "this removes the binary, shell completions, and any registered background service."
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"
  [ "$ACTION" = "uninstall" ] && uninstall

  detect_platform
  setup_proxy
  resolve_version
  preflight

  acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install running?)"; exit 1; }

  if already_installed_at_version && [ "$FORCE" != 1 ]; then
    ok "$BINARY_NAME $VERSION already installed at $DEST/$BINARY_NAME; skipping download (use --force to reinstall)"
  elif [ -n "$OFFLINE_TARBALL" ]; then
    verify_and_install_offline "$OFFLINE_TARBALL"
  else
    download_and_install
  fi

  install_completions
  check_path
  install_daemon
  print_summary
  print_uninstall_instructions
}

main "$@"