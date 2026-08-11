#!/usr/bin/env bash
#
# flowctl installer
# ------------------
# Installs the `flowctl` CLI (https://github.com/acme/flowctl) from a prebuilt
# release binary, falling back to a from-source build when no prebuilt is
# available for your platform.
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/flowctl/main/install.sh?$(date +%s)" | bash
#
# Flags (all also settable as env vars, see below):
#   --version VERSION        install a specific version           (VERSION)
#   --daemon                 also register flowctl-sync as a background
#                             service (systemd --user on Linux, launchd
#                             LaunchAgent on macOS), started on login
#   --prefix DIR              install destination (default: ~/.local/bin)
#   --force                  reinstall even if already up to date
#   --build-from-source      consent to installing a Rust toolchain and
#                             building locally                      (BUILD_FROM_SOURCE=1)
#   --offline TARBALL        install from a local tarball, no network calls
#   --uninstall              remove flowctl, its completions, and any
#                             registered background service
#   --verify                 run a self-test against the installed binary
#   --easy-mode              append the install dir to your shell rc if
#                             it's not already on PATH
#   --no-verify              skip SHA256 checksum verification (not recommended)
#   --quiet                  only print errors
#   --no-color / --no-gum    disable styled/gum output (also honors NO_COLOR)
#   -h, --help               show this help and exit
#
# Env vars: HTTPS_PROXY / HTTP_PROXY / NO_PROXY, NO_COLOR, QUIET,
#           BUILD_FROM_SOURCE, FLOWCTL_INSTALL_DIR

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="flowctl"
BINARY_NAME="flowctl"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/\.github/workflows/release\.ya?ml@refs/tags/v.*$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
SYSTEMD_UNIT_NAME="flowctl-sync.service"
LAUNCHD_LABEL="com.acme.flowctl.sync"
LAUNCHD_PLIST_NAME="${LAUNCHD_LABEL}.plist"

DEST="${FLOWCTL_INSTALL_DIR:-$HOME/.local/bin}"
VERSION="${VERSION:-}"
FORCE=0
DAEMON=0
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
OFFLINE_TARBALL=""
DO_UNINSTALL=0
DO_VERIFY=0
EASY_MODE=0
NO_VERIFY=0
QUIET="${QUIET:-0}"
NO_GUM=0
FROM_SOURCE=0
TMP=""
LOCK_HELD=""

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && NO_GUM=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

# ---------------------------------------------------------------------------
# Cleanup / locking
# ---------------------------------------------------------------------------
cleanup() {
  local rc=$?
  [ -n "$LOCK_HELD" ] && rm -rf "$LOCK_HELD" 2>/dev/null || true
  [ -n "$TMP" ] && rm -rf "$TMP" 2>/dev/null || true
  return $rc
}
TMP="$(mktemp -d "${TMPDIR:-/tmp}/flowctl-install.XXXXXX")"
trap cleanup EXIT

acquire_lock() { # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    (( $(date +%s) - start >= w )) && return 1
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD="$d"
}

# ---------------------------------------------------------------------------
# Usage / flags
# ---------------------------------------------------------------------------
usage() { sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --daemon) DAEMON=1; shift ;;
    --prefix) DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --build-from-source) BUILD_FROM_SOURCE=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    --verify) DO_VERIFY=1; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "unknown flag: $1"; usage; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
OS=""; ARCH=""; TARGET=""
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z'); ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — systemd --user daemon support depends on your distro's WSL systemd config"
  fi
}

