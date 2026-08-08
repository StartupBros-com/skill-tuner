#!/usr/bin/env bash
#
# redlens installer
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/redlens/main/install.sh?$(date +%s)" | bash
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/redlens/main/install.sh?$(date +%s)" | bash -s -- --version 1.4.0
#
# Flags (pass after `--` when piping into bash):
#   --version VERSION   Install a specific version instead of latest
#   --prefix DIR        Install directory (default: $HOME/.local/bin)
#   --force             Reinstall even if the same version is already installed
#   --no-verify         Skip SHA256 checksum verification (NOT recommended)
#   --offline TARBALL   Install from a local tarball, no network calls
#   --uninstall         Remove redlens and exit
#   --quiet             Only print errors
#   --no-color          Disable ANSI colors
#   --no-gum            Disable gum styling even if gum is installed
#   -h, --help          Show this help and exit
#
# Env:
#   HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call
#   NO_COLOR                    Disable colors (same as --no-color)

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# --- constants ---------------------------------------------------------
OWNER="hovlabs"
REPO="redlens"
BINARY_NAME="redlens"
COSIGN_ID_RE="https://github\.com/${OWNER}/${REPO}/\.github/workflows/.*"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# --- defaults ------------------------------------------------------------
VERSION=""
PREFIX="${PREFIX:-$HOME/.local/bin}"
FORCE=0
NO_VERIFY=0
OFFLINE_TARBALL=""
QUIET=0
NO_COLOR_FLAG=0
NO_GUM_FLAG=0
DO_UNINSTALL=0

TMP=""
OS="" ARCH="" TARGET=""
FROM_SOURCE=0
SKIP_DOWNLOAD=0
EXTRACT_DIR=""
BASH_COMPLETION_INSTALLED=""
ZSH_COMPLETION_INSTALLED=""
PATH_WARNED=0
LOCK_FD_OPENED=0
LOCK_DIR=""

# --- output stack: gum-if-TTY, ANSI fallback, honors NO_COLOR/non-TTY --
_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" = 1 && "$level" != err ]] && return 0
  local use_gum=0 use_color=1
  command -v gum >/dev/null 2>&1 && [[ -t 1 ]] && [[ "$NO_GUM_FLAG" = 0 ]] && use_gum=1
  { [[ -n "${NO_COLOR:-}" ]] || [[ "$NO_COLOR_FLAG" = 1 ]] || [[ ! -t 1 ]]; } && use_color=0
  if [[ "$use_gum" = 1 ]]; then
    gum style --foreground "$color" "$glyph $*"
  elif [[ "$use_color" = 1 ]]; then
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  else
    printf '%s %s\n' "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@" 1>&2; }
err()  { _log err  196 '✗'  "$@" 1>&2; }
die()  { err "$@"; exit 1; }

print_help() {
  cat <<'EOF'
redlens installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/hovlabs/redlens/main/install.sh?$(date +%s)" | bash
  curl -fsSL ".../install.sh?$(date +%s)" | bash -s -- [flags]

Flags:
  --version VERSION   Install a specific version instead of latest
  --prefix DIR        Install directory (default: $HOME/.local/bin)
  --force             Reinstall even if the same version is already installed
  --no-verify         Skip SHA256 checksum verification (NOT recommended)
  --offline TARBALL   Install from a local tarball, no network calls
  --uninstall         Remove redlens and exit
  --quiet             Only print errors
  --no-color          Disable ANSI colors
  --no-gum            Disable gum styling even if gum is installed
  -h, --help          Show this help and exit

Env:
  HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call
  NO_COLOR                    Disable colors (same as --no-color)
EOF
}

# --- platform detection (musl on Linux for a static binary) ------------
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
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions install under Linux-side XDG paths; make sure that's the shell you use"
  fi
}

# --- proxy ---------------------------------------------------------------
PROXY_ARGS=()
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [[ -n "${HTTP_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi
curl_dl() { curl -fsSL --connect-timeout 10 "${PROXY_ARGS[@]}" "$@"; }

run_with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$@"
  else
    shift; "$@"
  fi
}

# --- atomic lock: flock-first, mkdir fallback, stale-PID heal ----------
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-300}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    LOCK_FD_OPENED=1
    flock -w "$w" 9
    return $?
  fi
  local d="${lf}.d" start
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
  LOCK_DIR="$d"
  return 0
}
release_lock() {
  if [[ "$LOCK_FD_OPENED" = 1 ]]; then { exec 9>&-; } 2>/dev/null || true; fi
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR"
}

