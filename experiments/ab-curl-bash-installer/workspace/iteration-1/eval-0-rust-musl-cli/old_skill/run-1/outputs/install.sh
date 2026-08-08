#!/usr/bin/env bash
#
# redlens installer
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/redlens/main/install.sh?$(date +%s)" | bash
#
# Flags (pass after `-- ` when piping, e.g. `... | bash -s -- --force`):
#   --version X.Y.Z   install a specific version (default: latest release)
#   --prefix DIR      install directory (default: $HOME/.local/bin)
#   --dest DIR        alias for --prefix
#   --force           reinstall even if the resolved version is already installed
#   --offline FILE    install from a local redlens-<version>-<target>.tar.gz, no network
#   --no-verify       skip SHA256 + Sigstore verification (not recommended)
#   --easy-mode       append the install dir to PATH in your shell rc if it's missing
#   --uninstall       remove the installed binary + completions
#   --quiet           only print errors
#   --no-color        disable ANSI colors
#   --no-gum          disable gum styling even if gum is installed
#   -h, --help        show this help and exit
#
# Env vars: REDLENS_VERSION, REDLENS_INSTALL_DIR, HTTPS_PROXY/HTTP_PROXY, NO_COLOR
#
set -euo pipefail
umask 022

OWNER="hovlabs"
REPO="redlens"
BINARY_NAME="redlens"
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/\.github/workflows/.*@refs/tags/v.*\$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

QUIET=0
FORCE=0
NO_GUM=0
NO_VERIFY=0
EASY_MODE=0
UNINSTALL=0
OFFLINE_TARBALL=""
VERSION="${REDLENS_VERSION:-}"
DEST="${REDLENS_INSTALL_DIR:-$HOME/.local/bin}"
LOCKFILE="${TMPDIR:-/tmp}/redlens-install-$(id -u).lock"

PROXY_ARGS=()
TMP=""
LOCK_DIR=""
EXTRACT_DIR=""

HAS_GUM=0
if command -v gum >/dev/null 2>&1 && [[ -t 1 ]]; then
  HAS_GUM=1
fi

_log() {
  local level="$1" color="$2" icon="$3"
  if [[ "${QUIET:-0}" == 1 && "$level" != err ]]; then
    return 0
  fi
  local msg="${*:4}"
  if [[ "$HAS_GUM" == 1 && "${NO_GUM:-0}" != 1 ]]; then
    gum style --foreground "$color" "$icon $msg"
  elif [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
    printf '%s %s\n' "$icon" "$msg"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$icon" "$msg"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

curl_fetch() {
  curl "${PROXY_ARGS[@]+"${PROXY_ARGS[@]}"}" "$@"
}

run_with_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
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

print_help() {
  cat <<EOF
redlens installer

Usage: install.sh [flags]

  --version X.Y.Z   install a specific version (default: latest release)
  --prefix DIR      install directory (default: \$HOME/.local/bin)
  --dest DIR        alias for --prefix
  --force           reinstall even if the resolved version is already installed
  --offline FILE    install from a local redlens-<version>-<target>.tar.gz, no network
  --no-verify       skip SHA256 + Sigstore verification (not recommended)
  --easy-mode       append the install dir to PATH in your shell rc if missing
  --uninstall       remove the installed binary + completions
  --quiet           only print errors
  --no-color        disable ANSI colors
  --no-gum          disable gum styling even if gum is installed
  -h, --help        show this help and exit

Env vars: REDLENS_VERSION, REDLENS_INSTALL_DIR, HTTPS_PROXY/HTTP_PROXY, NO_COLOR

Example:
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash -s -- --force
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --quiet) QUIET=1; shift ;;
      --force) FORCE=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --offline) OFFLINE_TARBALL="${2:?--offline requires a tarball path}"; shift 2 ;;
      --uninstall) UNINSTALL=1; shift ;;
      --version) VERSION="${2:?--version requires a value}"; shift 2 ;;
      --prefix|--dest) DEST="${2:?$1 requires a directory}"; shift 2 ;;
      --easy-mode) EASY_MODE=1; shift ;;
      -h|--help) print_help; exit 0 ;;
      *) err "unknown flag: $1"; print_help; exit 1 ;;
    esac
  done
}

detect_platform() {
  FROM_SOURCE=0
  OS=$(uname -s | tr 'A-Z' 'a-z'); ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features may need extra config"
  fi
}

