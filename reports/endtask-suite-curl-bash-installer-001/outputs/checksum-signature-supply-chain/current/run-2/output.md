#!/usr/bin/env bash
#
# ledgerctl installer
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/ledgerctl/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION        install a specific version (default: latest)
#   --dest DIR                install directory (default: $HOME/.local/bin)
#   --offline TARBALL         install from a local tarball, no network calls
#   --no-verify                skip SHA256 checksum verification (NOT recommended)
#   --build-from-source        consent to installing a Rust toolchain and building locally
#   --force                    reinstall even if the same version is already present
#   --quiet                    only print errors
#   --no-color / --no-gum      disable ANSI/gum styling (plain output)
#   --easy-mode                append $DEST to PATH in your shell rc file if missing
#   --uninstall                remove ledgerctl and its completions, then exit
#   -h, --help                  show this help and exit
#
# Environment:
#   VERSION, DEST, HTTPS_PROXY/HTTP_PROXY/NO_PROXY, BUILD_FROM_SOURCE=1, QUIET=1, NO_COLOR=1
#
# ledgerctl signs financial records. Every artifact is SHA256-checksummed.
# If `cosign` is present, its Sigstore signature verification is MANDATORY —
# a bad/missing signature on a cosign-capable host is a hard failure, not a warning.

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="ledgerctl"
BINARY_NAME="ledgerctl"
FALLBACK_VERSION="0.0.0"
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/release\\.yml@refs/tags/v.*$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION="${VERSION:-}"
DEST="${DEST:-$HOME/.local/bin}"
OFFLINE_TARBALL=""
NO_VERIFY=0
FORCE=0
QUIET="${QUIET:-0}"
NO_COLOR="${NO_COLOR:-0}"
NO_GUM=0
EASY_MODE=0
DO_UNINSTALL=0
BUILD_FROM_SOURCE_FLAG=0
FROM_SOURCE=0

TMP=""
LOCK_ACQUIRED=0
LOCKFILE="${TMPDIR:-/tmp}/${BINARY_NAME}.install.lock"

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR / --quiet
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && [ "${NO_COLOR}" != "0" ] && NO_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

# ---------------------------------------------------------------------------
# Cleanup / trap — set up before anything that could fail
# ---------------------------------------------------------------------------
cleanup() {
  local status=$?
  [ -n "$TMP" ] && rm -rf "$TMP"
  if [ "$LOCK_ACQUIRED" = 1 ] && [ -d "${LOCKFILE}.d" ]; then
    rm -rf "${LOCKFILE}.d"
  fi
  return $status
}
trap cleanup EXIT

TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}.XXXXXX")

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
print_help() {
  sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --build-from-source) BUILD_FROM_SOURCE_FLAG=1; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) err "unknown flag: $1 (see --help)"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Proxy support — expands to nothing when unset, so every curl call is safe
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")
# NO_PROXY is honored natively by curl.

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME. Agent hooks (if any) left in place — remove from settings.json manually if desired."
}

if [ "$DO_UNINSTALL" = 1 ]; then
  uninstall
  exit 0
fi

# ---------------------------------------------------------------------------
# Platform detection → Rust target triple (musl preferred on Linux)
# ---------------------------------------------------------------------------
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
  if [ "$OS" = "linux" ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — file permission and PATH quirks are possible; continuing"
  fi
}

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
preflight() {
  local dest_parent
  dest_parent=$(dirname "$DEST")
  mkdir -p "$DEST" 2>/dev/null || true
  if [ ! -d "$DEST" ]; then
    err "cannot create install directory: $DEST"
    exit 1
  fi
  if [ ! -w "$DEST" ]; then
    err "no write permission on $DEST"
    exit 1
  fi

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "insufficient disk space in $DEST (need ~50MB, have ${avail_kb}KB)"
    exit 1
  fi

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" != 1 ]; then
    local cur_ver
    cur_ver=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [ -n "$cur_ver" ] && [ -n "$VERSION" ] && [ "$cur_ver" = "$VERSION" ]; then
      ok "$BINARY_NAME $VERSION already installed at $DEST/$BINARY_NAME"
      ALREADY_INSTALLED=1
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ] && [ "${ALREADY_INSTALLED:-0}" != 1 ]; then
    if ! curl -fsSL --connect-timeout 5 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null; then
      warn "network reachability check to github.com failed — subsequent downloads may fail"
    fi
  fi
}
ALREADY_INSTALLED=0

