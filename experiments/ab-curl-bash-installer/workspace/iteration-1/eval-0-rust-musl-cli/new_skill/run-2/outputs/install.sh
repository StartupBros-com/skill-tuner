#!/usr/bin/env bash
#
# redlens installer
# https://github.com/hovlabs/redlens
#
# Usage (README one-liner, cache-busted so proxies/CDNs don't serve a stale copy):
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/redlens/main/install.sh?$(date +%s)" | bash
#
# Passing flags through a pipe (use -s --):
#   curl -fsSL https://raw.githubusercontent.com/hovlabs/redlens/main/install.sh | bash -s -- --version 1.4.0
#
# Flags:
#   --version VERSION   install a specific version (default: latest release)
#   --prefix DIR        install directory (default: $HOME/.local/bin); --dest is an alias
#   --force             reinstall even if the requested version is already present
#   --no-verify         skip SHA256 checksum verification (not recommended)
#   --offline TARBALL   install from a local tarball, no network access
#                        (needs TARBALL.sha256 alongside it, unless --no-verify)
#   --easy-mode         append the install directory to PATH in your shell rc
#   --uninstall         remove the installed binary and shell completions
#   --quiet             suppress non-error output
#   --no-color          disable ANSI colors
#   --no-gum            disable gum styling even if gum is installed
#   -h, --help          show this help and exit
#
# Environment:
#   REDLENS_VERSION       same as --version
#   REDLENS_INSTALL_DIR   same as --prefix
#   HTTPS_PROXY / HTTP_PROXY   used for every network call
#   NO_COLOR              same as --no-color

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OWNER="hovlabs"
REPO="redlens"
BINARY_NAME="redlens"

COSIGN_ID_RE='^https://github\.com/hovlabs/redlens/'
COSIGN_ISSUER='https://token.actions.githubusercontent.com'

XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
BASH_COMPLETION_DIR="$XDG_DATA_HOME/bash-completion/completions"
ZSH_COMPLETION_DIR="$XDG_DATA_HOME/zsh/site-functions"

LOCKFILE="${TMPDIR:-/tmp}/.${BINARY_NAME}-install-$(id -u).lock"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

VERSION="${REDLENS_VERSION:-}"
DEST="${REDLENS_INSTALL_DIR:-$HOME/.local/bin}"
FORCE=0
QUIET=0
NO_COLOR_FLAG=0
NO_GUM=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
ACTION="install"

TARGET=""
FROM_SOURCE=0
INSTALL_METHOD="prebuilt"
PROXY_ARGS=()
LOCK_DIR=""
BACKUP_PATH=""
EXTRACT_DIR=""
TMP=""

HAS_GUM=0
NO_GUM_EFFECTIVE=0
PLAIN=0
[ -t 1 ] || PLAIN=1

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR + non-TTY
# ---------------------------------------------------------------------------

_log() {
  [ "${QUIET:-0}" = 1 ] && [ "$1" != err ] && return 0
  local level="$1" color="$2" glyph="$3"
  shift 3
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM_EFFECTIVE:-0}" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$PLAIN" = 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39 '->' "$@"; }
ok()   { _log ok   42 '✓'  "$@"; }
warn() { _log warn 214 '⚠' "$@"; }
err()  { _log err  196 '✗' "$@" 1>&2; }

configure_output() {
  command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
  { [ -n "${NO_COLOR:-}" ] || [ "$NO_COLOR_FLAG" = 1 ] || [ ! -t 1 ]; } && PLAIN=1
  [ "$PLAIN" = 1 ] && NO_GUM_EFFECTIVE=1
  [ "$NO_GUM" = 1 ] && NO_GUM_EFFECTIVE=1
}

run_with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 1 "$@"
  else
    "$@"
  fi
}

draw_box() {
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

# ---------------------------------------------------------------------------
# Cleanup / locking
# ---------------------------------------------------------------------------

cleanup() {
  local ec=$?
  [[ -n "${TMP:-}" && -d "$TMP" ]] && rm -rf "$TMP"
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR"
  exit "$ec"
}

acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    if { exec 9>>"$lf"; } 2>/dev/null; then
      if flock -w "$w" 9; then
        return 0
      else
        return 1
      fi
    fi
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
  return 0
}

# ---------------------------------------------------------------------------
# Platform / proxy
# ---------------------------------------------------------------------------