setup_proxy() {
  if [[ -n "${HTTPS_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

cleanup() {
  local ec=$?
  if [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]]; then
    rm -rf "$LOCK_DIR"
  fi
  if [[ -n "$TMP" && -d "$TMP" ]]; then
    rm -rf "$TMP"
  fi
  exit $ec
}

acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
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

preflight() {
  local check_dir="$DEST"
  while [[ ! -d "$check_dir" ]]; do
    check_dir=$(dirname "$check_dir")
  done
  if [[ ! -w "$check_dir" ]]; then
    err "no write permission to $check_dir"
    exit 1
  fi
  local avail
  avail=$(df -Pk "$check_dir" 2>/dev/null | awk 'NR==2{print $4}' || true)
  if [[ -n "$avail" ]] && [[ "$avail" -lt 51200 ]]; then
    err "insufficient disk space in $check_dir — need ~50MB, have ${avail}KB"
    exit 1
  fi
  if ! curl_fetch -fsSL --connect-timeout 5 -o /dev/null "https://github.com" 2>/dev/null; then
    err "cannot reach github.com — check network connectivity or HTTPS_PROXY/HTTP_PROXY"
    exit 1
  fi
}

resolve_version() {
  if [[ -n "$VERSION" ]]; then
    return 0
  fi
  info "resolving latest redlens version"
  VERSION=$(curl_fetch -fsSL --connect-timeout 5 \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/' || true)
  if [[ -n "$VERSION" ]]; then
    return 0
  fi
  VERSION=$(curl_fetch -fsSL -o /dev/null -w '%{url_effective}' \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||' || true)
  if [[ -n "$VERSION" ]]; then
    return 0
  fi
  err "could not determine latest version (network/API unreachable); pass --version X.Y.Z explicitly"
  exit 1
}

check_existing_version() {
  ALREADY_CURRENT=0
  local target_bin="" cur=""
  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    target_bin="$BINARY_NAME"
  elif [[ -x "$DEST/$BINARY_NAME" ]]; then
    target_bin="$DEST/$BINARY_NAME"
  fi
  if [[ -n "$target_bin" ]]; then
    cur=$(run_with_timeout 1 "$target_bin" --version 2>/dev/null | awk '{print $NF}' || true)
    cur="${cur#v}"
    if [[ -n "$cur" && "$cur" == "$VERSION" ]]; then
      ALREADY_CURRENT=1
    fi
  fi
}

verify_checksum() {  # $1=file $2=sha256_file
  local expected actual
  expected=$(awk '{print $1}' "$2" | head -1)
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | awk '{print $1}')
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | awk '{print $1}')
  else
    warn "no sha256sum/shasum available; skipping checksum verification"
    return 0
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $(basename "$1") — want $expected got $actual"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not found; skipping signature verification"
    return 0
  fi
  if ! curl_fetch -fsSL "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle at $2; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED for $(basename "$1")"
  return 1
}

extract_and_install() {
  local archive="$1" bin
  local dir="$TMP/extracted"
  mkdir -p "$dir"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$dir" ;;
    *.tar.xz) tar -xJf "$archive" -C "$dir" ;;
    *.zip) unzip -q "$archive" -d "$dir" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  bin=$(find "$dir" -type f -name "$BINARY_NAME" | head -1)
  if [[ -z "$bin" ]]; then
    err "binary '$BINARY_NAME' not found in archive"
    return 1
  fi
  mkdir -p "$DEST"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME v$VERSION -> $DEST/$BINARY_NAME"
  EXTRACT_DIR="$dir"
}

download_and_install() {
  local artifact="${REPO}-${VERSION}-${TARGET}.tar.gz"
  local url found=0
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$artifact" \
    "https://github.com/$OWNER/$REPO/releases/download/$VERSION/$artifact"; do
    info "trying $url"
    if curl_fetch -fsSL "$url" -o "$TMP/$artifact" 2>/dev/null; then
      found=1
      break
    fi
  done
  if [[ "$found" != 1 ]]; then
    return 1
  fi
  if [[ "$NO_VERIFY" != 1 ]]; then
    if curl_fetch -fsSL "$url.sha256" -o "$TMP/$artifact.sha256" 2>/dev/null; then
      if ! verify_checksum "$TMP/$artifact" "$TMP/$artifact.sha256"; then
        err "checksum verification failed for $artifact — aborting (possible corrupt download or tampering)"
        exit 1
      fi
    else
      warn "no .sha256 file found at $url.sha256; skipping checksum verification"
    fi
    if ! verify_sigstore "$TMP/$artifact" "$url.sigstore.bundle"; then
      err "Sigstore verification failed for $artifact — aborting"
      exit 1
    fi
  fi
  extract_and_install "$TMP/$artifact"
}

