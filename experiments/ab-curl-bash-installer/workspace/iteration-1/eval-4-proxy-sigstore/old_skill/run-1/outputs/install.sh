#!/usr/bin/env bash
#
# pgshim installer — https://github.com/hovlabs/pgshim
#
# Usage:
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash -s -- [flags]
#
# Flags:
#   --version VERSION   Install a specific version (default: latest)
#   --prefix DIR        Install directory (default: /usr/local/bin if writable, else ~/.local/bin)
#   --force             Reinstall even if the requested version is already installed
#   --no-verify         Skip SHA256 / Sigstore verification (NOT recommended)
#   --offline TARBALL   Install from a local tarball, no network calls
#   --easy-mode         Append the install dir to PATH in your shell rc file
#   --uninstall         Remove pgshim and its shell completions
#   --quiet             Errors only
#   --no-color          Disable ANSI colors (also honored via $NO_COLOR)
#   --no-gum            Disable gum styling, fall back to plain ANSI
#   -h, --help          Show this help
#
# Env:
#   HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call (NO_PROXY honored natively by curl)
#   NO_COLOR                   Disable ANSI colors
#   PGSHIM_VERSION              Same as --version
#
# Security: every downloaded artifact is SHA256-verified against its companion .sha256 file.
# When `cosign` is present, the .sigstore.json bundle is also verified against hovlabs/pgshim's
# GitHub Actions OIDC identity; verification failure aborts the install (no silent fallback).

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# --- constants ---------------------------------------------------------
OWNER="hovlabs"
REPO="pgshim"
BINARY_NAME="pgshim"
FALLBACK_VERSION="0.1.0"   # last-resort only; bumped by release CI on each tag push
# TODO(security): narrow to the exact release workflow filename once stable, e.g.
# ".github/workflows/release.yml" instead of the current any-workflow wildcard.
COSIGN_ID_RE='^https://github\.com/hovlabs/pgshim/\.github/workflows/[^@]+@refs/tags/v[0-9].*$'
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# --- defaults ------------------------------------------------------------
VERSION="${PGSHIM_VERSION:-}"
PREFIX=""
FORCE=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
QUIET=0
NO_GUM=0
NO_COLOR_ON_FLAG=0
DO_UNINSTALL=0
FROM_SOURCE=0
TMP=""
LOCK_DIR=""

usage() {
  cat <<'EOF'
pgshim installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash
  ... | bash -s -- [flags]

Flags:
  --version VERSION   Install a specific version (default: latest)
  --prefix DIR        Install directory (default: /usr/local/bin if writable, else ~/.local/bin)
  --force             Reinstall even if the requested version is already installed
  --no-verify         Skip SHA256 / Sigstore verification (NOT recommended)
  --offline TARBALL   Install from a local tarball, no network calls
  --easy-mode         Append the install dir to PATH in your shell rc file
  --uninstall         Remove pgshim and its shell completions
  --quiet             Errors only
  --no-color          Disable ANSI colors (also honored via $NO_COLOR)
  --no-gum            Disable gum styling, fall back to plain ANSI
  -h, --help          Show this help

Env:
  HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call
  NO_COLOR                    Disable ANSI colors
  PGSHIM_VERSION               Same as --version
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --version=*) VERSION="${1#*=}"; shift ;;
      --prefix) PREFIX="$2"; shift 2 ;;
      --prefix=*) PREFIX="${1#*=}"; shift ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
      --offline=*) OFFLINE_TARBALL="${1#*=}"; shift ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR_ON_FLAG=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) echo "unknown flag: $1" >&2; usage; exit 1 ;;
    esac
  done
}

# --- output stack: gum-if-TTY, ANSI fallback, honor NO_COLOR + non-TTY ---
HAS_GUM=0
NO_COLOR_ON=0

