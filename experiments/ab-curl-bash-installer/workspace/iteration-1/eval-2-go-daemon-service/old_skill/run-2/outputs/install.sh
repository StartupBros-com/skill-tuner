#!/usr/bin/env bash
#
# moorhen installer
# ------------------
# Installs the moorhen binary (github.com/hovlabs/moorhen) from a release
# tarball and wires it up as a background service: a systemd --user unit on
# Linux, a launchd LaunchAgent on macOS. The service is started immediately
# and configured to start again on every login.
#
# Usage:
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/moorhen/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION   install a specific version (default: latest)
#   --dest DIR           install directory (default: $HOME/.local/bin)
#   --force               reinstall even if the target version is already installed
#   --no-service          install the binary only; skip systemd/launchd setup
#   --no-verify            skip SHA256 / Sigstore verification (NOT recommended)
#   --offline TARBALL      install from a local tarball, no network calls
#   --quiet                errors only
#   --no-color              disable ANSI colors
#   --no-gum                 disable gum styling even if installed
#   --uninstall               remove the binary, service, and completions
#   -h, --help                 show this help and exit
#
# Environment:
#   HTTPS_PROXY / HTTP_PROXY   proxied network access
#   MOORHEN_VERSION             same as --version
#   NO_COLOR                     same as --no-color

set -euo pipefail
umask 022

# ---------------------------------------------------------------------------
# constants + defaults
# ---------------------------------------------------------------------------
OWNER="hovlabs"
REPO="moorhen"
BINARY_NAME="moorhen"
SERVICE_NAME="moorhen"                # systemd unit: moorhen.service
SERVICE_LABEL="com.hovlabs.moorhen"   # launchd label
FALLBACK_VERSION="0.1.0"              # pinned last-resort; bumped by release CI
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION="${MOORHEN_VERSION:-}"
DEST="${XDG_BIN_HOME:-$HOME/.local/bin}"
FORCE=0
NO_SERVICE=0
NO_VERIFY=0
OFFLINE_TARBALL=""
QUIET=0
NO_GUM=0
DO_UNINSTALL=0
NO_COLOR=0
[ -n "${NO_COLOR_ENV:-${NO_COLOR:-}}" ] && NO_COLOR=1 || true

LOCK_DIR=""
CURRENT_VERSION=""
TMP=""

HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------
_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ] && [ "$NO_COLOR" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$NO_COLOR" = 1 ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

draw_box() {  # $1=color, rest=lines
  local color="$1"; shift; local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); (( ${#s} > max )) && max=${#s}; done
  local inner=$((max+4)) border=""; for ((i=0;i<inner;i++)); do border+="═"; done
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); local pad=$((max-${#s})) p=""
    for ((i=0;i<pad;i++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

print_help() {
  cat <<'EOF'
moorhen installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/hovlabs/moorhen/main/install.sh?$(date +%s)" | bash

Flags:
  --version VERSION   install a specific version (default: latest)
  --dest DIR           install directory (default: $HOME/.local/bin)
  --force               reinstall even if the target version is already installed
  --no-service          install the binary only; skip systemd/launchd setup
  --no-verify            skip SHA256 / Sigstore verification (NOT recommended)
  --offline TARBALL      install from a local tarball, no network calls
  --quiet                errors only
  --no-color              disable ANSI colors
  --no-gum                 disable gum styling even if installed
  --uninstall               remove the binary, service, and completions
  -h, --help                 show this help and exit

Environment:
  HTTPS_PROXY / HTTP_PROXY   proxied network access
  MOORHEN_VERSION             same as --version
  NO_COLOR                     same as --no-color
EOF
}

# ---------------------------------------------------------------------------
# platform + proxy
# ---------------------------------------------------------------------------
detect_platform() {
  local os arch
  os=$(uname -s | tr 'A-Z' 'a-z')
  arch=$(uname -m)
  case "$arch" in
    x86_64|amd64)  arch=amd64 ;;
    arm64|aarch64) arch=arm64 ;;
    *) err "unsupported architecture: $arch"; exit 1 ;;
  esac
  case "$os" in
    linux)  OS=linux ;;
    darwin) OS=darwin ;;
    *) err "unsupported OS: $os (moorhen ships linux/darwin only)"; exit 1 ;;
  esac
  ARCH="$arch"
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — systemd --user needs 'systemd=true' under [boot] in /etc/wsl.conf (then 'wsl --shutdown')"
  fi
}

PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# cleanup + locking
# ---------------------------------------------------------------------------
cleanup() {
  local ec=$?
  [ -n "$TMP" ] && rm -rf -- "$TMP" 2>/dev/null
  [ -n "$LOCK_DIR" ] && rm -rf -- "$LOCK_DIR" 2>/dev/null
  exit "$ec"
}

acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-120}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    [ $(( $(date +%s) - start )) -ge "$w" ] && return 1
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST"
  [ -w "$DEST" ] || { err "cannot write to $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ] 2>/dev/null; then
    err "less than 50MB free at $DEST"; exit 1
  fi

  if [ -z "$OFFLINE_TARBALL" ] && ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
    err "no network reachability to github.com (use --offline TARBALL for an airgapped install)"; exit 1
  fi

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" = 0 ]; then
    if command -v timeout >/dev/null 2>&1; then
      CURRENT_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
    else
      CURRENT_VERSION=$("$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
    fi
  fi
}

# ---------------------------------------------------------------------------
# version resolution
# ---------------------------------------------------------------------------
resolve_version() {
  if [ -n "$VERSION" ]; then VERSION="${VERSION#v}"; return 0; fi
  info "resolving latest moorhen version..."
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && return 0
  warn "could not resolve latest version from GitHub; falling back to pinned $FALLBACK_VERSION"
  VERSION="$FALLBACK_VERSION"
}

# ---------------------------------------------------------------------------
# checksum + sigstore
# ---------------------------------------------------------------------------
verify_checksum_from_manifest() {  # $1=file $2=manifest $3=expected_name
  local expected actual
  expected=$(awk -v f="$3" '$2==f || $2=="*"f {print $1; exit}' "$2")
  if [ -z "$expected" ]; then
    err "no checksum entry for $3 in checksums.txt"; return 1
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no SHA256 tool found; skipping checksum verification"
    return 0
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified ($3)"; return 0
  fi
  err "checksum mismatch for $3 (want $expected, got $actual)"
  return 1
}

verify_sigstore() {  # $1=checksums_file $2=base_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  local sig="$TMP/checksums.txt.sig" pem="$TMP/checksums.txt.pem"
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2/checksums.txt.sig" -o "$sig" 2>/dev/null \
     || ! curl -fsSL "${PROXY_ARGS[@]}" "$2/checksums.txt.pem" -o "$pem" 2>/dev/null; then
    warn "no Sigstore bundle published for this release; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --signature "$sig" --certificate "$pem" \
       --certificate-identity-regexp "$COSIGN_ID_RE" \
       --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"; return 0
  fi
  err "Sigstore verification FAILED for checksums.txt — refusing to trust this download"
  return 1
}

# ---------------------------------------------------------------------------
# download / build / install
# ---------------------------------------------------------------------------
extract_and_install() {
  tar -xzf "$1" -C "$TMP"
  local bin
  bin=$(find "$TMP" -maxdepth 2 -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found in archive"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

build_from_source() {
  command -v git >/dev/null 2>&1 || { err "git not found; cannot build from source"; exit 1; }
  command -v go  >/dev/null 2>&1 || { err "Go toolchain not found (https://go.dev/dl/); cannot build from source"; exit 1; }
  info "cloning $OWNER/$REPO @ v$VERSION..."
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$TMP/src" \
    || { err "clone failed for tag v$VERSION"; exit 1; }
  (
    cd "$TMP/src"
    go build -trimpath -ldflags="-s -w" -o "$TMP/$BINARY_NAME" "./cmd/$BINARY_NAME" 2>/dev/null \
      || go build -trimpath -ldflags="-s -w" -o "$TMP/$BINARY_NAME" .
  ) || { err "go build failed"; exit 1; }
  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

download_and_install() {
  local artifact="${REPO}_${VERSION}_${OS}_${ARCH}.tar.gz"
  local release_base="https://github.com/$OWNER/$REPO/releases/download/v$VERSION"
  local latest_base="https://github.com/$OWNER/$REPO/releases/latest/download"
  local base ok_dl=0 download_base=""
  for base in "$release_base" "$latest_base"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$base/$artifact" -o "$TMP/$artifact" 2>/dev/null; then
      ok_dl=1; download_base="$base"; break
    fi
  done
  if [ "$ok_dl" = 0 ]; then
    warn "no prebuilt binary for $OS/$ARCH at version $VERSION; building from source"
    build_from_source
    return $?
  fi
  if [ "$NO_VERIFY" = 0 ]; then
    curl -fsSL "${PROXY_ARGS[@]}" "$download_base/checksums.txt" -o "$TMP/checksums.txt" \
      || { err "failed to download checksums.txt"; exit 1; }
    verify_checksum_from_manifest "$TMP/$artifact" "$TMP/checksums.txt" "$artifact" || exit 1
    verify_sigstore "$TMP/checksums.txt" "$download_base" || exit 1
  else
    warn "--no-verify set; skipping checksum and signature verification"
  fi
  extract_and_install "$TMP/$artifact"
}

install_offline() {
  [ -f "$OFFLINE_TARBALL" ] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  info "installing from local tarball (offline mode): $OFFLINE_TARBALL"
  if [ "$NO_VERIFY" = 0 ]; then
    local manifest; manifest="$(dirname "$OFFLINE_TARBALL")/checksums.txt"
    if [ -f "$manifest" ]; then
      verify_checksum_from_manifest "$OFFLINE_TARBALL" "$manifest" "$(basename "$OFFLINE_TARBALL")" || exit 1
    else
      warn "no checksums.txt next to tarball; skipping checksum verification"
    fi
  fi
  extract_and_install "$OFFLINE_TARBALL"
}

install_completions() {
  "$DEST/$BINARY_NAME" completion bash >/dev/null 2>&1 || { warn "binary does not support 'completion'; skipping"; return 0; }
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completion zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "shell completions installed (bash/zsh/fish)"
}

# ---------------------------------------------------------------------------
# background service: systemd --user (Linux) / launchd (macOS)
# ---------------------------------------------------------------------------
install_service_linux() {
  if ! command -v systemctl >/dev/null 2>&1; then
    warn "systemctl not found; skipping service setup (binary is installed, run it manually)"
    return 0
  fi
  local unit_dir="$HOME/.config/systemd/user"
  local unit_file="$unit_dir/${SERVICE_NAME}.service"
  mkdir -p "$unit_dir"
  cat > "$unit_file" <<EOF
[Unit]
Description=moorhen background agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DEST/$BINARY_NAME
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
  if ! systemctl --user daemon-reload 2>/dev/null; then
    warn "systemd --user manager unreachable (no session bus); unit written to $unit_file but not enabled"
    warn "on WSL, enable 'systemd=true' under [boot] in /etc/wsl.conf, run 'wsl --shutdown', then re-run with --force"
    return 0
  fi
  systemctl --user enable --now "${SERVICE_NAME}.service"
  if command -v loginctl >/dev/null 2>&1; then
    if loginctl enable-linger "$USER" 2>/dev/null; then
      ok "lingering enabled — service also starts at boot, not just at login"
    else
      warn "could not enable lingering (needs polkit/root); service starts on login sessions only"
    fi
  fi
  ok "systemd --user service installed and started: $unit_file"
}

install_service_macos() {
  local plist_dir="$HOME/Library/LaunchAgents"
  local plist="$plist_dir/${SERVICE_LABEL}.plist"
  local log_dir="$HOME/Library/Logs/$BINARY_NAME"
  mkdir -p "$plist_dir" "$log_dir"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$SERVICE_LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$DEST/$BINARY_NAME</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$log_dir/stdout.log</string>
  <key>StandardErrorPath</key><string>$log_dir/stderr.log</string>
</dict>
</plist>
EOF
  local uid; uid=$(id -u)
  launchctl bootout "gui/$uid/$SERVICE_LABEL" >/dev/null 2>&1 || true
  if launchctl bootstrap "gui/$uid" "$plist" 2>/dev/null; then
    launchctl kickstart -k "gui/$uid/$SERVICE_LABEL" 2>/dev/null || true
  else
    launchctl unload "$plist" 2>/dev/null || true
    if ! launchctl load -w "$plist" 2>/dev/null; then
      warn "launchctl load failed; plist written to $plist but not loaded — load it manually"
      return 0
    fi
  fi
  ok "launchd agent installed and started: $plist"
}

install_service() {
  if [ "$NO_SERVICE" = 1 ]; then info "skipping service setup (--no-service)"; return 0; fi
  case "$OS" in
    linux)  install_service_linux ;;
    darwin) install_service_macos ;;
  esac
}

uninstall_service() {
  case "$OS" in
    linux)
      if command -v systemctl >/dev/null 2>&1; then
        systemctl --user disable --now "${SERVICE_NAME}.service" 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/${SERVICE_NAME}.service"
        systemctl --user daemon-reload 2>/dev/null || true
      fi
      ;;
    darwin)
      local uid plist
      uid=$(id -u)
      plist="$HOME/Library/LaunchAgents/${SERVICE_LABEL}.plist"
      launchctl bootout "gui/$uid/$SERVICE_LABEL" >/dev/null 2>&1 || launchctl unload "$plist" >/dev/null 2>&1 || true
      rm -f "$plist"
      ;;
  esac
}

uninstall() {
  detect_platform
  uninstall_service
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME, removed the background service and shell completions"
  exit 0
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
main() {
  if [ "$DO_UNINSTALL" = 1 ]; then
    uninstall
  fi

  detect_platform
  TMP=$(mktemp -d "${TMPDIR:-/tmp}/moorhen-install.XXXXXX")
  trap cleanup EXIT

  preflight

  if [ -n "$OFFLINE_TARBALL" ]; then
    install_offline
  else
    acquire_lock "${TMPDIR:-/tmp}/.moorhen-install.lock" 120 \
      || { err "could not acquire install lock (another install in progress?)"; exit 1; }
    resolve_version
    if [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" = "$VERSION" ] && [ "$FORCE" = 0 ]; then
      ok "moorhen $VERSION already installed at $DEST/$BINARY_NAME"
    else
      download_and_install
    fi
  fi

  install_completions
  install_service

  local service_line
  if [ "$NO_SERVICE" = 1 ]; then service_line="skipped (--no-service)"; else service_line="started, enabled on login"; fi

  draw_box 42 \
    "moorhen $VERSION installed" \
    "" \
    "binary:      $DEST/$BINARY_NAME" \
    "service:     $service_line" \
    "completions: bash/zsh/fish" \
    "" \
    "uninstall:   curl -fsSL https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh | bash -s -- --uninstall"

  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *) warn "$DEST is not on PATH — add: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# flag parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --version)      VERSION="$2"; shift 2 ;;
    --version=*)    VERSION="${1#*=}"; shift ;;
    --dest)         DEST="$2"; shift 2 ;;
    --dest=*)       DEST="${1#*=}"; shift ;;
    --force)        FORCE=1; shift ;;
    --no-service)   NO_SERVICE=1; shift ;;
    --no-verify)    NO_VERIFY=1; shift ;;
    --offline)      OFFLINE_TARBALL="$2"; shift 2 ;;
    --offline=*)    OFFLINE_TARBALL="${1#*=}"; shift ;;
    --quiet)        QUIET=1; shift ;;
    --no-color)     NO_COLOR=1; shift ;;
    --no-gum)       NO_GUM=1; shift ;;
    --uninstall)    DO_UNINSTALL=1; shift ;;
    -h|--help)      print_help; exit 0 ;;
    *) echo "unknown flag: $1" >&2; print_help >&2; exit 1 ;;
  esac
done

main