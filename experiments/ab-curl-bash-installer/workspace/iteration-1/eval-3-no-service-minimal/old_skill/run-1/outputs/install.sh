#!/usr/bin/env bash
#
# quill installer — github.com/hovlabs/quill
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/quill/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION    install a specific version (default: latest)
#   --dest DIR            install directory (default: $HOME/.local/bin)
#   --offline TARBALL     install from a local tarball, no network calls (airgap mode)
#   --no-verify            skip SHA256 checksum verification
#   --force                 reinstall even if the target version is already installed
#   --quiet                 errors only
#   --no-color               disable ANSI color output
#   --no-gum                 disable gum styling (ANSI fallback)
#   --uninstall               remove quill and exit
#   -h, --help                 show this help
#
# Env:
#   QUILL_LOCAL_TARBALL   same as --offline TARBALL — set this for airgapped CI
#   HTTPS_PROXY / HTTP_PROXY   proxied downloads
#   NO_COLOR                    disable color output
#
# quill is a plain binary — this installer never registers a service, daemon,
# or background process, and never touches AI-agent hook configuration.

set -euo pipefail
umask 022

OWNER="hovlabs"
REPO="quill"
BINARY_NAME="quill"
FALLBACK_VERSION="0.1.0"   # bump when hovlabs/quill cuts its first tagged release

DEST="${DEST:-$HOME/.local/bin}"
VERSION="${VERSION:-}"
FORCE=0
QUIET=0
NO_VERIFY=0
NO_GUM=0
DO_UNINSTALL=0
OFFLINE_TARBALL="${QUILL_LOCAL_TARBALL:-}"

COSIGN_ID_RE="https://github.com/${OWNER}/${REPO}/\.github/workflows/release\.yml@refs/tags/.*"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

[ -n "${NO_COLOR:-}" ] && NO_GUM=1
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

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
err()  { _log err  196 '✗'  "$@" >&2; }

usage() {
  cat <<'EOF'
quill installer — github.com/hovlabs/quill

Usage: install.sh [options]

  --version VERSION    install a specific version (default: latest)
  --dest DIR            install directory (default: $HOME/.local/bin)
  --offline TARBALL     install from a local tarball, no network calls (airgap mode)
  --no-verify            skip SHA256 checksum verification
  --force                 reinstall even if the target version is already installed
  --quiet                 errors only
  --no-color               disable ANSI color output
  --no-gum                 disable gum styling (ANSI fallback)
  --uninstall               remove quill and exit
  -h, --help                 show this help

Env:
  QUILL_LOCAL_TARBALL   same as --offline TARBALL — set this for airgapped CI
  HTTPS_PROXY / HTTP_PROXY   proxied downloads
  NO_COLOR                    disable color output
EOF
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage ;;
    *) err "unknown flag: $1"; exit 1 ;;
  esac
done

TMP=""
LOCK_DIR=""
cleanup() {
  [ -n "$TMP" ] && rm -rf "$TMP"
  [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR"
}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")
trap cleanup EXIT

PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

OS="" ARCH="" TARGET="" FROM_SOURCE=0
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)  ARCH=x86_64 ;;
    arm64|aarch64) ARCH=aarch64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — quill installs fine; PATH/completions may need extra shell-rc config"
  fi
}

resolve_version() {
  [ -n "$VERSION" ] && return 0
  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"
}

preflight() {
  local avail=""
  avail=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}') || true
  [ -z "$avail" ] && { avail=$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2{print $4}') || true; }
  if [ -n "$avail" ] && [ "$avail" -lt 51200 ] 2>/dev/null; then
    err "insufficient disk space near $DEST (need ~50MB free)"; exit 1
  fi
  mkdir -p "$DEST" 2>/dev/null || true
  if [ ! -w "$DEST" ]; then
    err "no write permission for $DEST"; exit 1
  fi
  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || { err "no network reachability to github.com (use --offline TARBALL, or set QUILL_LOCAL_TARBALL, for an airgapped install)"; exit 1; }
  fi
}

acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
  fi
  local d="${lf}.d" start opid
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"; continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

safe_version() {
  local bin="$1" out=""
  if command -v timeout >/dev/null 2>&1; then
    out=$(timeout 1 "$bin" --version 2>/dev/null) || true
  else
    out=$("$bin" --version 2>/dev/null) || true
  fi
  printf '%s\n' "$out"
}

fetch_expected_sha() {
  curl -fsSL "${PROXY_ARGS[@]}" "$1" 2>/dev/null | awk '{print $1}' || true
}

