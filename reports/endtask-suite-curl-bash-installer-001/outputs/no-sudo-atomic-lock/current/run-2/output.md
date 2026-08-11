#!/usr/bin/env bash
#
# install.sh — installer for bexport (github.com/acme/bexport)
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --prefix DIR          Install directory (default: $HOME/.local/bin). No sudo required, ever.
#   --version VERSION     Install a specific version instead of latest.
#   --force                Reinstall even if the requested version is already installed.
#   --no-verify            Skip SHA256 checksum verification (not recommended).
#   --build-from-source    Consent (for non-TTY runs) to build via cargo if no prebuilt artifact matches.
#   --offline TARBALL       Install from a local tarball, no network calls at all.
#   --quiet                 Only print errors.
#   --no-color              Disable ANSI colors.
#   --no-gum                 Disable gum styling even if gum is present.
#   --uninstall              Remove the installed binary/completions and exit.
#   -h, --help               Show this help and exit.
#
# Environment:
#   HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call.
#   NO_COLOR                    Disable ANSI colors (same as --no-color).
#   BUILD_FROM_SOURCE=1         Same as --build-from-source, for non-interactive CI.
#   PREFIX                      Same as --prefix.
#   VERSION                     Same as --version.
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="bexport"
BINARY_NAME="bexport"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

QUIET=0
FORCE=0
NO_VERIFY=0
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
OFFLINE_TARBALL=""
NO_GUM="${NO_GUM:-0}"
UNINSTALL=0
VERSION="${VERSION:-}"
PREFIX="${PREFIX:-$HOME/.local/bin}"

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honor NO_COLOR + non-TTY
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && NO_GUM=1
[ -t 1 ] || NO_GUM=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$NO_GUM" = 1 ] || [ -n "${NO_COLOR:-}" ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" 1>&2; }

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
usage() { sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix)              PREFIX="$2"; shift 2 ;;
    --prefix=*)             PREFIX="${1#*=}"; shift ;;
    --version)              VERSION="$2"; shift 2 ;;
    --version=*)             VERSION="${1#*=}"; shift ;;
    --force)                  FORCE=1; shift ;;
    --no-verify)               NO_VERIFY=1; shift ;;
    --build-from-source)        BUILD_FROM_SOURCE=1; shift ;;
    --offline)                   OFFLINE_TARBALL="$2"; shift 2 ;;
    --offline=*)                  OFFLINE_TARBALL="${1#*=}"; shift ;;
    --quiet)                       QUIET=1; shift ;;
    --no-color)                     NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum)                        NO_GUM=1; shift ;;
    --uninstall)                      UNINSTALL=1; shift ;;
    -h|--help)                         usage; exit 0 ;;
    *) err "unknown flag: $1"; usage; exit 1 ;;
  esac
done

# Normalize prefix to an absolute path (handles "~", relative dirs, trailing slash)
case "$PREFIX" in
  "~") PREFIX="$HOME" ;;
  "~/"*) PREFIX="$HOME/${PREFIX#\~/}" ;;
esac
mkdir -p "$PREFIX" 2>/dev/null || true
PREFIX="$(cd "$PREFIX" 2>/dev/null && pwd -P || echo "$PREFIX")"
DEST="$PREFIX"

XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
LOCK_DIR="${XDG_DATA_HOME}/${BINARY_NAME}"
mkdir -p "$LOCK_DIR" 2>/dev/null || true
LOCK_FILE="${LOCK_DIR}/install.lock"

# ---------------------------------------------------------------------------
# Proxy support
# ---------------------------------------------------------------------------
PROXY_ARGS=()
if [ -n "${HTTPS_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [ -n "${HTTP_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi

# ---------------------------------------------------------------------------
# Temp dir + cleanup trap (must be right after temp dir creation)
# ---------------------------------------------------------------------------
TMP=""
LOCK_HELD_DIR=""
cleanup() {
  local ec=$?
  [ -n "$TMP" ] && rm -rf "$TMP"
  # release mkdir-spinlock fallback if we're holding it
  if [ -n "$LOCK_HELD_DIR" ] && [ -d "$LOCK_HELD_DIR" ]; then
    local pid; pid=$(cat "$LOCK_HELD_DIR/pid" 2>/dev/null || true)
    [ "$pid" = "$$" ] && rm -rf "$LOCK_HELD_DIR"
  fi
  exit "$ec"
}
trap cleanup EXIT
TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}.XXXXXX")

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
OS=""; ARCH=""; TARGET=""; FROM_SOURCE=0
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64) ARCH=x86_64 ;;
    arm64|aarch64) ARCH=aarch64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt artifact for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = "linux" ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features (e.g. filesystem watch) may need extra config"
  fi
}