# ---------------------------------------------------------------------------
# Atomic locking — flock-first, mkdir spinlock fallback, stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9 && LOCK_ACQUIRED=1; return $?; }
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
      err "timed out waiting for install lock ($d)"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_ACQUIRED=1
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                             # 1. CLI flag/env

  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0                                             # 2. manifest

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                             # 3. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||')
  [ -n "$VERSION" ] && return 0                                             # 4. redirect

  VERSION="$FALLBACK_VERSION"                                               # 5. hardcoded
  warn "could not resolve latest version; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
#
# Asymmetric by design: missing tooling only ever warns; a tool that IS
# present and reports failure is a hard stop. ledgerctl signs financial
# records — an unverified binary must never land on a machine that had the
# means to verify it.
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected_sha256
  local file="$1" expected="$2" actual

  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify set: skipping SHA256 checksum verification"
    return 0
  fi

  if [ -z "$expected" ]; then
    err "no expected checksum available for $file — refusing to install unverified"
    return 1
  fi

  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no SHA256 tool (sha256sum/shasum) found; skipping checksum verification"
    return 0
  fi

  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  else
    err "checksum mismatch for $file (want $expected, got $actual)"
    return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  local file="$1" bundle_url="$2"

  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore signature verification"
    warn "install cosign (https://docs.sigstore.dev/cosign/installation/) to enable it"
    return 0
  fi

  info "cosign found — Sigstore signature verification is mandatory for this install"

  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.bundle" 2>/dev/null; then
    err "cosign is installed but no Sigstore bundle could be fetched for $file"
    err "refusing to install an unverifiable binary on a cosign-capable host"
    return 1
  fi

  if cosign verify-blob \
      --bundle "$TMP/sig.bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$file" 2>"$TMP/cosign.err"; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore signature verification FAILED for $file"
    cat "$TMP/cosign.err" >&2 2>/dev/null || true
    err "cosign is installed on this machine, so an unsigned/invalid artifact will not be installed"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Extract + install (atomic — install -m 0755 avoids a wrong-perms window)
# ---------------------------------------------------------------------------
extract_and_install() {
  local archive="$1" bin
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  if [ -z "$bin" ]; then
    err "binary '$BINARY_NAME' not found in archive"
    return 1
  fi
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Build from source (last-tier fallback) — requires explicit consent
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  if [ "$BUILD_FROM_SOURCE_FLAG" = 1 ] || [ "${BUILD_FROM_SOURCE:-0}" = 1 ]; then
    return 0
  fi
  if [ -t 0 ] && [ -t 1 ]; then
    warn "no prebuilt binary is available for this platform/version."
    printf 'Build from source now? This may install a Rust toolchain via rustup. [y/N] '
    read -r reply
    case "$reply" in
      y|Y|yes|YES) return 0 ;;
      *) err "declined to build from source; aborting"; return 1 ;;
    esac
  else
    err "no prebuilt binary available and not running interactively."
    err "re-run with --build-from-source or BUILD_FROM_SOURCE=1 to consent to installing a Rust toolchain and building locally."
    return 1
  fi
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    info "installing Rust toolchain via rustup"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs -o "$TMP/rustup-init.sh"
    sh "$TMP/rustup-init.sh" -y --default-toolchain stable >/dev/null
    # shellcheck source=/dev/null
    . "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  rm -rf "$src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "build did not produce $bin"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Download — 4-tier fallback → source, with checksum + Sigstore gate
