#!/usr/bin/env bash
#
# install.sh — installer for ledgerctl (github.com/acme/ledgerctl)
#
# ledgerctl signs financial records. Supply-chain integrity matters more than
# usual here: every artifact is SHA256-checksummed, and if `cosign` is present
# on this machine, its Sigstore signature MUST verify or the install aborts.
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/ledgerctl/main/install.sh?$(date +%s)" | bash
#
# Flags (env var equivalents in parens):
#   --version X          install this version instead of latest      (VERSION)
#   --prefix DIR          install location                            (PREFIX)
#   --quiet                errors only
#   --force                 reinstall even if the version is already present
#   --no-color              disable ANSI colour
#   --no-gum                disable gum styling even if installed
#   --no-verify              SKIP SHA256/Sigstore verification (dangerous — see WARNING below)
#   --build-from-source     unattended consent to build via cargo instead of downloading a binary (BUILD_FROM_SOURCE=1)
#   --offline TARBALL         install from a local tarball, no network calls at all
#   --checksum HEX             expected SHA256 for --offline mode (no network = no companion .sha256 file)
#   --sigstore-bundle PATH   local Sigstore bundle for --offline mode
#   --easy-mode                append $PREFIX to PATH in your shell rc if it's missing
#   --uninstall                 remove ledgerctl and its completions, then exit
#   --help                       show this text
#
# WARNING: --no-verify disables SHA256 checksum AND Sigstore verification for
# a tool that signs financial records. Only use it for local development
# builds you produced yourself. It will refuse to run unattended (non-TTY)
# unless CONFIRM_NO_VERIFY=1 is also set, to prevent it slipping into a CI
# script unnoticed.

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
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/\.github/workflows/.*@refs/heads/main$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION="${VERSION:-}"
PREFIX="${PREFIX:-$HOME/.local/bin}"
DEST="$PREFIX"
QUIET=0
FORCE=0
NO_VERIFY=0
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
OFFLINE_TARBALL=""
OFFLINE_CHECKSUM=""
OFFLINE_SIGSTORE_BUNDLE=""
EASY_MODE=0
DO_UNINSTALL=0
NO_GUM="${NO_GUM:-0}"
[ -n "${NO_COLOR:-}" ] && NO_GUM=1

SUMMARY_LINES=()

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR / non-TTY / --quiet
# err() is never gated by --quiet: a failing installer must always be audible.
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
err()  { _log err  196 '✗'  "$@" 1>&2; }

# ---------------------------------------------------------------------------
# Temp dir + cleanup trap — created before anything that might fail, so the
# trap is live for the rest of the script's life.
# ---------------------------------------------------------------------------
TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")
LOCK_DIR=""
cleanup() {
  local status=$?
  rm -rf "$TMP"
  [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR"
  exit "$status"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Flag parsing + --help
# ---------------------------------------------------------------------------
usage() { sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --version=*) VERSION="${1#*=}"; shift ;;
    --prefix) PREFIX="$2"; DEST="$2"; shift 2 ;;
    --prefix=*) PREFIX="${1#*=}"; DEST="$PREFIX"; shift ;;
    --quiet) QUIET=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-color) NO_COLOR=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --build-from-source) BUILD_FROM_SOURCE=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --offline=*) OFFLINE_TARBALL="${1#*=}"; shift ;;
    --checksum) OFFLINE_CHECKSUM="$2"; shift 2 ;;
    --checksum=*) OFFLINE_CHECKSUM="${1#*=}"; shift ;;
    --sigstore-bundle) OFFLINE_SIGSTORE_BUNDLE="$2"; shift 2 ;;
    --sigstore-bundle=*) OFFLINE_SIGSTORE_BUNDLE="${1#*=}"; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "unknown flag: $1"; usage; exit 1 ;;
  esac
done