# --- checksum + Sigstore --------------------------------------------------
verify_checksum() {  # $1=file $2=sha256_file
  [[ "$NO_VERIFY" = 1 ]] && { warn "checksum verification skipped (--no-verify)"; return 0; }
  if [[ ! -f "$2" ]]; then
    err "no .sha256 file available for $(basename "$1"); refusing to install unverified (use --no-verify to override)"
    return 1
  fi
  local expected actual
  expected=$(awk '{print tolower($1)}' "$2")
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | awk '{print tolower($1)}')
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | awk '{print tolower($1)}')
  else
    warn "no sha256sum/shasum available; skipping checksum verification"
    return 0
  fi
  if [[ -n "$actual" && "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  else
    err "checksum mismatch for $(basename "$1") (want $expected, got $actual)"
    return 1
  fi
}

verify_sigstore() {  # $1=file $2=artifact_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not installed; skipping signature verification"; return 0; }
  local bundle="$TMP/artifact.sigstore.json"
  if ! curl_dl "${2}.sigstore" -o "$bundle" 2>/dev/null; then
    warn "no Sigstore bundle published for this release; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore verification FAILED for $(basename "$1") — refusing to install"
    return 1
  fi
}

# --- version resolution (flag/env -> GitHub API -> redirect) -----------
# No local-manifest tier: this script runs standalone on the target
# machine, there is no Cargo.toml/package.json to read.
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  info "resolving latest redlens version..."
  VERSION=$(curl_dl "https://api.github.com/repos/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | head -1 | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL "${PROXY_ARGS[@]}" -o /dev/null -w '%{url_effective}' \
    "https://github.com/${OWNER}/${REPO}/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [[ -n "$VERSION" ]] && return 0
  die "could not resolve the latest redlens version (no network, or rate-limited); pass --version X.Y.Z"
}

# --- preflight -------------------------------------------------------------
preflight() {
  mkdir -p "$PREFIX" 2>/dev/null || die "cannot create install dir: $PREFIX"
  [[ -w "$PREFIX" ]] || die "no write permission on $PREFIX (try --prefix, or fix ownership)"

  local avail_kb
  avail_kb=$(df -Pk "$PREFIX" 2>/dev/null | awk 'NR==2{print $4}') || true
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    die "insufficient disk space at $PREFIX (need ~50MB, have $((avail_kb/1024))MB)"
  fi

  if [[ -x "$PREFIX/$BINARY_NAME" ]]; then
    local cur=""
    cur=$(run_with_timeout 1 "$PREFIX/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
    if [[ -n "$cur" && "$cur" == "$VERSION" && "$FORCE" != 1 ]]; then
      ok "redlens $VERSION is already installed at $PREFIX/$BINARY_NAME"
      SKIP_DOWNLOAD=1
    elif [[ -n "$cur" ]]; then
      info "found existing redlens $cur; installing $VERSION"
    fi
  fi

  curl -fsSL "${PROXY_ARGS[@]}" --connect-timeout 5 -o /dev/null "https://github.com" 2>/dev/null \
    || die "no network reachability to github.com (behind a firewall? set HTTPS_PROXY, or use --offline TARBALL)"
}

# --- extract, install binary + completions ------------------------------
install_completions() {
  local src_dir
  src_dir=$(find "$EXTRACT_DIR" -type d -iname completions 2>/dev/null | head -1)
  if [[ -z "$src_dir" ]]; then
    warn "no completions/ directory found in archive; skipping shell completions"
    return 0
  fi

  local bash_dst_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dst_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"

  local bash_src
  bash_src=$(find "$src_dir" -maxdepth 2 -type f -iname '*bash*' | head -1)
  if [[ -n "$bash_src" ]]; then
    mkdir -p "$bash_dst_dir"
    install -m 0644 "$bash_src" "$bash_dst_dir/$BINARY_NAME"
    BASH_COMPLETION_INSTALLED="$bash_dst_dir/$BINARY_NAME"
    ok "bash completion → $BASH_COMPLETION_INSTALLED"
  fi

  local zsh_src
  zsh_src=$(find "$src_dir" -maxdepth 2 -type f \( -iname '_redlens' -o -iname '*zsh*' \) | head -1)
  if [[ -n "$zsh_src" ]]; then
    mkdir -p "$zsh_dst_dir"
    install -m 0644 "$zsh_src" "$zsh_dst_dir/_${BINARY_NAME}"
    ZSH_COMPLETION_INSTALLED="$zsh_dst_dir/_${BINARY_NAME}"
    ok "zsh completion → $ZSH_COMPLETION_INSTALLED"
  fi
}

extract_and_install() {  # $1 = tarball path
  EXTRACT_DIR="$TMP/extract"
  mkdir -p "$EXTRACT_DIR"
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$EXTRACT_DIR" ;;
    *) err "unsupported archive format: $1"; return 1 ;;
  esac
  local bin
  bin=$(find "$EXTRACT_DIR" -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found inside archive"; return 1; }
  install -m 0755 "$bin" "$PREFIX/$BINARY_NAME"
  ok "installed $BINARY_NAME $VERSION → $PREFIX/$BINARY_NAME"
  install_completions
  return 0
}

# --- build-from-source fallback ------------------------------------------
build_from_source() {
  info "building redlens from source (this can take a few minutes)..."
  command -v git >/dev/null 2>&1 || die "git is required to build from source but was not found"
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup default stable
    else
      warn "rustup not found; installing it from rustup.rs"
      curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
      # shellcheck disable=SC1090
      source "$HOME/.cargo/env"
    fi
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v${VERSION}" "https://github.com/${OWNER}/${REPO}.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/${OWNER}/${REPO}.git" "$src" \
    || die "failed to clone ${OWNER}/${REPO}"
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/${BINARY_NAME}"
  [[ -x "$bin" ]] || die "build succeeded but binary not found at $bin"
  install -m 0755 "$bin" "$PREFIX/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $PREFIX/$BINARY_NAME"
  EXTRACT_DIR="$src"
  install_completions
}

# --- download (3-tier) -> verify -> install, else build from source ----
download_and_install() {
  local artifact="${REPO}-${VERSION}-${TARGET}.tar.gz"
  local url ok_url=""
  while IFS= read -r url; do
    info "trying $url"
    if curl_dl "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      curl_dl "${url}.sha256" -o "$TMP/artifact.tar.gz.sha256" 2>/dev/null || true
      if verify_checksum "$TMP/artifact.tar.gz" "$TMP/artifact.tar.gz.sha256" \
          && verify_sigstore "$TMP/artifact.tar.gz" "$url"; then
        ok_url="$url"
        break
      else
        warn "verification failed for $url; trying next source"
        rm -f "$TMP/artifact.tar.gz" "$TMP/artifact.tar.gz.sha256"
      fi
    fi
  done < <(printf '%s\n' \
    "https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}/${artifact}" \
    "https://github.com/${OWNER}/${REPO}/releases/download/${VERSION}/${artifact}" \
    "https://github.com/${OWNER}/${REPO}/releases/latest/download/${artifact}")

  if [[ -n "$ok_url" ]]; then
    extract_and_install "$TMP/artifact.tar.gz"
    return 0
  fi

  warn "no verified prebuilt binary available; falling back to source build"
  build_from_source
}

# --- offline / airgap install --------------------------------------------
install_offline() {
  [[ -f "$OFFLINE_TARBALL" ]] || die "--offline file not found: $OFFLINE_TARBALL"
  info "installing from local tarball: $OFFLINE_TARBALL (no network calls)"
  verify_checksum "$OFFLINE_TARBALL" "${OFFLINE_TARBALL}.sha256" || die "aborting: checksum verification failed"
  if command -v cosign >/dev/null 2>&1 && [[ -f "${OFFLINE_TARBALL}.sigstore" ]]; then
    if cosign verify-blob --bundle "${OFFLINE_TARBALL}.sigstore" \
        --certificate-identity-regexp "$COSIGN_ID_RE" \
        --certificate-oidc-issuer "$COSIGN_ISSUER" "$OFFLINE_TARBALL" >/dev/null 2>&1; then
      ok "Sigstore signature verified"
    else
      die "Sigstore verification FAILED for offline tarball"
    fi
  fi
  extract_and_install "$OFFLINE_TARBALL"
}

# --- PATH check ------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$PREFIX:"*) ;;
    *)
      PATH_WARNED=1
      warn "$PREFIX is not on your PATH"
      warn "add to your shell rc (~/.bashrc, ~/.zshrc): export PATH=\"$PREFIX:\$PATH\""
      ;;
  esac
}

