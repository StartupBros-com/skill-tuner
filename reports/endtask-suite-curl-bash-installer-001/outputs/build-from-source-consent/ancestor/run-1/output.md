#!/usr/bin/env bash
#
# octoparse installer
#
#   curl -fsSL "https://octoparse.dev/install.sh?$(date +%s)" | bash
#
# Flags (also settable via env, see --help):
#   --version=X.Y.Z              install a specific version (default: latest)
#   --dest=PATH                  install directory (default: $HOME/.local/bin)
#   --force                      reinstall even if the target version is already present
#   --quiet                      errors only
#   --no-color                   disable ANSI/gum styling
#   --no-gum                     never use gum even if present
#   --no-verify                  skip SHA256 checksum verification (not recommended)
#   --offline TARBALL            install from a local tarball, no network calls
#   --allow-build-from-source    consent to installing a Rust toolchain and building
#                                 from source when no prebuilt binary matches this
#                                 platform. Required non-interactively; can also be
#                                 granted via OCTOPARSE_ALLOW_BUILD_FROM_SOURCE=1.
#   -h, --help                   show this help and exit
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="octoparse"
BINARY_NAME="octoparse"
DEST="${DEST:-$HOME/.local/bin}"
FALLBACK_VERSION="1.0.0"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/\.github/workflows/release\.yml@refs/tags/v.*\$"

VERSION="${VERSION:-}"
FORCE=0
QUIET="${QUIET:-0}"
NO_GUM="${NO_GUM:-0}"
NO_VERIFY=0
OFFLINE_TARBALL=""
ALLOW_BUILD_FROM_SOURCE=0
FROM_SOURCE=0

[ -n "${NO_COLOR:-}" ] && NO_GUM=1

# ---------------------------------------------------------------------------
# output stack: gum-if-tty, ANSI fallback, honor NO_COLOR + non-TTY, err never gated
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

# ---------------------------------------------------------------------------
# flags
# ---------------------------------------------------------------------------
usage() {
  cat <<'EOF'
octoparse installer

Usage: install.sh [flags]

  --version=X.Y.Z              install a specific version (default: latest)
  --dest=PATH                  install directory (default: $HOME/.local/bin)
  --force                      reinstall even if that version is already present
  --quiet                      errors only
  --no-color                   disable ANSI/gum styling
  --no-gum                     never use gum even if present
  --no-verify                  skip SHA256 checksum verification (not recommended)
  --offline TARBALL             install from a local tarball, no network calls
  --allow-build-from-source     consent to installing a Rust toolchain and building
                                 from source if no prebuilt binary matches this platform
  -h, --help                    show this help and exit

Environment:
  VERSION, DEST, HTTPS_PROXY, HTTP_PROXY, NO_COLOR, NO_GUM, QUIET
  OCTOPARSE_ALLOW_BUILD_FROM_SOURCE=1   same as --allow-build-from-source
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --version=*) VERSION="${1#*=}" ;;
    --dest=*) DEST="${1#*=}" ;;
    --force) FORCE=1 ;;
    --quiet) QUIET=1 ;;
    --no-color) NO_GUM=1 ;;
    --no-gum) NO_GUM=1 ;;
    --no-verify) NO_VERIFY=1 ;;
    --offline)
      shift
      [ $# -gt 0 ] || { err "--offline requires a TARBALL path"; exit 1; }
      OFFLINE_TARBALL="$1"
      ;;
    --allow-build-from-source) ALLOW_BUILD_FROM_SOURCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) err "unknown flag: $1"; usage; exit 1 ;;
  esac
  shift
done

[ -n "${OCTOPARSE_ALLOW_BUILD_FROM_SOURCE:-}" ] && ALLOW_BUILD_FROM_SOURCE=1

# ---------------------------------------------------------------------------
# temp dir + cleanup trap (must exist before anything can fail)
# ---------------------------------------------------------------------------
TMP="$(mktemp -d "${TMPDIR:-/tmp}/octoparse-install.XXXXXX")"
LOCK_DIR=""
cleanup() {
  local code=$?
  rm -rf "$TMP"
  [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR"
  exit "$code"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# proxy support — expands to nothing when unset, so every curl call stays unconditional
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# platform detection
# ---------------------------------------------------------------------------
OS="" ARCH="" TARGET=""
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
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features (e.g. shell completions autodetect) may need extra config"
  fi
}

# ---------------------------------------------------------------------------
# version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                                    # 1. flag/env
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0                                                    # 2. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && return 0                                                    # 3. redirect
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"                                 # 4/5. hardcoded
  warn "could not resolve latest version from network; falling back to ${VERSION}"
}

# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install dir: $DEST"; exit 1; }
  [ -w "$DEST" ] || { err "no write permission on $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "less than 50MB free at $DEST; aborting"
    exit 1
  fi

  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    local cur
    cur=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || cur=""
    if [ -n "$cur" ] && [ "$cur" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
      ok "${BINARY_NAME} ${VERSION} already installed — nothing to do (use --force to reinstall)"
      exit 0
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || warn "network reachability check to github.com failed; downloads may fail"
  fi
}

# ---------------------------------------------------------------------------
# atomic lock — flock-first, mkdir spinlock fallback (macOS has no flock), stale-PID heal
# ---------------------------------------------------------------------------
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
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"
      continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

# ---------------------------------------------------------------------------
# checksum + sigstore — missing tool = warn+continue; tool present + bad sig = hard fail
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected
  [ "$NO_VERIFY" = 1 ] && { warn "checksum verification skipped (--no-verify)"; return 0; }
  local expected="$2" actual
  if [ -z "$expected" ]; then
    warn "no expected checksum available; skipping"
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no SHA256 tool found; skipping checksum"
    return 0
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $expected got $actual)"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not found; skipping signature verification"
    return 0
  fi
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle available; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED"
  return 1
}

# ---------------------------------------------------------------------------
# build-from-source consent gate
#
# stdin isn't a TTY when this script runs as `curl | bash` — it's the pipe
# feeding the script itself — so "interactive" is judged by /dev/tty, and the
# prompt/read are pointed at /dev/tty explicitly, not stdin.
# ---------------------------------------------------------------------------
is_interactive() {
  [ -t 1 ] && [ -r /dev/tty ] && [ -w /dev/tty ]
}

confirm_build_from_source() {
  if [ "$ALLOW_BUILD_FROM_SOURCE" = 1 ]; then
    return 0
  fi

  warn "No prebuilt ${BINARY_NAME} binary is available for this platform (${OS}/${ARCH})."
  warn "The only remaining option is to install a Rust toolchain (via rustup) and build from source."

  if is_interactive; then
    local reply
    printf '\033[33m?\033[0m Install a Rust toolchain and build %s from source now? [y/N] ' "$BINARY_NAME" > /dev/tty
    read -r reply < /dev/tty || reply=""
    case "$reply" in
      y|Y|yes|YES|Yes) return 0 ;;
      *) err "build-from-source declined; aborting"; return 1 ;;
    esac
  fi

  err "Refusing to install a Rust toolchain unattended — that's a large, surprising"
  err "change to make to this machine without explicit consent."
  err "Re-run with --allow-build-from-source, or set OCTOPARSE_ALLOW_BUILD_FROM_SOURCE=1, to permit it."
  return 1
}

build_from_source() {
  confirm_build_from_source || exit 1

  if ! command -v cargo >/dev/null 2>&1; then
    info "installing Rust toolchain via rustup..."
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal
    # shellcheck disable=SC1090
    . "$HOME/.cargo/env"
  fi

  info "cloning ${OWNER}/${REPO}..."
  git clone --depth 1 --branch "v${VERSION}" "https://github.com/${OWNER}/${REPO}.git" "$TMP/src" \
    || git clone --depth 1 "https://github.com/${OWNER}/${REPO}.git" "$TMP/src"

  info "building (this may take a while)..."
  (cd "$TMP/src" && cargo build --release)

  local bin="$TMP/src/target/release/${BINARY_NAME}"
  [ -x "$bin" ] || { err "build did not produce $bin"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed ${BINARY_NAME} → $DEST"
}

# ---------------------------------------------------------------------------
# extract + install prebuilt artifact
# ---------------------------------------------------------------------------
extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$archive" -C "$TMP" ;;
    *.zip) unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed ${BINARY_NAME} → $DEST"
}