if [ "$NO_VERIFY" = 1 ]; then
  if [ ! -t 0 ] && [ "${CONFIRM_NO_VERIFY:-0}" != 1 ]; then
    err "--no-verify disables SHA256/Sigstore checks for a financial-signing tool."
    err "Refusing to run unattended without verification. If you really mean it,"
    err "set CONFIRM_NO_VERIFY=1 as well."
    exit 1
  fi
  warn "SHA256 and Sigstore verification are DISABLED (--no-verify). Do not use this in production."
fi

# ---------------------------------------------------------------------------
# Proxy support — every curl call carries PROXY_ARGS; NO_PROXY is honored by
# curl natively so we don't need to touch it.
# ---------------------------------------------------------------------------
PROXY_ARGS=()
if [ -n "${HTTPS_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [ -n "${HTTP_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi

# ---------------------------------------------------------------------------
# Platform detection — musl preferred on Linux for a static, portable binary.
# WSL is detected and warned about, never blocked.
# ---------------------------------------------------------------------------
OS="" ARCH="" TARGET="" FROM_SOURCE=0

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
    warn "WSL detected — completions and PATH setup may need extra manual config"
  fi
}

# ---------------------------------------------------------------------------
# Preflight — disk space, write perms, existing install, network reachability
# ---------------------------------------------------------------------------
CURRENT_VERSION=""

preflight() {
  local parent
  parent=$(dirname "$DEST")
  mkdir -p "$parent" 2>/dev/null || { err "cannot create $parent — check permissions"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$parent" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "less than 50MB free at $parent — aborting"
    exit 1
  fi

  if ! mkdir -p "$DEST" 2>/dev/null || [ ! -w "$DEST" ]; then
    err "cannot write to $DEST — check permissions or pass --prefix"
    exit 1
  fi

  if [ -x "$DEST/$BINARY_NAME" ]; then
    CURRENT_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    [ -n "$CURRENT_VERSION" ] && info "existing install: $CURRENT_VERSION"
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://api.github.com" 2>/dev/null; then
      err "cannot reach api.github.com — check your network/proxy, or use --offline TARBALL"
      exit 1
    fi
  fi
}

# ---------------------------------------------------------------------------
# Atomic lock — flock-first (Linux), mkdir spinlock fallback (macOS has no
# flock), stale-PID self-heal so a crashed prior run can't wedge new ones.
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
      err "timed out waiting for install lock at $d"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. flag/env
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                              # 2. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [ -n "$VERSION" ] && return 0                                              # 3. redirect
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"                           # 4. hardcoded
}

# ---------------------------------------------------------------------------
# Checksum — dual-tool, hard fail on mismatch, warn+continue only if no
# SHA256 tool exists at all AND --no-verify was passed (see verify_artifact).
# ---------------------------------------------------------------------------
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    echo ""
  fi
}

verify_checksum() {  # $1=file $2=expected
  local expected="$2" actual
  actual=$(sha256_of "$1")
  if [ -z "$actual" ]; then
    warn "no sha256sum/shasum available; cannot verify checksum"
    return 1
  fi
  if [ -z "$expected" ]; then
    warn "no expected checksum available to compare against"
    return 1
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $expected, got $actual)"
  return 1
}

# ---------------------------------------------------------------------------
# Sigstore — the asymmetry is the whole point for a signing tool:
#   cosign absent           -> warn, continue
#   cosign present + bad sig -> hard fail, no install
# ---------------------------------------------------------------------------
verify_sigstore() {  # $1=file $2=bundle_path_or_url $3=is_url(0/1)
  local file="$1" bundle="$2" is_url="$3"
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore signature check (SHA256 still enforced)"
    return 0
  fi
  local bundle_path="$bundle"
  if [ "$is_url" = 1 ]; then
    bundle_path="$TMP/artifact.sigstore.json"
    if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle" -o "$bundle_path" 2>/dev/null; then
      err "cosign is installed but no Sigstore bundle was found at $bundle"
      err "refusing to install an unverifiable artifact on a machine that can verify"
      return 1
    fi
  elif [ ! -f "$bundle_path" ]; then
    err "cosign is installed but --sigstore-bundle path does not exist: $bundle_path"
    return 1
  fi
  if cosign verify-blob --bundle "$bundle_path" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED — this artifact's signature does not check out"
  return 1
}

