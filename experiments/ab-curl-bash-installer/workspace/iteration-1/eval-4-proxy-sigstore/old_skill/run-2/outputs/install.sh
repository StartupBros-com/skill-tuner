#!/usr/bin/env bash
#
# pgshim installer — installs the pgshim Postgres connection shim binary.
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION   Install a specific version (default: resolve latest)
#   --dest DIR           Install directory (default: $PGSHIM_INSTALL_DIR or ~/.local/bin)
#   --force               Reinstall even if the target version is already installed
#   --no-verify           Skip SHA256 checksum and Sigstore signature verification
#   --offline TARBALL     Install from a local tarball, no network calls (airgap mode)
#   --easy-mode            Append install dir to PATH in your shell rc if missing
#   --quiet                 Errors only
#   --no-color               Disable ANSI/gum colored output
#   --no-gum                  Disable gum styling even if gum is installed
#   --self-test               Check local environment/dependencies and exit
#   --uninstall                Remove pgshim and its completions
#   -h, --help                  Show this help
#
# Env: HTTPS_PROXY / HTTP_PROXY (corporate proxy), NO_COLOR, PGSHIM_INSTALL_DIR,
#      PGSHIM_VERSION, COSIGN_CERT_IDENTITY_REGEXP, COSIGN_OIDC_ISSUER

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

OWNER="hovlabs"
REPO="pgshim"
BINARY_NAME="pgshim"

VERSION="${PGSHIM_VERSION:-}"
DEST="${PGSHIM_INSTALL_DIR:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
FORCE=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
QUIET=0
NO_COLOR_FLAG=0
NO_GUM_FLAG=0
SELF_TEST=0
DO_UNINSTALL=0
SHOW_HELP=0

COSIGN_OIDC_ISSUER="${COSIGN_OIDC_ISSUER:-https://token.actions.githubusercontent.com}"
COSIGN_CERT_IDENTITY_REGEXP="${COSIGN_CERT_IDENTITY_REGEXP:-^https://github.com/${OWNER}/${REPO}/\.github/workflows/.+@refs/heads/.+$}"

TMP=""
LOCKFILE="${TMPDIR:-/tmp}/.${BINARY_NAME}-install.lock"
SKIP_DOWNLOAD=0
INSTALL_STATUS="not attempted"
COMPLETIONS_STATUS="skipped"

# ---------- output stack ----------
HAS_GUM_BIN=0
command -v gum >/dev/null 2>&1 && HAS_GUM_BIN=1
USE_COLOR=1
[ -t 1 ] || USE_COLOR=0
[ -n "${NO_COLOR:-}" ] && USE_COLOR=0

_log() {  # $1=color $2=glyph $3=level, rest=message
  local color="$1" glyph="$2" level="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM_BIN" = 1 ] && [ "$NO_GUM_FLAG" = 0 ] && [ "$USE_COLOR" = 1 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$USE_COLOR" = 1 ]; then
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  else
    printf '%s %s\n' "$glyph" "$*"
  fi
}
info() { _log 39 '->' info "$@"; }
ok()   { _log 42 '✓'  ok "$@"; }
warn() { _log 214 '⚠' warn "$@"; }
err()  { _log 196 '✗' err "$@" 1>&2; }

cleanup() {
  local rc=$?
  [ -n "$TMP" ] && rm -rf "$TMP"
  [ -d "${LOCKFILE}.d" ] && [ "${LOCK_OWNED:-0}" = 1 ] && rm -rf "${LOCKFILE}.d"
  return $rc
}