# ---------------------------------------------------------------------------
# Preflight — disk, perms, existing install, network reachability
# ---------------------------------------------------------------------------
preflight() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    [ -f "$OFFLINE_TARBALL" ] || { err "--offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  fi

  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install prefix: $DEST (no sudo needed — pick a writable --prefix)"; exit 1; }
  [ -w "$DEST" ] || { err "prefix not writable: $DEST — pick a different --prefix, no sudo will help here"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "insufficient disk space at $DEST (need ~50MB, have ${avail_kb}KB)"
    exit 1
  fi

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" != 1 ]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [ -n "$cur" ] && [ -n "$VERSION" ] && [ "$cur" = "$VERSION" ]; then
      ok "bexport $cur already installed at $DEST — skipping download (use --force to reinstall)"
      SKIP_DOWNLOAD=1
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ] && [ "${SKIP_DOWNLOAD:-0}" != 1 ]; then
    curl -fsSL --connect-timeout 5 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null \
      || warn "network reachability check to github.com failed; will still attempt downloads"
  fi
}
SKIP_DOWNLOAD=0

# ---------------------------------------------------------------------------
# Atomic locking — flock-first, mkdir spinlock fallback, stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9 || { err "timed out waiting for install lock ($lf) after ${w}s"; return 1; }; return 0; }
  fi
  # mkdir spinlock fallback (macOS has no flock; also used if exec redirection failed)
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then
      warn "stale lock from dead process $opid; recovering"
      rm -rf "$d"
      continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then
      err "timed out waiting for install lock ($d) after ${w}s"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD_DIR="$d"
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. CLI flag/env
  [ -f Cargo.toml ] && VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  [ -n "$VERSION" ] && return 0                                              # 2. manifest
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                              # 3. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"                           # 4. redirect  5. hardcoded
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
# ---------------------------------------------------------------------------
fetch_expected_sha() {  # $1=artifact_url -> echoes sha or empty
  local shasums_url="https://github.com/$OWNER/$REPO/releases/download/v$VERSION/SHASUMS256.txt"
  local base; base=$(basename "$1")
  curl -fsSL "${PROXY_ARGS[@]}" "$shasums_url" 2>/dev/null | awk -v f="$base" '$2==f || $2=="*"f {print $1; exit}'
}

verify_checksum() {  # $1=file $2=expected
  [ "$NO_VERIFY" = 1 ] && { warn "--no-verify set; skipping checksum verification"; return 0; }
  local expected="$2"
  if [ -z "$expected" ]; then
    warn "no checksum available for this artifact; skipping (use --no-verify to silence)"
    return 0
  fi
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no SHA256 tool available; skipping checksum verification"
    return 0
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  else
    err "checksum mismatch (want $expected, got $actual)"
    return 1
  fi
}

verify_sigstore() {  # $1=file
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  local bundle_url="https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$(basename "$1").sigstore.json"
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle found; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore verification FAILED — refusing to install"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Build from source (consent-gated)
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  if [ "$BUILD_FROM_SOURCE" = 1 ]; then
    return 0
  fi
  if [ -t 0 ] && [ -t 1 ]; then
    printf '\033[214m⚠\033[0m No prebuilt binary is available. Build from source with cargo? [y/N] '
    read -r reply
    case "$reply" in
      y|Y|yes|YES) return 0 ;;
      *) err "declined build-from-source"; exit 1 ;;
    esac
  else
    err "no prebuilt binary and not running interactively; re-run with --build-from-source or BUILD_FROM_SOURCE=1"
    exit 1
  fi
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup toolchain install stable >/dev/null 2>&1 || true
    else
      err "cargo not found and rustup not available; install Rust (no sudo needed: https://rustup.rs uses \$HOME) and retry"
      exit 1
    fi
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "build did not produce $BINARY_NAME"; exit 1; }
  atomic_install "$bin"
}

