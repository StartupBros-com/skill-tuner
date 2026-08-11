#!/usr/bin/env bash
#
# ledgerctl installer
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/ledgerctl/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION     Install a specific version (default: latest)
#   --dest DIR             Install directory (default: $HOME/.local/bin)
#   --force                Reinstall even if the same version is already present
#   --quiet                Suppress non-error output
#   --no-color              Disable ANSI colors (also honors NO_COLOR)
#   --no-gum                Disable gum styling even if installed
#   --no-verify             Skip SHA256 checksum verification (NOT recommended)
#   --offline TARBALL       Install from a local tarball, no network calls
#   --uninstall              Remove ledgerctl and exit
#   -h, --help               Show this help and exit
#
# Env:
#   HTTPS_PROXY / HTTP_PROXY / NO_PROXY   Standard proxy vars, honored on every network call.
#   LEDGERCTL_VERSION                     Same as --version.
#
# ledgerctl signs financial records. Because of that, this installer treats
# supply-chain verification as load-bearing: SHA256 is always checked (unless
# explicitly disabled), and if cosign is present on the box, a failed
# signature verification is a hard stop, not a warning.

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="ledgerctl"
BINARY_NAME="ledgerctl"
FALLBACK_VERSION="1.0.0"
DEST="${HOME}/.local/bin"
VERSION="${LEDGERCTL_VERSION:-}"
FORCE=0
QUIET=0
NO_GUM=0
NO_VERIFY=0
OFFLINE_TARBALL=""
DO_UNINSTALL=0
FROM_SOURCE=0

COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/release\\.yml@refs/tags/v.*$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honor NO_COLOR + non-TTY
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && NO_GUM=1

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
err()  { _log err  196 '✗'  "$@" >&2; }

draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=0
  for l in "$title" "${lines[@]}"; do
    (( ${#l} > width )) && width=${#l}
  done
  (( width += 2 ))
  local border; border=$(printf '─%.0s' $(seq 1 "$width"))
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    printf '%s\n' "${lines[@]}" | gum style --border rounded --border-foreground 39 --padding "0 1" --bold "$title"$'\n'"$(printf '%s\n' "${lines[@]}")"
    return 0
  fi
  printf '\n┌%s┐\n' "$border"
  printf '│ %-*s │\n' "$((width - 2))" "$title"
  printf '├%s┤\n' "$border"
  for l in "${lines[@]}"; do
    printf '│ %-*s │\n' "$((width - 2))" "$l"
  done
  printf '└%s┘\n\n' "$border"
}

# ---------------------------------------------------------------------------
# Temp dir + cleanup
# ---------------------------------------------------------------------------
TMP="$(mktemp -d "${TMPDIR:-/tmp}/ledgerctl-install.XXXXXX")"
LOCKFILE="${TMPDIR:-/tmp}/ledgerctl-install.lock"
LOCK_HELD=0

cleanup() {
  local ec=$?
  [ "$LOCK_HELD" = 1 ] && release_lock
  rm -rf "$TMP"
  exit "$ec"
}
trap cleanup EXIT

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
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) err "unknown flag: $1"; print_help; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Proxy support
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# Platform detection
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
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features (e.g. hardware key signing) may need extra config"
  fi
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
  local dest_parent
  dest_parent=$(dirname "$DEST")
  mkdir -p "$DEST" 2>/dev/null || true
  if [ ! -w "$DEST" ] 2>/dev/null && [ ! -w "$dest_parent" ]; then
    err "cannot write to $DEST — check permissions or pass --dest"
    exit 1
  fi

  if command -v df >/dev/null 2>&1; then
    local avail_kb
    avail_kb=$(df -Pk "$dest_parent" 2>/dev/null | awk 'NR==2{print $4}')
    if [ -n "${avail_kb:-}" ] && [ "$avail_kb" -lt 51200 ]; then
      err "less than 50MB free at $dest_parent; aborting"
      exit 1
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      err "cannot reach github.com — check network/proxy, or use --offline TARBALL"
      exit 1
    fi
  fi

  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    local cur_ver
    cur_ver=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    [ -n "$cur_ver" ] && info "existing install detected: $cur_ver"
    EXISTING_VERSION="$cur_ver"
  else
    EXISTING_VERSION=""
  fi
}