print_help() {
  cat <<'EOF'
pgshim installer

Usage: install.sh [flags]

  --version VERSION      Install a specific version (default: resolve latest)
  --dest DIR              Install directory (default: $PGSHIM_INSTALL_DIR or ~/.local/bin)
  --force                  Reinstall even if the target version is already installed
  --no-verify              Skip SHA256 checksum and Sigstore signature verification
  --offline TARBALL        Install from a local tarball, no network calls
  --easy-mode                Append install dir to PATH in your shell rc if missing
  --quiet                     Errors only
  --no-color                   Disable ANSI/gum colored output
  --no-gum                      Disable gum styling even if gum is installed
  --self-test                    Check local environment/dependencies and exit
  --uninstall                     Remove pgshim and its completions
  -h, --help                        Show this help

Env: HTTPS_PROXY / HTTP_PROXY, NO_COLOR, PGSHIM_INSTALL_DIR, PGSHIM_VERSION,
     COSIGN_CERT_IDENTITY_REGEXP, COSIGN_OIDC_ISSUER
EOF
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --dest) DEST="$2"; shift 2 ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR_FLAG=1; USE_COLOR=0; shift ;;
      --no-gum) NO_GUM_FLAG=1; shift ;;
      --self-test) SELF_TEST=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      -h|--help) SHOW_HELP=1; shift ;;
      *) err "unknown flag: $1"; print_help; exit 1 ;;
    esac
  done
}

# ---------- platform ----------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z'); ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  FROM_SOURCE=0
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features may need extra config"
  fi
}

# ---------- proxy ----------
PROXY_ARGS=()
setup_proxy() {
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
  [ "${#PROXY_ARGS[@]}" -gt 0 ] && info "using proxy: ${PROXY_ARGS[1]}"
}

# ---------- version resolution ----------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                             # 1. flag/env

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && { info "resolved version $VERSION via GitHub API"; return 0; }  # 2. API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && { info "resolved version $VERSION via redirect"; return 0; }     # 3. redirect

  err "could not resolve latest version (network/proxy issue?); pass --version explicitly"
  exit 1
}

# ---------- preflight ----------
preflight_network() {
  curl -fsSL -o /dev/null --connect-timeout 5 "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null \
    || { err "cannot reach github.com — check network/HTTPS_PROXY"; exit 1; }
}

preflight() {
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install dir: $DEST"; exit 1; }
  [ -w "$DEST" ] || { err "install dir not writable: $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}') || true
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "less than 50MB free at $DEST"; exit 1
  fi

  for c in curl tar mkdir install; do
    command -v "$c" >/dev/null 2>&1 || { err "required tool missing: $c"; exit 1; }
  done
}

check_existing_install() {
  local bin="$DEST/$BINARY_NAME" cur=""
  [ -x "$bin" ] || return 0
  cur=$(timeout 1 "$bin" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) || true
  if [ -n "$cur" ] && [ "$cur" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
    SKIP_DOWNLOAD=1
  fi
}

# ---------- lock ----------
LOCK_OWNED=0
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; LOCK_OWNED=1; return $?; }
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
  LOCK_OWNED=1
}

# ---------- checksum + sigstore ----------
fetch_sidecar_sha() {  # $1=artifact_url -> prints hash or empty
  local base="${1%.tar.gz}"
  curl -fsSL "${PROXY_ARGS[@]}" "${base}.sha256" 2>/dev/null | awk '{print $1; exit}' || true
}

verify_checksum() {  # $1=file $2=expected
  local a=""
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool available; skipping checksum"; return 0; fi
  if [ "$a" = "$2" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2 got $a)"; return 1; fi
}

verify_sigstore() {  # $1=file $2=artifact_url
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore signature check"
    return 0
  fi
  local base="${2%.tar.gz}"
  if ! curl -fsSL "${PROXY_ARGS[@]}" "${base}.sigstore.json" -o "$TMP/sig.json" 2>/dev/null; then
    err "cosign is present but no Sigstore bundle was found at ${base}.sigstore.json"
    return 1
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_CERT_IDENTITY_REGEXP" \
      --certificate-oidc-issuer "$COSIGN_OIDC_ISSUER" "$1" 2>/dev/null; then
    ok "Sigstore signature verified (GitHub Actions OIDC)"
    return 0
  else
    err "Sigstore verification FAILED — refusing to install unsigned/tampered binary"
    return 1
  fi
}

# ---------- extract + install ----------
extract_and_install() {  # $1=archive
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$1" -C "$TMP" ;;
    *.zip) unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin; bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME $VERSION → $DEST/$BINARY_NAME"
}