verify_checksum() {
  local file="$1" expected="$2" actual=""
  if [ -z "$expected" ]; then
    warn "no published checksum for this artifact; skipping checksum verification"
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no SHA256 tool found; skipping checksum verification"
    return 0
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $expected, got $actual)"
  return 1
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle published for this release; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED — refusing to install"
  return 1
}

extract_and_install() {
  local archive="$1" bin=""
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

build_from_source() {
  info "building $BINARY_NAME from source (this can take a few minutes)"
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal >/dev/null
    # shellcheck disable=SC1091
    . "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  if [ -n "$VERSION" ]; then
    git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
      || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  else
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  fi
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "build produced no binary at $bin"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

install_from_tarball() {
  local archive="$1" expected=""
  [ -f "$archive" ] || { err "offline tarball not found: $archive"; exit 1; }
  info "installing from local tarball: $archive"
  if [ "$NO_VERIFY" = 0 ] && [ -f "$archive.sha256" ]; then
    expected=$(awk '{print $1}' "$archive.sha256")
  fi
  if [ "$NO_VERIFY" = 0 ]; then
    verify_checksum "$archive" "$expected" || exit 1
  fi
  extract_and_install "$archive"
}

download_and_install() {
  local artifact="$TMP/artifact.tar.gz" url="" expected=""
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      if [ "$NO_VERIFY" = 0 ]; then
        expected=$(fetch_expected_sha "${url}.sha256")
        verify_checksum "$artifact" "$expected" || { rm -f "$artifact"; continue; }
        verify_sigstore "$artifact" "${url}.sigstore.json" || { rm -f "$artifact"; continue; }
      fi
      extract_and_install "$artifact" && return 0
    fi
  done
  warn "no prebuilt binary available for $TARGET; building from source"
  build_from_source
}

install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || true
  [ -x "$DEST/$BINARY_NAME" ] || return 0
  if "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
    "$DEST/$BINARY_NAME" completions zsh  > "$zsh_dir/_$BINARY_NAME"      2>/dev/null || true
    "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  else
    rm -f "$bash_dir/$BINARY_NAME"
    warn "$BINARY_NAME has no 'completions' subcommand yet; skipping shell completions"
  fi
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *)
      warn "$DEST is not on your PATH"
      info "add this to your shell rc: export PATH=\"$DEST:\$PATH\""
      ;;
  esac
}

draw_box() {
  local color="$1"; shift
  local lines=("$@") max=0 esc strip i
  esc=$(printf '\033')
  strip="s/${esc}\\[[0-9;]*m//g"
  for i in "${lines[@]}"; do
    local s; s=$(printf '%b' "$i" | LC_ALL=C sed "$strip")
    [ "${#s}" -gt "$max" ] && max=${#s}
  done
  local inner=$((max + 4)) border="" j
  for ((j = 0; j < inner; j++)); do border+="═"; done
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for i in "${lines[@]}"; do
    local s pad p=""
    s=$(printf '%b' "$i" | LC_ALL=C sed "$strip")
    pad=$((max - ${#s}))
    for ((j = 0; j < pad; j++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$i" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

do_uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f \
    "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
    "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME"
  exit 0
}

summarize() {
  local status="$1" ver=""
  ver=$(safe_version "$DEST/$BINARY_NAME")
  [ -z "$ver" ] && ver="$VERSION"
  draw_box 42 \
    "quill — $status" \
    "binary:    $DEST/$BINARY_NAME" \
    "version:   $ver" \
    "uninstall: curl -fsSL https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh | bash -s -- --uninstall"
}

main() {
  [ "$DO_UNINSTALL" = 1 ] && do_uninstall

  detect_platform

  if [ -n "$OFFLINE_TARBALL" ]; then
    preflight
    acquire_lock "${TMPDIR:-/tmp}/${BINARY_NAME}-install.lock" 2400 \
      || { err "could not acquire install lock"; exit 1; }
    install_from_tarball "$OFFLINE_TARBALL"
  else
    resolve_version
    preflight

    if [ "$FORCE" = 0 ] && [ -x "$DEST/$BINARY_NAME" ]; then
      local installed=""
      installed=$(safe_version "$DEST/$BINARY_NAME" | awk '{print $NF}')
      if [ -n "$installed" ] && [ "$installed" = "$VERSION" ]; then
        info "$BINARY_NAME $VERSION already installed at $DEST/$BINARY_NAME"
        install_completions
        check_path
        summarize "already installed"
        return 0
      fi
    fi

    acquire_lock "${TMPDIR:-/tmp}/${BINARY_NAME}-install.lock" 2400 \
      || { err "could not acquire install lock (another install in progress?)"; exit 1; }

    if [ "$FROM_SOURCE" = 1 ]; then
      build_from_source
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  summarize "installed"
}

main