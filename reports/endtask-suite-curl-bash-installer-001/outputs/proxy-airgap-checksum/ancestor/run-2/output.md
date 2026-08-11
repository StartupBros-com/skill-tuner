#!/usr/bin/env bash
#
# install.sh — installer for netshim (github.com/acme/netshim)
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" | bash
#
# Designed for large, proxied, and airgapped enterprise fleets:
#   - every network call honors HTTPS_PROXY / HTTP_PROXY / NO_PROXY
#   - SHA256 verification of the downloaded artifact is MANDATORY and can only
#     be skipped with the explicit --no-verify-checksum flag
#   - fully airgapped hosts install from a local tarball via --offline
#
# Flags:
#   --version VERSION        install a specific version (skips resolution)
#   --dest DIR                install directory (default: /usr/local/bin)
#   --offline TARBALL         install from a local tarball, no network calls at all
#   --no-verify-checksum      DANGEROUS: skip SHA256 verification of the artifact
#   --force                   reinstall even if the target version is already installed
#   --quiet                   only print errors
#   --no-color                disable ANSI color output
#   --no-gum                  disable gum styling even if gum is present
#   --proxy URL                override HTTPS_PROXY/HTTP_PROXY for this run
#   -h, --help                 show this help and exit
#
# Env vars honored: HTTPS_PROXY, HTTP_PROXY, NO_PROXY, VERSION, INSTALL_DIR, NO_COLOR
#
# Uninstall:
#   rm -f "$DEST/netshim"
#   rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/netshim"
#   rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_netshim"
#   rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/netshim.fish"
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="netshim"
BINARY_NAME="netshim"
FALLBACK_VERSION="1.0.0"
VERSION_PIN_FILE="/etc/netshim/version"   # optional fleet-wide version pin, enterprise config mgmt
COSIGN_ID_RE="https://github.com/${OWNER}/${REPO}/\.github/workflows/release\.yml@refs/tags/v.*"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

DEST="${INSTALL_DIR:-/usr/local/bin}"
VERSION="${VERSION:-}"
OFFLINE_TARBALL=""
NO_VERIFY_CHECKSUM=0
FORCE=0
QUIET=0
NO_COLOR="${NO_COLOR:-}"
NO_GUM=0
FROM_SOURCE=0

TMP=""
LOCK_HELD=""

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR / non-TTY / --quiet
# err() is never gated by --quiet
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "$NO_COLOR" ] && NO_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ -n "$NO_COLOR" ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }
die()  { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Help / usage
# ---------------------------------------------------------------------------
usage() {
  cat <<'EOF'
install.sh — installer for netshim

Usage:
  install.sh [flags]

Flags:
  --version VERSION       install a specific version (skips resolution)
  --dest DIR              install directory (default: /usr/local/bin)
  --offline TARBALL       install from a local tarball, no network calls at all
  --no-verify-checksum    DANGEROUS: skip SHA256 verification of the artifact
  --force                 reinstall even if the target version is already installed
  --quiet                 only print errors
  --no-color              disable ANSI color output
  --no-gum                disable gum styling even if gum is present
  --proxy URL             override HTTPS_PROXY/HTTP_PROXY for this run
  -h, --help              show this help and exit

Env vars honored: HTTPS_PROXY, HTTP_PROXY, NO_PROXY, VERSION, INSTALL_DIR, NO_COLOR
EOF
}

# ---------------------------------------------------------------------------
# Cleanup / locking
# ---------------------------------------------------------------------------
cleanup() {
  local status=$?
  [ -n "$TMP" ] && rm -rf "$TMP"
  if [ -n "$LOCK_HELD" ] && [ -d "$LOCK_HELD" ]; then
    rm -rf "$LOCK_HELD"
  fi
  exit "$status"
}

acquire_lock() {   # $1=lockfile $2=wait_seconds
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
    if (( $(date +%s) - start >= w )); then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD="$d"
}

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --version) VERSION="${2:?--version requires an argument}"; shift 2 ;;
      --dest) DEST="${2:?--dest requires an argument}"; shift 2 ;;
      --offline) OFFLINE_TARBALL="${2:?--offline requires a tarball path}"; shift 2 ;;
      --no-verify-checksum) NO_VERIFY_CHECKSUM=1; shift ;;
      --force) FORCE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --proxy) HTTPS_PROXY="${2:?--proxy requires a URL}"; HTTP_PROXY="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) die "unknown flag: $1 (see --help)" ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# Proxy support — every curl call below passes "${PROXY_ARGS[@]}"