# ---------------------------------------------------------------------------
# Extract + atomic install
#   install(1) into a temp file in the SAME directory as DEST, then rename(2)
#   into place — rename is atomic on a POSIX filesystem, so concurrent readers
#   (or a crashed second run) never observe a partially-written binary.
# ---------------------------------------------------------------------------
extract_archive() {  # $1=archive -> echoes path to extracted binary
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$1" -C "$TMP" ;;
    *.zip)          unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  find "$TMP" -name "$BINARY_NAME" -type f | head -1
}

atomic_install() {  # $1=path to built/extracted binary
  local src="$1"
  local staging
  staging=$(mktemp "$DEST/.${BINARY_NAME}.XXXXXX")
  cp "$src" "$staging"
  chmod 0755 "$staging"
  mv -f "$staging" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

download_and_install() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    info "offline mode: installing from $OFFLINE_TARBALL"
    local bin; bin=$(extract_archive "$OFFLINE_TARBALL")
    [ -n "$bin" ] || { err "binary not found in offline tarball"; exit 1; }
    verify_checksum "$OFFLINE_TARBALL" "${EXPECTED_SHA:-}" || exit 1
    atomic_install "$bin"
    return 0
  fi

  local tried=0
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    tried=$((tried+1))
    info "attempting download (tier $tried): $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      local expected; expected=$(fetch_expected_sha "$url")
      if verify_checksum "$TMP/artifact.tar.gz" "$expected" && verify_sigstore "$TMP/artifact.tar.gz"; then
        local bin; bin=$(extract_archive "$TMP/artifact.tar.gz")
        if [ -n "$bin" ]; then
          atomic_install "$bin"
          return 0
        fi
      else
        return 1
      fi
    fi
  done

  warn "no prebuilt binary found for $TARGET; falling back to source build"
  confirm_build_from_source
  build_from_source
}

# ---------------------------------------------------------------------------
# Shell completions (XDG paths, not rc-file guesses)
# ---------------------------------------------------------------------------
install_completions() {
  local bash_dir="${XDG_DATA_HOME}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || return 0
  local exe="$DEST/$BINARY_NAME"
  [ -x "$exe" ] || return 0
  if timeout 1 "$exe" completions bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
  fi
  if timeout 1 "$exe" completions zsh >"$zsh_dir/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  fi
  if timeout 1 "$exe" completions fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions → $fish_dir/$BINARY_NAME.fish"
  fi
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *) warn "$DEST is not on your PATH — add it, e.g.: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME from $DEST. Agent hooks (if any) left in place — remove from settings.json manually if desired."
}

# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------
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

print_summary() {
  local ver
  ver=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null || echo "$VERSION")
  draw_box 42 \
    "bexport installed successfully" \
    "" \
    "Binary:      $DEST/$BINARY_NAME" \
    "Version:     $ver" \
    "Completions: ${XDG_DATA_HOME}/bash-completion/completions, zsh/site-functions, fish/completions" \
    "" \
    "Uninstall:   curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall --prefix $DEST"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  detect_platform

  if [ "$UNINSTALL" = 1 ]; then
    uninstall
    exit 0
  fi

  preflight

  if [ "$SKIP_DOWNLOAD" != 1 ]; then
    acquire_lock "$LOCK_FILE" 2400 || exit 1

    if [ -z "$OFFLINE_TARBALL" ]; then
      resolve_version
      info "installing bexport $VERSION for $TARGET into $DEST"
    fi

    if [ "$FROM_SOURCE" = 1 ] && [ -z "$OFFLINE_TARBALL" ]; then
      confirm_build_from_source
      build_from_source
    else
      download_and_install
    fi
  else
    info "reusing existing install; re-checking integrations"
  fi

  install_completions
  check_path
  print_summary
}

main "$@"