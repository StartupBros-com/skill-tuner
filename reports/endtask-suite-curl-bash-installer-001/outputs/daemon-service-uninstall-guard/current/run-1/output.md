#!/usr/bin/env bash
#
# install.sh — installer for flowctl (github.com/acme/flowctl)
#
# Usage:
#   curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh?$(date +%s)" | bash
#   curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh?$(date +%s)" | bash -s -- --daemon
#
# Flags:
#   --daemon               Also register flowctl as a background sync service
#                           (systemd --user unit on Linux, launchd LaunchAgent on macOS)
#                           that starts on login. Omit for a CLI-only install.
#   --uninstall             Remove flowctl: binary, shell completions, and the
#                           background service (if one was ever registered).
#   --version VERSION       Install a specific version instead of latest.
#   --prefix DIR             Install destination (default: $HOME/.local/bin).
#   --offline TARBALL        Airgapped install from a local tarball, no network calls.
#   --no-verify              Skip SHA256 checksum verification (not recommended).
#   --build-from-source      Consent, non-interactively, to installing a Rust
#                           toolchain and building from source if no prebuilt
#                           binary is available.
#   --force                 Reinstall even if the target version is already installed.
#   --quiet, -q               Errors only.
#   --no-color               Disable ANSI colors.
#   --no-gum                 Disable gum-styled output even if gum is installed.
#   --self-test              Check environment/tooling only; install nothing.
#   -h, --help                 Show this help and exit.
#
# Env vars: VERSION, BUILD_FROM_SOURCE=1, HTTPS_PROXY / HTTP_PROXY / NO_PROXY, NO_COLOR.

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="flowctl"
BINARY_NAME="flowctl"
FALLBACK_VERSION="0.4.0"
COSIGN_ID_RE='^https://github\.com/acme/flowctl/\.github/workflows/release\.ya?ml@refs/tags/v.*$'
COSIGN_ISSUER='https://token.actions.githubusercontent.com'

DEST="${PREFIX:-$HOME/.local/bin}"
VERSION="${VERSION:-}"
DAEMON=0
UNINSTALL=0
OFFLINE_TARBALL=""
NO_VERIFY=0
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
FORCE=0
QUIET=0
NO_GUM=0
SELF_TEST=0
ASSUME_YES=0
[[ -n "${NO_COLOR:-}" ]] && NO_GUM_COLOR=1 || NO_GUM_COLOR=0

# ---------------------------------------------------------------------------
# output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR + non-TTY
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$level" != err ] && [ "${QUIET:-0}" = 1 ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM:-0}" = 0 ] && [ "${NO_GUM_COLOR:-0}" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ -t 1 ] && [ "${NO_GUM_COLOR:-0}" = 0 ]; then
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  else
    printf '%s %s\n' "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }
die()  { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# temp dir + cleanup (trap set immediately after temp-dir creation)
# ---------------------------------------------------------------------------
TMP="$(mktemp -d "${TMPDIR:-/tmp}/flowctl-install.XXXXXX")"
LOCKFILE="${TMPDIR:-/tmp}/flowctl-install.lock"
LOCKDIR=""
LOCKFD=""

cleanup() {
  local ec=$?
  [ -n "$LOCKDIR" ] && [ -d "$LOCKDIR" ] && rm -rf "$LOCKDIR"
  if [ -n "$LOCKFD" ]; then exec 9>&- 2>/dev/null || true; fi
  [ -d "$TMP" ] && rm -rf "$TMP"
  exit $ec
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# help
# ---------------------------------------------------------------------------
print_help() {
  cat <<'EOF'
flowctl installer

Usage: install.sh [flags]

  --daemon              Register flowctl as a background sync service that
                         starts on login (systemd --user on Linux, launchd on
                         macOS). Default install is CLI-only.
  --uninstall            Remove flowctl completely (binary, completions,
                         background service if any). Always succeeds, even if
                         --daemon was never used.
  --version VERSION      Install a specific version instead of latest.
  --prefix DIR           Install destination (default: $HOME/.local/bin).
  --offline TARBALL      Airgapped install from a local tarball; no network.
  --no-verify            Skip SHA256 checksum verification.
  --build-from-source    Consent to installing a Rust toolchain and building
                         from source when no prebuilt binary is available.
  --force                Reinstall even if already at the target version.
  --quiet, -q            Errors only.
  --no-color             Disable ANSI colors.
  --no-gum               Disable gum-styled output.
  --self-test            Check environment/tooling only; install nothing.
  -h, --help             Show this help.

Env: VERSION, BUILD_FROM_SOURCE=1, HTTPS_PROXY/HTTP_PROXY/NO_PROXY, NO_COLOR
EOF
}

# ---------------------------------------------------------------------------
# arg parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --daemon) DAEMON=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --version) VERSION="${2:-}"; shift ;;
    --prefix) DEST="${2:-}"; shift ;;
    --offline) OFFLINE_TARBALL="${2:-}"; shift ;;
    --no-verify) NO_VERIFY=1 ;;
    --build-from-source) BUILD_FROM_SOURCE=1 ;;
    --force) FORCE=1 ;;
    --quiet|-q) QUIET=1 ;;
    --no-color) NO_GUM_COLOR=1 ;;
    --no-gum) NO_GUM=1 ;;
    --self-test) SELF_TEST=1 ;;
    -y|--yes) ASSUME_YES=1 ;;
    -h|--help) print_help; trap - EXIT; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
  shift