verify_and_install() {  # $1=archive $2=source_url
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify set: skipping checksum and signature verification"
  else
    local expected; expected=$(fetch_sidecar_sha "$2")
    if [ -z "$expected" ]; then
      err "no .sha256 sidecar found for $2"; return 1
    fi
    verify_checksum "$1" "$expected" || return 1
    verify_sigstore "$1" "$2" || return 1
  fi
  extract_and_install "$1"
}

download_and_install() {
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/download/$VERSION/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
  )
  if [ "$FROM_SOURCE" != 1 ]; then
    local url
    for url in "${urls[@]}"; do
      if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
        if verify_and_install "$TMP/artifact.tar.gz" "$url"; then
          INSTALL_STATUS="downloaded (${url##*/})"
          return 0
        fi
        rm -f "$TMP/artifact.tar.gz"
      fi
    done
    warn "no prebuilt binary available or verification failed; building from source"
  fi
  build_from_source
}

build_from_source() {
  command -v git >/dev/null 2>&1 || { err "git required to build from source"; exit 1; }
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || { err "source clone failed"; exit 1; }

  if [ -f "$src/go.mod" ]; then
    command -v go >/dev/null 2>&1 || { err "go toolchain required to build from source"; exit 1; }
    ( cd "$src" && go build -o "$TMP/$BINARY_NAME" . ) || { err "source build failed"; exit 1; }
  elif [ -f "$src/Cargo.toml" ]; then
    if ! command -v cargo >/dev/null 2>&1; then
      command -v rustup >/dev/null 2>&1 && rustup default stable >/dev/null 2>&1
    fi
    command -v cargo >/dev/null 2>&1 || { err "cargo required to build from source"; exit 1; }
    ( cd "$src" && cargo build --release ) || { err "source build failed"; exit 1; }
    cp "$src/target/release/$BINARY_NAME" "$TMP/$BINARY_NAME"
  else
    err "no recognized build system (go.mod/Cargo.toml) in $REPO"; exit 1
  fi

  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
  INSTALL_STATUS="built from source"
}

install_from_local() {  # $1=tarball
  local archive="$1" expected="" base
  [ -f "$archive" ] || { err "offline tarball not found: $archive"; exit 1; }
  base="${archive%.tar.gz}"
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify set: skipping checksum and signature verification"
  else
    if [ -f "${base}.sha256" ]; then
      expected=$(awk '{print $1; exit}' "${base}.sha256")
      verify_checksum "$archive" "$expected" || exit 1
    else
      warn "no local .sha256 sidecar next to $archive; skipping checksum"
    fi
    if command -v cosign >/dev/null 2>&1; then
      if [ -f "${base}.sigstore.json" ]; then
        cosign verify-blob --bundle "${base}.sigstore.json" \
          --certificate-identity-regexp "$COSIGN_CERT_IDENTITY_REGEXP" \
          --certificate-oidc-issuer "$COSIGN_OIDC_ISSUER" "$archive" 2>/dev/null \
          && ok "Sigstore signature verified" \
          || { err "Sigstore verification FAILED"; exit 1; }
      else
        err "cosign is present but no local .sigstore.json sidecar next to $archive"
        exit 1
      fi
    else
      warn "cosign not installed; skipping Sigstore signature check"
    fi
  fi
  extract_and_install "$archive"
  INSTALL_STATUS="installed offline from $archive"
}

# ---------- completions ----------
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  if ! "$bin" completion bash >/dev/null 2>&1; then
    warn "binary does not support 'completion' subcommand; skipping shell completions"
    return 0
  fi
  local d
  d="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"; mkdir -p "$d"
  "$bin" completion bash > "$d/$BINARY_NAME" 2>/dev/null && ok "bash completion installed"
  d="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"; mkdir -p "$d"
  "$bin" completion zsh > "$d/_$BINARY_NAME" 2>/dev/null && ok "zsh completion installed"
  d="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"; mkdir -p "$d"
  "$bin" completion fish > "$d/$BINARY_NAME.fish" 2>/dev/null && ok "fish completion installed"
  COMPLETIONS_STATUS="installed"
}

