#!/usr/bin/env bash
#
# flowctl installer
#
# One-liner:
#   curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh?$(date +%s)" | bash
#
# With flags (curl-pipe-bash requires `bash -s --` to pass args through):
#   curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh" | bash -s -- --daemon
#
# Flags:
#   --version VERSION   Install a specific version instead of latest (env: FLOWCTL_VERSION)
#   --prefix DIR         Install destination (default: ~/.local/bin, env: FLOWCTL_INSTALL_DIR)
#   --daemon              Also register flowctl-sync as a background service:
#                           systemd --user unit on Linux, launchd LaunchAgent on macOS.
#                           Default install (no --daemon) installs only the CLI binary.
#   --force               Reinstall even if the same version is already present
#   --no-verify            Skip SHA256/Sigstore verification (NOT recommended)
#   --offline TARBALL      Install from a local tarball, no network access at all
#   --easy-mode             Append install dir to PATH in ~/.bashrc / ~/.zshrc if missing
#   --quiet                 Only print errors
#   --no-color               Disable ANSI colors
#   --no-gum                 Disable gum styling even if `gum` is installed
#   --uninstall               Remove the binary, shell completions, and any registered
#                              background service. Safe to run even if --daemon was never used.
#   -h, --help                 Show this help and exit
#
# Env: HTTPS_PROXY / HTTP_PROXY are honored on every network call. NO_COLOR disables styling.
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER=acme
REPO=flowctl
BINARY_NAME=flowctl
FALLBACK_VERSION="1.4.0"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/release\\.yml@refs/tags/v.*\$"

VERSION="${FLOWCTL_VERSION:-}"
DEST="${FLOWCTL_INSTALL_DIR:-$HOME/.local/bin}"
FORCE=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
QUIET=0
NO_COLOR_FLAG=0
NO_GUM=0
DAEMON=0
DO_UNINSTALL=0

TMP=""
LOCKFILE="${TMPDIR:-/tmp}/flowctl-install-$(id -u).lock"
LOCK_DIR=""
LOCK_METHOD=""
PROXY_ARGS=()

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR + non-TTY.
# err() is never gated by --quiet.
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local color="$1" icon="$2" stream="$3"; shift 3
  local msg="$*" no_gum=0 no_ansi=0
  [ -n "${NO_COLOR:-}" ] && no_gum=1 && no_ansi=1
  [ "$NO_GUM" = 1 ] && no_gum=1
  [ "$NO_COLOR_FLAG" = 1 ] && no_gum=1 && no_ansi=1
  [ -t 1 ] || no_ansi=1
  if [ "$HAS_GUM" = 1 ] && [ "$no_gum" != 1 ]; then
    if [ "$stream" = 2 ]; then gum style --foreground "$color" "$icon $msg" >&2
    else gum style --foreground "$color" "$icon $msg"; fi
  elif [ "$no_ansi" != 1 ]; then
    if [ "$stream" = 2 ]; then printf '\033[%sm%s\033[0m %s\n' "$color" "$icon" "$msg" >&2
    else printf '\033[%sm%s\033[0m %s\n' "$color" "$icon" "$msg"; fi
  else
    if [ "$stream" = 2 ]; then printf '%s %s\n' "$icon" "$msg" >&2
    else printf '%s %s\n' "$icon" "$msg"; fi
  fi
}
info() { [ "$QUIET" = 1 ] && return 0; _log 39 '->' 1 "$@"; }
ok()   { [ "$QUIET" = 1 ] && return 0; _log 42 '✓'  1 "$@"; }
warn() { [ "$QUIET" = 1 ] && return 0; _log 214 '⚠' 1 "$@"; }
err()  { _log 196 '✗' 2 "$@"; }

usage() {
  cat <<'EOF'
flowctl installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh" | bash -s -- [flags]

Flags:
  --version VERSION   Install a specific version (env: FLOWCTL_VERSION)
  --prefix DIR        Install destination (default: ~/.local/bin, env: FLOWCTL_INSTALL_DIR)
  --daemon            Register flowctl-sync as a background service (systemd --user / launchd)
  --force             Reinstall even if the same version is already present
  --no-verify         Skip SHA256/Sigstore verification (NOT recommended)
  --offline TARBALL   Install from a local tarball, no network access
  --easy-mode         Append install dir to PATH in shell rc if missing
  --quiet             Only print errors
  --no-color          Disable ANSI colors
  --no-gum            Disable gum styling even if installed
  --uninstall         Remove binary, completions, and any registered service
  -h, --help          Show this help
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version) VERSION="${2:?--version requires an argument}"; shift 2 ;;
      --prefix|--dest) DEST="${2:?--prefix requires an argument}"; shift 2 ;;
      --daemon) DAEMON=1; shift ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --offline) OFFLINE_TARBALL="${2:?--offline requires a tarball path}"; shift 2 ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR_FLAG=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# Platform detection → Rust target triple. Prefer musl on Linux (static).