# ---------------------------------------------------------------------------
# Proxy
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# Version resolution — 5-tier
# ---------------------------------------------------------------------------
resolve_version() {
  [[ -n "$VERSION" ]] && return 0                                          # 1. CLI flag/env
  [[ -f Cargo.toml ]] && VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  [[ -n "$VERSION" ]] && return 0                                          # 2. manifest
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0                                          # 3. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"                       # 4. redirect  5. hardcoded
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install dir: $DEST"; exit 1; }
  [[ -w "$DEST" ]] || { err "no write permission on $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    err "less than 50MB free at $DEST"; exit 1
  fi

  if [[ -x "$DEST/$BINARY_NAME" && "$FORCE" != 1 ]]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [[ -n "$cur" && "$cur" == "$VERSION" ]]; then
      ok "flowctl $VERSION already installed at $DEST — reconfiguring daemon only"
      SKIP_DOWNLOAD=1
      return 0
    fi
  fi
  SKIP_DOWNLOAD=0

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || { err "cannot reach github.com — check network/proxy, or use --offline TARBALL"; exit 1; }
  fi
}

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
verify_checksum() { # $1=file $2=expected
  local a
  if [[ -z "$2" ]]; then warn "no expected checksum available; skipping"; return 0; fi
  if [[ "$NO_VERIFY" == 1 ]]; then warn "--no-verify passed; skipping checksum"; return 0; fi
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool; skipping checksum"; return 0; fi
  [[ "$a" == "$2" ]] && { ok "SHA256 verified"; return 0; } || { err "checksum mismatch (want $2 got $a)"; return 1; }
}

verify_sigstore() { # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign absent; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no sigstore bundle; skipping"; return 0; }
  cosign verify-blob --bundle "$TMP/sig.json" \
    --certificate-identity-regexp "$COSIGN_ID_RE" \
    --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null \
    && { ok "signature verified"; return 0; } || { err "Sigstore verification FAILED"; return 1; }
}

fetch_checksum() { # $1=artifact_url -> echoes sha256 or empty
  curl -fsSL "${PROXY_ARGS[@]}" "$1.sha256" 2>/dev/null | awk '{print $1}'
}

# ---------------------------------------------------------------------------
# Extract + install
# ---------------------------------------------------------------------------
extract_and_install() { # $1=archive
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

# ---------------------------------------------------------------------------
# Build from source
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  if [[ "$BUILD_FROM_SOURCE" == 1 ]]; then return 0; fi
  if [[ -t 0 ]]; then
    read -r -p "No prebuilt binary is available. Install a Rust toolchain and build from source? [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]] && return 0
    err "declined build-from-source"; exit 1
  fi
  err "no prebuilt binary and not running interactively; re-run with --build-from-source or BUILD_FROM_SOURCE=1"
  exit 1
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    info "installing rustup toolchain (minimal profile)"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal --no-modify-path
    # shellcheck disable=SC1090
    source "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  install -m 0755 "$src/target/release/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Download — 4-tier fallback → source
# ---------------------------------------------------------------------------
download_and_install() {
  if [[ "$FROM_SOURCE" == 1 ]]; then
    confirm_build_from_source
    build_from_source
    return 0
  fi
  local url sha bundle
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      sha=$(fetch_checksum "$url")
      bundle="$url.sigstore"
      if verify_checksum "$TMP/artifact.tar.gz" "$sha" && verify_sigstore "$TMP/artifact.tar.gz" "$bundle"; then
        extract_and_install "$TMP/artifact.tar.gz" && return 0
      fi
      rm -f "$TMP/artifact.tar.gz"
    fi
  done
  warn "no prebuilt binary reachable; falling back to source build"
  confirm_build_from_source
  build_from_source
}

# ---------------------------------------------------------------------------
# Shell completions (XDG)
# ---------------------------------------------------------------------------
install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "shell completions installed"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
      warn "$DEST is not on your PATH"
      if [[ "$EASY_MODE" == 1 ]]; then
        local rc="$HOME/.bashrc"
        [[ -n "${ZSH_VERSION:-}" ]] && rc="$HOME/.zshrc"
        echo "export PATH=\"$DEST:\$PATH\"" >> "$rc"
        ok "appended PATH export to $rc (restart your shell)"
      else
        info "add this to your shell rc, or re-run with --easy-mode:  export PATH=\"$DEST:\$PATH\""
      fi
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Background daemon (systemd --user / launchd)
# ---------------------------------------------------------------------------
install_service() {
  [[ "$DAEMON" == 1 ]] || return 0
  case "$OS" in
    linux)
      if ! command -v systemctl >/dev/null 2>&1; then
        warn "systemctl not found; skipping daemon registration"
        return 0
      fi
      local unit_dir="$HOME/.config/systemd/user"
      mkdir -p "$unit_dir"
      cat > "$unit_dir/$SYSTEMD_UNIT_NAME" <<EOF
[Unit]
Description=flowctl background sync daemon

[Service]
ExecStart=$DEST/$BINARY_NAME sync --daemon
Restart=on-failure

[Install]
WantedBy=default.target
EOF
      systemctl --user daemon-reload
      systemctl --user enable --now "$SYSTEMD_UNIT_NAME" \
        && ok "registered and started systemd --user service: $SYSTEMD_UNIT_NAME" \
        || warn "installed unit but failed to start it; check: systemctl --user status $SYSTEMD_UNIT_NAME"
      loginctl enable-linger "$USER" 2>/dev/null || true
      ;;
    darwin)
      local plist_dir="$HOME/Library/LaunchAgents"
      mkdir -p "$plist_dir"
      cat > "$plist_dir/$LAUNCHD_PLIST_NAME" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LAUNCHD_LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$DEST/$BINARY_NAME</string><string>sync</string><string>--daemon</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
EOF
      launchctl unload "$plist_dir/$LAUNCHD_PLIST_NAME" 2>/dev/null || true
      launchctl load -w "$plist_dir/$LAUNCHD_PLIST_NAME" \
        && ok "registered and started launchd agent: $LAUNCHD_LABEL" \
        || warn "installed plist but failed to load it; check: launchctl list | grep $LAUNCHD_LABEL"
      ;;
    *)
      warn "no daemon support for $OS; skipping"
      ;;
  esac
}