# --- final summary box -----------------------------------------------------
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
  [[ "$QUIET" = 1 ]] && return 0
  local status_line
  if [[ "$FROM_SOURCE" = 1 ]]; then status_line="method: built from source"
  elif [[ "$SKIP_DOWNLOAD" = 1 ]]; then status_line="method: already up to date (skipped download)"
  else status_line="method: prebuilt binary ($TARGET)"; fi

  local lines=(
    "redlens $VERSION installed"
    "binary:  $PREFIX/$BINARY_NAME"
    "$status_line"
  )
  [[ -n "$BASH_COMPLETION_INSTALLED" ]] && lines+=("bash completion: $BASH_COMPLETION_INSTALLED")
  [[ -n "$ZSH_COMPLETION_INSTALLED" ]] && lines+=("zsh completion:  $ZSH_COMPLETION_INSTALLED")
  [[ "$PATH_WARNED" = 1 ]] && lines+=("⚠ $PREFIX is not on PATH — see warning above")

  local use_color=1
  { [[ -n "${NO_COLOR:-}" ]] || [[ "$NO_COLOR_FLAG" = 1 ]] || [[ ! -t 1 ]]; } && use_color=0

  if [[ "$use_color" = 1 ]]; then
    draw_box 42 "${lines[@]}"
  else
    printf -- '--- redlens install summary ---\n'
    printf '%s\n' "${lines[@]}"
  fi

  cat <<EOF

