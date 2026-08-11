#!/usr/bin/env bash
#
# octoparse installer
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/octoparse/main/install.sh?$(date +%s)" | bash
#
# Run with --help (or see print_help below) for the full flag list. Highlights:
#   --version VERSION | --prefix DIR | --force | --quiet | --no-color | --no-gum
#   --no-verify | --build-from-source | --offline TARBALL | --easy-mode | --uninstall
#
# Env equivalents: VERSION, PREFIX, QUIET, NO_COLOR, BUILD_FROM_SOURCE, HTTPS_PROXY/HTTP_PROXY.
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# --- safety prelude: temp dir + trap must exist before anything that can fail ---
TMP=""
LOCK_DIR=""
cleanup() {
  local ec=$?
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP" 2>/dev/null
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR" 2>/dev/null
  exit "$ec"
}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/octoparse-install.XXXXXX")
trap cleanup EXIT

# --- constants ---
OWNER="acme"
REPO="octoparse"
BINARY_NAME="octoparse"
FALLBACK_VERSION="0.1.0"
LOCKFILE="${XDG_CACHE_HOME:-$HOME/.cache}/octoparse/install.lock"
LOCK_WAIT=600
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/release\\.ya?ml@refs/tags/v.*\$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION="${VERSION:-}"
PREFIX="${PREFIX:-$HOME/.local/bin}"
DEST="$PREFIX"
QUIET="${QUIET:-0}"
FORCE=0
NO_VERIFY=0
NO_COLOR_FLAG=0
NO_GUM=0
EASY_MODE=0
OFFLINE_TARBALL=""
DO_UNINSTALL=0
FLAG_BUILD_FROM_SOURCE=0
ALREADY_INSTALLED=0
OS=""
ARCH=""
TARGET=""
EXPECTED_SHA=""

print_help() {
  cat <<'EOF'
octoparse installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/acme/octoparse/main/install.sh?$(date +%s)" | bash
  ./install.sh [flags]

Flags (env var equivalents in parentheses):
  --version VERSION       install a specific version                    (VERSION)
  --prefix DIR            install location, default: $HOME/.local/bin   (PREFIX)
  --force                 reinstall even if the target version is already present
  --quiet                 only print errors                             (QUIET=1)
  --no-color              disable ANSI colors                           (NO_COLOR=1)
  --no-gum                disable gum styling even if gum is installed
  --no-verify             skip SHA256/Sigstore verification (not recommended)
  --build-from-source     consent to installing a Rust toolchain and building
                          octoparse from source if no prebuilt binary matches
                          this platform                                  (BUILD_FROM_SOURCE=1)
  --offline TARBALL       install from a local tarball, no network calls
  --easy-mode             append a PATH export to your shell rc file if needed
  --uninstall             remove octoparse and its shell completions
  -h, --help              show this help and exit

Proxy: HTTPS_PROXY / HTTP_PROXY are honored on every network call.
NO_PROXY is honored natively by curl.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --version=*) VERSION="${1#*=}"; shift ;;
    --prefix) PREFIX="$2"; DEST="$PREFIX"; shift 2 ;;
    --prefix=*) PREFIX="${1#*=}"; DEST="$PREFIX"; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR_FLAG=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --build-from-source) FLAG_BUILD_FROM_SOURCE=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --offline=*) OFFLINE_TARBALL="${1#*=}"; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "unknown flag: $1 (see --help)" >&2; exit 1 ;;
  esac
done
[[ -n "${NO_COLOR:-}" ]] && NO_COLOR_FLAG=1

# --- output stack: gum-if-TTY, ANSI fallback, honors NO_COLOR/non-TTY; err() never gated by --quiet ---
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [[ -t 1 ]] && HAS_GUM=1
[[ "$NO_COLOR_FLAG" == 1 ]] && NO_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" == 1 && "$level" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "$NO_GUM" != 1 ]]; then
    gum style --foreground "$color" "$glyph $*"
  elif [[ "$NO_COLOR_FLAG" == 1 || ! -t 1 ]]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" 1>&2; }

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

# --- platform detection: prefer musl on Linux for static portability; WSL is warned, never blocked ---
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
    *) warn "no prebuilt binary for ${OS}/${ARCH}; the only path forward is building from source"; TARGET="" ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completion paths and PATH detection may need extra config"
  fi
}