# ---------------------------------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  FROM_SOURCE=0
  case "$ARCH" in
    x86_64|amd64) ARCH=x86_64 ;;
    arm64|aarch64) ARCH=aarch64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — --daemon needs WSL2 with systemd enabled (see /etc/wsl.conf); CLI install is unaffected"
  fi
}

setup_proxy() {
  if [[ -n "${HTTPS_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
  # NO_PROXY is honored by curl natively.
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback.
# ---------------------------------------------------------------------------
resolve_version() {
  [[ -n "$VERSION" ]] && return 0                                            # 1. CLI flag/env
  if [[ -f Cargo.toml ]]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml) || true
  fi
  [[ -n "$VERSION" ]] && return 0                                            # 2. manifest
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [[ -n "$VERSION" ]] && return 0                                            # 3. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"                         # 4. redirect  5. hardcoded
  info "resolved version: $VERSION"
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install directory: $DEST"; exit 1; }
  [[ -w "$DEST" ]] || { err "no write permission on $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2 {print $4}') || true
  if [[ -n "$avail_kb" ]] && [[ "$avail_kb" -lt 51200 ]]; then
    err "less than 50MB free at $DEST; aborting"
    exit 1
  fi

  if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
    warn "cannot reach github.com — check network or HTTPS_PROXY/HTTP_PROXY"
  fi
}

check_existing_install() {
  SKIP_DOWNLOAD=0
  [[ -x "$DEST/$BINARY_NAME" ]] || return 0
  local current
  current=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
  if [[ -n "$current" ]] && [[ "$current" == "$VERSION" ]] && [[ "$FORCE" != 1 ]]; then
    SKIP_DOWNLOAD=1
  fi
}

# ---------------------------------------------------------------------------
# Atomic lock — flock-first, mkdir spinlock fallback (macOS has no flock),
# stale-PID self-heal. Brace-scoped so `2>/dev/null` doesn't leak onto the
# caller's stderr permanently.
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    flock -w "$w" 9 && { LOCK_METHOD=flock; return 0; }
    return 1
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"
      continue
    fi
    if (( $(date +%s) - start >= w )); then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
  LOCK_METHOD=mkdir
  return 0
}

release_lock() {
  if [[ "$LOCK_METHOD" == mkdir ]] && [[ -n "$LOCK_DIR" ]]; then
    rm -rf "$LOCK_DIR"
    LOCK_DIR=""
  fi
  # flock's fd 9 releases automatically when the process exits.
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore. Missing tool = warn+continue; tool present + bad
# verification = hard fail.
# ---------------------------------------------------------------------------
fetch_expected_sha() {
  curl -fsSL "${PROXY_ARGS[@]}" "${1}.sha256" 2>/dev/null | awk '{print $1}' || true
}

verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0; fi
  [[ "$a" == "$2" ]] && { ok "SHA256 verified"; return 0; } || { err "checksum mismatch (want $2 got $a)"; return 1; }
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no Sigstore bundle for this artifact; skipping"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "signature verified"
    return 0
  fi
  err "Sigstore verification FAILED"
  return 1
}

# ---------------------------------------------------------------------------
# Download — 4-tier fallback → build from source.
# ---------------------------------------------------------------------------
download_and_install() {
  local url artifact="$TMP/artifact.tar.gz" sha
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$OS-$ARCH.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      if [[ "$NO_VERIFY" == 1 ]]; then
        warn "--no-verify set; skipping checksum and signature verification"
      else
        sha=$(fetch_expected_sha "$url")
        if [[ -n "$sha" ]]; then
          verify_checksum "$artifact" "$sha" || { rm -f "$artifact"; continue; }
        else
          warn "no published checksum for this artifact; skipping SHA256 check"
        fi
        verify_sigstore "$artifact" "${url}.sigstore.json" || { rm -f "$artifact"; continue; }
      fi
      extract_and_install "$artifact" && return 0
    fi
  done
  warn "no prebuilt binary available; building from source"
  rm -f "$artifact"
  build_from_source
}

extract_and_install() {
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$1" -C "$TMP" ;;
    *.zip)          unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

install_offline() {
  [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install directory: $DEST"; exit 1; }
  extract_and_install "$OFFLINE_TARBALL"
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup toolchain install stable >/dev/null 2>&1 || true
    else
      warn "rustup not found; bootstrapping via rustup.rs"
      curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable >/dev/null 2>&1 \
        || { err "failed to install a Rust toolchain"; exit 1; }
      # shellcheck source=/dev/null
      source "$HOME/.cargo/env"
    fi
  fi
  command -v cargo >/dev/null 2>&1 || { err "cargo still unavailable after rustup install"; exit 1; }

  local src="$TMP/src"
  git clone --depth 1 ${VERSION:+--branch "v$VERSION"} "https://github.com/$OWNER/$REPO.git" "$src" \
    || { err "git clone failed"; exit 1; }
  ( cd "$src" && cargo build --release ) || { err "cargo build failed"; exit 1; }
  install -m 0755 "$src/target/release/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built from source and installed → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Completions (XDG paths, not rc-file guesses)
# ---------------------------------------------------------------------------
install_completions() {
  [[ -x "$DEST/$BINARY_NAME" ]] || return 0
  if ! timeout 1 "$DEST/$BINARY_NAME" completions bash >/dev/null 2>&1; then
    warn "this build of flowctl doesn't support 'completions'; skipping"
    return 0
  fi
  local data_home="${XDG_DATA_HOME:-$HOME/.local/share}"

  mkdir -p "$data_home/bash-completion/completions"
  "$DEST/$BINARY_NAME" completions bash > "$data_home/bash-completion/completions/flowctl" 2>/dev/null \
    && ok "installed bash completions"

  mkdir -p "$data_home/zsh/site-functions"
  "$DEST/$BINARY_NAME" completions zsh > "$data_home/zsh/site-functions/_flowctl" 2>/dev/null \
    && ok "installed zsh completions"

  mkdir -p "$data_home/fish/vendor_completions.d"
  "$DEST/$BINARY_NAME" completions fish > "$data_home/fish/vendor_completions.d/flowctl.fish" 2>/dev/null \
    && ok "installed fish completions"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [[ "$EASY_MODE" == 1 ]]; then
    local rc
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
      [[ -f "$rc" ]] || continue
      grep -qF "$DEST" "$rc" 2>/dev/null || {
        printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
        ok "added $DEST to PATH in $rc"
      }
    done
  else
    warn "$DEST is not on your PATH — add it yourself, or re-run with --easy-mode"
  fi
}

# ---------------------------------------------------------------------------
# Background service — systemd --user (Linux) / launchd LaunchAgent (macOS).
# Only touched when --daemon is passed at install time.
# ---------------------------------------------------------------------------
register_service() {
  [[ "$DAEMON" == 1 ]] || return 0
  info "registering flowctl-sync as a background service..."
  case "$(uname -s)" in
    Linux)
      if ! command -v systemctl >/dev/null 2>&1; then
        warn "systemctl not found; skipping service registration (run 'flowctl daemon run' manually)"
        return 0
      fi
      local unit_dir="$HOME/.config/systemd/user"
      mkdir -p "$unit_dir"
      local unit="$unit_dir/flowctl-sync.service"
      cat > "$unit" <<EOF
[Unit]
Description=flowctl background sync daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DEST/$BINARY_NAME daemon run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
      systemctl --user daemon-reload
      systemctl --user enable --now flowctl-sync.service
      loginctl enable-linger "$USER" >/dev/null 2>&1 || true
      ok "systemd --user service installed and started: $unit"
      ;;
    Darwin)
      local agent_dir="$HOME/Library/LaunchAgents"
      mkdir -p "$agent_dir"
      local plist="$agent_dir/com.acme.flowctl.sync.plist"
      cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.acme.flowctl.sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>$DEST/$BINARY_NAME</string>
    <string>daemon</string>
    <string>run</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/flowctl-sync.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/flowctl-sync.log</string>
</dict>
</plist>
EOF
      launchctl unload "$plist" >/dev/null 2>&1 || true
      launchctl load -w "$plist"
      ok "launchd agent installed and started: $plist"
      ;;
    *)
      warn "no supported service manager on this OS; skipping --daemon registration"
      ;;
  esac
}

uninstall_service() {
  case "$(uname -s)" in
    Linux)
      local unit="$HOME/.config/systemd/user/flowctl-sync.service"
      if [[ -f "$unit" ]]; then
        if command -v systemctl >/dev/null 2>&1; then
          systemctl --user disable --now flowctl-sync.service >/dev/null 2>&1 || true
        fi
        rm -f "$unit"
        command -v systemctl >/dev/null 2>&1 && systemctl --user daemon-reload >/dev/null 2>&1 || true
        ok "removed systemd --user service: $unit"
      else
        info "no systemd service registered; nothing to remove"
      fi
      ;;
    Darwin)
      local plist="$HOME/Library/LaunchAgents/com.acme.flowctl.sync.plist"
      if [[ -f "$plist" ]]; then
        launchctl unload "$plist" >/dev/null 2>&1 || true
        rm -f "$plist"
        ok "removed launchd agent: $plist"
      else
        info "no launchd agent registered; nothing to remove"
      fi
      ;;
    *)
      info "no service manager on this OS; nothing to remove"
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Uninstall — must succeed and report success even if --daemon was never used.
# ---------------------------------------------------------------------------
do_uninstall() {
  info "uninstalling flowctl..."
  local removed_any=0

  if [[ -f "$DEST/$BINARY_NAME" ]]; then
    rm -f "$DEST/$BINARY_NAME"
    ok "removed binary: $DEST/$BINARY_NAME"
    removed_any=1
  else
    info "binary not found at $DEST/$BINARY_NAME; nothing to remove there"
  fi

  local data_home="${XDG_DATA_HOME:-$HOME/.local/share}" comp
  for comp in \
    "$data_home/bash-completion/completions/flowctl" \
    "$data_home/zsh/site-functions/_flowctl" \
    "$data_home/fish/vendor_completions.d/flowctl.fish"; do
    if [[ -f "$comp" ]]; then
      rm -f "$comp"
      ok "removed completion: $comp"
      removed_any=1
    fi
  done

  uninstall_service

  echo
  if [[ "$removed_any" == 1 ]]; then
    ok "flowctl uninstalled successfully"
  else
    ok "flowctl was already absent; nothing to do (uninstall is a success either way)"
  fi
  exit 0
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
draw_box() {
  local max=0 line
  for line in "$@"; do (( ${#line} > max )) && max=${#line}; done
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" != 1 ]; then
    printf '%s\n' "$@" | gum style --border rounded --padding "0 1" --foreground 42
    return
  fi
  local border
  border=$(printf -- '-%.0s' $(seq 1 $((max + 2))))
  printf '+%s+\n' "$border"
  for line in "$@"; do
    printf '| %-*s |\n' "$max" "$line"
  done
  printf '+%s+\n' "$border"
}

print_summary() {
  [[ "$QUIET" == 1 ]] && return 0
  local lines=("flowctl $VERSION installed successfully")
  lines+=("binary:      $DEST/$BINARY_NAME")
  lines+=("completions: ${XDG_DATA_HOME:-$HOME/.local/share}/{bash-completion,zsh,fish}/...")
  if [[ "$DAEMON" == 1 ]]; then
    case "$(uname -s)" in
      Linux)  lines+=("service:     systemd --user flowctl-sync.service (enabled, running)") ;;
      Darwin) lines+=("service:     launchd com.acme.flowctl.sync (loaded, running)") ;;
      *)      lines+=("service:     not supported on this OS") ;;
    esac
  else
    lines+=("service:     none (pass --daemon at install time to enable background sync)")
  fi
  echo
  draw_box "${lines[@]}"
  echo
}

print_uninstall_instructions() {
  [[ "$QUIET" == 1 ]] && return 0
  info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "  (removes the binary, shell completions, and any registered background service)"
}

# ---------------------------------------------------------------------------
cleanup() {
  local ec=$?
  [[ -n "$TMP" ]] && [[ -d "$TMP" ]] && rm -rf "$TMP"
  release_lock
  return $ec
}

main() {
  parse_args "$@"

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    do_uninstall
  fi

  TMP="$(mktemp -d "${TMPDIR:-/tmp}/flowctl-install.XXXXXX")"
  trap cleanup EXIT

  detect_platform
  setup_proxy

  acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock — another flowctl install may be running"; exit 1; }

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    install_offline
  else
    preflight
    resolve_version
    check_existing_install
    if [[ "${SKIP_DOWNLOAD:-0}" == 1 ]]; then
      info "flowctl $VERSION already installed at $DEST/$BINARY_NAME; skipping download (use --force to reinstall)"
    elif [[ "$FROM_SOURCE" == 1 ]]; then
      build_from_source
    else
      download_and_install
    fi
  fi

  release_lock

  install_completions
  check_path
  register_service
  print_summary
  print_uninstall_instructions
}

main "$@"