done

# ---------------------------------------------------------------------------
# proxy — every curl call gets "${PROXY_ARGS[@]}"; NO_PROXY honored natively
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# platform detection
# ---------------------------------------------------------------------------
OS=""; ARCH=""; TARGET=""; FROM_SOURCE=0
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
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
    warn "WSL detected — systemd --user may need 'systemd=true' in /etc/wsl.conf for --daemon to work"
  fi
}

# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
preflight_checks() {
  mkdir -p "$DEST" 2>/dev/null || true
  [ -w "$DEST" ] || die "cannot write to $DEST — check permissions or pass --prefix DIR"

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 20480 ]; then
    die "insufficient disk space in $DEST (need at least 20MB free)"
  fi

  CURRENT_VERSION=""
  if [ -x "$DEST/$BINARY_NAME" ]; then
    CURRENT_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || die "cannot reach github.com — behind a proxy? set HTTPS_PROXY, or use --offline TARBALL"
  fi
}

# ---------------------------------------------------------------------------
# self-test — checks environment only, installs nothing
# ---------------------------------------------------------------------------
self_test() {
  detect_platform
  info "platform: ${OS}-${ARCH} -> ${TARGET:-<none, source build required>}"
  for tool in curl tar sha256sum shasum cosign flock systemctl launchctl gum; do
    if command -v "$tool" >/dev/null 2>&1; then ok "$tool: found"; else warn "$tool: not found"; fi
  done
  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      && ok "network: reachable" || warn "network: unreachable"
  fi
  ok "self-test complete; nothing was installed"
}

# ---------------------------------------------------------------------------
# version resolution — 4-tier fallback (flag/env, Cargo.toml, GitHub API, redirect, hardcoded)
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. flag/env
  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0                                              # 2. local manifest
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                              # 3. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"                           # 4. redirect  5. hardcoded
}

# ---------------------------------------------------------------------------
# atomic lock — flock-first, mkdir spinlock fallback, stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { LOCKFD=9; flock -w "$w" 9; return $?; }
    return 0
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then return 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCKDIR="$d"
}

# ---------------------------------------------------------------------------
# checksum + sigstore
# ---------------------------------------------------------------------------
fetch_sha() {  # $1=artifact_url -> prints expected sha256 (empty if unavailable)
  curl -fsSL "${PROXY_ARGS[@]}" "${1}.sha256" 2>/dev/null | awk '{print $1}'
}

verify_checksum() {  # $1=file $2=expected
  [ "$NO_VERIFY" = 1 ] && { warn "checksum verification skipped (--no-verify)"; return 0; }
  [ -z "${2:-}" ] && { warn "no checksum available for this artifact; skipping"; return 0; }
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0; fi
  if [ "$a" = "$2" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $a)"; return 1; fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  [ "$NO_VERIFY" = 1 ] && return 0
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no Sigstore bundle published; skipping"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"; return 0
  else
    err "Sigstore verification FAILED"; return 1
  fi
}

# ---------------------------------------------------------------------------
# extract + install (atomic: install -m 0755, no wrong-perms window)
# ---------------------------------------------------------------------------
extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$archive" -C "$TMP" ;;
    *.zip) unzip -q "$archive" -d "$TMP" ;;
    *) die "unrecognized archive format: $archive" ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary not found inside archive"; return 1; }
  chmod +x "$bin"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME -> $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# build from source — rustup -> git clone --depth 1 -> cargo build --release
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  if [ "$BUILD_FROM_SOURCE" = 1 ]; then return 0; fi
  if [ -t 0 ] && [ -t 1 ]; then
    printf 'No prebuilt binary is available. Install a Rust toolchain and build from source? [y/N] '
    read -r reply
    case "$reply" in y|Y|yes|YES) return 0 ;; *) die "aborted — rerun with --build-from-source to consent non-interactively" ;; esac
  fi
  die "no prebuilt binary and not running in a terminal — rerun with --build-from-source or BUILD_FROM_SOURCE=1 to consent to a toolchain install"
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    info "installing Rust toolchain via rustup..."
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable >/dev/null
    # shellcheck disable=SC1090
    source "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || die "build succeeded but binary not found at $bin"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source -> $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# download — 3 URL tiers, then source-build fallback
