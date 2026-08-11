#!/usr/bin/env bash
#
# install.sh — installer for netshim (github.com/acme/netshim)
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" | bash
#
# Enterprise notes:
#   - Every network call this script makes goes through HTTPS_PROXY/HTTP_PROXY (or --proxy).
#   - Airgapped hosts: use --offline TARBALL (with --checksum, or a TARBALL.sha256 sibling file)
#     to install with zero network calls.
#   - Downloaded artifacts are SHA256-verified against the upstream checksums.txt (or an
#     explicit --checksum) before they are trusted. Skipping that check requires the explicit
#     --no-verify flag; it is never silently skipped.
#
# Flags:
#   --version VERSION      Install a specific version (default: latest)
#   --dest DIR              Install directory (default: ~/.local/bin, or /usr/local/bin if root)
#   --offline TARBALL       Airgap mode: install from a local tarball, no network calls at all
#   --checksum SHA256       Expected SHA256 of the artifact/tarball (required with --offline
#                            unless a TARBALL.sha256 sibling file exists, or --no-verify is passed)
#   --proxy URL              Explicit proxy URL (overrides HTTPS_PROXY/HTTP_PROXY env)
#   --no-verify              Skip SHA256/signature verification (explicit opt-out; not default)
#   --force                  Reinstall even if the target version is already present
#   --quiet                  Errors only
#   --no-color / --no-gum    Disable styled output (also honors NO_COLOR env)
#   --easy-mode               Append DEST to PATH in your shell rc file if it's missing
#   --help                    Show this help and exit
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
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION=""
DEST=""
OFFLINE_TARBALL=""
EXPECTED_SHA=""
PROXY_OVERRIDE=""
NO_VERIFY=0
FORCE=0
QUIET=0
NO_GUM="${NO_GUM:-0}"
EASY_MODE=0
FROM_SOURCE=0

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR + non-TTY.
# err() is never gated by --quiet.
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
die()  { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Prelude: temp dir + cleanup trap, right after temp-dir creation
# ---------------------------------------------------------------------------
TMP=""
LOCK_HELD=""
cleanup() {
  local ec=$?
  [ -n "$LOCK_HELD" ] && rm -rf "$LOCK_HELD" 2>/dev/null
  [ -n "$TMP" ] && rm -rf "$TMP"
  exit "$ec"
}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/netshim-install.XXXXXX")
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
    --version=*) VERSION="${1#*=}"; shift ;;
    --dest) DEST="$2"; shift 2 ;;
    --dest=*) DEST="${1#*=}"; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --offline=*) OFFLINE_TARBALL="${1#*=}"; shift ;;
    --checksum) EXPECTED_SHA="$2"; shift 2 ;;
    --checksum=*) EXPECTED_SHA="${1#*=}"; shift ;;
    --proxy) PROXY_OVERRIDE="$2"; shift 2 ;;
    --proxy=*) PROXY_OVERRIDE="${1#*=}"; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --help|-h) print_help; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done

if [ -z "$DEST" ]; then
  if [ "$(id -u)" = 0 ]; then DEST="/usr/local/bin"; else DEST="${HOME}/.local/bin"; fi
fi

# ---------------------------------------------------------------------------
# Proxy support — every curl call in this script passes "${PROXY_ARGS[@]}".
# NO_PROXY is honored natively by curl.
# ---------------------------------------------------------------------------
PROXY_ARGS=()
if [ -n "$PROXY_OVERRIDE" ]; then
  PROXY_ARGS=(--proxy "$PROXY_OVERRIDE")
elif [ -n "${HTTPS_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [ -n "${HTTP_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi
[ "${#PROXY_ARGS[@]}" -gt 0 ] && info "using proxy: ${PROXY_ARGS[1]}"

curl_fetch() { curl -fsSL --connect-timeout 10 "${PROXY_ARGS[@]}" "$@"; }

# ---------------------------------------------------------------------------
# Platform detection — OS/ARCH -> Go GOOS/GOARCH, WSL warned not blocked.
# Go binaries are static by default (no musl-equivalent step needed unless
# cgo is involved, which this project does not use).
# ---------------------------------------------------------------------------
detect_platform() {
  local uname_s uname_m
  uname_s=$(uname -s | tr 'A-Z' 'a-z')
  uname_m=$(uname -m)
  case "$uname_s" in
    linux)  GOOS=linux ;;
    darwin) GOOS=darwin ;;
    *) die "unsupported OS: $uname_s" ;;
  esac
  case "$uname_m" in
    x86_64|amd64)  GOARCH=amd64 ;;
    arm64|aarch64) GOARCH=arm64 ;;
    armv7l)        GOARCH=arm ;;
    *) warn "no prebuilt binary for ${uname_s}/${uname_m}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$GOOS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — networking/proxy behavior may differ slightly from native Linux"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. --version flag

  if [ -f go.mod ]; then
    VERSION=$(awk '/^\/\/ netshim-version:/{print $3; exit}' go.mod 2>/dev/null || true)
  fi
  [ -n "$VERSION" ] && return 0                                              # 2. repo manifest hint

  VERSION=$(curl_fetch "https://api.github.com/repos/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0                                              # 3. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/${OWNER}/${REPO}/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && return 0                                              # 4. redirect resolution

  VERSION="$FALLBACK_VERSION"                                                # 5. hardcoded fallback
  warn "could not resolve latest version from network; falling back to v${VERSION}"
}

