#!/usr/bin/env bash
#
# moorhen installer
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/moorhen/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION   install a specific version (default: latest release)
#   --prefix DIR        install directory (default: $HOME/.local/bin)
#   --force             reinstall/reconfigure even if this version is already installed
#   --no-verify         skip SHA256 checksum + Sigstore verification (NOT recommended)
#   --no-service        skip systemd/launchd service setup
#   --easy-mode         append the install dir to PATH in your shell rc if missing
#   --offline TARBALL   install from a local tarball, no network access
#   --uninstall         remove the binary, completions, and the background service
#   --quiet             errors only
#   --no-color          disable ANSI colors (also honors $NO_COLOR)
#   --no-gum            disable gum styling even if gum is installed
#   -h, --help          show this help and exit
#
# Env:
#   HTTPS_PROXY / HTTP_PROXY   used for every network call (NO_PROXY honored natively by curl)
#   MOORHEN_VERSION            same as --version
#   PREFIX                     same as --prefix
#
# Examples:
#   curl -fsSL .../install.sh | bash -s -- --version 1.4.2
#   curl -fsSL .../install.sh | bash -s -- --uninstall

set -euo pipefail
umask 022

OWNER="hovlabs"
REPO="moorhen"
BINARY_NAME="moorhen"
SERVICE_NAME="moorhen"                 # systemd --user unit name (no .service suffix)
SERVICE_LABEL="com.hovlabs.moorhen"    # launchd label
FALLBACK_VERSION="0.1.0"               # last-resort pin; bump alongside tagged releases
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/\.github/workflows/.*@refs/tags/.*\$"

QUIET=0
NO_COLOR="${NO_COLOR:-}"
NO_GUM=0
FORCE=0
NO_VERIFY=0
NO_SERVICE=0
EASY_MODE=0
OFFLINE=0
OFFLINE_TARBALL=""
DO_UNINSTALL=0
VERSION="${MOORHEN_VERSION:-}"
PREFIX="${PREFIX:-$HOME/.local/bin}"
PROXY_URL=""
HAS_GUM=0
CURRENT_VERSION=""
SERVICE_STATUS=""
SKIP_DOWNLOAD=0
TMP=""

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ -n "$NO_COLOR" ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

print_help() {
  sed -n '2,29p' "$0" | sed 's/^# \{0,1\}//'
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --version=*) VERSION="${1#*=}"; shift ;;
      --prefix) PREFIX="$2"; shift 2 ;;
      --prefix=*) PREFIX="${1#*=}"; shift ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --no-service) NO_SERVICE=1; shift ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --offline) OFFLINE=1; OFFLINE_TARBALL="${2:-}"; shift 2 ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      -h|--help) print_help; exit 0 ;;
      *) err "unknown flag: $1 (see --help)"; exit 1 ;;
    esac
  done
}

detect_platform() {
  local uname_s uname_m
  uname_s=$(uname -s)
  uname_m=$(uname -m)
  case "$uname_s" in
    Linux) OS=linux ;;
    Darwin) OS=darwin ;;
    *) err "unsupported OS: $uname_s"; exit 1 ;;
  esac
  case "$uname_m" in
    x86_64|amd64) ARCH=amd64 ;;
    arm64|aarch64) ARCH=arm64 ;;
    *) err "unsupported architecture: $uname_m"; exit 1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — systemd user services need systemd enabled in /etc/wsl.conf (https://learn.microsoft.com/windows/wsl/systemd); the installer continues regardless"
  fi
}

setup_proxy() {
  PROXY_URL="${HTTPS_PROXY:-${https_proxy:-}}"
  [ -z "$PROXY_URL" ] && PROXY_URL="${HTTP_PROXY:-${http_proxy:-}}"
}

