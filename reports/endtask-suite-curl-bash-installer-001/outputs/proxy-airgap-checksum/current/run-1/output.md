#!/usr/bin/env bash
#
# install.sh — installer for netshim (github.com/acme/netshim)
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" | bash
#
# Flags (also settable via matching env vars, see --help):
#   --version <ver>          Install a specific version instead of latest
#   --dest <dir>              Install directory (default: $HOME/.local/bin)
#   --prefix <dir>             Alias for --dest
#   --offline <tarball>       Airgap mode: install from a local tarball, no network calls
#   --sha256 <hex>             Expected SHA256 for --offline (or to override online lookup)
#   --no-verify                Skip SHA256 verification (INSECURE — explicit opt-out required)
#   --force                    Reinstall even if the same version is already present
#   --quiet                    Errors only
#   --no-color                  Disable ANSI colour output
#   --no-gum                    Disable gum styling even if gum is installed
#   --build-from-source        Consent to installing a Go toolchain / building from source
#   -h, --help                  Show this help and exit
#
# Env: HTTPS_PROXY / HTTP_PROXY / NO_PROXY (honoured on every network call),
#      NETSHIM_VERSION, NETSHIM_INSTALL_DIR, BUILD_FROM_SOURCE=1, NO_COLOR
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="netshim"
BINARY_NAME="netshim"
FALLBACK_VERSION="1.0.0"
COSIGN_ID_RE="https://github.com/${OWNER}/${REPO}/.github/workflows/release.yml@.*"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# ---------------------------------------------------------------------------
# Flags / globals
# ---------------------------------------------------------------------------
VERSION="${NETSHIM_VERSION:-}"
DEST="${NETSHIM_INSTALL_DIR:-$HOME/.local/bin}"
OFFLINE_TARBALL=""
EXPECTED_SHA_OVERRIDE=""
VERIFY=1
FORCE=0
QUIET=0
NO_COLOR="${NO_COLOR:-0}"
NO_GUM=0
BUILD_FROM_SOURCE_CONSENT="${BUILD_FROM_SOURCE:-0}"
FROM_SOURCE=0

usage() {
  cat <<'EOF'
netshim installer

Usage:
  install.sh [flags]

Flags:
  --version <ver>       Install a specific version instead of latest
  --dest <dir>          Install directory (default: $HOME/.local/bin)
  --prefix <dir>        Alias for --dest
  --offline <tarball>   Airgap mode: install from a local tarball, no network calls
  --sha256 <hex>        Expected SHA256 (required with --offline unless --no-verify)
  --no-verify           Skip SHA256 verification (INSECURE)
  --force               Reinstall even if the same version is already present
  --quiet               Errors only
  --no-color            Disable ANSI colour output
  --no-gum              Disable gum styling even if gum is installed
  --build-from-source   Consent to installing a Go toolchain / building from source
  -h, --help            Show this help and exit

Env:
  HTTPS_PROXY / HTTP_PROXY / NO_PROXY   Honoured on every network call
  NETSHIM_VERSION                       Same as --version
  NETSHIM_INSTALL_DIR                   Same as --dest
  BUILD_FROM_SOURCE=1                   Same as --build-from-source
  NO_COLOR                              Same as --no-color

Example (corporate proxy):
  HTTPS_PROXY=http://proxy.corp:8080 curl -fsSL \
    "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" | bash

Example (airgap):
  ./install.sh --offline netshim_1.4.0_linux_amd64.tar.gz --sha256 <hex>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest|--prefix) DEST="$2"; shift 2 ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --sha256) EXPECTED_SHA_OVERRIDE="$2"; shift 2 ;;
    --no-verify) VERIFY=0; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --build-from-source) BUILD_FROM_SOURCE_CONSENT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Temp dir + cleanup