# ---------- PATH ----------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on your PATH"
  if [ "$EASY_MODE" != 1 ]; then
    info "add it with: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
    return 0
  fi
  local shell_name; shell_name=$(basename "${SHELL:-bash}")
  case "$shell_name" in
    fish)
      mkdir -p "$HOME/.config/fish"
      printf '\nfish_add_path %s\n' "$DEST" >> "$HOME/.config/fish/config.fish"
      ok "added $DEST to PATH in ~/.config/fish/config.fish"
      ;;
    zsh)
      printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$HOME/.zshrc"
      ok "added $DEST to PATH in ~/.zshrc"
      ;;
    *)
      printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$HOME/.bashrc"
      ok "added $DEST to PATH in ~/.bashrc"
      ;;
  esac
  info "restart your shell or source the rc file to pick up PATH"
}

# ---------- box + summary ----------
draw_box() {  # $1=color, rest=lines
  local color="$1"; shift; local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); [ "${#s}" -gt "$max" ] && max=${#s}; done
  local inner=$((max+4)) border="" i
  for ((i=0;i<inner;i++)); do border+="═"; done
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); local pad=$((max-${#s})) p="" j
    for ((j=0;j<pad;j++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

final_summary() {
  [ "$QUIET" = 1 ] && return 0
  draw_box 42 \
    "pgshim install complete" \
    "" \
    "binary:      $DEST/$BINARY_NAME" \
    "version:     $VERSION" \
    "status:      $INSTALL_STATUS" \
    "completions: $COMPLETIONS_STATUS"
}

print_uninstall() {
  [ "$QUIET" = 1 ] && return 0
  echo
  info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "or locally:   $0 --uninstall"
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME"
}

# ---------- self test ----------
self_test() {
  local rc=0
  for c in curl tar install mkdir df; do
    if command -v "$c" >/dev/null 2>&1; then ok "$c present"; else err "$c missing"; rc=1; fi
  done
  if command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1; then
    ok "sha256 tool present"
  else
    err "no sha256 tool (sha256sum/shasum)"; rc=1
  fi
  command -v cosign >/dev/null 2>&1 && ok "cosign present — Sigstore verification will run" \
    || warn "cosign absent — Sigstore verification will be soft-skipped"
  command -v flock >/dev/null 2>&1 && ok "flock present" || warn "flock absent — using mkdir spinlock fallback"
  [ -n "${HTTPS_PROXY:-}${HTTP_PROXY:-}" ] && info "proxy configured: ${HTTPS_PROXY:-$HTTP_PROXY}" \
    || info "no proxy configured"
  [ -w "$DEST" ] || mkdir -p "$DEST" 2>/dev/null
  [ -w "$DEST" ] && ok "install dir writable: $DEST" || { err "install dir not writable: $DEST"; rc=1; }
  return $rc
}

# ---------- main ----------
main() {
  parse_args "$@"
  [ "$SHOW_HELP" = 1 ] && { print_help; exit 0; }
  [ "$DO_UNINSTALL" = 1 ] && { uninstall; exit 0; }
  [ "$SELF_TEST" = 1 ] && { self_test; exit $?; }

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")
  trap cleanup EXIT

  detect_platform
  setup_proxy

  if [ -n "$OFFLINE_TARBALL" ]; then
    info "offline mode: installing from $OFFLINE_TARBALL"
    VERSION="${VERSION:-offline}"
    preflight
    acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install running?)"; exit 1; }
    install_from_local "$OFFLINE_TARBALL"
  else
    preflight_network
    resolve_version
    preflight
    check_existing_install
    acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install running?)"; exit 1; }
    if [ "$SKIP_DOWNLOAD" = 1 ]; then
      info "$BINARY_NAME $VERSION already installed at $DEST/$BINARY_NAME; skipping download (use --force to reinstall)"
      INSTALL_STATUS="already installed (unchanged)"
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  final_summary
  print_uninstall
}

main "$@"