# ---------------------------------------------------------------------------
download_and_install() {
  if [ "$FROM_SOURCE" = 1 ]; then
    confirm_build_from_source
    build_from_source
    return 0
  fi
  local url sha
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      sha=$(fetch_sha "$url")
      if verify_checksum "$TMP/artifact.tar.gz" "$sha" \
          && verify_sigstore "$TMP/artifact.tar.gz" "${url}.sigstore.json" \
          && extract_and_install "$TMP/artifact.tar.gz"; then
        return 0
      fi
      rm -f "$TMP/artifact.tar.gz"
    fi
  done
  warn "no prebuilt binary found for ${OS}/${ARCH} at version $VERSION"
  confirm_build_from_source
  build_from_source
}

# ---------------------------------------------------------------------------
# --offline install
# ---------------------------------------------------------------------------
offline_install() {
  [ -f "$OFFLINE_TARBALL" ] || die "--offline tarball not found: $OFFLINE_TARBALL"
  info "installing offline from $OFFLINE_TARBALL"
  local sha=""
  [ -f "${OFFLINE_TARBALL}.sha256" ] && sha=$(awk '{print $1}' "${OFFLINE_TARBALL}.sha256")
  verify_checksum "$OFFLINE_TARBALL" "$sha" || die "checksum verification failed for offline tarball"
  extract_and_install "$OFFLINE_TARBALL"
  [ -z "$VERSION" ] && VERSION="offline"
}

# ---------------------------------------------------------------------------
# shell completions (XDG paths, not rc-file guesses)
# ---------------------------------------------------------------------------
install_completions() {
  [ -x "$DEST/$BINARY_NAME" ] || return 0
  local dir

  dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  mkdir -p "$dir"
  if "$DEST/$BINARY_NAME" completions bash >"$dir/$BINARY_NAME.tmp" 2>/dev/null; then
    mv "$dir/$BINARY_NAME.tmp" "$dir/$BINARY_NAME"; ok "bash completions -> $dir/$BINARY_NAME"
  else rm -f "$dir/$BINARY_NAME.tmp"; fi

  dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  mkdir -p "$dir"
  if "$DEST/$BINARY_NAME" completions zsh >"$dir/_${BINARY_NAME}.tmp" 2>/dev/null; then
    mv "$dir/_${BINARY_NAME}.tmp" "$dir/_${BINARY_NAME}"; ok "zsh completions -> $dir/_${BINARY_NAME}"
  else rm -f "$dir/_${BINARY_NAME}.tmp"; fi

  dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$dir"
  if "$DEST/$BINARY_NAME" completions fish >"$dir/${BINARY_NAME}.fish.tmp" 2>/dev/null; then
    mv "$dir/${BINARY_NAME}.fish.tmp" "$dir/${BINARY_NAME}.fish"; ok "fish completions -> $dir/${BINARY_NAME}.fish"
  else rm -f "$dir/${BINARY_NAME}.fish.tmp"; fi
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on your PATH — add: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# background service — systemd --user (linux) / launchd LaunchAgent (macOS)
# only touched when --daemon is passed at install time; uninstall_service()
# below is always safe to call, even if a service was never registered.
# ---------------------------------------------------------------------------
install_service_systemd() {
  local unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  local unit_file="$unit_dir/flowctl.service"
  mkdir -p "$unit_dir"
  cat >"$unit_file" <<UNIT
[Unit]
Description=flowctl background sync daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DEST/$BINARY_NAME daemon --foreground
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
UNIT
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload
    systemctl --user enable --now flowctl.service
    loginctl enable-linger "$(id -un)" >/dev/null 2>&1 \
      || warn "could not enable linger for $(id -un); the daemon will only run while you're logged in"
    ok "systemd --user service installed and started: flowctl.service"
  else
    warn "systemctl not found; unit written to $unit_file but not activated"
  fi
}

install_service_launchd() {
  local plist_dir="$HOME/Library/LaunchAgents"
  local plist="$plist_dir/com.acme.flowctl.plist"
  mkdir -p "$plist_dir"
  cat >"$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.acme.flowctl</string>
  <key>ProgramArguments</key>
  <array>
    <string>$DEST/$BINARY_NAME</string>
    <string>daemon</string>
    <string>--foreground</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/flowctl.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/flowctl.log</string>
</dict>
</plist>
PLIST
  if command -v launchctl >/dev/null 2>&1; then
    launchctl bootout "gui/$(id -u)" "$plist" >/dev/null 2>&1 || true
    if launchctl bootstrap "gui/$(id -u)" "$plist" 2>/dev/null; then
      launchctl enable "gui/$(id -u)/com.acme.flowctl" >/dev/null 2>&1 || true
    else
      launchctl load -w "$plist" 2>/dev/null \
        || warn "could not load LaunchAgent; plist written to $plist"
    fi
    ok "launchd agent installed and started: com.acme.flowctl"
  else
    warn "launchctl not found; plist written to $plist but not activated"
  fi
}

install_service() {
  [ "$DAEMON" = 1 ] || return 0
  case "$OS" in
    linux) install_service_systemd ;;
    darwin) install_service_launchd ;;
    *) warn "background service not supported on $OS; skipping --daemon" ;;
  esac
}