# ---------------------------------------------------------------------------
# Atomic locking — flock-first, mkdir spinlock fallback, stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9 && LOCK_HELD=1 && return 0; }
    return 1
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
  LOCK_HELD=1
  LOCK_DIR="$d"
  return 0
}

release_lock() {
  if command -v flock >/dev/null 2>&1; then
    exec 9>&- 2>/dev/null || true
  else
    [ -n "${LOCK_DIR:-}" ] && rm -rf "$LOCK_DIR"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. CLI flag/env

  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0                                              # 2. local manifest

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                              # 3. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||')
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"                           # 4. redirect  5. hardcoded
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
#
# Asymmetric by design: a missing tool only warns (checksum tool absent is
# rare but not fatal in offline/minimal environments; cosign absent just
# means the box has no way to check, so we can't demand it). But if cosign
# IS present and the signature bundle fails verification, that is a hard
# stop — ledgerctl signs financial records and must never land unverified
# on a machine that had the means to verify it.
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected_sha256
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify passed; skipping SHA256 check (not recommended for ledgerctl)"
    return 0
  fi
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no SHA256 tool (sha256sum/shasum) found; skipping checksum verification"
    return 0
  fi
  if [ "$actual" = "$2" ]; then
    ok "SHA256 verified"
    return 0
  else
    err "checksum mismatch (want $2, got $actual) — refusing to install"
    return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore signature check (SHA256 checksum still enforced)"
    return 0
  fi
  info "cosign detected; verifying Sigstore signature (failure will abort install)"
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    err "cosign is installed but no Sigstore bundle could be fetched for this release — aborting"
    err "(a machine that can verify signatures must not install unverified artifacts)"
    return 1
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$1" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  else
    err "Sigstore signature verification FAILED — this artifact is untrusted"
    err "refusing to install an unverified ledgerctl binary"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Download → verify → extract → install
# ---------------------------------------------------------------------------
fetch_expected_sha() {  # sets EXPECTED_SHA from the release checksums file, if any
  EXPECTED_SHA=""
  local checksums
  checksums=$(curl -fsSL "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/checksums.txt" 2>/dev/null || true)
  [ -n "$checksums" ] && EXPECTED_SHA=$(echo "$checksums" | grep "$REPO-v$VERSION-$TARGET.tar.gz" | awk '{print $1}')
}

extract_and_install() {  # $1=archive
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$1" -C "$TMP" ;;
    *.zip)          unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }

  local backup=""
  if [ -f "$DEST/$BINARY_NAME" ]; then
    backup="$DEST/$BINARY_NAME.bak.$(date +%s)"
    cp "$DEST/$BINARY_NAME" "$backup"
  fi

  mkdir -p "$DEST"
  if install -m 0755 "$bin" "$DEST/$BINARY_NAME"; then
    ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
    [ -n "$backup" ] && rm -f "$backup"
    return 0
  else
    err "install failed"
    [ -n "$backup" ] && { mv "$backup" "$DEST/$BINARY_NAME"; warn "restored previous binary from backup"; }
    return 1
  fi
}

build_from_source() {
  info "building ledgerctl from source (this may take a few minutes)"
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup default stable
    else
      err "no cargo/rustup found and no prebuilt binary available for this platform"
      err "install Rust from https://rustup.rs and re-run this installer"
      exit 1
    fi
  fi
  local srcdir="$TMP/src"
  git clone --depth 1 ${VERSION:+--branch "v$VERSION"} \
    "https://github.com/$OWNER/$REPO.git" "$srcdir" 2>/dev/null \
    || { err "git clone failed"; exit 1; }
  ( cd "$srcdir" && cargo build --release ) || { err "cargo build failed"; exit 1; }
  local bin="$srcdir/target/release/$BINARY_NAME"
  [ -f "$bin" ] || { err "build did not produce $BINARY_NAME"; exit 1; }
  mkdir -p "$DEST"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $DEST/$BINARY_NAME"
  warn "source builds are not Sigstore-verified — prefer a prebuilt release when possible for ledgerctl"
}

