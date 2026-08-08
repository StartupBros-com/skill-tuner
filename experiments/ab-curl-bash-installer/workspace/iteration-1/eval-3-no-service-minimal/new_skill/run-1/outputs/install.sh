#!/usr/bin/env bash
#
# quill installer — github.com/hovlabs/quill
# A small Rust markdown formatter. Plain binary install only: no services,
# no daemons, nothing runs in the background.
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/quill/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION       Install a specific version (default: latest release)
#   --prefix DIR            Install directory (default: $HOME/.local/bin)
#   --offline TARBALL       Install from a local tarball, no network calls
#   --no-verify             Skip SHA256 checksum verification
#   --force                 Reinstall even if the requested version is already present
#   --quiet                 Errors only
#   --no-color              Disable colored/gum output (also honors NO_COLOR)
#   --no-gum                Disable gum styling, ANSI fallback only
#   --uninstall             Remove quill and exit
#   -h, --help              Show this help and exit
#
# Env:
#   QUILL_LOCAL_TARBALL      Same effect as --offline <path>; set this in
#                            airgapped CI to install from a local tarball
#                            with zero network access.
#   HTTPS_PROXY / HTTP_PROXY Honored on every network call.
#   NO_COLOR                 Disables styled output.
#
set -euo pipefail
umask 022

# ---- constants ----
OWNER="hovlabs"
REPO="quill"
BINARY_NAME="quill"
FALLBACK_VERSION=""
COSIGN_ID_RE="https://github.com/${OWNER}/${REPO}/\.github/workflows/release\.ya?ml@.*"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
LOCKFILE="${TMPDIR:-/tmp}/quill-install.lock"

# ---- defaults (overridable by flags/env) ----
VERSION=""
INSTALL_DIR="${HOME}/.local/bin"
OFFLINE_TARBALL="${QUILL_LOCAL_TARBALL:-}"
NO_VERIFY=0
FORCE=0
QUIET=0
NO_GUM=0
DO_UNINSTALL=0
ALREADY_INSTALLED=0
FROM_SOURCE=0
TMP=""
LOCKDIR=""
TARGET=""
OS=""
ARCH=""
[ -n "${NO_COLOR:-}" ] && NO_GUM=1

# ---- functions ----

usage() {
  cat <<'EOF'
quill installer — github.com/hovlabs/quill

  curl -fsSL "https://raw.githubusercontent.com/hovlabs/quill/main/install.sh?$(date +%s)" | bash

Flags:
  --version VERSION       Install a specific version (default: latest release)
  --prefix DIR            Install directory (default: $HOME/.local/bin)
  --offline TARBALL       Install from a local tarball, no network calls
  --no-verify             Skip SHA256 checksum verification
  --force                 Reinstall even if the requested version is already present
  --quiet                 Errors only
  --no-color              Disable colored/gum output (also honors NO_COLOR)
  --no-gum                Disable gum styling, ANSI fallback only
  --uninstall             Remove quill and exit
  -h, --help              Show this help and exit

Env:
  QUILL_LOCAL_TARBALL      Same as --offline <path>; set in airgapped CI.
  HTTPS_PROXY / HTTP_PROXY Honored on every network call.
  NO_COLOR                 Disables styled output.
EOF
}

_log() { [ "$QUIET" = 1 ] && [ "$1" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then gum style --foreground "$2" "$3 ${*:4}"
  else printf '\033[%sm%s\033[0m %s\n' "$2" "$3" "${*:4}"; fi; }
info() { _log info 39 '->' "$@"; }
ok()   { _log ok   42 '✓'  "$@"; }
warn() { _log warn 214 '⚠' "$@"; }
err()  { _log err  196 '✗' "$@"; }

run_with_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "$secs" "$@"
  else "$@"; fi
}

cleanup() {
  [ -n "$LOCKDIR" ] && rm -rf "$LOCKDIR" 2>/dev/null
  [ -n "$TMP" ] && rm -rf "$TMP" 2>/dev/null
  true
}

detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions paths may need extra shell config"
  fi
}

resolve_version() {
  [ -n "$VERSION" ] && return 0
  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [ -z "$VERSION" ] && VERSION="$FALLBACK_VERSION"
  if [ -z "$VERSION" ]; then
    err "could not resolve a version to install (network unreachable and no --version given)"
    exit 1
  fi
}