resolve_version() {
  [ -n "$VERSION" ] && return 0                                             # 1. flag / env
  if [ -f VERSION ]; then VERSION=$(tr -d ' \t\n\r' < VERSION); fi          # 2. local VERSION file
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 ${PROXY_URL:+--proxy "$PROXY_URL"} \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | head -1 | sed -E 's/.*"v?([^"]+)".*/\1/')          # 3. GitHub API
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' ${PROXY_URL:+--proxy "$PROXY_URL"} \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')  # 4. redirect
  if [ -z "$VERSION" ]; then
    VERSION="$FALLBACK_VERSION"                                             # 5. hardcoded
    warn "could not resolve latest version from GitHub; falling back to v$FALLBACK_VERSION"
  fi
}

# checksums.txt is sha256sum-style: "<hex>  <filename>" per line, one optional leading '*'.
fetch_checksum() {
  local fname="$1" sums="$TMP/checksums.txt"
  if [ ! -f "$sums" ]; then
    curl -fsSL ${PROXY_URL:+--proxy "$PROXY_URL"} \
      "https://github.com/$OWNER/$REPO/releases/download/$TAG/checksums.txt" -o "$sums" 2>/dev/null || return 1
  fi
  awk -v f="$fname" '{ fn=$2; sub(/^\*/,"",fn); if (fn==f) { print $1; found=1 } } END { exit !found }' "$sums"
}

verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum verification"; return 0; fi
  if [ "$a" = "$2" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $a)"; return 1; fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  curl -fsSL ${PROXY_URL:+--proxy "$PROXY_URL"} "$2" -o "$TMP/sig.bundle" 2>/dev/null \
    || { warn "no Sigstore bundle at $2; skipping signature verification"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "signature verified"; return 0
  else
    err "Sigstore signature verification FAILED for $1"; return 1
  fi
}

verify_artifact() {  # $1=file $2=filename $3=source_url
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify set; skipping checksum and signature verification"
    return 0
  fi
  local expected
  expected=$(fetch_checksum "$2") || { warn "no checksums.txt entry for $2"; return 1; }
  verify_checksum "$1" "$expected" || return 1
  verify_sigstore "$1" "${3}.bundle" || return 1
  return 0
}

acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-600}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }; return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null && { rm -rf "$d"; continue; }
    [ $(( $(date +%s) - start )) -ge "$w" ] && return 1
    sleep 2
  done
  echo $$ > "$d/pid"
  trap 'rm -rf "'"$d"'"' EXIT
}

extract_and_install() {  # $1=archive
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$1" -C "$TMP" ;;
    *.zip) unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin; bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found inside archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME v$VERSION -> $DEST/$BINARY_NAME"
}

build_from_source() {
  warn "no prebuilt binary available for ${OS}/${ARCH}; building from source with 'go install'"
  command -v go >/dev/null 2>&1 || { err "go toolchain not found; install Go from https://go.dev/dl/ or download a release manually"; exit 1; }
  # assumes the module's CLI entrypoint lives at cmd/moorhen; adjust if the layout differs
  if ! GOBIN="$DEST" go install "github.com/${OWNER}/${REPO}/cmd/${BINARY_NAME}@${TAG}"; then
    err "go install failed"; exit 1
  fi
  ok "built and installed $BINARY_NAME v$VERSION -> $DEST/$BINARY_NAME (from source)"
}

download_and_install() {
  local candidates=(
    "https://github.com/$OWNER/$REPO/releases/download/$TAG/$ARTIFACT"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$ARTIFACT"
  )
  local alt_arch=""
  case "$ARCH" in amd64) alt_arch=x86_64 ;; arm64) alt_arch=aarch64 ;; esac
  if [ -n "$alt_arch" ]; then
    candidates+=("https://github.com/$OWNER/$REPO/releases/download/$TAG/${REPO}_${VERSION}_${OS}_${alt_arch}.tar.gz")
  fi

  local url
  for url in "${candidates[@]}"; do
    info "trying $url"
    if curl -fsSL ${PROXY_URL:+--proxy "$PROXY_URL"} "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      local fname="${url##*/}"
      if verify_artifact "$TMP/artifact.tar.gz" "$fname" "$url"; then
        extract_and_install "$TMP/artifact.tar.gz"
        return 0
      fi
      warn "verification failed for $fname; trying next source"
    fi
    rm -f "$TMP/artifact.tar.gz"
  done
  build_from_source
}

