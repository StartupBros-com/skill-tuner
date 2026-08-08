#!/usr/bin/env bash
#
# install.sh — installer for quill (github.com/hovlabs/quill)
# A small Rust markdown formatter. Installs a single binary. No services,
# no daemons, nothing is started or left running in the background.
#
# Usage:
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/quill/main/install.sh?$(date +%s)" | bash
#
# Airgapped / offline (e.g. CI):
#   QUILL_LOCAL_TARBALL=/path/to/quill-vX.Y.Z-<target>.tar.gz bash install.sh
#   # or equivalently:
#   bash install.sh --offline /path/to/quill-vX.Y.Z-<target>.tar.gz
#
# Flags:
#   -V, --version VERSION   Install a specific version (default: latest)
#   -d, --dir DIR           Install destination (default: $HOME/.local/bin)
#       --offline TARBALL   Install from a local tarball, no network calls
#       --no-verify         Skip checksum + signature verification
#       --quiet             Only print errors
#       --force             Reinstall even if the target version is already installed
#       --no-color          Disable ANSI color output
#       --no-gum            Disable gum styling even if gum is present
#   -h, --help              Show this help and exit
#
# Environment:
#   QUILL_VERSION           Same as --version
#   QUILL_INSTALL_DIR       Same as --dir
#   QUILL_LOCAL_TARBALL     Same as --offline
#   QUILL_SHA256            Expected SHA256 for the local tarball (--offline mode)
#   HTTPS_PROXY / HTTP_PROXY  Proxied for every network call
#   NO_COLOR                 Disable ANSI color output
#
# Uninstall: rerun with --help for the printed uninstall command, or see the
# summary printed at the end of a successful install.

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

TMP="$(mktemp -d "${TMPDIR:-/tmp}/quill-install.XXXXXX")"
cleanup() { rm -rf "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
OWNER="hovlabs"
REPO="quill"
BINARY_NAME="quill"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE='^https://github\.com/hovlabs/quill/\.github/workflows/.*@refs/tags/.*$'
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION="${QUILL_VERSION:-}"
DEST="${QUILL_INSTALL_DIR:-$HOME/.local/bin}"
LOCAL_TARBALL="${QUILL_LOCAL_TARBALL:-}"
EXPECTED_SHA_OVERRIDE="${QUILL_SHA256:-}"
LOCK_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/quill/install.lock"

QUIET=0
FORCE=0
NO_VERIFY=0
NO_GUM=0
[ -n "${NO_COLOR:-}" ] && NO_GUM=1

FROM_SOURCE=0

# ---------------------------------------------------------------------------
# output helpers — gum-if-TTY, ANSI fallback, honor NO_COLOR + non-TTY
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
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
die()  { err "$@"; exit 1; }

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
# flags
# ---------------------------------------------------------------------------
usage() { sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    -V|--version) VERSION="$2"; shift 2 ;;
    -d|--dir) DEST="$2"; shift 2 ;;
    --offline) LOCAL_TARBALL="$2"; shift 2 ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done

OFFLINE=0
[ -n "$LOCAL_TARBALL" ] && OFFLINE=1

# ---------------------------------------------------------------------------
# proxy
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# platform detection
# ---------------------------------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z'); ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions install fine, PATH setup may need extra care in your shell rc"
  fi
}

# ---------------------------------------------------------------------------
# version resolution — flag/env, Cargo.toml (if run from a checkout),
# GitHub API, GitHub redirect, hardcoded fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ "$OFFLINE" = 1 ] && { VERSION="${VERSION:-local}"; return 0; }
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

# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
preflight() {
  if [ -n "$LOCAL_TARBALL" ]; then
    [ -f "$LOCAL_TARBALL" ] || die "--offline/QUILL_LOCAL_TARBALL file not found: $LOCAL_TARBALL"
    [ -r "$LOCAL_TARBALL" ] || die "cannot read local tarball: $LOCAL_TARBALL"
  fi

  mkdir -p "$DEST" 2>/dev/null || true
  [ -d "$DEST" ] || die "install destination does not exist and could not be created: $DEST"
  [ -w "$DEST" ] || die "install destination is not writable: $DEST (try --dir or run with correct perms)"

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 20480 ]; then
    die "less than 20MB free at $DEST"
  fi

  if [ "$OFFLINE" = 0 ]; then
    curl -fsSL -o /dev/null --connect-timeout 5 "${PROXY_ARGS[@]}" "https://github.com" \
      || die "cannot reach github.com — check network/proxy, or use --offline TARBALL"
  fi

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" = 0 ] && [ "$OFFLINE" = 0 ]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
    if [ -n "$cur" ] && [ "$cur" = "$VERSION" ]; then
      SKIP_INSTALL=1
    fi
  fi
}
SKIP_INSTALL=0

# ---------------------------------------------------------------------------
# atomic lock — flock-first, mkdir spinlock fallback, stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-300}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
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
  trap 'rm -rf "'"$d"'"; cleanup' EXIT
}