uninstall_service() {
  local removed=0
  local unit_dir="$HOME/.config/systemd/user"
  if [[ -f "$unit_dir/$SYSTEMD_UNIT_NAME" ]]; then
    if command -v systemctl >/dev/null 2>&1; then
      systemctl --user disable --now "$SYSTEMD_UNIT_NAME" 2>/dev/null || true
    fi
    rm -f "$unit_dir/$SYSTEMD_UNIT_NAME"
    command -v systemctl >/dev/null 2>&1 && systemctl --user daemon-reload 2>/dev/null || true
    removed=1
  fi

  local plist_dir="$HOME/Library/LaunchAgents"
  if [[ -f "$plist_dir/$LAUNCHD_PLIST_NAME" ]]; then
    launchctl unload "$plist_dir/$LAUNCHD_PLIST_NAME" 2>/dev/null || true
    rm -f "$plist_dir/$LAUNCHD_PLIST_NAME"
    removed=1
  fi

  if [[ "$removed" == 1 ]]; then
    ok "background sync service unregistered"
  else
    info "no background service was registered; nothing to remove"
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Summary box
# ---------------------------------------------------------------------------
draw_box() { # $1=color, rest=lines
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

print_uninstall_instructions() {
  local svc="none"
  [[ -f "$HOME/.config/systemd/user/$SYSTEMD_UNIT_NAME" ]] && svc="$SYSTEMD_UNIT_NAME (systemd --user)"
  [[ -f "$HOME/Library/LaunchAgents/$LAUNCHD_PLIST_NAME" ]] && svc="$LAUNCHD_LABEL (launchd)"
  draw_box 244 \
    "\033[1mUninstall\033[0m" \
    "curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall" \
    "binary:       $DEST/$BINARY_NAME" \
    "completions:  bash/zsh/fish under XDG data/config dirs" \
    "service:      $svc"
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
do_uninstall() {
  info "uninstalling $BINARY_NAME"
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"

  if declare -F uninstall_service >/dev/null; then uninstall_service; fi

  draw_box 42 \
    "\033[1m$BINARY_NAME uninstalled\033[0m" \
    "binary removed:        $DEST/$BINARY_NAME" \
    "completions removed:   bash/zsh/fish" \
    "service:                (checked and removed if present)"
  ok "uninstall complete"
  exit 0
}

# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
do_verify() {
  [[ -x "$DEST/$BINARY_NAME" ]] || { err "$BINARY_NAME not found at $DEST"; exit 1; }
  local v
  v=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null) || { err "$BINARY_NAME --version failed"; exit 1; }
  ok "self-test passed: $v"
  exit 0
}

# ---------------------------------------------------------------------------
# Offline install
# ---------------------------------------------------------------------------
do_offline_install() {
  [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  info "installing from local tarball (offline mode, no network calls)"
  local sha_file="$OFFLINE_TARBALL.sha256"
  local expected=""
  [[ -f "$sha_file" ]] && expected=$(awk '{print $1}' "$sha_file")
  verify_checksum "$OFFLINE_TARBALL" "$expected"
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  detect_platform

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    do_uninstall
  fi

  if [[ "$DO_VERIFY" == 1 ]]; then
    do_verify
  fi

  acquire_lock "${TMPDIR:-/tmp}/flowctl-install.lock" 2400 \
    || { err "could not acquire install lock (another install in progress?)"; exit 1; }

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    preflight
    do_offline_install
  else
    resolve_version
    preflight
    if [[ "${SKIP_DOWNLOAD:-0}" != 1 ]]; then
      download_and_install
    fi
  fi

  install_completions
  check_path
  install_service

  local svc_line="disabled (default install)"
  [[ "$DAEMON" == 1 ]] && svc_line="enabled — starts on login"

  draw_box 42 \
    "\033[1mflowctl $VERSION installed\033[0m" \
    "binary:       $DEST/$BINARY_NAME" \
    "completions:  bash/zsh/fish (XDG paths)" \
    "daemon:       $svc_line"

  print_uninstall_instructions
  ok "done"
}

main "$@"