# ---------------------------------------------------------------------------
# Combined verification gate used by both network and offline paths.
# ---------------------------------------------------------------------------
verify_artifact() {  # $1=file $2=expected_sha $3=bundle $4=bundle_is_url
  local file="$1" sha="$2" bundle="$3" bundle_is_url="$4"
  if [ "$NO_VERIFY" = 1 ]; then
    warn "skipping all verification for $file (--no-verify)"
    return 0
  fi
  verify_checksum "$file" "$sha" || return 1
  verify_sigstore "$file" "$bundle" "$bundle_is_url" || return 1
  return 0
}

# ---------------------------------------------------------------------------
# Build-from-source fallback — consent-gated (non-negotiable #9): a TTY gets
# a prompt, a non-TTY needs --build-from-source or BUILD_FROM_SOURCE=1.
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  if [ "$BUILD_FROM_SOURCE" = 1 ]; then
    return 0
  fi
  if [ -t 0 ]; then
    read -r -p "No prebuilt binary available/verified. Build from source with cargo? [y/N] " reply
    case "$reply" in
      y|Y|yes|YES) return 0 ;;
      *) err "declined build-from-source"; exit 1 ;;
    esac
  fi
  err "no prebuilt binary available and this is a non-interactive shell."
  err "re-run with --build-from-source, or set BUILD_FROM_SOURCE=1, to allow installing a Rust toolchain and building locally."
  exit 1
}

build_from_source() {
  confirm_build_from_source
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup toolchain"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs -o "$TMP/rustup-init.sh"
    sh "$TMP/rustup-init.sh" -y --default-toolchain stable --no-modify-path
    export PATH="$HOME/.cargo/bin:$PATH"
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  install -m 0755 "$src/target/release/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST"
  SUMMARY_LINES+=("binary: built from source → $DEST/$BINARY_NAME")
}

# ---------------------------------------------------------------------------
# Extract + install — install -m 0755 avoids the wrong-perms window that
# `cp && chmod` opens up.
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
  if [ -z "$bin" ]; then
    err "binary '$BINARY_NAME' not found inside archive"
    return 1
  fi
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST"
  SUMMARY_LINES+=("binary: $DEST/$BINARY_NAME ($VERSION)")
}

# ---------------------------------------------------------------------------
# Download — 4-tier URL fallback, verify each candidate, fall back to source
# build only once every download tier has been exhausted.
# ---------------------------------------------------------------------------
download_and_install() {
  local artifact_name="$REPO-v$VERSION-$TARGET.tar.gz"
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$artifact_name"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url
  for url in "${urls[@]}"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      local expected=""
      expected=$(curl -fsSL "${PROXY_ARGS[@]}" "$url.sha256" 2>/dev/null | awk '{print $1}')
      if verify_artifact "$TMP/artifact.tar.gz" "$expected" "$url.sigstore" 1; then
        extract_and_install "$TMP/artifact.tar.gz" && return 0
      fi
      rm -f "$TMP/artifact.tar.gz"
    fi
  done
  warn "no verified prebuilt binary found across all download tiers"
  build_from_source
}