uninstall_service() {
  local removed=0
  local unit_file="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/flowctl.service"
  if [ -f "$unit_file" ]; then
    if command -v systemctl >/dev/null 2>&1; then
      systemctl --user disable --now flowctl.service >/dev/null 2>&1 || true
      systemctl --user daemon-reload >/dev/null 2>&1 || true
    fi
    rm -f "$unit_file"
    ok "removed systemd --user service"
    removed=1
  fi

  local plist="$HOME/Library/LaunchAgents/com.acme.flowctl.plist"
  if [ -f "$plist" ]; then
    if command -v launchctl >/dev/null 2>&1; then
      launchctl bootout "gui/$(id -u)" "$plist" >/dev/null 2>&1 \
        || launchctl unload -w "$plist" >/dev/null 2>&1 || true
    fi
    rm -f "$plist"
    ok "removed launchd agent"
    removed=1
  fi

  [ "$removed" = 0 ] && info "no background service was ever registered; nothing to remove"
  return 0
}

# ---------------------------------------------------------------------------
# final summary box
# ---------------------------------------------------------------------------
draw_box() {  # $1=color, rest=lines
  local color="$1"; shift
  local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    [ "${#s}" -gt "$max" ] && max=${#s}
  done
  local inner=$((max+4)) border="" i
  for ((i=0;i<inner;i++)); do border+="═"; done
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    local pad=$((max-${#s})) p=""
    for ((i=0;i<pad;i++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

print_summary() {
  local svc="not installed (run again with --daemon to enable)"
  if [ "$DAEMON" = 1 ]; then
    case "$OS" in
      linux) svc="systemd --user service: flowctl.service (enabled, starts on login)" ;;
      darwin) svc="launchd agent: com.acme.flowctl (enabled, starts on login)" ;;
      *) svc="not supported on $OS" ;;
    esac
  fi
  [ "$QUIET" = 1 ] && return 0
  draw_box 42 \
    "\033[1mflowctl $VERSION installed\033[0m" \
    "binary:      $DEST/$BINARY_NAME" \
    "completions: bash/zsh/fish (XDG paths)" \
    "service:     $svc"
  check_path
}

print_uninstall_instructions() {
  [ "$QUIET" = 1 ] && return 0
  info "to uninstall later, run:"
  info "  curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)\" | bash -s -- --uninstall"
}

print_uninstall_summary() {
  [ "$QUIET" = 1 ] && return 0
  draw_box 42 "\033[1mflowctl uninstalled\033[0m" "binary, completions, and any background service were removed"
}

# ---------------------------------------------------------------------------
# uninstall path — safe to run even if --daemon was never used
# ---------------------------------------------------------------------------
uninstall() {
  acquire_lock "$LOCKFILE" 60 || die "could not acquire install lock (another install/uninstall is running?)"
  info "uninstalling $BINARY_NAME..."
  local had_binary=0
  [ -f "$DEST/$BINARY_NAME" ] && had_binary=1
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  uninstall_service
  if [ "$had_binary" = 1 ]; then
    ok "removed $BINARY_NAME from $DEST"
  else
    info "$BINARY_NAME was not installed at $DEST; completions/service (if any) were still cleaned up"
  fi
  print_uninstall_summary
  exit 0
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
main() {
  detect_platform

  if [ "$SELF_TEST" = 1 ]; then self_test; exit 0; fi
  if [ "$UNINSTALL" = 1 ]; then uninstall; fi

  if [ -n "$OFFLINE_TARBALL" ]; then
    acquire_lock "$LOCKFILE" 60 || die "could not acquire install lock"
    preflight_checks
    offline_install
    install_completions
    install_service
    print_summary
    print_uninstall_instructions
    exit 0
  fi

  resolve_version
  preflight_checks
  acquire_lock "$LOCKFILE" 2400 || die "could not acquire install lock — another install running?"

  if [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
    info "$BINARY_NAME $VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
  else
    download_and_install
  fi

  # always re-run integration steps: idempotent, not a full no-op even when
  # the binary itself was already up to date
  install_completions
  install_service
  print_summary
  print_uninstall_instructions
}

main