# ---------------------------------------------------------------------------
TMP="$(mktemp -d "${TMPDIR:-/tmp}/netshim-install.XXXXXX")"
LOCKFILE="${TMPDIR:-/tmp}/.netshim-install.lock"
LOCK_HELD=0
cleanup() {
  local ec=$?
  [[ "$LOCK_HELD" == 1 ]] && release_lock
  rm -rf "$TMP"
  exit "$ec"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" == 1 && "$kind" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "$NO_GUM" == 0 && "$NO_COLOR" == 0 ]]; then
    gum style --foreground "$color" "$glyph $*"
  elif [[ "$NO_COLOR" == 1 || ! -t 1 ]]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

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
# Proxy — every curl call below passes "${PROXY_ARGS[@]}"
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")
# NO_PROXY is honored natively by curl.
[[ ${#PROXY_ARGS[@]} -gt 0 ]] && info "using proxy: ${PROXY_ARGS[1]}"

# ---------------------------------------------------------------------------
# Platform detection (Go GOOS/GOARCH naming, not Rust triples)
# ---------------------------------------------------------------------------
OS=""; ARCH=""; ASSET_OS=""; ASSET_ARCH=""
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)   ARCH=amd64 ;;
    arm64|aarch64)  ARCH=arm64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-amd64)   ASSET_OS=linux;  ASSET_ARCH=amd64 ;;
    linux-arm64)   ASSET_OS=linux;  ASSET_ARCH=arm64 ;;
    darwin-amd64)  ASSET_OS=darwin; ASSET_ARCH=amd64 ;;
    darwin-arm64)  ASSET_OS=darwin; ASSET_ARCH=arm64 ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — corporate proxy settings usually need to be set inside WSL too, not just Windows"
  fi
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST" 2>/dev/null || true
  if [[ ! -w "$DEST" ]]; then
    err "no write permission on $DEST"; exit 1
  fi

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    err "less than 50MB free at $DEST (have ${avail_kb}KB)"; exit 1
  fi

  if [[ -x "$DEST/$BINARY_NAME" ]]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [[ -n "$cur" && "$cur" == "$VERSION" && "$FORCE" != 1 ]]; then
      ok "netshim $cur already installed at $DEST — use --force to reinstall"
      SKIP_DOWNLOAD=1
    fi
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      err "cannot reach github.com — check network/proxy, or use --offline <tarball> for airgapped install"
      exit 1
    fi
  fi
}
SKIP_DOWNLOAD=0

# ---------------------------------------------------------------------------
# Atomic lock — flock-first, mkdir spinlock fallback (macOS has no flock),
# stale-PID self-heal.
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    if flock -w "$w" 9; then LOCK_HELD=1; return 0; else return 1; fi
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      warn "clearing stale lock from dead process $opid"; rm -rf "$d"; continue
    fi
    (( $(date +%s) - start >= w )) && return 1
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD=1
  MKDIR_LOCK_DIR="$d"
}
release_lock() {
  if [[ -n "${MKDIR_LOCK_DIR:-}" ]]; then rm -rf "$MKDIR_LOCK_DIR"; fi
  LOCK_HELD=0
}

# ---------------------------------------------------------------------------
# Version resolution
#   1. --version / NETSHIM_VERSION
#   2. local ./VERSION file (repo checkout, relevant for --build-from-source)
#   3. GitHub API "latest" tag
#   4. redirect-scrape of /releases/latest
#   5. hardcoded FALLBACK_VERSION
# ---------------------------------------------------------------------------
resolve_version() {
  [[ -n "$VERSION" ]] && return 0

  if [[ -f VERSION ]]; then
    VERSION=$(head -n1 VERSION | tr -d '[:space:]')
    [[ -n "$VERSION" ]] && return 0
  fi

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] && return 0

  VERSION="$FALLBACK_VERSION"
  warn "could not resolve latest version; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# Checksum verification — mandatory unless --no-verify is passed explicitly.
# Unlike a "soft-skip on missing tool" policy, netshim requires a known-good
# SHA256 before trusting a downloaded artifact; a missing checksums.txt entry
# or a missing sha256 tool is a hard failure, not a warning, when VERIFY=1.
# ---------------------------------------------------------------------------
compute_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    return 1
  fi
}

verify_checksum() {  # $1=file $2=expected(may be empty)
  if [[ "$VERIFY" == 0 ]]; then
    warn "SHA256 verification skipped (--no-verify). This artifact is UNVERIFIED."
    return 0
  fi
  if [[ -z "$2" ]]; then
    err "no known-good SHA256 for this artifact; refusing to install unverified."
    err "supply one with --sha256 <hex>, or re-run with --no-verify (not recommended)."
    return 1
  fi
  local actual
  if ! actual=$(compute_sha256 "$1"); then
    err "no sha256 tool found (need sha256sum or shasum); install one or re-run with --no-verify"
    return 1
  fi
  if [[ "$actual" == "$2" ]]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $2, got $actual) — artifact rejected"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign absent; skipping signature check"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle published for this release; skipping signature check"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "signature verified"
    return 0
  fi
  err "Sigstore verification FAILED — artifact rejected"
  return 1
}