install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  if "$bin" completion bash >/dev/null 2>&1; then
    local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
    local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
    local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
    mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
    "$bin" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
    "$bin" completion zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
    "$bin" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
    ok "installed shell completions (bash/zsh/fish)"
  else
    warn "this build of $BINARY_NAME has no 'completion' subcommand; skipping"
  fi
}

install_systemd_service() {
  if ! command -v systemctl >/dev/null 2>&1; then
    warn "systemctl not found; start manually with: $DEST/$BINARY_NAME"
    SERVICE_STATUS="not configured (no systemd)"
    return 0
  fi
  local unit_dir="$HOME/.config/systemd/user"
  local unit="$unit_dir/${SERVICE_NAME}.service"
  mkdir -p "$unit_dir"
  cat > "$unit" <<EOF
[Unit]
Description=moorhen agent
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
  systemctl --user daemon-reload
  if systemctl --user enable --now "${SERVICE_NAME}.service" 2>/dev/null; then
    ok "systemd user service installed and started (${SERVICE_NAME}.service)"
    SERVICE_STATUS="running (systemd --user)"
    if command -v loginctl >/dev/null 2>&1 && ! loginctl show-user "$(id -un)" -p Linger 2>/dev/null | grep -q 'Linger=yes'; then
      info "service starts at login; to also run without an active login session: loginctl enable-linger $(id -un)"
    fi
  else
    warn "failed to enable/start the systemd user service; check: systemctl --user status ${SERVICE_NAME}.service"
    SERVICE_STATUS="install failed — see warning above"
  fi
}

install_launchd_service() {
  if ! command -v launchctl >/dev/null 2>&1; then
    warn "launchctl not found; start manually with: $DEST/$BINARY_NAME"
    SERVICE_STATUS="not configured (no launchd)"
    return 0
  fi
  local uid plist_dir plist
  uid=$(id -u)
  plist_dir="$HOME/Library/LaunchAgents"
  plist="$plist_dir/${SERVICE_LABEL}.plist"
  mkdir -p "$plist_dir" "$HOME/Library/Logs"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${SERVICE_LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>$DEST/$BINARY_NAME</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/${SERVICE_LABEL}.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/${SERVICE_LABEL}.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$uid/${SERVICE_LABEL}" >/dev/null 2>&1 || true
  if launchctl bootstrap "gui/$uid" "$plist" 2>/dev/null; then
    launchctl enable "gui/$uid/${SERVICE_LABEL}" 2>/dev/null || true
    launchctl kickstart -k "gui/$uid/${SERVICE_LABEL}" 2>/dev/null || true
  elif ! launchctl load -w "$plist" 2>/dev/null; then
    warn "failed to load launchd agent; check: launchctl list | grep moorhen"
    SERVICE_STATUS="install failed — see warning above"
    return 0
  fi
  ok "launchd agent installed and started (${SERVICE_LABEL})"
  SERVICE_STATUS="running (launchd)"
}

install_service() {
  if [ "$NO_SERVICE" = 1 ]; then
    info "--no-service set; skipping service setup"
    SERVICE_STATUS="not configured (--no-service)"
    return 0
  fi
  case "$OS" in
    linux) install_systemd_service ;;
    darwin) install_launchd_service ;;
    *) warn "no service integration for $OS; run $DEST/$BINARY_NAME manually"
       SERVICE_STATUS="not configured (unsupported OS)" ;;
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
      if [ -f "$plist" ]; then
        launchctl bootout "gui/$uid/${SERVICE_LABEL}" >/dev/null 2>&1 || launchctl unload "$plist" 2>/dev/null || true
        rm -f "$plist"
      fi
      ;;
  esac
}

uninstall() {
  uninstall_service
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME. Config left in place — remove manually if desired."
}