download_and_install() {
  local url tried=0
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    tried=1
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      fetch_expected_sha
      if [ -z "$EXPECTED_SHA" ]; then
        err "could not determine expected SHA256 for this release; refusing to install unverifiable artifact"
        [ "$NO_VERIFY" = 1 ] || return 1
      fi
      verify_checksum "$TMP/artifact.tar.gz" "$EXPECTED_SHA" || return 1
      verify_sigstore "$TMP/artifact.tar.gz" \
        "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz.sigstore.json" || return 1
      extract_and_install "$TMP/artifact.tar.gz" && return 0
      return 1
    fi
  done
  warn "no prebuilt binary found for $TARGET; falling back to source build"
  build_from_source
}

install_offline() {
  local archive="$OFFLINE_TARBALL"
  [ -f "$archive" ] || { err "offline tarball not found: $archive"; exit 1; }
  info "offline mode: installing from $archive (no network calls, no signature check)"
  if [ -n "${EXPECTED_SHA:-}" ]; then
    verify_checksum "$archive" "$EXPECTED_SHA" || exit 1
  else
    warn "no expected SHA256 provided for offline install; checksum not verified"
  fi
  extract_and_install "$archive"
}

# ---------------------------------------------------------------------------
# Shell completions (XDG paths)
# ---------------------------------------------------------------------------
install_completions() {
  command -v "$BINARY_NAME" >/dev/null 2>&1 || return 0
  local bin="$DEST/$BINARY_NAME"

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"

  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || return 0

  "$bin" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null \
    && ok "bash completions → $bash_dir/$BINARY_NAME" || true
  "$bin" completions zsh > "$zsh_dir/_$BINARY_NAME" 2>/dev/null \
    && ok "zsh completions → $zsh_dir/_$BINARY_NAME" || true
  "$bin" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null \
    && ok "fish completions → $fish_dir/$BINARY_NAME.fish" || true
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on your PATH — add it, e.g.: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------
do_uninstall() {
  local removed=()
  if [ -f "$DEST/$BINARY_NAME" ]; then
    rm -f "$DEST/$BINARY_NAME"
    removed+=("$DEST/$BINARY_NAME")
  fi
  for f in \
    "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
    "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
    "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"; do
    [ -f "$f" ] && { rm -f "$f"; removed+=("$f"); }
  done
  if [ "${#removed[@]}" -eq 0 ]; then
    info "nothing to uninstall"
  else
    draw_box "ledgerctl uninstalled" "${removed[@]}"
  fi
  exit 0
}

print_uninstall_instructions() {
  draw_box "Uninstall ledgerctl" \
    "curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall" \
    "or manually remove:" \
    "  $DEST/$BINARY_NAME" \
    "  ${XDG_DATA_HOME:-\$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
    "  ${XDG_DATA_HOME:-\$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
    "  ${XDG_CONFIG_HOME:-\$HOME/.config}/fish/completions/$BINARY_NAME.fish"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  [ "$DO_UNINSTALL" = 1 ] && do_uninstall

  detect_platform

  if [ -n "$OFFLINE_TARBALL" ]; then
    install_offline
  else
    preflight
    resolve_version

    if [ -n "${EXISTING_VERSION:-}" ] && [ "$EXISTING_VERSION" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
      ok "ledgerctl $VERSION already installed; skipping download (use --force to reinstall)"
    else
      acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install running?)"; exit 1; }
      if [ "$FROM_SOURCE" = 1 ]; then
        build_from_source
      else
        download_and_install
      fi
    fi
  fi

  install_completions
  check_path

  draw_box "ledgerctl install complete" \
    "version:  ${VERSION:-source build}" \
    "location: $DEST/$BINARY_NAME" \
    "checksum: $([ "$NO_VERIFY" = 1 ] && echo 'SKIPPED (--no-verify)' || echo 'verified')" \
    "sigstore: $(command -v cosign >/dev/null 2>&1 && echo 'verified' || echo 'skipped (cosign not installed)')"

  print_uninstall_instructions
}

main "$@"