# ---------------------------------------------------------------------------
# Preflight — disk space, write perms, existing install, network reachability
# ---------------------------------------------------------------------------
preflight() {
  local dest_parent
  dest_parent=$(dirname "$DEST")
  mkdir -p "$DEST" 2>/dev/null || true
  [ -w "$DEST" ] || [ -w "$dest_parent" ] || die "no write permission for $DEST (try --dest or run with sufficient privileges)"

  local free_kb
  free_kb=$(df -Pk "$dest_parent" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$free_kb" ] && [ "$free_kb" -lt 51200 ]; then
    die "insufficient disk space in $dest_parent (need ~50MB free)"
  fi

  if command -v "$BINARY_NAME" >/dev/null 2>&1 || [ -x "$DEST/$BINARY_NAME" ]; then
    local existing
    existing=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [ -n "$existing" ] && [ "$existing" = "$VERSION" ] && [ "$FORCE" = 0 ]; then
      ALREADY_INSTALLED=1
      ok "netshim v${VERSION} already installed at $DEST/$BINARY_NAME"
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL -o /dev/null --connect-timeout 5 "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null \
      || die "cannot reach github.com — check network/proxy, or use --offline TARBALL for airgapped install"
  fi
}
ALREADY_INSTALLED=0

# ---------------------------------------------------------------------------
# Atomic lock — flock-first, mkdir-fallback (macOS has no flock), stale-PID heal.
# Braced so a bare "exec 9>f" doesn't permanently redirect the caller's stderr.
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
      rm -rf "$d"; continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD="$d"
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
# Missing tool = warn+continue. Tool present + bad result = hard fail.
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected_sha256
  local file="$1" expected="$2" actual
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify passed: skipping SHA256 verification (not recommended)"
    return 0
  fi
  if [ -z "$expected" ]; then
    die "no expected SHA256 available for $(basename "$file") — pass --checksum SHA256 or use --no-verify to explicitly bypass verification"
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    die "no SHA256 tool (sha256sum/shasum) available — cannot verify artifact; install one or pass --no-verify to explicitly bypass"
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
  else
    die "checksum mismatch for $(basename "$file") (want $expected, got $actual) — refusing to install"
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  local file="$1" bundle_url="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  curl_fetch "$bundle_url" -o "$TMP/sig.json" 2>/dev/null || { warn "no Sigstore bundle available; skipping signature verification"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" 2>/dev/null; then
    ok "Sigstore signature verified"
  else
    die "Sigstore signature verification FAILED for $(basename "$file")"
  fi
}

# ---------------------------------------------------------------------------
# Fetch expected SHA256 from upstream checksums.txt for a given artifact name
# ---------------------------------------------------------------------------
fetch_expected_sha() {  # $1=artifact_filename
  local artifact="$1" checksums_url sums
  [ -n "$EXPECTED_SHA" ] && { echo "$EXPECTED_SHA"; return 0; }
  [ "$NO_VERIFY" = 1 ] && { echo ""; return 0; }
  checksums_url="https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}/${REPO}_${VERSION}_checksums.txt"
  sums=$(curl_fetch "$checksums_url" 2>/dev/null) || true
  echo "$sums" | awk -v f="$artifact" '$2==f{print $1}'
}

# ---------------------------------------------------------------------------
# Download — 4-tier fallback across common goreleaser naming conventions,
# then build-from-source.
# ---------------------------------------------------------------------------
download_and_install() {
  local names=(
    "${REPO}_${VERSION}_${GOOS}_${GOARCH}.tar.gz"
    "${REPO}_${GOOS}_${GOARCH}.tar.gz"
    "${REPO}-${GOOS}-${GOARCH}.tar.gz"
  )
  local urls=(
    "https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}/${names[0]}"
    "https://github.com/${OWNER}/${REPO}/releases/latest/download/${names[1]}"
    "https://github.com/${OWNER}/${REPO}/releases/latest/download/${names[2]}"
  )
  local i
  for i in 0 1 2; do
    local url="${urls[$i]}" name="${names[$i]}"
    info "trying $url"
    if curl_fetch "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      local expected
      expected=$(fetch_expected_sha "$name")
      verify_checksum "$TMP/artifact.tar.gz" "$expected"
      verify_sigstore "$TMP/artifact.tar.gz" "https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}/${name}.sig"
      extract_and_install "$TMP/artifact.tar.gz"
      return 0
    fi
  done
  warn "no prebuilt binary found for ${GOOS}/${GOARCH}; building from source"
  build_from_source
}

