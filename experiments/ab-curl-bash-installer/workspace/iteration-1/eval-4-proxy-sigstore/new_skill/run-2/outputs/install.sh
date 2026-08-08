#!/usr/bin/env bash
#
# install.sh — installer for pgshim (https://github.com/hovlabs/pgshim)
# A Postgres connection shim binary.
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash
#
# Flags (pass after `bash -s --`, e.g. `... | bash -s -- --force`):
#   --version VERSION   Install a specific version (default: latest release)
#   --prefix DIR        Install directory (default: $HOME/.local/bin)
#   --force              Reinstall even if the target version is already installed
#   --quiet               Print errors only
#   --no-color             Disable ANSI/gum color output
#   --no-gum                Disable gum styling even if gum is present
#   --no-verify              Skip SHA256/Sigstore verification (NOT recommended)
#   --offline TARBALL        Install from a local tarball; makes no network calls
#   --easy-mode                Append the install dir to PATH in your shell rc if missing
#   --uninstall                 Remove pgshim (and completions) and exit
#   --verify                     Self-test: check environment/current install and exit
#   -h, --help                    Show this help
#
# Env:
#   HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call (curl, git, rustup)
#   NO_COLOR                     Disable color output
#   PGSHIM_VERSION               Same as --version
#   PGSHIM_INSTALL_DIR            Same as --prefix
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

OWNER="hovlabs"
REPO="pgshim"
BINARY_NAME="pgshim"
FALLBACK_VERSION="0.1.0"

# GitHub Actions OIDC identity that signs official releases.
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE='^https://github\.com/hovlabs/pgshim/\.github/workflows/.+@refs/(heads|tags)/.+$'

VERSION="${PGSHIM_VERSION:-}"
DEST="${PGSHIM_INSTALL_DIR:-$HOME/.local/bin}"
QUIET=0
FORCE=0
NO_COLOR="${NO_COLOR:-}"
NO_GUM=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
DO_UNINSTALL=0
SELF_TEST=0
FROM_SOURCE=0
HAS_GUM=0

PROXY_ARGS=()
LOCK_DIR=""
TMP=""
OS=""
ARCH=""
TARGET=""

print_help() {
  cat <<'EOF'
pgshim installer

Usage: install.sh [flags]

  --version VERSION   Install a specific version (default: latest release)
  --prefix DIR        Install directory (default: $HOME/.local/bin)
  --force              Reinstall even if the target version is already installed
  --quiet               Print errors only
  --no-color             Disable ANSI/gum color output
  --no-gum                Disable gum styling even if gum is present
  --no-verify              Skip SHA256/Sigstore verification (NOT recommended)
  --offline TARBALL        Install from a local tarball; makes no network calls
  --easy-mode                Append the install dir to PATH in your shell rc if missing
  --uninstall                 Remove pgshim (and completions) and exit
  --verify                     Self-test: check environment/current install and exit
  -h, --help                    Show this help

Env:
  HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call
  NO_COLOR                     Disable color output
  PGSHIM_VERSION               Same as --version
  PGSHIM_INSTALL_DIR            Same as --prefix
EOF
}

_log() {  # $1=level $2=color $3=icon ; rest=message
  local level="$1" color="$2" icon="$3"; shift 3
  if [ "$QUIET" = 1 ] && [ "$level" != err ]; then return 0; fi
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM:-0}" = 0 ]; then
    gum style --foreground "$color" "$icon $*"
  elif [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$icon" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$icon" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version)
        [ $# -ge 2 ] || { printf 'missing value for --version\n' >&2; exit 1; }
        VERSION="$2"; shift 2 ;;
      --prefix)
        [ $# -ge 2 ] || { printf 'missing value for --prefix\n' >&2; exit 1; }
        DEST="$2"; shift 2 ;;
      --offline)
        [ $# -ge 2 ] || { printf 'missing value for --offline\n' >&2; exit 1; }
        OFFLINE_TARBALL="$2"; shift 2 ;;
      --force) FORCE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      --verify) SELF_TEST=1; shift ;;
      -h|--help) print_help; exit 0 ;;
      *) printf 'unknown flag: %s\n' "$1" >&2; print_help; exit 1 ;;
    esac
  done
}

setup_logging_flags() {
  if command -v gum >/dev/null 2>&1 && [ -t 1 ]; then HAS_GUM=1; fi
  [ -n "${NO_COLOR:-}" ] && NO_GUM=1
}

configure_proxy() {
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
  [ -n "${HTTPS_PROXY:-}" ] && export https_proxy="$HTTPS_PROXY"
  [ -n "${HTTP_PROXY:-}" ] && export http_proxy="$HTTP_PROXY"
  # NO_PROXY is honored natively by curl and git.
}

curl_p() {
  curl -fsSL "${PROXY_ARGS[@]+"${PROXY_ARGS[@]}"}" "$@"
}

cleanup() {
  [ -n "${LOCK_DIR:-}" ] && rm -rf "$LOCK_DIR" 2>/dev/null || true
  [ -n "${TMP:-}" ] && rm -rf "$TMP" 2>/dev/null || true
}

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
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some Postgres connection features may need extra config"
  fi
}