Uninstall:
  curl -fsSL "https://raw.githubusercontent.com/${OWNER}/${REPO}/main/install.sh?\$(date +%s)" | bash -s -- --uninstall
  (or manually remove: $PREFIX/$BINARY_NAME${BASH_COMPLETION_INSTALLED:+, $BASH_COMPLETION_INSTALLED}${ZSH_COMPLETION_INSTALLED:+, $ZSH_COMPLETION_INSTALLED})
EOF
}

# --- uninstall ---------------------------------------------------------
uninstall() {
  rm -f "$PREFIX/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  # uninstall_service is only defined when a background service was
  # installed; redlens ships none, so this is a permanent no-op guard.
  if declare -F uninstall_service >/dev/null; then uninstall_service; fi
  ok "uninstalled $BINARY_NAME. Agent hooks (if any) left in place — remove from settings.json manually if desired."
}

cleanup() {
  local ec=$?
  release_lock
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP"
  exit $ec
}

# --- flag parsing --------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="${2:?--version requires an argument}"; shift 2 ;;
    --prefix) PREFIX="${2:?--prefix requires an argument}"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_TARBALL="${2:?--offline requires a tarball path}"; shift 2 ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR_FLAG=1; shift ;;
    --no-gum) NO_GUM_FLAG=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done
VERSION="${VERSION#v}"

if [[ "$DO_UNINSTALL" = 1 ]]; then
  uninstall
  exit 0
fi

command -v tar >/dev/null 2>&1 || die "required command not found: tar"
if [[ -z "$OFFLINE_TARBALL" ]]; then
  command -v curl >/dev/null 2>&1 || die "required command not found: curl"
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/redlens-install.XXXXXX")
trap cleanup EXIT

detect_platform

if [[ -n "$OFFLINE_TARBALL" ]]; then
  VERSION=$(basename "$OFFLINE_TARBALL" | sed -E "s/^${REPO}-([0-9][^-]*)-.*/\1/")
  [[ "$VERSION" == "$(basename "$OFFLINE_TARBALL")" ]] && VERSION="unknown"
  mkdir -p "$PREFIX" 2>/dev/null || die "cannot create install dir: $PREFIX"
  [[ -w "$PREFIX" ]] || die "no write permission on $PREFIX"
  acquire_lock "$PREFIX/.${BINARY_NAME}.lock" 300 || die "could not acquire install lock"
  install_offline
else
  resolve_version
  preflight
  if [[ "$SKIP_DOWNLOAD" != 1 ]]; then
    acquire_lock "$PREFIX/.${BINARY_NAME}.lock" 300 || die "could not acquire install lock (another install running?)"
    if [[ "$FROM_SOURCE" = 1 ]]; then
      build_from_source
    else
      download_and_install
    fi
  fi
fi

check_path
print_summary