extract_and_install() {  # $1=archive
  local archive="$1" bin
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) die "unrecognized archive format: $archive" ;;
  esac
  bin=$(find "$TMP" -maxdepth 3 -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || die "binary '$BINARY_NAME' not found inside archive"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME v${VERSION} → $DEST/$BINARY_NAME"
}

build_from_source() {
  command -v go >/dev/null 2>&1 || die "Go toolchain not found — install Go, or download a prebuilt release manually"
  command -v git >/dev/null 2>&1 || die "git not found — required to build from source"
  local src="$TMP/src"
  git clone --depth 1 --branch "v${VERSION}" "https://github.com/${OWNER}/${REPO}.git" "$src" \
    || die "failed to clone ${OWNER}/${REPO} @ v${VERSION}"
  ( cd "$src" && go build -trimpath -ldflags "-s -w -X main.version=${VERSION}" -o "$TMP/${BINARY_NAME}" "./cmd/${BINARY_NAME}" ) \
    || die "build from source failed"
  install -m 0755 "$TMP/${BINARY_NAME}" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME v${VERSION} from source → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Offline / airgap install — zero network calls.
# ---------------------------------------------------------------------------
install_offline() {
  [ -f "$OFFLINE_TARBALL" ] || die "offline tarball not found: $OFFLINE_TARBALL"
  local expected="$EXPECTED_SHA" sidecar="${OFFLINE_TARBALL}.sha256"
  if [ -z "$expected" ] && [ -f "$sidecar" ]; then
    expected=$(awk '{print $1}' "$sidecar")
  fi
  verify_checksum "$OFFLINE_TARBALL" "$expected"
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Shell completions — XDG paths, not guessed rc-file locations.
# ---------------------------------------------------------------------------
install_completions() {
  command -v "$DEST/$BINARY_NAME" >/dev/null 2>&1 || [ -x "$DEST/$BINARY_NAME" ] || return 0

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"

  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completion zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "shell completions installed (bash/zsh/fish)"
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on your PATH"
  if [ "$EASY_MODE" = 1 ]; then
    local rc
    case "${SHELL:-}" in
      */zsh)  rc="$HOME/.zshrc" ;;
      */fish) rc="$HOME/.config/fish/config.fish" ;;
      *)      rc="$HOME/.bashrc" ;;
    esac
    printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
    ok "appended PATH export to $rc (restart your shell, or: export PATH=\"$DEST:\$PATH\")"
  else
    info "add this to your shell rc, or re-run with --easy-mode: export PATH=\"$DEST:\$PATH\""
  fi
}

# ---------------------------------------------------------------------------
# Final summary box
# ---------------------------------------------------------------------------
draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=0 l
  for l in "$title" "${lines[@]}"; do
    [ "${#l}" -gt "$width" ] && width="${#l}"
  done
  width=$((width + 2))
  local border
  border=$(printf '─%.0s' $(seq 1 "$width"))
  printf '┌%s┐\n' "$border"
  printf '│ %-*s │\n' $((width - 2)) "$title"
  printf '├%s┤\n' "$border"
  for l in "${lines[@]}"; do
    printf '│ %-*s │\n' $((width - 2)) "$l"
  done
  printf '└%s┘\n' "$border"
}

print_summary() {
  local mode_line
  if [ "$OFFLINE_TARBALL" != "" ]; then mode_line="mode: offline (airgap)"
  elif [ "$FROM_SOURCE" = 1 ]; then mode_line="mode: built from source"
  else mode_line="mode: prebuilt release"; fi

  draw_box "netshim install summary" \
    "version:  v${VERSION}" \
    "binary:   ${DEST}/${BINARY_NAME}" \
    "${mode_line}" \
    "verified: $([ "$NO_VERIFY" = 1 ] && echo 'SKIPPED (--no-verify)' || echo 'SHA256 ok')" \
    "completions: bash/zsh/fish (XDG dirs)"
}

print_uninstall() {
  info "to uninstall netshim:"
  info "  rm -f '${DEST}/${BINARY_NAME}'"
  info "  rm -f '${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/${BINARY_NAME}'"
  info "  rm -f '${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_${BINARY_NAME}'"
  info "  rm -f '${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/${BINARY_NAME}.fish'"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    info "offline mode: installing from $OFFLINE_TARBALL (no network calls)"
    [ -z "$VERSION" ] && VERSION="local"
    detect_platform || true
    LOCKFILE="${XDG_RUNTIME_DIR:-/tmp}/.netshim-install.lock"
    acquire_lock "$LOCKFILE" 300 || die "could not acquire install lock (another install in progress?)"
    install_offline
  else
    detect_platform
    resolve_version
    preflight

    LOCKFILE="${XDG_RUNTIME_DIR:-/tmp}/.netshim-install.lock"
    acquire_lock "$LOCKFILE" 300 || die "could not acquire install lock (another install in progress?)"

    if [ "$ALREADY_INSTALLED" = 1 ] && [ "$FORCE" = 0 ]; then
      info "skipping download (already at v${VERSION}); re-checking completions"
    elif [ "$FROM_SOURCE" = 1 ]; then
      build_from_source
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  print_summary
  print_uninstall
}

main "$@"