detect_platform() {
  local os arch
  os=$(uname -s | tr 'A-Z' 'a-z')
  arch=$(uname -m)
  case "$arch" in
    x86_64|amd64) arch=x86_64 ;;
    arm64|aarch64) arch=aarch64 ;;
  esac
  case "${os}-${arch}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${os}/${arch}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$os" == "linux" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — PATH and completions setup may need extra manual steps"
  fi
}

setup_proxy() {
  PROXY_ARGS=()
  if [[ -n "${HTTPS_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

preflight() {
  info "running preflight checks..."
  local need_kb=20480
  [[ "$FROM_SOURCE" -eq 1 ]] && need_kb=524288
  local parent="$DEST"
  while [[ ! -d "$parent" ]]; do parent="$(dirname "$parent")"; done
  local avail_kb
  avail_kb=$(df -Pk "$parent" 2>/dev/null | awk 'NR==2 {print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt "$need_kb" ]]; then
    err "insufficient disk space at $parent (need ~$((need_kb/1024))MB, have $((avail_kb/1024))MB)"
    exit 1
  fi
  mkdir -p "$DEST" 2>/dev/null || true
  if [[ ! -w "$DEST" ]]; then
    err "no write permission for $DEST — pass --prefix DIR to choose a writable location"
    exit 1
  fi
  if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
    warn "could not reach github.com; network-dependent steps may fail (use --offline TARBALL for airgapped installs)"
  fi
}

preflight_local_only() {
  mkdir -p "$DEST" 2>/dev/null || true
  if [[ ! -w "$DEST" ]]; then
    err "no write permission for $DEST — pass --prefix DIR to choose a writable location"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — CLI/env, manifest, GitHub API, redirect
# ---------------------------------------------------------------------------

resolve_version() {
  [[ -n "$VERSION" ]] && { info "using requested version $VERSION"; return 0; }

  if [[ -f Cargo.toml ]]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml 2>/dev/null) || true
  fi
  [[ -n "$VERSION" ]] && { info "resolved version $VERSION from Cargo.toml"; return 0; }

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [[ -n "$VERSION" ]] && { info "resolved version $VERSION from GitHub API"; return 0; }

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [[ -n "$VERSION" ]] && { info "resolved version $VERSION from release redirect"; return 0; }

  err "could not resolve a version automatically; pass --version X.Y.Z"
  exit 1
}

check_existing_install() {
  SKIP_INSTALL=0
  if [[ -x "$DEST/$BINARY_NAME" && "$FORCE" -ne 1 ]]; then
    local cur
    cur=$(run_with_timeout "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
    if [[ -n "$cur" && "$cur" == "$VERSION" ]]; then
      SKIP_INSTALL=1
    fi
  fi
}

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

verify_checksum() {
  local file="$1" expected="$2" actual
  if [[ "$NO_VERIFY" -eq 1 ]]; then
    warn "--no-verify: skipping checksum verification for $(basename "$file")"
    return 0
  fi
  if [[ -z "$expected" ]]; then
    err "no expected SHA256 available for $(basename "$file")"
    return 1
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no SHA256 tool available; skipping checksum verification"
    return 0
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  else
    err "checksum mismatch for $(basename "$file") (want $expected, got $actual)"
    return 1
  fi
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle at $bundle_url; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore verification FAILED for $(basename "$file")"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Download / build / install
# ---------------------------------------------------------------------------

extract_and_install() {
  local archive="$1"
  rm -rf "$TMP/extract"
  mkdir -p "$TMP/extract"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP/extract" ;;
    *) err "unsupported archive format: $archive"; return 1 ;;
  esac
  EXTRACT_DIR="$TMP/extract"
  local bin
  bin=$(find "$TMP/extract" -type f -name "$BINARY_NAME" | head -1)
  if [[ -z "$bin" ]]; then
    err "binary '$BINARY_NAME' not found in archive"
    return 1
  fi
  install_binary_atomic "$bin"
  return 0
}

install_binary_atomic() {
  local src="$1" tmp_dest
  if [[ -x "$DEST/$BINARY_NAME" ]]; then
    local backup="$DEST/$BINARY_NAME.bak.$(date +%Y%m%d%H%M%S).$$"
    cp "$DEST/$BINARY_NAME" "$backup" 2>/dev/null && BACKUP_PATH="$backup"
  fi
  tmp_dest="$DEST/.$BINARY_NAME.tmp.$$"
  install -m 0755 "$src" "$tmp_dest"
  mv -f "$tmp_dest" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME $VERSION -> $DEST/$BINARY_NAME"
}

download_and_install() {
  local ok_dl=0
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/download/$VERSION/$REPO-$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$VERSION-$TARGET.tar.gz"
  )
  local url
  for url in "${urls[@]}"; do
    info "downloading $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      local expected=""
      if curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" -o "$TMP/artifact.tar.gz.sha256" 2>/dev/null; then
        expected=$(awk '{print $1}' "$TMP/artifact.tar.gz.sha256")
      fi
      if verify_checksum "$TMP/artifact.tar.gz" "$expected"; then
        if ! verify_sigstore "$TMP/artifact.tar.gz" "${url}.sigstore.json"; then
          err "aborting install due to signature verification failure"
          exit 1
        fi
        if extract_and_install "$TMP/artifact.tar.gz"; then
          ok_dl=1
          break
        fi
      fi
    fi
  done
  if [[ "$ok_dl" -ne 1 ]]; then
    warn "no verified prebuilt binary found for $TARGET; falling back to build from source"
    build_from_source
  fi
}

build_from_source() {
  INSTALL_METHOD="source"
  info "building $BINARY_NAME from source ($VERSION)..."
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup default stable >/dev/null 2>&1 || true
    else
      info "installing rustup toolchain..."
      curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable >/dev/null
      [[ -f "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
    fi
  fi
  command -v cargo >/dev/null 2>&1 || { err "cargo unavailable; cannot build from source"; exit 1; }
  local src_dir="$TMP/src"
  rm -rf "$src_dir"
  if ! git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src_dir" 2>/dev/null; then
    rm -rf "$src_dir"
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src_dir"
  fi
  ( cd "$src_dir" && cargo build --release )
  local bin="$src_dir/target/release/$BINARY_NAME"
  [[ -x "$bin" ]] || { err "build did not produce $BINARY_NAME"; exit 1; }
  install_binary_atomic "$bin"
  warn "shell completions are only shipped in prebuilt tarballs; skipping completions install"
}

install_offline() {
  local archive="$1"
  INSTALL_METHOD="offline"
  [[ -f "$archive" ]] || { err "offline tarball not found: $archive"; exit 1; }
  info "installing from local tarball (offline, no network): $archive"
  detect_platform || true
  preflight_local_only
  local expected=""
  if [[ -f "$archive.sha256" ]]; then
    expected=$(awk '{print $1}' "$archive.sha256")
  fi
  if ! verify_checksum "$archive" "$expected"; then
    exit 1
  fi
  extract_and_install "$archive" || exit 1
  install_completions
  path_check
}

# ---------------------------------------------------------------------------
# Completions / PATH
# ---------------------------------------------------------------------------

install_completions() {
  [[ -n "${EXTRACT_DIR:-}" && -d "$EXTRACT_DIR/completions" ]] || return 0
  mkdir -p "$BASH_COMPLETION_DIR" "$ZSH_COMPLETION_DIR"
  local bash_src zsh_src
  bash_src=$(find "$EXTRACT_DIR/completions" -type f -iname "*.bash" | head -1)
  zsh_src=$(find "$EXTRACT_DIR/completions" -type f \( -iname "_*" -o -iname "*.zsh" \) | head -1)
  if [[ -n "$bash_src" ]]; then
    cp "$bash_src" "$BASH_COMPLETION_DIR/$BINARY_NAME"
    ok "bash completions -> $BASH_COMPLETION_DIR/$BINARY_NAME"
  fi
  if [[ -n "$zsh_src" ]]; then
    cp "$zsh_src" "$ZSH_COMPLETION_DIR/_$BINARY_NAME"
    ok "zsh completions -> $ZSH_COMPLETION_DIR/_$BINARY_NAME"
  fi
}

path_check() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [[ "$EASY_MODE" -eq 1 ]]; then
    local rc
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      *) rc="$HOME/.profile" ;;
    esac
    if ! grep -qF "$DEST" "$rc" 2>/dev/null; then
      printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
      warn "added $DEST to PATH in $rc — restart your shell or run: source $rc"
    fi
  else
    warn "$DEST is not on your PATH. Add it with:"
    warn "  export PATH=\"$DEST:\$PATH\""
    warn "or re-run with --easy-mode to do this automatically."
  fi
}

# ---------------------------------------------------------------------------
# Uninstall / summary
# ---------------------------------------------------------------------------

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "$BASH_COMPLETION_DIR/$BINARY_NAME" "$ZSH_COMPLETION_DIR/_$BINARY_NAME"
  ok "uninstalled $BINARY_NAME"
}

finish() {
  local installed_version
  installed_version=$(run_with_timeout "$DEST/$BINARY_NAME" --version 2>/dev/null | head -1) || true
  [[ -n "$installed_version" ]] || installed_version="$VERSION"
  local lines=(
    "\033[1mredlens\033[0m installed successfully"
    "  binary:   $DEST/$BINARY_NAME"
    "  version:  $installed_version"
    "  method:   ${INSTALL_METHOD} (${TARGET:-n/a})"
  )
  [[ -n "$BACKUP_PATH" ]] && lines+=("  backup:   $BACKUP_PATH")
  [[ -f "$BASH_COMPLETION_DIR/$BINARY_NAME" ]] && lines+=("  bash comp: $BASH_COMPLETION_DIR/$BINARY_NAME")
  [[ -f "$ZSH_COMPLETION_DIR/_$BINARY_NAME" ]] && lines+=("  zsh comp:  $ZSH_COMPLETION_DIR/_$BINARY_NAME")
  echo
  draw_box 42 "${lines[@]}"
  echo
  info "uninstall: curl -fsSL https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh | bash -s -- --uninstall"
  info "   manual: rm -f $DEST/$BINARY_NAME $BASH_COMPLETION_DIR/$BINARY_NAME $ZSH_COMPLETION_DIR/_$BINARY_NAME"
}

show_help() {
  cat <<EOF
redlens installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash
  curl -fsSL https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh | bash -s -- [flags]

Flags:
  --version VERSION   install a specific version (default: latest release)
  --prefix DIR        install directory (default: \$HOME/.local/bin); --dest is an alias
  --force             reinstall even if the requested version is already present
  --no-verify         skip SHA256 checksum verification (not recommended)
  --offline TARBALL   install from a local tarball, no network access
                       (needs TARBALL.sha256 alongside it, unless --no-verify)
  --easy-mode         append the install directory to PATH in your shell rc
  --uninstall         remove the installed binary and shell completions
  --quiet             suppress non-error output
  --no-color          disable ANSI colors
  --no-gum            disable gum styling even if gum is installed
  -h, --help          show this help and exit

Environment:
  REDLENS_VERSION       same as --version
  REDLENS_INSTALL_DIR   same as --prefix
  HTTPS_PROXY / HTTP_PROXY   used for every network call
  NO_COLOR              same as --no-color
EOF
}

# ---------------------------------------------------------------------------
# Args / main
# ---------------------------------------------------------------------------

parse_args() {
  ACTION="install"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version)
        [[ $# -ge 2 ]] || { err "--version requires an argument"; exit 1; }
        VERSION="$2"; shift 2 ;;
      --version=*) VERSION="${1#*=}"; shift ;;
      --prefix|--dest)
        [[ $# -ge 2 ]] || { err "$1 requires an argument"; exit 1; }
        DEST="$2"; shift 2 ;;
      --prefix=*) DEST="${1#*=}"; shift ;;
      --dest=*) DEST="${1#*=}"; shift ;;
      --offline)
        [[ $# -ge 2 ]] || { err "--offline requires a tarball path"; exit 1; }
        OFFLINE_TARBALL="$2"; shift 2 ;;
      --offline=*) OFFLINE_TARBALL="${1#*=}"; shift ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --uninstall) ACTION="uninstall"; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR_FLAG=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      -h|--help) show_help; exit 0 ;;
      *) err "unknown flag: $1"; show_help; exit 1 ;;
    esac
  done
}

main() {
  parse_args "$@"
  configure_output

  if [[ "$ACTION" == "uninstall" ]]; then
    uninstall
    exit 0
  fi

  TMP="$(mktemp -d "${TMPDIR:-/tmp}/redlens-install.XXXXXX")"
  trap cleanup EXIT

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    install_offline "$OFFLINE_TARBALL"
    finish
    exit 0
  fi

  detect_platform
  setup_proxy
  preflight
  acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install may be running)"; exit 1; }

  resolve_version
  check_existing_install

  if [[ "$SKIP_INSTALL" -ne 1 ]]; then
    if [[ "$FROM_SOURCE" -eq 1 ]]; then
      build_from_source
    else
      download_and_install
    fi
  else
    ok "redlens $VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
  fi

  install_completions
  path_check
  finish
}

main "$@"