build_from_source() {
  warn "falling back to build from source"
  if ! command -v cargo >/dev/null 2>&1; then
    if ! command -v rustup >/dev/null 2>&1; then
      info "installing rustup toolchain"
      curl_fetch -fsSL https://sh.rustup.rs | sh -s -- -y -q || { err "rustup install failed"; exit 1; }
    fi
    export PATH="$HOME/.cargo/bin:$PATH"
    command -v cargo >/dev/null 2>&1 || { err "cargo still not found after rustup install"; exit 1; }
  fi
  command -v git >/dev/null 2>&1 || { err "git is required to build from source"; exit 1; }
  local src="$TMP/src"
  if ! git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null; then
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" || { err "git clone failed"; exit 1; }
  fi
  ( cd "$src" && cargo build --release ) || { err "cargo build failed"; exit 1; }
  local bin="$src/target/release/$BINARY_NAME"
  if [[ ! -x "$bin" ]]; then
    err "built binary not found at $bin"
    exit 1
  fi
  mkdir -p "$DEST"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME -> $DEST/$BINARY_NAME"
  EXTRACT_DIR="$src"
}

install_offline() {
  if [[ ! -f "$OFFLINE_TARBALL" ]]; then
    err "offline tarball not found: $OFFLINE_TARBALL"
    exit 1
  fi
  mkdir -p "$DEST"
  if [[ "$NO_VERIFY" != 1 ]]; then
    if [[ -f "$OFFLINE_TARBALL.sha256" ]]; then
      if ! verify_checksum "$OFFLINE_TARBALL" "$OFFLINE_TARBALL.sha256"; then
        err "checksum verification failed — aborting"
        exit 1
      fi
    else
      warn "no .sha256 sidecar next to $OFFLINE_TARBALL; skipping checksum"
    fi
  fi
  extract_and_install "$OFFLINE_TARBALL"
  VERSION="${VERSION:-unknown (offline install)}"
}

setup_completions() {
  if [[ -z "$EXTRACT_DIR" ]]; then
    return 0
  fi
  local comp_dir
  comp_dir=$(find "$EXTRACT_DIR" -type d -name completions 2>/dev/null | head -1)
  if [[ -z "$comp_dir" ]]; then
    warn "no completions/ directory found; skipping"
    return 0
  fi

  local bash_dst="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dst="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local bash_src zsh_src

  bash_src=$(find "$comp_dir" -maxdepth 1 -iname "${BINARY_NAME}.bash" | head -1)
  if [[ -n "$bash_src" ]]; then
    mkdir -p "$bash_dst"
    install -m 0644 "$bash_src" "$bash_dst/$BINARY_NAME"
    ok "bash completions -> $bash_dst/$BINARY_NAME"
  else
    warn "bash completion file not found in tarball"
  fi

  zsh_src=$(find "$comp_dir" -maxdepth 1 \( -iname "_${BINARY_NAME}" -o -iname "${BINARY_NAME}.zsh" \) | head -1)
  if [[ -n "$zsh_src" ]]; then
    mkdir -p "$zsh_dst"
    install -m 0644 "$zsh_src" "$zsh_dst/_${BINARY_NAME}"
    ok "zsh completions -> $zsh_dst/_${BINARY_NAME}"
  else
    warn "zsh completion file not found in tarball"
  fi
}

detect_shell_rc() {
  case "${SHELL:-}" in
    */zsh) echo "$HOME/.zshrc" ;;
    */bash) echo "$HOME/.bashrc" ;;
    *) echo "$HOME/.profile" ;;
  esac
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *)
      warn "$DEST is not on your PATH"
      if [[ "$EASY_MODE" == 1 ]]; then
        local rc
        rc=$(detect_shell_rc)
        printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
        ok "added $DEST to PATH in $rc (restart your shell or: source $rc)"
      else
        info "add this to your shell rc: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_${BINARY_NAME}"
  ok "uninstalled $BINARY_NAME"
  info "config (if any) left in place"
}

print_summary() {
  draw_box 42 \
    "\033[1mredlens\033[0m installed" \
    "version : $VERSION" \
    "binary  : $DEST/$BINARY_NAME" \
    "" \
    "uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
}

main() {
  parse_args "$@"

  if [[ "$UNINSTALL" == 1 ]]; then
    uninstall
    exit 0
  fi

  detect_platform
  setup_proxy

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/redlens-install.XXXXXX")
  trap cleanup EXIT

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    install_offline
  else
    preflight
    if ! acquire_lock "$LOCKFILE" 2400; then
      err "could not acquire install lock at $LOCKFILE (another install already running?)"
      exit 1
    fi

    resolve_version
    VERSION="${VERSION#v}"
    check_existing_version

    local completions_present=0
    if [[ -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" ]]; then
      completions_present=1
    fi

    if [[ "$ALREADY_CURRENT" == 1 && "$FORCE" != 1 && "$completions_present" == 1 ]]; then
      ok "redlens v$VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
    elif [[ "$FROM_SOURCE" == 1 ]]; then
      build_from_source
    else
      if ! download_and_install; then
        build_from_source
      fi
    fi
  fi

  setup_completions
  check_path
  print_summary
}

main "$@"