# --- proxy: expands to nothing when empty, so every curl call below stays unconditional ---
PROXY_ARGS=()
[[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# --- version resolution: flag/env -> Cargo.toml -> GitHub API -> redirect -> hardcoded fallback ---
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  if [[ -f Cargo.toml ]]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"
}

# --- preflight: disk, perms, existing install, reachability ---
preflight_common() {
  mkdir -p "$DEST" 2>/dev/null || true
  if [[ ! -w "$DEST" ]]; then
    err "no write permission at $DEST"
    exit 1
  fi
  local avail
  avail=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail" && "$avail" -lt 51200 ]]; then
    err "insufficient disk space at $DEST (need at least ~50MB free)"
    exit 1
  fi
}

preflight() {
  preflight_common
  if [[ -x "$DEST/$BINARY_NAME" ]]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [[ -n "$cur" && "$cur" == "$VERSION" && "$FORCE" != 1 ]]; then
      ALREADY_INSTALLED=1
      ok "octoparse v$VERSION is already installed at $DEST/$BINARY_NAME"
    fi
  fi
  if ! curl -fsSL --connect-timeout 5 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null; then
    warn "could not reach github.com; network may be unavailable (proxy configured? try --offline)"
  fi
}

# --- atomic lock: flock-first, mkdir fallback (macOS has no flock), stale-PID self-heal ---
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    flock -w "$w" 9
    return $?
  fi
  LOCK_DIR="${lf}.d"
  local start; start=$(date +%s)
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    local opid; opid=$(cat "$LOCK_DIR/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$LOCK_DIR"; continue
    fi
    if (( $(date +%s) - start >= w )); then
      err "timed out waiting for install lock at $LOCK_DIR"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$LOCK_DIR/pid"
}

# --- checksum + sigstore: missing tool = warn+continue, tool present + bad sig = hard fail ---
verify_checksum() {
  local file="$1" expected="$2" actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no sha256sum/shasum available; skipping checksum verification"
    return 0
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $(basename "$file") (expected $expected, got $actual)"
  return 1
}

fetch_checksum() {
  local artifact_name="$1" sums
  EXPECTED_SHA=""
  sums=$(curl -fsSL "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/checksums.txt" 2>/dev/null) || return 0
  EXPECTED_SHA=$(printf '%s\n' "$sums" | grep "$artifact_name" | awk '{print $1}' | head -1)
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not installed; skipping signature verification"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle found for $(basename "$file"); skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore signature verification FAILED for $(basename "$file")"
  return 1
}

extract_and_install() {
  local archive="$1" extract_dir="$TMP/extract"
  mkdir -p "$extract_dir"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$extract_dir" ;;
    *.tar.xz) tar -xJf "$archive" -C "$extract_dir" ;;
    *.zip) unzip -q "$archive" -d "$extract_dir" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$extract_dir" -name "$BINARY_NAME" -type f | head -1)
  if [[ -z "$bin" ]]; then
    err "binary '$BINARY_NAME' not found in archive"
    return 1
  fi
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# --- build-from-source consent: TTY prompt if a human is watching, explicit flag/env if not ---
# curl | bash means stdin is the pipe from curl, not the terminal — so we must prompt on
# /dev/tty directly rather than trusting `[[ -t 0 ]]`, which would be false even when a
# human is watching the install run.
confirm_build_from_source() {
  if [[ "${BUILD_FROM_SOURCE:-0}" == "1" || "$FLAG_BUILD_FROM_SOURCE" == "1" ]]; then
    info "build-from-source consent given via --build-from-source / BUILD_FROM_SOURCE=1"
    return 0
  fi

  if [[ -r /dev/tty && -w /dev/tty ]]; then
    warn "No prebuilt binary is available for your platform (${OS}/${ARCH})."
    warn "The only remaining option is to install a Rust toolchain (via rustup) and build octoparse from source."
    local reply
    printf 'Install a Rust toolchain and build octoparse from source now? [y/N] ' > /dev/tty
    read -r reply < /dev/tty || reply=""
    case "$reply" in
      y|Y|yes|YES) ok "proceeding with build from source"; return 0 ;;
      *) err "aborted: declined to install a Rust toolchain."; exit 1 ;;
    esac
  fi

  err "No prebuilt binary for ${OS}/${ARCH} and no interactive terminal available to ask for consent."
  err "Refusing to silently install a Rust toolchain in an unattended environment."
  err "Re-run with --build-from-source, or set BUILD_FROM_SOURCE=1, to allow this explicitly."
  exit 1
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    info "installing Rust toolchain via rustup..."
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal
    # shellcheck disable=SC1091
    source "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  install -m 0755 "$src/target/release/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# --- download: 4-tier fallback, then build-from-source as last resort ---
