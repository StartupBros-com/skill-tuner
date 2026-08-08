#!/usr/bin/env bash
#
# quill installer — github.com/hovlabs/quill
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/quill/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION   install a specific version (default: latest via GitHub API)
#   --offline TARBALL   install from a local tarball; no network calls are made
#   --prefix DIR        install directory (default: ~/.local/bin)
#   --force             reinstall even if the requested version is already installed
#   --no-verify         skip SHA256 checksum verification (NOT recommended)
#   --quiet             suppress non-error output
#   --no-color          disable ANSI colors
#   --no-gum            disable gum styling even if gum is installed
#   --uninstall         remove quill and its shell completions, then exit
#   -h, --help          show this help and exit
#
# Env:
#   QUILL_LOCAL_TARBALL   path to a local tarball; equivalent to --offline TARBALL.
#                         Used for airgapped CI — when set, no network calls are made.
#   QUILL_VERSION         equivalent to --version
#   HTTPS_PROXY / HTTP_PROXY   proxy used for every network call
#   NO_COLOR              disable ANSI colors
#
set -euo pipefail
umask 022

OWNER=hovlabs
REPO=quill
BINARY_NAME=quill
FALLBACK_VERSION="0.4.0"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/.*@refs/tags/v.*$"

QUIET=0
FORCE=0
NO_GUM=0
NO_VERIFY=0
NO_COLOR_FLAG=0
[ -n "${NO_COLOR:-}" ] && NO_COLOR_FLAG=1
VERSION="${QUILL_VERSION:-}"
OFFLINE_TARBALL="${QUILL_LOCAL_TARBALL:-}"
DEST="${XDG_BIN_HOME:-$HOME/.local/bin}"
DO_UNINSTALL=0

OS=""
ARCH=""
TARGET=""
FROM_SOURCE=0
PROXY_ARGS=()
TMP=""
LOCK_DIR=""
CHECKSUM_STATUS="skipped"
SIGSTORE_STATUS="skipped"
COMPLETIONS_STATUS="skipped"
INSTALL_METHOD=""

HAS_GUM=0

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM" = 1 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$NO_COLOR_FLAG" = 1 ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

usage() {
  cat <<'EOF'
quill installer

Usage: install.sh [flags]

  --version VERSION   install a specific version (default: latest)
  --offline TARBALL   install from a local tarball, no network calls
  --prefix DIR        install directory (default: ~/.local/bin)
  --force             reinstall even if already installed at that version
  --no-verify         skip SHA256 checksum verification
  --quiet             errors only
  --no-color          disable ANSI colors
  --no-gum            disable gum styling
  --uninstall         remove quill and exit
  -h, --help          show this help

Env: QUILL_LOCAL_TARBALL, QUILL_VERSION, HTTPS_PROXY, HTTP_PROXY, NO_COLOR
EOF
}

cleanup() {
  local ec=$?
  [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR" 2>/dev/null
  [ -n "$TMP" ] && rm -rf "$TMP" 2>/dev/null
  exit "$ec"
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
    *)
      warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"
      FROM_SOURCE=1
      ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some features may need extra configuration"
  fi
}

setup_proxy() {
  PROXY_ARGS=()
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

resolve_version() {
  [ -n "$VERSION" ] && return 0
  if [ -n "$OFFLINE_TARBALL" ]; then
    VERSION="local"
    return 0
  fi
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"
}

_ver_of() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 1 "$1" --version 2>/dev/null
  else
    "$1" --version 2>/dev/null
  fi
}

preflight() {
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create $DEST"; exit 1; }
  [ -w "$DEST" ] || { err "$DEST is not writable"; exit 1; }

  local free_kb
  free_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}') || true
  if [ -n "$free_kb" ] && [ "$free_kb" -lt 51200 ] 2>/dev/null; then
    err "less than 50MB free at $DEST; aborting"
    exit 1
  fi

  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    local cur
    cur=$(_ver_of "$BINARY_NAME" | awk '{print $NF}') || true
    if [ -n "$cur" ] && [ "$cur" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
      ok "$BINARY_NAME $VERSION already installed at $(command -v "$BINARY_NAME")"
      exit 0
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || { err "cannot reach github.com — check network/proxy, or use --offline TARBALL"; exit 1; }
  fi
}

acquire_lock() {
  local lf="$1" w="${2:-2400}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    if { exec 9>>"$lf"; } 2>/dev/null; then
      flock -w "$w" 9
      return $?
    fi
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

fetch_sidecar_sha() {
  curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" "$1.sha256" 2>/dev/null | awk '{print $1}'
}

verify_checksum() {
  local file="$1" expected="$2" actual
  if [ -z "$expected" ]; then
    warn "no published checksum; skipping checksum check"
    CHECKSUM_STATUS="unavailable"
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1) || true
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" 2>/dev/null | cut -d' ' -f1) || true
  else
    warn "no SHA256 tool available; skipping checksum"
    CHECKSUM_STATUS="unavailable"
    return 0
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    CHECKSUM_STATUS="verified"
    return 0
  fi
  err "checksum mismatch (want $expected got $actual)"
  return 1
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not found; skipping signature check"
    SIGSTORE_STATUS="unavailable"
    return 0
  fi
  if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no sigstore bundle published; skipping signature check"
    SIGSTORE_STATUS="unavailable"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "signature verified"
    SIGSTORE_STATUS="verified"
    return 0
  fi
  err "Sigstore verification FAILED for $file"
  return 1
}

extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f 2>/dev/null | head -1) || true
  [ -n "$bin" ] || { err "binary not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

build_from_source() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    err "no prebuilt binary available and running in offline mode; cannot build from source"
    return 1
  fi
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs 2>/dev/null \
      | sh -s -- -y --default-toolchain stable -q
    # shellcheck disable=SC1091
    [ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"
  fi
  command -v cargo >/dev/null 2>&1 || { err "cargo still not available after rustup install"; return 1; }

  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "build succeeded but binary not found at $bin"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST"
  INSTALL_METHOD="source"
  CHECKSUM_STATUS="n/a (built locally)"
  SIGSTORE_STATUS="n/a (built locally)"
}

download_and_install() {
  local artifact="$REPO-v$VERSION-$TARGET.tar.gz"
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$artifact"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url

  if [ "$FROM_SOURCE" != 1 ]; then
    for url in "${urls[@]}"; do
      info "trying $url"
      if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
        if [ "$NO_VERIFY" = 1 ]; then
          warn "checksum/signature verification skipped (--no-verify)"
        else
          local sha
          sha=$(fetch_sidecar_sha "$url") || true
          if ! verify_checksum "$TMP/artifact.tar.gz" "$sha"; then
            warn "checksum check failed for $url; trying next source"
            continue
          fi
          if ! verify_sigstore "$TMP/artifact.tar.gz" "$url.sigstore.json"; then
            warn "signature check failed for $url; trying next source"
            continue
          fi
        fi
        if extract_and_install "$TMP/artifact.tar.gz"; then
          INSTALL_METHOD="prebuilt binary"
          return 0
        fi
      fi
    done
    warn "no prebuilt binary available"
  fi
  build_from_source
}

install_from_offline_tarball() {
  local tb="$OFFLINE_TARBALL"
  [ -f "$tb" ] || { err "offline tarball not found: $tb"; exit 1; }
  info "installing from local tarball: $tb (no network calls)"
  if [ "$NO_VERIFY" = 1 ]; then
    warn "checksum verification skipped (--no-verify)"
  else
    local shafile="$tb.sha256"
    if [ -f "$shafile" ]; then
      verify_checksum "$tb" "$(awk '{print $1}' "$shafile")" || { err "checksum mismatch for $tb"; exit 1; }
    else
      warn "no $shafile next to tarball; skipping checksum check"
    fi
  fi
  SIGSTORE_STATUS="n/a (offline)"
  extract_and_install "$tb" || { err "failed to install from $tb"; exit 1; }
  INSTALL_METHOD="offline tarball"
}

install_completions() {
  command -v "$DEST/$BINARY_NAME" >/dev/null 2>&1 || return 0
  local probe
  if command -v timeout >/dev/null 2>&1; then
    probe=$(timeout 5 "$DEST/$BINARY_NAME" completions bash 2>/dev/null) || true
  else
    probe=$("$DEST/$BINARY_NAME" completions bash 2>/dev/null) || true
  fi
  if [ -z "$probe" ]; then
    warn "binary does not support completion generation; skipping"
    return 0
  fi
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  printf '%s' "$probe" > "$bash_dir/$BINARY_NAME"
  "$DEST/$BINARY_NAME" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "installed shell completions (bash/zsh/fish)"
  COMPLETIONS_STATUS="installed"
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

print_summary() {
  [ "$QUIET" = 1 ] && return 0
  local path_note="on PATH"
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) path_note="NOT on PATH — add: export PATH=\"$DEST:\$PATH\"" ;;
  esac
  local lines=(
    "quill $VERSION installed"
    "Binary:      $DEST/$BINARY_NAME ($path_note)"
    "Method:      $INSTALL_METHOD"
    "Checksum:    $CHECKSUM_STATUS"
    "Signature:   $SIGSTORE_STATUS"
    "Completions: $COMPLETIONS_STATUS"
  )
  if [ "$HAS_GUM" = 1 ] || [ "$NO_COLOR_FLAG" = 1 ] || [ ! -t 1 ]; then
    printf '%s\n' "${lines[@]}"
  else
    draw_box 42 "${lines[@]}"
  fi
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME"
}

print_uninstall_instructions() {
  [ "$QUIET" = 1 ] && return 0
  info "to uninstall: rm -f '$DEST/$BINARY_NAME' (or re-run this script with --uninstall)"
}

main() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) VERSION="${2:?--version requires an argument}"; shift 2 ;;
      --offline) OFFLINE_TARBALL="${2:?--offline requires a tarball path}"; shift 2 ;;
      --prefix)  DEST="${2:?--prefix requires a directory}"; shift 2 ;;
      --force)   FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --quiet)   QUIET=1; shift ;;
      --no-color) NO_COLOR_FLAG=1; shift ;;
      --no-gum)  NO_GUM=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done

  if [ "$NO_GUM" != 1 ] && [ "$NO_COLOR_FLAG" != 1 ] && command -v gum >/dev/null 2>&1 && [ -t 1 ]; then
    HAS_GUM=1
  fi

  if [ "$DO_UNINSTALL" = 1 ]; then
    uninstall
    exit 0
  fi

  detect_platform
  setup_proxy

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/quill-install.XXXXXX") || { err "mktemp failed"; exit 1; }
  trap cleanup EXIT

  resolve_version
  preflight

  local lockfile="${XDG_CACHE_HOME:-$HOME/.cache}/quill/install.lock"
  acquire_lock "$lockfile" 2400 || { err "could not acquire install lock at $lockfile"; exit 1; }

  if [ -n "$OFFLINE_TARBALL" ]; then
    install_from_offline_tarball
  else
    download_and_install
  fi

  install_completions
  print_summary
  print_uninstall_instructions
}

main "$@"