# ---------------------------------------------------------------------------
# download — 4-tier fallback → build from source
# ---------------------------------------------------------------------------
download_and_install() {
  local expected_sha=""
  local shafile
  shafile=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}/${REPO}-v${VERSION}-${TARGET}.sha256" 2>/dev/null) || true
  expected_sha=$(printf '%s' "$shafile" | awk '{print $1}')

  local url
  for url in \
    "https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}/${REPO}-v${VERSION}-${TARGET}.tar.gz" \
    "https://github.com/${OWNER}/${REPO}/releases/latest/download/${REPO}-${TARGET}.tar.gz" \
    "https://github.com/${OWNER}/${REPO}/releases/latest/download/${REPO}-${OS}-${ARCH}.tar.gz"
  do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      if verify_checksum "$TMP/artifact.tar.gz" "$expected_sha" \
        && verify_sigstore "$TMP/artifact.tar.gz" "${url}.sig.json" \
        && extract_and_install "$TMP/artifact.tar.gz"; then
        return 0
      fi
    fi
  done

  build_from_source
}

# ---------------------------------------------------------------------------
# offline install
# ---------------------------------------------------------------------------
offline_install() {
  [ -f "$OFFLINE_TARBALL" ] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  info "installing from local tarball (offline mode)"
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# shell completions (XDG paths, not hardcoded rc-file guesses)
# ---------------------------------------------------------------------------
install_completions() {
  command -v "$BINARY_NAME" >/dev/null 2>&1 || return 0
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || bin="$(command -v "$BINARY_NAME")"

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"

  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$bin" completions bash > "$bash_dir/${BINARY_NAME}" 2>/dev/null \
    && ok "bash completions → $bash_dir/${BINARY_NAME}" \
    || warn "could not generate bash completions"
  "$bin" completions zsh > "$zsh_dir/_${BINARY_NAME}" 2>/dev/null \
    && ok "zsh completions → $zsh_dir/_${BINARY_NAME}" \
    || warn "could not generate zsh completions"
  "$bin" completions fish > "$fish_dir/${BINARY_NAME}.fish" 2>/dev/null \
    && ok "fish completions → $fish_dir/${BINARY_NAME}.fish" \
    || warn "could not generate fish completions"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on your PATH — add it to your shell rc, e.g.: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# summary box
# ---------------------------------------------------------------------------
draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=${#title}
  local l
  for l in "${lines[@]}"; do
    [ ${#l} -gt "$width" ] && width=${#l}
  done
  width=$((width + 2))
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    { printf '%s\n' "$title"; printf '%s\n' "${lines[@]}"; } | gum style --border rounded --padding "0 1" --border-foreground 42
    return
  fi
  printf '+'; printf -- '-%.0s' $(seq 1 "$width"); printf '+\n'
  printf '| %-*s |\n' $((width - 1)) "$title"
  printf '+'; printf -- '-%.0s' $(seq 1 "$width"); printf '+\n'
  for l in "${lines[@]}"; do
    printf '| %-*s |\n' $((width - 1)) "$l"
  done
  printf '+'; printf -- '-%.0s' $(seq 1 "$width"); printf '+\n'
}

print_summary() {
  local method="prebuilt binary"
  [ "$FROM_SOURCE" = 1 ] && method="built from source"
  draw_box "octoparse installed" \
    "version:   ${VERSION}" \
    "method:    ${method}" \
    "location:  ${DEST}/${BINARY_NAME}" \
    "path:      $(case ":$PATH:" in *":$DEST:"*) echo ok;; *) echo "NOT on PATH — see warning above";; esac)"
}

print_uninstall() {
  cat <<EOF

To uninstall:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/${BINARY_NAME}"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_${BINARY_NAME}"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/${BINARY_NAME}.fish"
EOF
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
main() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    detect_platform || true
    VERSION="${VERSION:-unknown (offline)}"
    offline_install
    install_completions
    check_path
    print_summary
    print_uninstall
    return 0
  fi

  detect_platform
  resolve_version
  preflight

  mkdir -p "$(dirname "$DEST")" 2>/dev/null || true
  acquire_lock "${TMPDIR:-/tmp}/octoparse-install.lock" 2400 \
    || { err "could not acquire install lock; another install may be in progress"; exit 1; }

  if [ "$FROM_SOURCE" = 1 ]; then
    build_from_source
  else
    download_and_install
  fi

  install_completions
  check_path
  print_summary
  print_uninstall
}

main "$@"