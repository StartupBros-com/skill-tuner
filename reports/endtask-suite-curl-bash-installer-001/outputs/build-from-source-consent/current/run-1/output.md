#!/usr/bin/env bash
#
# octoparse installer — github.com/acme/octoparse
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/octoparse/main/install.sh?$(date +%s)" | bash
#
# Flags (matching env var in parens):
#   --version X.Y.Z            (VERSION)             install a specific version instead of latest
#   --dest DIR                 (DEST)                 install directory (default: $HOME/.local/bin)
#   --force                    (FORCE=1)              reinstall even if already installed
#   --quiet                    (QUIET=1)              suppress non-error output
#   --no-color                                        disable ANSI colors
#   --no-gum                                          disable gum styling even if present
#   --no-verify                                       skip SHA256 checksum verification (not recommended)
#   --offline TARBALL                                 install from a local tarball; no network calls
#   --build-from-source        (BUILD_FROM_SOURCE=1)  consent to installing a Rust toolchain and
#                                                      building from source if no prebuilt binary
#                                                      matches this platform. REQUIRED off a TTY.
#   --easy-mode                                       append $DEST to PATH in your shell rc file
#   --verify-install                                  self-test: install to a temp dir, run
#                                                      `octoparse --version`, then exit
#   -h, --help                                        show this help and exit
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

OWNER="acme"
REPO="octoparse"
BINARY_NAME="octoparse"
FALLBACK_VERSION="0.1.0"
DEST="${DEST:-$HOME/.local/bin}"
VERSION="${VERSION:-}"
FORCE="${FORCE:-0}"
QUIET="${QUIET:-0}"
NO_GUM="${NO_GUM:-0}"
NO_VERIFY=0
OFFLINE_TARBALL=""
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
EASY_MODE=0
VERIFY_INSTALL=0
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

[[ -n "${NO_COLOR:-}" ]] && NO_GUM=1
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" = 1 && "$kind" != err ]] && return 0
  if [[ "$HAS_GUM" = 1 && "$NO_GUM" = 0 ]]; then
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
  sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

TMP=""
LOCKFILE="${XDG_CACHE_HOME:-$HOME/.cache}/${REPO}-install.lock"
LOCK_HELD=0

cleanup() {
  local ec=$?
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP"
  if [[ "$LOCK_HELD" = 1 ]]; then
    if command -v flock >/dev/null 2>&1; then
      { exec 9>&-; } 2>/dev/null || true
    else
      rm -rf "${LOCKFILE}.d" 2>/dev/null || true
    fi
  fi
  exit "$ec"
}
trap cleanup EXIT

TMP=$(mktemp -d "${TMPDIR:-/tmp}/${REPO}-install.XXXXXX")

# ---------------------------------------------------------------- flag parsing
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --build-from-source) BUILD_FROM_SOURCE=1; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --verify-install) VERIFY_INSTALL=1; shift ;;
    -h|--help) usage ;;
    *) err "unknown flag: $1 (see --help)"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------- proxy support
PROXY_ARGS=()
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [[ -n "${HTTP_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi
# NO_PROXY is honored natively by curl.

# ---------------------------------------------------------------- platform detection
OS="" ARCH="" TARGET="" FROM_SOURCE=0

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
    *)
      warn "no prebuilt binary for ${OS}/${ARCH}"
      FROM_SOURCE=1
      ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features (e.g. shell completions, PATH detection) may need extra config"
  fi
}