detect_shell_rc() {
  case "${SHELL:-}" in
    */zsh) echo "$HOME/.zshrc" ;;
    */fish) echo "$HOME/.config/fish/config.fish" ;;
    *) echo "$HOME/.bashrc" ;;
  esac
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
      warn "$DEST is not on your PATH"
      if [ "$EASY_MODE" = 1 ]; then
        local rc; rc=$(detect_shell_rc)
        printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
        ok "added $DEST to PATH in $rc (restart your shell or: source $rc)"
      else
        info "add it with: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

preflight() {
  info "running preflight checks"
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install directory $DEST"; exit 1; }
  [ -w "$DEST" ] || { err "install directory $DEST is not writable"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "less than 50MB free at $DEST"; exit 1
  fi

  if [ "$OFFLINE" != 1 ]; then
    curl -fsSL --connect-timeout 3 ${PROXY_URL:+--proxy "$PROXY_URL"} -o /dev/null https://github.com 2>/dev/null \
      || warn "could not reach github.com; network-dependent steps may fail"
  fi

  if [ -x "$DEST/$BINARY_NAME" ]; then
    CURRENT_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
    if [ -n "$CURRENT_VERSION" ]; then
      info "found existing install: v$CURRENT_VERSION"
      if [ "$CURRENT_VERSION" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
        ok "v$VERSION already installed at $DEST/$BINARY_NAME"
        SKIP_DOWNLOAD=1
      fi
    fi
  fi
}

draw_box() {  # $1=color, rest=lines
  local color="$1"; shift; local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); [ ${#s} -gt "$max" ] && max=${#s}; done
  local inner=$((max+4)) border="" i
  for ((i=0;i<inner;i++)); do border+="═"; done
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for l in "${lines[@]}"; do
    local s pad p=""
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    pad=$((max-${#s}))
    for ((i=0;i<pad;i++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

cleanup() {
  [ -n "$TMP" ] && rm -rf "$TMP"
}

main() {
  parse_args "$@"
  DEST="$PREFIX"

  if command -v gum >/dev/null 2>&1 && [ -t 1 ] && [ "$NO_GUM" != 1 ] && [ -z "$NO_COLOR" ]; then
    HAS_GUM=1
  fi

  detect_platform
  setup_proxy

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/moorhen-install.XXXXXX")
  trap cleanup EXIT

  if [ "$DO_UNINSTALL" = 1 ]; then
    uninstall
    exit 0
  fi

  if [ "$OFFLINE" = 1 ]; then
    VERSION="${VERSION:-offline}"
  else
    resolve_version
  fi
  VERSION="${VERSION#v}"
  TAG="v${VERSION}"
  ARTIFACT="${REPO}_${VERSION}_${OS}_${ARCH}.tar.gz"

  preflight

  local lock_dir="${XDG_CACHE_HOME:-$HOME/.cache}/moorhen"
  mkdir -p "$lock_dir"
  acquire_lock "$lock_dir/install.lock" 600 || { err "could not acquire install lock (another install running?)"; exit 1; }

  if [ "$SKIP_DOWNLOAD" != 1 ]; then
    if [ "$OFFLINE" = 1 ]; then
      [ -n "$OFFLINE_TARBALL" ] && [ -f "$OFFLINE_TARBALL" ] || { err "--offline requires an existing tarball path"; exit 1; }
      warn "offline mode: skipping checksum/signature verification"
      cp "$OFFLINE_TARBALL" "$TMP/artifact.tar.gz"
      extract_and_install "$TMP/artifact.tar.gz"
    else
      download_and_install
    fi
  fi

  install_completions
  install_service
  check_path

  echo
  draw_box 39 \
    "moorhen v$VERSION" \
    "" \
    "binary:      $DEST/$BINARY_NAME" \
    "service:     ${SERVICE_STATUS:-not configured}" \
    "completions: bash/zsh/fish (if supported by this build)"
  echo

  info "uninstall with: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "  (or re-run this script with --uninstall)"
}

main "$@"