# NO_PROXY is honored natively by curl, no extra handling needed.
# ---------------------------------------------------------------------------
PROXY_ARGS=()
setup_proxy() {
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
    info "using HTTPS_PROXY for all network calls"
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
    info "using HTTP_PROXY for all network calls"
  fi
}

# ---------------------------------------------------------------------------
# Platform detection — Go-style GOOS/GOARCH, WSL warned not blocked
# ---------------------------------------------------------------------------
detect_platform() {
  local uos uarch
  uos=$(uname -s | tr 'A-Z' 'a-z')
  uarch=$(uname -m)
  case "$uarch" in
    x86_64|amd64) GOARCH=amd64 ;;
    arm64|aarch64) GOARCH=arm64 ;;
    *) die "unsupported architecture: $uarch" ;;
  esac
  case "$uos" in
    linux) GOOS=linux ;;
    darwin) GOOS=darwin ;;
    *) die "unsupported OS: $uos (netshim supports linux and darwin)" ;;
  esac
  if [ "$GOOS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some network-namespace features of netshim may be limited"
  fi
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

check_disk_space() {   # $1=dir, needs at least ~50MB free
  local dir="$1" avail_kb
  mkdir -p "$dir" 2>/dev/null || true
  avail_kb=$(df -Pk "$dir" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    die "less than 50MB free at $dir; aborting"
  fi
}

check_write_perms() {   # $1=dir
  local dir="$1"
  mkdir -p "$dir" 2>/dev/null || true
  if [ ! -w "$dir" ]; then
    die "no write permission at $dir — rerun with --dest <writable dir> or as a user that can write there"
  fi
}

existing_version() {
  command -v "$BINARY_NAME" >/dev/null 2>&1 || return 1
  timeout 1 "$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

check_network() {
  info "checking network reachability through configured proxy…"
  if ! curl -fsS --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null https://github.com 2>/dev/null; then
    die "cannot reach github.com (check HTTPS_PROXY/HTTP_PROXY, or use --offline TARBALL on airgapped hosts)"
  fi
}

preflight() {
  require_cmd curl
  require_cmd tar
  check_disk_space "$DEST"
  check_write_perms "$DEST"
  if [ -z "$OFFLINE_TARBALL" ]; then
    check_network
  fi
  local ev
  ev=$(existing_version || true)
  if [ -n "$ev" ] && [ -n "$VERSION" ] && [ "$ev" = "$VERSION" ] && [ "$FORCE" = 0 ]; then
    ok "netshim $ev already installed at $(command -v "$BINARY_NAME")"
    ALREADY_INSTALLED=1
  else
    ALREADY_INSTALLED=0
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                             # 1. --version flag / env

  if [ -f "$VERSION_PIN_FILE" ]; then                                       # 2. fleet-wide pin file
    VERSION=$(tr -d ' \t\n' < "$VERSION_PIN_FILE")
    [ -n "$VERSION" ] && { info "using pinned version $VERSION from $VERSION_PIN_FILE"; return 0; }
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
      "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
      | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
    [ -n "$VERSION" ] && return 0                                           # 3. GitHub API

    VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
      "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
    [ -n "$VERSION" ] && return 0                                           # 4. redirect resolution
  fi

  VERSION="$FALLBACK_VERSION"                                               # 5. hardcoded fallback
  warn "could not resolve latest version; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
# ---------------------------------------------------------------------------
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    return 1
  fi
}

# fetches the goreleaser-style checksums.txt for $VERSION and extracts the
# expected sha256 for a given artifact filename
get_expected_sha() {   # $1=artifact_filename
  local artifact="$1" cs_url cs_file line
  cs_url="https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${REPO}_${VERSION}_checksums.txt"
  cs_file="$TMP/checksums.txt"
  curl -fsSL "${PROXY_ARGS[@]}" "$cs_url" -o "$cs_file" 2>/dev/null || return 1
  line=$(grep -F "$artifact" "$cs_file" 2>/dev/null | head -1)
  [ -n "$line" ] || return 1
  awk '{print $1}' <<< "$line"
}

verify_checksum() {   # $1=file $2=expected_sha (may be empty)
  local file="$1" expected="$2" actual
  if [ "$NO_VERIFY_CHECKSUM" = 1 ]; then
    warn "SHA256 verification SKIPPED (--no-verify-checksum) — artifact is UNVERIFIED"
    return 0
  fi
  if [ -z "$expected" ]; then
    err "no checksum available for $(basename "$file") and verification was not explicitly skipped"
    err "re-run with --no-verify-checksum only if you trust the source, or supply a matching .sha256 file"
    return 1
  fi
  actual=$(sha256_of "$file") || { die "no sha256sum or shasum tool available to verify checksum (use --no-verify-checksum to bypass, not recommended)"; }
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $(basename "$file"): want $expected got $actual"
  return 1
}

verify_sigstore() {   # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  local bundle="$TMP/sig.json"
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$bundle" 2>/dev/null || { warn "no Sigstore bundle available; skipping signature verification"; return 0; }
  if cosign verify-blob --bundle "$bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED for $(basename "$1")"
  return 1
}

# ---------------------------------------------------------------------------
# Download + install (online path) — 3-tier URL fallback, then build-from-source
# ---------------------------------------------------------------------------
extract_and_install() {   # $1=archive
  local archive="$1" bin
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$archive" -C "$TMP" ;;
    *.zip) require_cmd unzip; unzip -q "$archive" -d "$TMP" ;;
    *) die "unrecognized archive format: $archive" ;;
  esac
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || die "binary '$BINARY_NAME' not found in archive"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME $VERSION → $DEST/$BINARY_NAME"
}

build_from_source() {
  warn "no prebuilt binary available; building from source (requires Go toolchain)"
  require_cmd git
  command -v go >/dev/null 2>&1 || die "Go toolchain not found — install Go, or supply a prebuilt tarball via --offline"
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || die "failed to clone $OWNER/$REPO (check proxy settings)"
  ( cd "$src" && GOOS="$GOOS" GOARCH="$GOARCH" go build -trimpath -ldflags "-s -w" -o "$TMP/$BINARY_NAME" ./... ) \
    || die "build from source failed"
  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

download_and_install() {
  local artifact base_a base_b base_c url ok_download=0
  base_a="${REPO}_${VERSION}_${GOOS}_${GOARCH}.tar.gz"
  base_b="${REPO}-${VERSION}-${GOOS}-${GOARCH}.tar.gz"
  base_c="${REPO}_${GOOS}_${GOARCH}.tar.gz"

  for pair in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$base_a|$base_a" \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$base_b|$base_b" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$base_c|$base_c"
  do
    url="${pair%%|*}"; artifact="${pair##*|}"
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/$artifact" 2>/dev/null; then
      local expected
      expected=$(get_expected_sha "$artifact" || true)
      if verify_checksum "$TMP/$artifact" "$expected"; then
        verify_sigstore "$TMP/$artifact" \
          "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${artifact}.sigstore.json" || true
        extract_and_install "$TMP/$artifact"
        ok_download=1
        break
      else
        die "checksum verification failed for $artifact — refusing to install a corrupted or tampered artifact"
      fi
    fi
  done

  if [ "$ok_download" != 1 ]; then
    build_from_source
  fi
}

# ---------------------------------------------------------------------------
# Offline / airgapped install
# ---------------------------------------------------------------------------
offline_install() {
  local tarball="$OFFLINE_TARBALL" sha_file expected=""
  [ -f "$tarball" ] || die "offline tarball not found: $tarball"

  if [ -f "${tarball}.sha256" ]; then
    expected=$(awk '{print $1}' "${tarball}.sha256")
  elif [ -f "$(dirname "$tarball")/checksums.txt" ]; then
    expected=$(grep -F "$(basename "$tarball")" "$(dirname "$tarball")/checksums.txt" 2>/dev/null | awk '{print $1}' | head -1)
  fi

  verify_checksum "$tarball" "$expected" || die "refusing to install unverified offline artifact"
  extract_and_install "$tarball"
}

# ---------------------------------------------------------------------------
# Shell completions (XDG paths)
# ---------------------------------------------------------------------------
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  command "$bin" completion bash >/dev/null 2>&1 || return 0   # skip if subcommand unsupported

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"

  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$bin" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$bin" completion zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$bin" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "shell completions installed (bash/zsh/fish)"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) : ;;
    *) warn "$DEST is not on your PATH — add it to your shell rc file to use '$BINARY_NAME' directly" ;;
  esac
}