# ---------------------------------------------------------------------------
# Download + install (online path) — 3 URL tiers, then checksums.txt fetch,
# then verify, then extract.
# ---------------------------------------------------------------------------
download_and_install() {
  local asset="${REPO}_${VERSION}_${ASSET_OS}_${ASSET_ARCH}.tar.gz"
  local sums="${REPO}_${VERSION}_checksums.txt"
  local expected_sha="$EXPECTED_SHA_OVERRIDE"

  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$asset"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$asset"
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${REPO}-${ASSET_OS}-${ASSET_ARCH}.tar.gz"
  )

  if [[ -z "$expected_sha" && "$VERIFY" == 1 ]]; then
    if curl -fsSL "${PROXY_ARGS[@]}" \
        "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$sums" \
        -o "$TMP/checksums.txt" 2>/dev/null; then
      expected_sha=$(awk -v f="$asset" '$2==f{print $1}' "$TMP/checksums.txt")
    fi
  fi

  local url
  for url in "${urls[@]}"; do
    info "downloading $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      if verify_checksum "$TMP/artifact.tar.gz" "$expected_sha" \
        && verify_sigstore "$TMP/artifact.tar.gz" "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${asset}.sigstore.json" \
        && extract_and_install "$TMP/artifact.tar.gz"; then
        return 0
      fi
      rm -f "$TMP/artifact.tar.gz"
    fi
  done

  warn "no prebuilt binary available; falling back to building from source"
  confirm_build_from_source
  build_from_source
}

# ---------------------------------------------------------------------------
# Build-from-source — needs a Go toolchain. Installing a toolchain requires
# explicit consent: prompt on a TTY, else require --build-from-source or
# BUILD_FROM_SOURCE=1.
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  [[ "$BUILD_FROM_SOURCE_CONSENT" == 1 ]] && return 0
  if [[ -t 0 ]]; then
    read -r -p "Build netshim from source? This may install/use a Go toolchain. [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]] && { BUILD_FROM_SOURCE_CONSENT=1; return 0; }
    err "declined; aborting."; exit 1
  fi
  err "no prebuilt binary and no TTY for consent; re-run with --build-from-source or BUILD_FROM_SOURCE=1"
  exit 1
}

build_from_source() {
  if ! command -v go >/dev/null 2>&1; then
    err "Go toolchain not found. Install Go (https://go.dev/dl/) or supply a prebuilt binary via --offline"
    exit 1
  fi
  info "cloning $OWNER/$REPO @ v$VERSION"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$TMP/src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$TMP/src"
  ( cd "$TMP/src" && GOFLAGS=-mod=mod go build -o "$TMP/$BINARY_NAME" ./... )
  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $DEST"
}

# ---------------------------------------------------------------------------
# Extract + atomic install
# ---------------------------------------------------------------------------
extract_and_install() {
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$1" -C "$TMP" ;;
    *.zip)          unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -maxdepth 3 -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST"
}

# ---------------------------------------------------------------------------
# Offline / airgap install — no network calls at all.
# ---------------------------------------------------------------------------
offline_install() {
  [[ -f "$OFFLINE_TARBALL" ]] || { err "--offline tarball not found: $OFFLINE_TARBALL"; exit 1; }

  local expected_sha="$EXPECTED_SHA_OVERRIDE"
  if [[ -z "$expected_sha" && -f "${OFFLINE_TARBALL}.sha256" ]]; then
    expected_sha=$(awk '{print $1}' "${OFFLINE_TARBALL}.sha256")
  fi

  verify_checksum "$OFFLINE_TARBALL" "$expected_sha" || exit 1
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Shell completions — XDG paths, not hardcoded rc-file guesses.
# ---------------------------------------------------------------------------
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [[ -x "$bin" ]] || return 0
  command "$bin" completion bash >/dev/null 2>&1 || { warn "binary has no 'completion' subcommand; skipping"; return 0; }

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"

  "$bin" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null && ok "bash completions → $bash_dir/$BINARY_NAME"
  "$bin" completion zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null && ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  "$bin" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null && ok "fish completions → $fish_dir/$BINARY_NAME.fish"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on PATH — add it, e.g. echo 'export PATH=\"$DEST:\$PATH\"' >> ~/.bashrc" ;;
  esac
}

# ---------------------------------------------------------------------------
# Uninstall instructions — printed every run.
# ---------------------------------------------------------------------------
print_uninstall_instructions() {
  cat <<EOF

Uninstall:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
EOF
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if [[ -n "$OFFLINE_TARBALL" ]]; then
    info "airgap mode: installing from $OFFLINE_TARBALL (no network calls)"
    preflight
    if [[ "$SKIP_DOWNLOAD" != 1 ]]; then
      offline_install
      install_completions
    fi
  else
    detect_platform
    resolve_version
    preflight
    acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install in progress?)"; exit 1; }
    if [[ "$SKIP_DOWNLOAD" != 1 ]]; then
      if [[ "$FROM_SOURCE" == 1 ]]; then
        confirm_build_from_source
        build_from_source
      else
        download_and_install
      fi
    fi
    install_completions
    release_lock
  fi

  check_path

  draw_box 42 \
    "netshim install complete" \
    "  binary:  $DEST/$BINARY_NAME" \
    "  version: ${VERSION:-local build}"

  print_uninstall_instructions
}

main "$@"