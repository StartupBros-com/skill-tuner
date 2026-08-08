#!/usr/bin/env bash
#
# tapwire installer
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/tapwire/main/install.sh?$(date +%s)" | bash
#
# Flags (pass after `bash -s --`, e.g. `curl ... | bash -s -- --force`):
#   --version VERSION   Install a specific version (default: latest)
#   --dest DIR           Install directory (default: $HOME/.local/bin)
#   --force               Reinstall even if the same version is already installed
#   --no-verify           Skip SHA256 checksum verification (not recommended)
#   --offline FILE         Install from a local binary or .tar.gz/.tgz, no network calls
#   --quiet                 Only print errors
#   --no-color               Disable ANSI colors (also respects $NO_COLOR)
#   --no-gum                  Disable gum styling even if gum is installed
#   --uninstall                Remove tapwire and exit
#   -h, --help                  Show this help and exit
#
# Environment:
#   HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call
#   TAPWIRE_INSTALL_DIR         Same as --dest
#   TAPWIRE_VERSION               Same as --version
#   NO_COLOR                       Same as --no-color
#
# Dependencies: curl + standard coreutils (sha256sum/shasum, mkdir, install,
# df, uname, timeout, find, grep, sed, awk) on the target machine — no node
# or bun needed to run tapwire. Building from source (only used when no
# prebuilt binary matches your platform) additionally needs git, and will
# install bun itself if it is not already present.

set -euo pipefail
umask 022

OWNER="hovlabs"
REPO="tapwire"
BINARY_NAME="tapwire"
# Last-resort version if the GitHub API and release-redirect tiers both fail.
# Bump on release; see resolve_version().
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
LOCKFILE="${XDG_CACHE_HOME:-$HOME/.cache}/tapwire/install.lock"

VERSION="${TAPWIRE_VERSION:-}"
DEST="${TAPWIRE_INSTALL_DIR:-$HOME/.local/bin}"
FORCE=0
NO_VERIFY=0
OFFLINE_FILE=""
QUIET=0
NO_GUM=0
DO_UNINSTALL=0
FROM_SOURCE=0
ALREADY_INSTALLED=0
FORCE_NO_COLOR=0
HAS_GUM=0
[ -n "${NO_COLOR:-}" ] && { FORCE_NO_COLOR=1; NO_GUM=1; }

usage() {
  cat <<EOF
tapwire installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh" | bash -s -- [flags]

Flags:
  --version VERSION   Install a specific version (default: latest)
  --dest DIR           Install directory (default: \$HOME/.local/bin)
  --force               Reinstall even if the same version is already installed
  --no-verify           Skip SHA256 checksum verification (not recommended)
  --offline FILE         Install from a local binary or .tar.gz/.tgz, no network calls
  --quiet                 Only print errors
  --no-color               Disable ANSI colors (also respects \$NO_COLOR)
  --no-gum                  Disable gum styling even if gum is installed
  --uninstall                Remove tapwire and exit
  -h, --help                  Show this help and exit

Environment:
  HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call
  TAPWIRE_INSTALL_DIR         Same as --dest
  TAPWIRE_VERSION               Same as --version
  NO_COLOR                       Same as --no-color
EOF
}

_log() {
  local color="$1" icon="$2"; shift 2
  [ "$QUIET" = 1 ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" != 1 ]; then
    gum style --foreground "$color" "$icon $*"
    return 0
  fi
  if [ "$FORCE_NO_COLOR" = 1 ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$icon" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$icon" "$*"
  fi
}
info() { _log 39  '->' "$@"; }
ok()   { _log 42  '✓'  "$@"; }
warn() { _log 214 '⚠'  "$@"; }
err() {
  if [ "$FORCE_NO_COLOR" = 1 ] || [ ! -t 2 ]; then
    printf '✗ %s\n' "$*" 1>&2
  else
    printf '\033[196m✗\033[0m %s\n' "$*" 1>&2
  fi
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --version=*) VERSION="${1#*=}"; shift ;;
      --dest) DEST="$2"; shift 2 ;;
      --dest=*) DEST="${1#*=}"; shift ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --offline) OFFLINE_FILE="$2"; shift 2 ;;
      --offline=*) OFFLINE_FILE="${1#*=}"; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) FORCE_NO_COLOR=1; NO_GUM=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done
}

detect_platform() {
  local os arch
  os=$(uname -s | tr 'A-Z' 'a-z')
  arch=$(uname -m)
  case "$arch" in
    x86_64|amd64) arch=x64 ;;
    arm64|aarch64) arch=arm64 ;;
  esac
  OS="$os"; ARCH="$arch"
  case "${os}-${arch}" in
    linux-x64)    ASSET="tapwire-linux-x64" ;;
    linux-arm64)  ASSET="tapwire-linux-arm64" ;;
    darwin-arm64) ASSET="tapwire-darwin-arm64" ;;
    *)
      warn "no prebuilt binary for ${os}/${arch}; will build from source"
      FROM_SOURCE=1
      ;;
  esac
  if [ "$os" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — tapwire should work, but some features may need extra config"
  fi
}