setup_output() {
  command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
  [ -n "${NO_COLOR:-}" ] && NO_COLOR_ON=1
  [ "$NO_COLOR_ON_FLAG" = 1 ] && NO_COLOR_ON=1
  [ -t 1 ] || NO_COLOR_ON=1
}

_log() {  # $1=level $2=color $3=glyph $4..=message
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  local line
  if [ "$NO_COLOR_ON" = 1 ]; then
    line="$glyph $*"
  elif [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    line=$(gum style --foreground "$color" "$glyph $*")
  else
    line=$(printf '\033[%sm%s\033[0m %s' "$color" "$glyph" "$*")
  fi
  if [ "$level" = err ]; then printf '%s\n' "$line" >&2; else printf '%s\n' "$line"; fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

draw_box() {  # $1=color, rest=lines
  local color="$1"; shift; local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); (( ${#s} > max )) && max=${#s}; done
  local inner=$((max+4)) border=""; for ((i=0;i<inner;i++)); do border+="═"; done
  if [ "$NO_COLOR_ON" = 1 ]; then
    printf "╔%s╗\n" "$border"
    for l in "${lines[@]}"; do
      local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); local pad=$((max-${#s})) p=""
      for ((i=0;i<pad;i++)); do p+=" "; done
      printf "║  %s%s  ║\n" "$s" "$p"
    done
    printf "╚%s╝\n" "$border"
    return 0
  fi
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip"); local pad=$((max-${#s})) p=""
    for ((i=0;i<pad;i++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

cleanup() {
  local ec=$?
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP"
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR"
  exit $ec
}

# --- platform detection --------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1; TARGET="${OS}-${ARCH}" ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features (e.g. keychain integration) may need extra config"
  fi
}

resolve_dest() {
  if [[ -n "$PREFIX" ]]; then
    DEST="$PREFIX"
  elif [[ -w /usr/local/bin ]] || { [[ ! -e /usr/local/bin ]] && [[ -w /usr/local ]]; }; then
    DEST="/usr/local/bin"
  else
    DEST="${XDG_BIN_HOME:-$HOME/.local/bin}"
  fi
}

# --- version resolution: flag/env -> manifest -> GH API -> redirect -> hardcoded
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  if [[ -f Cargo.toml ]]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [[ -z "$VERSION" && -f package.json ]] && VERSION=$(grep -m1 '"version"' package.json | sed -E 's/.*"([0-9][^"]*)".*/\1/')
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL --connect-timeout 10 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' --connect-timeout 10 "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"
  [[ -n "$VERSION" ]] || { err "could not resolve a version to install"; exit 1; }
}

# --- atomic lock: flock-first, mkdir spinlock fallback, stale-PID self-heal
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || { err "cannot open lock file: $lf"; return 1; }
    if flock -w "$w" 9; then return 0; else err "timed out waiting for install lock (flock)"; return 1; fi
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    if (( $(date +%s) - start >= w )); then err "timed out waiting for install lock: $d"; return 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
  return 0
}

# --- verification: SHA256 is always required; Sigstore is soft-skip/hard-fail on cosign presence
verify_checksum() {  # $1=file $2=sha256 companion file
  local file="$1" shafile="$2" expected actual
  expected=$(awk '{print $1; exit}' "$shafile" 2>/dev/null || true)
  if [[ -z "$expected" ]]; then err "empty or unreadable checksum file: $shafile"; return 1; fi
  if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else err "no SHA256 tool (sha256sum/shasum) found; refusing to install unverified — pass --no-verify to override"; return 1
  fi
  if [[ "$actual" == "$expected" ]]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch for $file (want $expected, got $actual)"; return 1
  fi
}

verify_sigstore() {  # $1=file $2=sigstore bundle
  local file="$1" bundle="$2"
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not found; skipping Sigstore signature verification"
    return 0
  fi
  if [[ ! -s "$bundle" ]]; then
    warn "no Sigstore bundle available; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$file" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore verification FAILED for $file — refusing to install"
    return 1
  fi
}

atomic_install_binary() {  # $1=path to built/extracted binary
  local src="$1" tmp_dest
  mkdir -p "$DEST"
  tmp_dest="$DEST/.$BINARY_NAME.tmp.$$"
  install -m 0755 "$src" "$tmp_dest"
  mv -f "$tmp_dest" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

extract_and_install() {  # $1=archive
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$archive" -C "$TMP" ;;
    *.zip) unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin; bin=$(find "$TMP" -maxdepth 3 -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  atomic_install_binary "$bin"
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      info "installing Rust toolchain via rustup"
      rustup default stable >/dev/null 2>&1 || true
    else
      err "no prebuilt binary for $TARGET and no Rust toolchain (cargo) available"
      err "install Rust from https://rustup.rs and re-run, or use --offline with a local tarball"
      return 1
    fi
  fi
  command -v git >/dev/null 2>&1 || { err "git is required to build from source"; return 1; }
  local src="$TMP/src"
  info "cloning $OWNER/$REPO (depth 1, tag v$VERSION) and building from source — this may take a while"
  if ! git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null; then
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  fi
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [[ -x "$bin" ]] || { err "build succeeded but binary not found at $bin"; return 1; }
  atomic_install_binary "$bin"
}

download_and_install() {
  if [[ "$FROM_SOURCE" == 1 ]]; then
    build_from_source
    return $?
  fi
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$BINARY_NAME-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$BINARY_NAME-$TARGET.tar.gz"
  )
  local url found=0
  for url in "${urls[@]}"; do
    info "downloading $url"
    if ! curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      continue
    fi
    found=1
    if [[ "$NO_VERIFY" != 1 ]]; then
      if ! curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" -o "$TMP/artifact.tar.gz.sha256" 2>/dev/null; then
        err "checksum file unavailable: ${url}.sha256 — refusing to install an unverified binary"
        return 1
      fi
      verify_checksum "$TMP/artifact.tar.gz" "$TMP/artifact.tar.gz.sha256" || return 1
      curl -fsSL "${PROXY_ARGS[@]}" "${url}.sigstore.json" -o "$TMP/artifact.tar.gz.sigstore.json" 2>/dev/null || true
      verify_sigstore "$TMP/artifact.tar.gz" "$TMP/artifact.tar.gz.sigstore.json" || return 1
    else
      warn "--no-verify: skipping SHA256 and Sigstore verification"
    fi
    extract_and_install "$TMP/artifact.tar.gz"
    return $?
  done
  if [[ "$found" == 1 ]]; then
    return 1
  fi
  warn "no prebuilt binary found for $TARGET at any release tier; building from source"
  build_from_source
}

preflight() {
  local check_dir="$DEST"
  [[ -d "$check_dir" ]] || check_dir=$(dirname "$DEST")
  [[ -d "$check_dir" ]] || check_dir="/"
  local avail_kb; avail_kb=$(df -Pk "$check_dir" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    err "insufficient disk space at $check_dir (need ~50MB, have $((avail_kb/1024))MB)"; exit 1
  fi

  if [[ -d "$DEST" ]]; then
    [[ -w "$DEST" ]] || { err "no write permission to $DEST — pass --prefix DIR or fix permissions"; exit 1; }
  else
    local parent; parent=$(dirname "$DEST")
    [[ -w "$parent" ]] || { err "no write permission to $parent (to create $DEST)"; exit 1; }
  fi

  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    local cur=""
    if command -v timeout >/dev/null 2>&1; then
      cur=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    fi
    if [[ -n "$cur" && "$cur" == "$VERSION" && "$FORCE" != 1 ]]; then
      ok "$BINARY_NAME $VERSION already installed at $(command -v "$BINARY_NAME") — pass --force to reinstall"
      install_completions
      check_path
      print_summary "already up to date"
      exit 0
    fi
  fi

  if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
    err "cannot reach github.com — check network/proxy settings (HTTPS_PROXY/HTTP_PROXY), or use --offline TARBALL"
    exit 1
  fi
}

install_offline() {
  [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  info "offline mode — installing from $OFFLINE_TARBALL (no network calls)"
  VERSION="${VERSION:-local}"
  if [[ "$NO_VERIFY" != 1 ]]; then
    if [[ -f "${OFFLINE_TARBALL}.sha256" ]]; then
      verify_checksum "$OFFLINE_TARBALL" "${OFFLINE_TARBALL}.sha256" || exit 1
    else
      warn "no ${OFFLINE_TARBALL}.sha256 found alongside the tarball; skipping checksum verification"
    fi
    if [[ -f "${OFFLINE_TARBALL}.sigstore.json" ]]; then
      verify_sigstore "$OFFLINE_TARBALL" "${OFFLINE_TARBALL}.sigstore.json" || exit 1
    fi
  else
    warn "--no-verify: skipping SHA256 and Sigstore verification"
  fi
  extract_and_install "$OFFLINE_TARBALL" || exit 1
}

install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  local bin="$DEST/$BINARY_NAME"
  [[ -x "$bin" ]] || return 0
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  if "$bin" completions bash > "$TMP/_bash_comp" 2>/dev/null; then
    install -m 0644 "$TMP/_bash_comp" "$bash_dir/$BINARY_NAME"
    ok "bash completions → $bash_dir/$BINARY_NAME"
  else
    warn "'$BINARY_NAME completions' not supported by this build; skipping shell completions"
    return 0
  fi
  "$bin" completions zsh  > "$TMP/_zsh_comp"  2>/dev/null && install -m 0644 "$TMP/_zsh_comp"  "$zsh_dir/_$BINARY_NAME"
  "$bin" completions fish > "$TMP/_fish_comp" 2>/dev/null && install -m 0644 "$TMP/_fish_comp" "$fish_dir/$BINARY_NAME.fish"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
      warn "$DEST is not on your PATH"
      if [[ "$EASY_MODE" == 1 ]]; then
        local rc
        case "${SHELL:-}" in
          */zsh) rc="$HOME/.zshrc" ;;
          */fish) rc="$HOME/.config/fish/config.fish" ;;
          *) rc="$HOME/.bashrc" ;;
        esac
        if ! grep -qF "$DEST" "$rc" 2>/dev/null; then
          printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
          ok "added $DEST to PATH in $rc — restart your shell or run: source $rc"
        fi
      else
        info "add it to your PATH, e.g.: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

do_uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME from $DEST. Config, if any, was left in place."
}

print_summary() {
  local status="$1" verified_line
  if [[ "$NO_VERIFY" == 1 ]]; then
    verified_line="skipped (--no-verify)"
  else
    verified_line="SHA256 required + Sigstore (when cosign present)"
  fi
  draw_box 42 \
    "pgshim ${VERSION} — ${status}" \
    "" \
    "Binary:      ${DEST}/${BINARY_NAME}" \
    "Completions: bash/zsh/fish (XDG paths, if supported by this build)" \
    "Verified:    ${verified_line}" \
    "" \
    "Uninstall:   curl -fsSL https://raw.githubusercontent.com/${OWNER}/${REPO}/main/install.sh | bash -s -- --uninstall"
}

main() {
  parse_args "$@"
  setup_output

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/pgshim-install.XXXXXX")
  trap cleanup EXIT

  detect_platform

  PROXY_ARGS=()
  [[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  [[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

  resolve_dest

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    do_uninstall
    exit 0
  fi

  local lockfile="/tmp/.pgshim-install-$(id -u 2>/dev/null || echo shared).lock"
  acquire_lock "$lockfile" 2400 || exit 1

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    install_offline
  else
    resolve_version
    preflight
    download_and_install || exit 1
  fi

  install_completions
  check_path
  print_summary "installed"
}

main "$@"