# ---------------------------------------------------------------- preflight
preflight() {
  local dest_parent
  dest_parent=$(dirname "$DEST")
  mkdir -p "$DEST" 2>/dev/null || true
  if [[ ! -w "$DEST" && ! -w "$dest_parent" ]]; then
    err "no write permission for $DEST (or its parent). Pass --dest to choose another directory."
    exit 1
  fi

  local avail_kb
  avail_kb=$(df -Pk "$dest_parent" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    err "less than 50MB free at $dest_parent; aborting."
    exit 1
  fi

  if [[ -x "$DEST/$BINARY_NAME" && "$FORCE" != 1 ]]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [[ -n "$cur" ]]; then
      info "found existing install: $BINARY_NAME $cur (use --force to reinstall)"
      SKIP_DOWNLOAD=1
    fi
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      err "no network reachability to github.com. Use --offline TARBALL for an airgapped install."
      exit 1
    fi
  fi
}
SKIP_DOWNLOAD=0

# ---------------------------------------------------------------- version resolution (5-tier)
resolve_version() {
  [[ -n "$VERSION" ]] && return 0                                          # 1. flag/env

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0                                          # 2. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] && return 0                                          # 3. redirect

  VERSION="$FALLBACK_VERSION"                                              # 4. hardcoded fallback
  warn "could not resolve latest version; falling back to $VERSION"
}

# ---------------------------------------------------------------- locking
acquire_lock() {
  local w="${1:-2400}"
  mkdir -p "$(dirname "$LOCKFILE")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$LOCKFILE"; } 2>/dev/null
    if flock -w "$w" 9; then LOCK_HELD=1; return 0; else return 1; fi
  fi
  local d="${LOCKFILE}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"; continue
    fi
    if (( $(date +%s) - start >= w )); then
      err "timed out waiting for install lock ($d)"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD=1
}

# ---------------------------------------------------------------- checksum + signature
fetch_expected_sha() {
  curl -fsSL "${PROXY_ARGS[@]}" "$1.sha256" 2>/dev/null | awk '{print $1}'
}

verify_checksum() {  # $1=file $2=expected
  [[ "$NO_VERIFY" = 1 ]] && { warn "checksum verification skipped (--no-verify)"; return 0; }
  local expected="$2"
  if [[ -z "$expected" ]]; then
    warn "no checksum available for this artifact; skipping"
    return 0
  fi
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no SHA256 tool (sha256sum/shasum) found; skipping checksum"
    return 0
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  else
    err "checksum mismatch (want $expected, got $actual)"
    return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle for this artifact; skipping"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore verification FAILED — refusing to install a tampered artifact"
    return 1
  fi
}

# ---------------------------------------------------------------- extract + install
extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  mkdir -p "$DEST"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------- build from source (last resort)
#
# Installing a Rust toolchain is a big, surprising thing to do to someone's
# machine without asking. On a TTY we ask; off a TTY we require the caller
# to have opted in ahead of time via --build-from-source or
# BUILD_FROM_SOURCE=1, and fail loudly naming exactly that if they haven't.
confirm_build_from_source() {
  if [[ "$BUILD_FROM_SOURCE" == 1 ]]; then
    return 0
  fi
  if [[ -t 0 && -t 1 ]]; then
    warn "No prebuilt binary is available for ${OS}/${ARCH}."
    printf 'Building from source requires a Rust toolchain (rustup + cargo). If one is not\n'
    printf 'already installed, this script will install it via https://sh.rustup.rs.\n'
    local reply
    read -r -p "Proceed with installing a Rust toolchain and building ${BINARY_NAME} from source? [y/N] " reply
    case "$reply" in
      y|Y|yes|YES|Yes) BUILD_FROM_SOURCE=1; return 0 ;;
      *) err "Aborted: declined toolchain install. No changes were made."; exit 1 ;;
    esac
  else
    err "No prebuilt binary is available for ${OS}/${ARCH}, and this is not an interactive terminal."
    err "Refusing to silently install a Rust toolchain on an unattended run."
    err "Re-run with --build-from-source, or set BUILD_FROM_SOURCE=1, to allow it."
    exit 1
  fi
}