existing_version() {
  local bin="$INSTALL_DIR/$BINARY_NAME"
  [ -x "$bin" ] || return 1
  run_with_timeout 1 "$bin" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

preflight() {
  local parent="$INSTALL_DIR"
  while [ ! -d "$parent" ]; do parent=$(dirname "$parent"); done
  if [ ! -w "$parent" ]; then
    err "no write permission on $parent — use --prefix DIR for a writable directory, or run with sudo"
    exit 1
  fi

  local avail_kb
  avail_kb=$(df -Pk "$parent" | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 20480 ]; then
    err "less than 20MB free on $parent — aborting"
    exit 1
  fi

  local cur
  cur=$(existing_version || true)
  if [ -n "$cur" ] && [ "$cur" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
    ALREADY_INSTALLED=1
    ok "quill $VERSION already installed at $INSTALL_DIR/$BINARY_NAME (use --force to reinstall)"
  fi

  if [ -z "$OFFLINE_TARBALL" ] && [ "$ALREADY_INSTALLED" != 1 ]; then
    if ! curl -fsSL --connect-timeout 3 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null; then
      err "cannot reach github.com — check network/proxy, or install with --offline TARBALL / QUILL_LOCAL_TARBALL"
      exit 1
    fi
  fi
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
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then return 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCKDIR="$d"
}

verify_checksum() {
  local file="$1" expected="$2" actual
  if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    err "no sha256sum/shasum available to verify checksum — install one or pass --no-verify"
    return 1
  fi
  if [ "$actual" = "$expected" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch for $(basename "$file") (want $expected, got $actual)"; return 1; fi
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  if ! command -v cosign >/dev/null 2>&1; then warn "cosign not found; skipping signature verification"; return 0; fi
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle published for this artifact; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "Sigstore signature verified"
  else
    err "Sigstore verification FAILED for $(basename "$file")"
    return 1
  fi
}

fetch_expected_sha() {
  local artifact_url="$1" out="$TMP/expected.sha256"
  if curl -fsSL "${PROXY_ARGS[@]}" "${artifact_url}.sha256" -o "$out" 2>/dev/null; then
    awk '{print $1}' "$out"
    return 0
  fi
  return 1
}

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
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  mkdir -p "$INSTALL_DIR"
  install -m 0755 "$bin" "$INSTALL_DIR/$BINARY_NAME"
  ok "installed $BINARY_NAME $VERSION → $INSTALL_DIR/$BINARY_NAME"
}

download_and_install() {
  local url artifact="$TMP/artifact.tar.gz" sha
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      if [ "$NO_VERIFY" = 1 ]; then
        warn "checksum verification skipped (--no-verify)"
        extract_and_install "$artifact" && return 0
      else
        sha=$(fetch_expected_sha "$url" || true)
        if [ -n "$sha" ] \
           && verify_checksum "$artifact" "$sha" \
           && verify_sigstore "$artifact" "${url}.sigstore" \
           && extract_and_install "$artifact"; then
          return 0
        fi
        warn "verification failed or unavailable for $(basename "$url"); trying next source"
      fi
    fi
  done
  return 1
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup toolchain"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    # shellcheck source=/dev/null
    source "$HOME/.cargo/env"
  fi
  local src="$TMP/src"
  git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "build succeeded but binary not found at $bin"; exit 1; }
  mkdir -p "$INSTALL_DIR"
  install -m 0755 "$bin" "$INSTALL_DIR/$BINARY_NAME"
  ok "built and installed $BINARY_NAME → $INSTALL_DIR/$BINARY_NAME"
}

install_offline() {
  [ -f "$OFFLINE_TARBALL" ] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  info "installing from local tarball: $OFFLINE_TARBALL (no network calls)"
  if [ "$NO_VERIFY" != 1 ] && [ -f "${OFFLINE_TARBALL}.sha256" ]; then
    local sha
    sha=$(awk '{print $1}' "${OFFLINE_TARBALL}.sha256")
    verify_checksum "$OFFLINE_TARBALL" "$sha" || exit 1
  fi
  extract_and_install "$OFFLINE_TARBALL"
}

install_completions() {
  local bin="$INSTALL_DIR/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  if command -v bash >/dev/null 2>&1; then
    local d="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
    mkdir -p "$d"
    run_with_timeout 3 "$bin" completions bash > "$d/$BINARY_NAME" 2>/dev/null || rm -f "$d/$BINARY_NAME"
  fi
  if command -v zsh >/dev/null 2>&1; then
    local d="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
    mkdir -p "$d"
    run_with_timeout 3 "$bin" completions zsh > "$d/_$BINARY_NAME" 2>/dev/null || rm -f "$d/_$BINARY_NAME"
  fi
  if command -v fish >/dev/null 2>&1; then
    local d="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
    mkdir -p "$d"
    run_with_timeout 3 "$bin" completions fish > "$d/$BINARY_NAME.fish" 2>/dev/null || rm -f "$d/$BINARY_NAME.fish"
  fi
}

check_path() {
  case ":$PATH:" in
    *":$INSTALL_DIR:"*) ;;
    *) warn "$INSTALL_DIR is not on PATH — add: export PATH=\"$INSTALL_DIR:\$PATH\"" ;;
  esac
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

uninstall() {
  rm -f "$INSTALL_DIR/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  # uninstall_service is intentionally never defined — quill installs a plain
  # binary only, no systemd/launchd unit. Guard kept so set -e can't trip here.
  if declare -F uninstall_service >/dev/null; then uninstall_service; fi
  ok "uninstalled $BINARY_NAME"
}

print_uninstall_info() {
  info "uninstall quill:"
  info "  rm '$INSTALL_DIR/$BINARY_NAME'"
  info "  rm -f '${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME'"
  info "  rm -f '${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME'"
  info "  rm -f '${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish'"
  info "or re-run this installer (saved locally) with --uninstall"
}

main() {
  detect_platform

  PROXY_ARGS=()
  [ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  [ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/quill-install.XXXXXX")
  trap cleanup EXIT

  if [ "$DO_UNINSTALL" = 1 ]; then uninstall; exit 0; fi

  if [ -n "$OFFLINE_TARBALL" ]; then
    VERSION="${VERSION:-local}"
  else
    resolve_version
  fi

  preflight

  if [ "$ALREADY_INSTALLED" != 1 ]; then
    acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install already running?)"; exit 1; }
    if [ -n "$OFFLINE_TARBALL" ]; then
      install_offline
    elif [ "$FROM_SOURCE" = 1 ]; then
      build_from_source
    elif ! download_and_install; then
      warn "no verified prebuilt binary available; building from source"
      build_from_source
    fi
  fi

  install_completions
  check_path

  draw_box 42 \
    "\033[1mquill $VERSION\033[0m — installed" \
    "binary: $INSTALL_DIR/$BINARY_NAME" \
    "mode:   plain binary only — no services or daemons installed"

  print_uninstall_info
}

# ---- parse flags ----
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --prefix) INSTALL_DIR="$2"; shift 2 ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown flag: $1" >&2; usage; exit 1 ;;
  esac
done

HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

main