set_proxy_args() {
  PROXY_ARGS=()
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

resolve_version() {
  [ -n "$VERSION" ] && return 0
  if [ -f package.json ]; then
    VERSION=$(grep -m1 '"version"' package.json \
      | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([0-9][^"]*)".*/\1/') || true
  fi
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] || VERSION="$FALLBACK_VERSION"
  info "resolved version: $VERSION"
}

preflight() {
  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install directory: $DEST"; exit 1; }
  [ -w "$DEST" ] || { err "no write permission: $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 102400 ]; then
    err "less than 100MB free at $DEST"
    exit 1
  fi

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" != 1 ]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) || true
    if [ -n "$cur" ]; then
      if [ -z "$VERSION" ]; then
        info "tapwire $cur is already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
        ALREADY_INSTALLED=1
      elif [ "$cur" = "$VERSION" ]; then
        info "tapwire $cur (requested version) is already installed at $DEST/$BINARY_NAME"
        ALREADY_INSTALLED=1
      fi
    fi
  fi

  if [ -z "$OFFLINE_FILE" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null https://api.github.com \
      || { err "cannot reach api.github.com — check network/proxy, or use --offline"; exit 1; }
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
  trap 'rm -rf "'"$d"'"' EXIT
}

verify_checksum() {
  local file="$1" expected="$2" actual
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
  fi
  err "checksum mismatch for $(basename "$file") (want $expected, got $actual)"
  return 1
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle published for this asset; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "signature verified"
    return 0
  fi
  err "Sigstore signature verification FAILED for $(basename "$file")"
  return 1
}

download_and_install() {
  local bases=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION"
    "https://github.com/$OWNER/$REPO/releases/download/$VERSION"
    "https://github.com/$OWNER/$REPO/releases/latest/download"
  )
  local base
  for base in "${bases[@]}"; do
    if ! curl -fsSL "${PROXY_ARGS[@]}" "$base/$ASSET" -o "$TMP/$ASSET" 2>/dev/null; then
      continue
    fi
    info "downloaded $ASSET from $base"

    if [ "$NO_VERIFY" = 1 ]; then
      warn "--no-verify set; skipping checksum verification"
    else
      if ! curl -fsSL "${PROXY_ARGS[@]}" "$base/SHA256SUMS" -o "$TMP/SHA256SUMS" 2>/dev/null; then
        err "could not fetch SHA256SUMS from $base"
        rm -f "$TMP/$ASSET"
        continue
      fi
      local expected
      expected=$(grep -E "[[:space:]]\*?${ASSET}\$" "$TMP/SHA256SUMS" | awk '{print $1}' | head -1)
      if [ -z "$expected" ]; then
        err "SHA256SUMS does not list $ASSET"
        rm -f "$TMP/$ASSET"
        continue
      fi
      if ! verify_checksum "$TMP/$ASSET" "$expected"; then
        rm -f "$TMP/$ASSET"
        continue
      fi
    fi

    verify_sigstore "$TMP/$ASSET" "$base/$ASSET.sigstore.json" || exit 1

    install -m 0755 "$TMP/$ASSET" "$DEST/$BINARY_NAME"
    ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
    return 0
  done

  warn "no prebuilt binary available for ${OS}/${ARCH}; building from source"
  build_from_source
}

build_from_source() {
  command -v git >/dev/null 2>&1 || { err "git is required to build tapwire from source"; exit 1; }

  if ! command -v bun >/dev/null 2>&1; then
    info "bun not found; installing bun (required to build from source)"
    curl -fsSL "${PROXY_ARGS[@]}" https://bun.sh/install | bash \
      || { err "bun installation failed"; exit 1; }
    export PATH="$HOME/.bun/bin:$PATH"
    command -v bun >/dev/null 2>&1 || { err "bun not found on PATH after install"; exit 1; }
  fi

  local src="$TMP/src"
  local clone_args=(--depth 1)
  [ -n "$VERSION" ] && clone_args+=(--branch "v$VERSION")
  if ! git clone "${clone_args[@]}" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null; then
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  fi

  (
    cd "$src"
    bun install --frozen-lockfile
    if grep -q '"build"[[:space:]]*:' package.json 2>/dev/null; then
      bun run build
    else
      bun build ./src/index.ts --compile --outfile "$BINARY_NAME"
    fi
  )

  local built
  built=$(find "$src" -maxdepth 3 -type f -name "$BINARY_NAME" -perm -u+x 2>/dev/null | head -1)
  [ -n "$built" ] || built="$src/$BINARY_NAME"
  [ -f "$built" ] || { err "build produced no binary"; exit 1; }
  install -m 0755 "$built" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

install_offline() {
  [ -f "$OFFLINE_FILE" ] || { err "offline file not found: $OFFLINE_FILE"; exit 1; }
  local bin="$OFFLINE_FILE"
  case "$OFFLINE_FILE" in
    *.tar.gz|*.tgz)
      command -v tar >/dev/null 2>&1 || { err "tar is required to extract $OFFLINE_FILE"; exit 1; }
      tar -xzf "$OFFLINE_FILE" -C "$TMP"
      bin=$(find "$TMP" -type f -name "$BINARY_NAME" | head -1)
      [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found inside $OFFLINE_FILE"; exit 1; }
      ;;
  esac

  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify set; skipping checksum verification"
  elif [ -f "$OFFLINE_FILE.sha256" ]; then
    verify_checksum "$bin" "$(awk '{print $1}' "$OFFLINE_FILE.sha256")" || exit 1
  elif [ -f "$(dirname "$OFFLINE_FILE")/SHA256SUMS" ]; then
    local expected
    expected=$(grep -E "[[:space:]]\*?$(basename "$bin")\$" "$(dirname "$OFFLINE_FILE")/SHA256SUMS" | awk '{print $1}' | head -1)
    [ -n "$expected" ] && { verify_checksum "$bin" "$expected" || exit 1; }
  else
    warn "no checksum file found alongside $OFFLINE_FILE; skipping verification"
  fi

  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME from local file → $DEST/$BINARY_NAME"
}

install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  local out d

  if out=$(timeout 1 "$bin" completions bash 2>/dev/null) && [ -n "$out" ]; then
    d="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
    mkdir -p "$d" && printf '%s\n' "$out" > "$d/$BINARY_NAME"
    ok "bash completions → $d/$BINARY_NAME"
  fi
  if out=$(timeout 1 "$bin" completions zsh 2>/dev/null) && [ -n "$out" ]; then
    d="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
    mkdir -p "$d" && printf '%s\n' "$out" > "$d/_$BINARY_NAME"
    ok "zsh completions → $d/_$BINARY_NAME"
  fi
  if out=$(timeout 1 "$bin" completions fish 2>/dev/null) && [ -n "$out" ]; then
    d="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
    mkdir -p "$d" && printf '%s\n' "$out" > "$d/$BINARY_NAME.fish"
    ok "fish completions → $d/$BINARY_NAME.fish"
  fi
  return 0
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on your PATH — add this to your shell profile: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

draw_box() {
  local color="$1"; shift
  local lines=("$@") max=0 esc strip
  esc=$(printf '\033')
  strip="s/${esc}\\[[0-9;]*m//g"
  local plain=0
  { [ "$FORCE_NO_COLOR" = 1 ] || [ ! -t 1 ]; } && plain=1

  local l s
  for l in "${lines[@]}"; do
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    [ "${#s}" -gt "$max" ] && max=${#s}
  done
  local inner=$((max + 4)) border="" i
  for ((i = 0; i < inner; i++)); do border+="═"; done

  if [ "$plain" = 1 ]; then
    printf '+'; for ((i = 0; i < inner; i++)); do printf '-'; done; printf '+\n'
  else
    printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  fi

  for l in "${lines[@]}"; do
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    local pad=$((max - ${#s})) p="" j
    for ((j = 0; j < pad; j++)); do p+=" "; done
    if [ "$plain" = 1 ]; then
      printf '| %s%s  |\n' "$s" "$p"
    else
      printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
    fi
  done

  if [ "$plain" = 1 ]; then
    printf '+'; for ((i = 0; i < inner; i++)); do printf '-'; done; printf '+\n'
  else
    printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
  fi
}

print_summary() {
  local ver
  ver=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null || echo unknown)
  draw_box 42 \
    "tapwire installed" \
    "" \
    "binary:   $DEST/$BINARY_NAME" \
    "version:  $ver" \
    "" \
    "run 'tapwire --help' to get started"
  echo
  info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "  (removes: $DEST/$BINARY_NAME and any installed shell completions)"
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  rm -f "$LOCKFILE"
  ok "uninstalled $BINARY_NAME"
}

cleanup() {
  [ -n "${TMP:-}" ] && rm -rf "$TMP"
}

main() {
  parse_args "$@"

  command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

  if [ "$DO_UNINSTALL" = 1 ]; then
    uninstall
    exit 0
  fi

  mkdir -p "$(dirname "$LOCKFILE")" 2>/dev/null || true
  TMP=$(mktemp -d "${TMPDIR:-/tmp}/tapwire-install.XXXXXX")
  trap cleanup EXIT

  detect_platform
  set_proxy_args
  preflight

  acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install already running?)"; exit 1; }

  if [ -n "$OFFLINE_FILE" ]; then
    install_offline
  elif [ "$ALREADY_INSTALLED" = 1 ]; then
    info "skipping download — already installed (use --force to reinstall)"
  else
    resolve_version
    if [ "$FROM_SOURCE" = 1 ]; then
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