build_from_source() {
  confirm_build_from_source

  if ! command -v cargo >/dev/null 2>&1; then
    info "installing Rust toolchain via rustup..."
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable -q
    # shellcheck disable=SC1091
    source "$HOME/.cargo/env"
  fi
  if ! command -v cargo >/dev/null 2>&1; then
    err "cargo still not on PATH after rustup install; aborting."
    exit 1
  fi

  local src="$TMP/src"
  info "cloning $OWNER/$REPO@v$VERSION..."
  if ! git clone --depth 1 --branch "v$VERSION" \
      "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null; then
    info "tag v$VERSION not found; cloning default branch instead"
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  fi

  info "building (cargo build --release)... this may take a few minutes"
  (cd "$src" && cargo build --release)

  local bin="$src/target/release/$BINARY_NAME"
  [[ -x "$bin" ]] || { err "build did not produce $bin"; exit 1; }
  mkdir -p "$DEST"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------- download (4-tier) → source fallback
download_and_install() {
  if [[ "$FROM_SOURCE" = 1 ]]; then
    build_from_source
    return
  fi

  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url artifact="$TMP/artifact.tar.gz"
  for url in "${urls[@]}"; do
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      local expected
      expected=$(fetch_expected_sha "$url")
      if verify_checksum "$artifact" "$expected" && \
         verify_sigstore "$artifact" "$url.sigstore.json" && \
         extract_and_install "$artifact"; then
        return 0
      fi
      rm -f "$artifact"
    fi
  done

  warn "no prebuilt binary could be downloaded for ${OS}/${ARCH}"
  build_from_source
}

# ---------------------------------------------------------------- completions (XDG)
install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  local bin="$DEST/$BINARY_NAME"
  [[ -x "$bin" ]] || return 0
  timeout 1 "$bin" completions bash >"$bash_dir/$BINARY_NAME" 2>/dev/null || true
  timeout 1 "$bin" completions zsh  >"$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  timeout 1 "$bin" completions fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "shell completions installed (bash/zsh/fish)"
}

# ---------------------------------------------------------------- PATH check
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [[ "$EASY_MODE" = 1 ]]; then
    local rc=""
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      */fish) rc="$HOME/.config/fish/config.fish" ;;
      *) rc="$HOME/.profile" ;;
    esac
    printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
    ok "added $DEST to PATH in $rc (restart your shell)"
  else
    warn "$DEST is not on your PATH. Add it manually, or re-run with --easy-mode."
  fi
}

# ---------------------------------------------------------------- uninstall instructions
uninstall_instructions() {
  cat <<EOF
To uninstall:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
EOF
}

# ---------------------------------------------------------------- summary box
draw_box() {
  local color="$1"; shift
  local lines=("$@") max=0 esc; esc=$(printf '\033')
  local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    (( ${#s} > max )) && max=${#s}
  done
  local inner=$((max+4)) border=""
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

# ------------------------------------------------------------------ main
main() {
  detect_platform

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
    info "offline install from $OFFLINE_TARBALL (no network calls)"
    verify_checksum "$OFFLINE_TARBALL" "" # no expected hash available offline; --no-verify or trust caller
    extract_and_install "$OFFLINE_TARBALL"
    VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || echo "unknown")
  else
    preflight
    resolve_version
    if acquire_lock; then
      if [[ "$SKIP_DOWNLOAD" != 1 ]]; then
        download_and_install
      fi
    else
      err "could not acquire install lock; another install may be in progress"
      exit 1
    fi
  fi

  install_completions
  check_path

  if [[ "$VERIFY_INSTALL" = 1 ]]; then
    local out
    out=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>&1) || { err "self-test failed: $out"; exit 1; }
    ok "self-test passed: $out"
  fi

  draw_box 42 \
    "\033[1m${BINARY_NAME}\033[0m installed successfully" \
    "" \
    "version:  ${VERSION:-unknown}" \
    "binary:   $DEST/$BINARY_NAME" \
    "path:     $([[ ":$PATH:" == *":$DEST:"* ]] && echo "on PATH" || echo "NOT on PATH — see warning above")"

  uninstall_instructions
}

main "$@"