download_and_install() {
  if [[ -z "$TARGET" ]]; then
    confirm_build_from_source
    build_from_source
    return 0
  fi

  local artifact="$REPO-v$VERSION-$TARGET.tar.gz"
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$artifact"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$OS-$ARCH.tar.gz"
  )
  local url out bn
  for url in "${urls[@]}"; do
    out="$TMP/artifact.tar.gz"
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$out" 2>/dev/null; then
      bn=$(basename "$url")
      if [[ "$NO_VERIFY" != 1 ]]; then
        fetch_checksum "$bn"
        if [[ -n "$EXPECTED_SHA" ]]; then
          verify_checksum "$out" "$EXPECTED_SHA" || { warn "trying next source"; continue; }
        else
          warn "no checksum found for $bn; proceeding unverified (pass --no-verify to silence this warning)"
        fi
        verify_sigstore "$out" "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$bn.sigstore.json" \
          || { warn "trying next source"; continue; }
      fi
      extract_and_install "$out" && return 0
    fi
  done

  warn "no prebuilt binary could be downloaded for ${OS}/${ARCH} (target: $TARGET)"
  rm -rf "${TMP:?}"/* 2>/dev/null || true
  confirm_build_from_source
  build_from_source
}

offline_install() {
  local tarball="$1"
  [[ -f "$tarball" ]] || { err "offline tarball not found: $tarball"; exit 1; }
  [[ -z "$VERSION" ]] && VERSION="local"
  if [[ -f "$tarball.sha256" && "$NO_VERIFY" != 1 ]]; then
    local expected; expected=$(awk '{print $1}' "$tarball.sha256")
    verify_checksum "$tarball" "$expected" || exit 1
  else
    warn "no sidecar .sha256 next to $tarball; skipping checksum verification"
  fi
  extract_and_install "$tarball"
}

# --- completions: XDG paths, not hardcoded rc-file guesses ---
install_completions() {
  [[ -x "$DEST/$BINARY_NAME" ]] || return 0
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || warn "could not generate bash completions"
  "$DEST/$BINARY_NAME" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || warn "could not generate zsh completions"
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || warn "could not generate fish completions"
}

detect_rc_file() {
  case "$(basename "${SHELL:-bash}")" in
    zsh) echo "$HOME/.zshrc" ;;
    fish) echo "$HOME/.config/fish/config.fish" ;;
    *) echo "$HOME/.bashrc" ;;
  esac
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *)
      if [[ "$EASY_MODE" == 1 ]]; then
        local rc; rc=$(detect_rc_file)
        echo "export PATH=\"$DEST:\$PATH\"" >> "$rc"
        ok "added $DEST to PATH in $rc (restart your shell, or run: source $rc)"
      else
        warn "$DEST is not on your PATH — add: export PATH=\"$DEST:\$PATH\" (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME and its shell completions from $DEST"
}

print_summary() {
  local status="installed"
  [[ "$ALREADY_INSTALLED" == 1 && "$FORCE" != 1 ]] && status="already up to date"
  local lines=(
    "octoparse v$VERSION — $status"
    "Binary:      $DEST/$BINARY_NAME"
    "Completions: bash/zsh/fish (XDG dirs)"
  )
  draw_box 42 "${lines[@]}"
  echo
  info "To uninstall: $0 --uninstall"
  info "  (or manually: rm -f \"$DEST/$BINARY_NAME\" plus the completion files listed above)"
}

main() {
  if [[ "$DO_UNINSTALL" == 1 ]]; then
    uninstall
    exit 0
  fi

  detect_platform

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    preflight_common
    offline_install "$OFFLINE_TARBALL"
  else
    resolve_version
    preflight
    if [[ "$ALREADY_INSTALLED" == 1 && "$FORCE" != 1 ]]; then
      info "skipping download (already at v$VERSION); re-checking completions/PATH"
    else
      acquire_lock "$LOCKFILE" "$LOCK_WAIT" || { err "could not acquire install lock (another install running?)"; exit 1; }
      download_and_install
    fi
  fi

  install_completions
  check_path
  print_summary
}

main