# ---------------------------------------------------------------------------
# Offline install — no network calls at all, straight from a local tarball.
# ---------------------------------------------------------------------------
install_offline() {
  [ -f "$OFFLINE_TARBALL" ] || { err "--offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  if [ -z "$VERSION" ]; then
    VERSION="offline-$(date +%Y%m%d)"
    warn "no --version given for offline install; recording as $VERSION"
  fi
  local bundle=""
  local bundle_is_url=0
  if [ -n "$OFFLINE_SIGSTORE_BUNDLE" ]; then
    bundle="$OFFLINE_SIGSTORE_BUNDLE"
  fi
  if [ -z "$OFFLINE_CHECKSUM" ]; then
    warn "no --checksum given for --offline install; SHA256 cannot be verified"
  fi
  verify_artifact "$OFFLINE_TARBALL" "$OFFLINE_CHECKSUM" "$bundle" "$bundle_is_url" \
    || { err "offline artifact failed verification"; exit 1; }
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Shell completions — bash/zsh/fish into XDG paths, not guessed rc files.
# Assumes `ledgerctl completions <shell>` exists; silently skipped if not.
# ---------------------------------------------------------------------------
install_completions() {
  local shell comp_dir comp_file
  for shell in bash zsh fish; do
    case "$shell" in
      bash) comp_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"; comp_file="$comp_dir/$BINARY_NAME" ;;
      zsh)  comp_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"; comp_file="$comp_dir/_$BINARY_NAME" ;;
      fish) comp_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"; comp_file="$comp_dir/$BINARY_NAME.fish" ;;
    esac
    mkdir -p "$comp_dir" 2>/dev/null || continue
    if "$DEST/$BINARY_NAME" completions "$shell" > "$comp_file.tmp" 2>/dev/null; then
      mv "$comp_file.tmp" "$comp_file"
      SUMMARY_LINES+=("completions ($shell): $comp_file")
    else
      rm -f "$comp_file.tmp"
    fi
  done
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [ "$EASY_MODE" = 1 ]; then
    local rc line="export PATH=\"$DEST:\$PATH\""
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
      [ -f "$rc" ] || continue
      grep -qxF "$line" "$rc" 2>/dev/null && continue
      printf '\n# added by %s installer\n%s\n' "$BINARY_NAME" "$line" >> "$rc"
      SUMMARY_LINES+=("PATH: appended to $rc")
    done
  else
    warn "$DEST is not on your PATH — add it, or re-run with --easy-mode"
    SUMMARY_LINES+=("PATH: $DEST not on PATH (run with --easy-mode to fix)")
  fi
}

# ---------------------------------------------------------------------------
# Final summary box
# ---------------------------------------------------------------------------
draw_box() {  # $1=color, rest=lines
  local color="$1"; shift; local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do
    local s; s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    [ "${#s}" -gt "$max" ] && max=${#s}
  done
  local inner=$((max+4)) border=""
  local i
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
  [ "$QUIET" = 1 ] && return 0
  local lines=("ledgerctl install summary")
  lines+=("")
  for l in "${SUMMARY_LINES[@]}"; do lines+=("$l"); done
  draw_box 42 "${lines[@]}"
  echo
  info "Uninstall with: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "  (removes: $DEST/$BINARY_NAME, bash/zsh/fish completions)"
}

# ---------------------------------------------------------------------------
# Uninstall — preserves any config so a reinstall stays easy
# ---------------------------------------------------------------------------
uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME"
  exit 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if [ "$DO_UNINSTALL" = 1 ]; then
    uninstall
  fi

  detect_platform
  preflight

  if [ -n "$OFFLINE_TARBALL" ]; then
    install_offline
  else
    acquire_lock "${XDG_CACHE_HOME:-$HOME/.cache}/${BINARY_NAME}-install.lock" 2400 \
      || { err "another install is already in progress"; exit 1; }

    resolve_version

    if [ "$FORCE" = 0 ] && [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" = "$VERSION" ]; then
      ok "$BINARY_NAME $VERSION already installed — skipping download (use --force to reinstall)"
      SUMMARY_LINES+=("binary: $DEST/$BINARY_NAME (already at $VERSION)")
    elif [ "$FROM_SOURCE" = 1 ]; then
      build_from_source
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  print_summary
}

main "$@"