resolve_version() {
  [ -n "$VERSION" ] && return 0
  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  if [ -z "$VERSION" ] && [ -f package.json ]; then
    VERSION=$(grep -m1 '"version"' package.json | sed -E 's/.*"([0-9][^"]*)".*/\1/')
  fi
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl_p --connect-timeout 5 \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl_p -o /dev/null -w '%{url_effective}' \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"
  info "resolved version: $VERSION"
}

preflight() {
  info "running preflight checks"
  mkdir -p "$DEST" 2>/dev/null || true
  [ -w "$DEST" ] || { err "no write permission on $DEST"; exit 1; }
  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ] 2>/dev/null; then
    err "insufficient disk space in $DEST (need ~50MB, have ${avail_kb}KB)"
    exit 1
  fi
  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    local cur
    cur=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null | head -1 || true)
    [ -n "$cur" ] && info "existing install detected: $cur"
  fi
  if [ -z "$OFFLINE_TARBALL" ]; then
    curl_p --connect-timeout 3 -o /dev/null https://github.com 2>/dev/null \
      || { err "cannot reach github.com — check network/proxy (HTTPS_PROXY=${HTTPS_PROXY:-unset})"; exit 1; }
  fi
  ok "preflight passed"
}

already_current() {
  [ "$FORCE" = 1 ] && return 1
  command -v "$BINARY_NAME" >/dev/null 2>&1 || return 1
  local cur
  cur=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
  [ -n "$cur" ] && [ "$cur" = "$VERSION" ]
}

acquire_lock() {  # $1=lockfile $2=wait_seconds
  local lf="$1" wait_s="${2:-2400}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$wait_s" 9; return $?; }
    return 0
  fi
  local dir="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$dir" 2>/dev/null; do
    local opid
    opid=$(cat "$dir/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$dir"
      continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$wait_s" ]; then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$dir/pid"
  LOCK_DIR="$dir"
  return 0
}

fetch_sidecar_sha() {  # $1 = artifact URL -> prints hash on stdout
  local out
  out=$(curl_p "$1.sha256" 2>/dev/null) || return 1
  [ -n "$out" ] || return 1
  printf '%s\n' "$out" | awk '{print $1; exit}'
}

fetch_sigstore_bundle() {  # $1 = artifact URL -> prints local bundle path on stdout
  local out="$TMP/$(basename "$1").sigstore.json"
  curl_p "$1.sigstore.json" -o "$out" 2>/dev/null && { printf '%s' "$out"; return 0; }
  return 1
}

verify_checksum() {  # $1=file $2=expected_sha
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no sha256sum/shasum available; skipping checksum verification"
    return 0
  fi
  if [ "$actual" = "$2" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $1 (want $2, got $actual)"
  return 1
}

verify_sigstore() {  # $1=file $2=local_bundle_path (may be empty)
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping Sigstore verification"; return 0; }
  [ -n "$2" ] && [ -f "$2" ] || { warn "no Sigstore bundle available; skipping"; return 0; }
  if cosign verify-blob --bundle "$2" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "Sigstore signature verified (OIDC: $COSIGN_ISSUER)"
    return 0
  fi
  err "Sigstore verification FAILED for $1"
  return 1
}

extract_and_install() {  # $1 = archive path
  local archive="$1" workdir="$TMP/extract"
  mkdir -p "$workdir"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$workdir" ;;
    *.tar.xz) tar -xJf "$archive" -C "$workdir" ;;
    *.zip) unzip -q "$archive" -d "$workdir" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$workdir" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found inside archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME -> $DEST/$BINARY_NAME"
}