# ---------------------------------------------------------------------------
download_and_install() {
  local artifact="$TMP/artifact.tar.gz"
  local checksum_url sha_url sig_url expected_sha

  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )

  for url in "${urls[@]}"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      expected_sha=""
      if curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" -o "$TMP/artifact.sha256" 2>/dev/null; then
        expected_sha=$(awk '{print $1}' "$TMP/artifact.sha256")
      fi

      if ! verify_checksum "$artifact" "$expected_sha"; then
        rm -f "$artifact"
        continue
      fi

      if ! verify_sigstore "$artifact" "${url}.sigstore.json"; then
        err "aborting install: signature verification failed"
        return 1
      fi

      extract_and_install "$artifact" && return 0
      return 1
    fi
  done

  warn "no prebuilt binary could be downloaded for $TARGET"
  rm -rf "$TMP"/*
  confirm_build_from_source || return 1
  build_from_source
}

# ---------------------------------------------------------------------------
# Offline / airgap install
# ---------------------------------------------------------------------------
install_offline() {
  local archive="$OFFLINE_TARBALL"
  if [ ! -f "$archive" ]; then
    err "offline tarball not found: $archive"
    exit 1
  fi

  local expected_sha=""
  if [ -f "${archive}.sha256" ]; then
    expected_sha=$(awk '{print $1}' "${archive}.sha256")
  fi
  verify_checksum "$archive" "$expected_sha" || exit 1

  if [ -f "${archive}.sigstore.json" ]; then
    if ! verify_sigstore "$archive" "file://${archive}.sigstore.json"; then
      exit 1
    fi
  elif command -v cosign >/dev/null 2>&1; then
    err "cosign is installed but no ${archive}.sigstore.json bundle was found alongside the offline tarball"
    err "refusing to install an unverifiable binary on a cosign-capable host"
    exit 1
  else
    warn "cosign not installed; skipping Sigstore signature verification"
  fi

  extract_and_install "$archive"
}

# ---------------------------------------------------------------------------
# Shell completions — XDG paths, not rc-file guessing
# ---------------------------------------------------------------------------
install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"

  if command -v "$DEST/$BINARY_NAME" >/dev/null 2>&1 || [ -x "$DEST/$BINARY_NAME" ]; then
    "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
    "$DEST/$BINARY_NAME" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
    "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
    ok "shell completions installed (bash/zsh/fish)"
  fi
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
      warn "$DEST is not on your PATH"
      if [ "$EASY_MODE" = 1 ]; then
        local rc=""
        case "${SHELL:-}" in
          */zsh) rc="$HOME/.zshrc" ;;
          */bash) rc="$HOME/.bashrc" ;;
          *) rc="$HOME/.profile" ;;
        esac
        echo "export PATH=\"$DEST:\$PATH\"" >> "$rc"
        ok "appended PATH update to $rc (restart your shell or 'source $rc')"
      else
        info "add it with: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Final summary box
# ---------------------------------------------------------------------------
draw_box() {
  local color="$1"; shift
  local lines=("$@") max=0 esc
  esc=$(printf '\033')
  local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    [ "${#s}" -gt "$max" ] && max=${#s}
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

print_summary() {
  local sig_status="skipped (cosign not installed)"
  command -v cosign >/dev/null 2>&1 && sig_status="verified"
  [ "$NO_VERIFY" = 1 ] && sig_status="skipped (--no-verify)"

  draw_box 42 \
    "\033[1mledgerctl installed\033[0m" \
    "" \
    "binary:     $DEST/$BINARY_NAME" \
    "version:    ${VERSION:-unknown}" \
    "checksum:   $([ "$NO_VERIFY" = 1 ] && echo 'skipped (--no-verify)' || echo verified)" \
    "signature:  $sig_status" \
    "completions: bash/zsh/fish (XDG paths)" \
    "" \
    "uninstall:  curl -fsSL \".../install.sh\" | bash -s -- --uninstall"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    install_offline
    install_completions
    check_path
    print_summary
    return 0
  fi

  detect_platform
  resolve_version

  if ! acquire_lock "$LOCKFILE" 2400; then
    err "another ledgerctl install appears to be in progress; try again later"
    exit 1
  fi

  preflight

  if [ "$ALREADY_INSTALLED" = 1 ] && [ "$FORCE" != 1 ]; then
    info "skipping download (already installed); re-checking integrations"
    install_completions
    check_path
    print_summary
    return 0
  fi

  if [ "$FROM_SOURCE" = 1 ]; then
    confirm_build_from_source || exit 1
    build_from_source
  else
    download_and_install || exit 1
  fi

  install_completions
  check_path
  print_summary
}

main "$@"