# ---------------------------------------------------------------------------
# checksum + signature
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected (may be empty)
  local file="$1" expected="$2" actual
  if [ "$NO_VERIFY" = 1 ]; then warn "--no-verify: skipping checksum"; return 0; fi
  if [ -z "$expected" ]; then warn "no checksum available for this artifact; skipping checksum verification"; return 0; fi
  if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else warn "no SHA256 tool (sha256sum/shasum) found; skipping checksum"; return 0
  fi
  if [ "$actual" = "$expected" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $expected got $actual)"; return 1
  fi
}

fetch_expected_sha() {  # $1=artifact basename -> prints sha to stdout, empty on failure
  [ "$OFFLINE" = 1 ] && return 0
  local name="$1" sums
  sums=$(curl -fsSL "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/checksums.txt" 2>/dev/null) || return 0
  printf '%s\n' "$sums" | awk -v f="$name" '$2==f{print $1}'
}

verify_sigstore() {  # $1=file $2=bundle_url (may be empty in offline mode)
  if [ "$NO_VERIFY" = 1 ]; then warn "--no-verify: skipping signature check"; return 0; fi
  command -v cosign >/dev/null 2>&1 || { warn "cosign absent; skipping signature check"; return 0; }
  if [ "$OFFLINE" = 1 ] || [ -z "$2" ]; then warn "no sigstore bundle available; skipping signature check"; return 0; fi
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no sigstore bundle; skipping"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.json" \
       --certificate-identity-regexp "$COSIGN_ID_RE" \
       --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "signature verified"
  else
    err "Sigstore verification FAILED"; return 1
  fi
}

# ---------------------------------------------------------------------------
# extract + install
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
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f 2>/dev/null | head -1)
  [ -n "$bin" ] || die "binary '$BINARY_NAME' not found inside archive"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# build from source (last-resort fallback, online only)
# ---------------------------------------------------------------------------
build_from_source() {
  info "building from source (this requires rustup/cargo and network access)"
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
    # shellcheck disable=SC1090
    source "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || die "git clone failed"
  ( cd "$src" && cargo build --release ) || die "cargo build failed"
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || die "build succeeded but binary not found at $bin"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# download — 4-tier fallback → source build
# ---------------------------------------------------------------------------
download_and_install() {
  local name url expected sig_url
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    name=$(basename "$url")
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      expected=$(fetch_expected_sha "$name")
      sig_url="https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$name.sigstore.json"
      if verify_checksum "$TMP/artifact.tar.gz" "$expected" \
         && verify_sigstore "$TMP/artifact.tar.gz" "$sig_url"; then
        extract_and_install "$TMP/artifact.tar.gz"
        return 0
      fi
      rm -f "$TMP/artifact.tar.gz"
    fi
  done
  warn "no prebuilt binary available; falling back to source build"
  build_from_source
}

install_offline() {
  local name; name=$(basename "$LOCAL_TARBALL")
  cp "$LOCAL_TARBALL" "$TMP/artifact.tar.gz"
  verify_checksum "$TMP/artifact.tar.gz" "$EXPECTED_SHA_OVERRIDE" || die "checksum verification failed for local tarball"
  verify_sigstore "$TMP/artifact.tar.gz" "" || die "signature verification failed for local tarball"
  extract_and_install "$TMP/artifact.tar.gz"
}

# ---------------------------------------------------------------------------
# completions
# ---------------------------------------------------------------------------
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  if ! timeout 1 "$bin" completions bash >/dev/null 2>&1; then
    info "$BINARY_NAME does not support 'completions'; skipping"
    return 0
  fi
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$bin" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$bin" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$bin" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "installed shell completions (bash/zsh/fish)"
}

path_check() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on your PATH — add: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
detect_platform
resolve_version
preflight
acquire_lock "$LOCK_FILE" 300 || die "could not acquire install lock (another install running?)"

if [ "$SKIP_INSTALL" = 1 ]; then
  ok "$BINARY_NAME $VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
elif [ "$OFFLINE" = 1 ]; then
  install_offline
elif [ "$FROM_SOURCE" = 1 ]; then
  build_from_source
else
  download_and_install
fi

install_completions
path_check

INSTALLED_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null || echo "$VERSION")

draw_box 42 \
  "quill installed" \
  "" \
  "binary:      $DEST/$BINARY_NAME" \
  "version:     $INSTALLED_VERSION" \
  "completions: bash/zsh/fish (XDG dirs)" \
  "mode:        $([ "$OFFLINE" = 1 ] && echo 'offline (local tarball)' || echo 'online')" \
  "" \
  "no services or daemons were installed — quill is a plain CLI binary."

info "uninstall: rm -f \"$DEST/$BINARY_NAME\" \\"
info "  \"${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME\" \\"
info "  \"${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME\" \\"
info "  \"${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish\""