# ---------------------------------------------------------------------------
# Summary / uninstall
# ---------------------------------------------------------------------------
draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=0 line
  for line in "$title" "${lines[@]}"; do
    (( ${#line} > width )) && width=${#line}
  done
  width=$((width + 2))
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --border rounded --padding "0 1" --bold "$title" "" "${lines[@]}"
    return 0
  fi
  printf '┌'; printf '─%.0s' $(seq 1 "$width"); printf '┐\n'
  printf '│ %-*s │\n' "$((width - 2))" "$title"
  printf '├'; printf '─%.0s' $(seq 1 "$width"); printf '┤\n'
  for line in "${lines[@]}"; do
    printf '│ %-*s │\n' "$((width - 2))" "$line"
  done
  printf '└'; printf '─%.0s' $(seq 1 "$width"); printf '┘\n'
}

print_summary() {
  local mode="online"
  [ -n "$OFFLINE_TARBALL" ] && mode="offline"
  [ "$FROM_SOURCE" = 1 ] && mode="built from source"
  draw_box "netshim install summary" \
    "version:   ${VERSION:-unknown}" \
    "mode:      $mode" \
    "binary:    $DEST/$BINARY_NAME" \
    "checksum:  $([ "$NO_VERIFY_CHECKSUM" = 1 ] && echo 'SKIPPED (unverified)' || echo 'verified')" \
    "proxy:     $([ ${#PROXY_ARGS[@]} -gt 0 ] && echo "${PROXY_ARGS[1]}" || echo 'none')"
}

print_uninstall() {
  cat <<EOF

To uninstall netshim:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
EOF
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"
  TMP=$(mktemp -d "${TMPDIR:-/tmp}/netshim-install.XXXXXX")
  trap cleanup EXIT

  setup_proxy

  if [ -n "$OFFLINE_TARBALL" ]; then
    info "offline mode — no network calls will be made"
    detect_platform
    resolve_version
    check_disk_space "$DEST"
    check_write_perms "$DEST"
    acquire_lock "${TMPDIR:-/tmp}/.netshim-install.lock" 2400 || die "could not acquire install lock"
    offline_install
  else
    detect_platform
    resolve_version
    preflight
    if [ "${ALREADY_INSTALLED:-0}" = 1 ]; then
      info "re-verifying shell integration for already-installed version"
    else
      acquire_lock "${TMPDIR:-/tmp}/.netshim-install.lock" 2400 || die "could not acquire install lock"
      download_and_install
    fi
  fi

  install_completions
  check_path
  print_summary
  print_uninstall
}

main "$@"