build_from_source() {
  FROM_SOURCE=1
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup toolchain"
    curl_p https://sh.rustup.rs | sh -s -- -y --default-toolchain stable >/dev/null 2>&1 \
      || { err "failed to install rustup/cargo"; exit 1; }
    # shellcheck disable=SC1091
    [ -f "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || { err "failed to clone $OWNER/$REPO"; exit 1; }
  ( cd "$src" && cargo build --release ) || { err "build from source failed"; exit 1; }
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "built binary not found at $bin"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source -> $DEST/$BINARY_NAME"
}

download_and_install() {
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url sha bundle
  for url in "${urls[@]}"; do
    info "trying $url"
    curl_p "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null || continue

    if [ "$NO_VERIFY" = 1 ]; then
      warn "--no-verify set; skipping SHA256 and Sigstore verification"
    else
      sha=$(fetch_sidecar_sha "$url") || {
        err "could not fetch checksum sidecar for $url; refusing to install unverified binary"
        rm -f "$TMP/artifact.tar.gz"
        continue
      }
      if ! verify_checksum "$TMP/artifact.tar.gz" "$sha"; then
        rm -f "$TMP/artifact.tar.gz"
        continue
      fi
      bundle=$(fetch_sigstore_bundle "$url") || bundle=""
      if ! verify_sigstore "$TMP/artifact.tar.gz" "$bundle"; then
        err "aborting install — Sigstore verification failed (possible tampering)"
        exit 1
      fi
    fi

    extract_and_install "$TMP/artifact.tar.gz" && return 0
    rm -f "$TMP/artifact.tar.gz"
  done
  warn "no prebuilt binary available; building from source"
  build_from_source
}

install_offline() {
  info "offline mode: installing from $OFFLINE_TARBALL"
  [ -f "$OFFLINE_TARBALL" ] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify set; skipping SHA256 and Sigstore verification"
  else
    if [ -f "$OFFLINE_TARBALL.sha256" ]; then
      local sha
      sha=$(awk '{print $1; exit}' "$OFFLINE_TARBALL.sha256")
      verify_checksum "$OFFLINE_TARBALL" "$sha" || exit 1
    else
      warn "no .sha256 sidecar next to $OFFLINE_TARBALL; skipping checksum (offline, unverifiable)"
    fi
    local bundle=""
    [ -f "$OFFLINE_TARBALL.sigstore.json" ] && bundle="$OFFLINE_TARBALL.sigstore.json"
    verify_sigstore "$OFFLINE_TARBALL" "$bundle" || exit 1
  fi
  extract_and_install "$OFFLINE_TARBALL"
}

install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  local bashd="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zshd="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fishd="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bashd" "$zshd" "$fishd" 2>/dev/null || true
  if timeout 2 "$bin" completions bash >"$bashd/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions -> $bashd/$BINARY_NAME"
  else
    rm -f "$bashd/$BINARY_NAME"
  fi
  if timeout 2 "$bin" completions zsh >"$zshd/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions -> $zshd/_$BINARY_NAME"
  else
    rm -f "$zshd/_$BINARY_NAME"
  fi
  if timeout 2 "$bin" completions fish >"$fishd/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions -> $fishd/$BINARY_NAME.fish"
  else
    rm -f "$fishd/$BINARY_NAME.fish"
  fi
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on your PATH"
  if [ "$EASY_MODE" = 1 ]; then
    local rc=""
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      */fish) rc="$HOME/.config/fish/config.fish" ;;
      *) rc="$HOME/.profile" ;;
    esac
    printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
    ok "added $DEST to PATH in $rc (restart your shell or 'source $rc')"
  else
    info "add it with: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
  fi
}

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
  local status="prebuilt binary"
  [ "$FROM_SOURCE" = 1 ] && status="built from source"
  local verify_status="SHA256 + Sigstore verified"
  [ "$NO_VERIFY" = 1 ] && verify_status="SKIPPED (--no-verify)"
  draw_box 32 \
    "pgshim installed successfully" \
    "" \
    "binary:       $DEST/$BINARY_NAME" \
    "version:      ${VERSION:-offline}" \
    "source:       $status" \
    "verification: $verify_status" \
    "completions:  bash/zsh/fish (XDG dirs, if supported by binary)"
}

print_uninstall_hint() {
  info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "  (removes $DEST/$BINARY_NAME and shell completions; leaves Postgres config untouched)"
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  if declare -F uninstall_service >/dev/null; then uninstall_service; fi
  ok "uninstalled $BINARY_NAME. Agent hooks left in place — remove from settings.json manually if desired."
}

self_test() {
  info "self-test: verifying environment and current install"
  info "platform: $OS/$ARCH -> target $TARGET"
  command -v curl >/dev/null 2>&1 && ok "curl available" || err "curl missing"
  if command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1; then
    ok "sha256 tool available"
  else
    warn "no sha256 tool available"
  fi
  if command -v cosign >/dev/null 2>&1; then
    ok "cosign available (Sigstore verification enabled)"
  else
    warn "cosign not found (Sigstore verification will be skipped)"
  fi
  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    local p v
    p=$(command -v "$BINARY_NAME")
    v=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null || true)
    ok "installed: $p ($v)"
  else
    warn "$BINARY_NAME not currently installed"
  fi
  case ":$PATH:" in
    *":$DEST:"*) ok "$DEST is on PATH" ;;
    *) warn "$DEST is not on PATH" ;;
  esac
  exit 0
}

main() {
  parse_args "$@"
  setup_logging_flags

  if [ "$DO_UNINSTALL" = 1 ]; then
    uninstall
    exit 0
  fi

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/pgshim-install.XXXXXX")
  trap cleanup EXIT

  configure_proxy
  detect_platform

  if [ "$SELF_TEST" = 1 ]; then
    self_test
  fi

  if [ -n "$OFFLINE_TARBALL" ]; then
    VERSION="${VERSION:-offline}"
  else
    resolve_version
  fi

  preflight

  local lockfile="${XDG_CACHE_HOME:-$HOME/.cache}/pgshim-install.lock"
  if [ -z "$OFFLINE_TARBALL" ] && already_current; then
    ok "pgshim $VERSION already installed at $(command -v "$BINARY_NAME") — skipping download (use --force to reinstall)"
  else
    acquire_lock "$lockfile" 2400 || { err "could not acquire install lock (another pgshim install running?)"; exit 1; }
    if [ -n "$OFFLINE_TARBALL" ]; then
      install_offline
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  print_summary
  print_uninstall_hint
}

main "$@"