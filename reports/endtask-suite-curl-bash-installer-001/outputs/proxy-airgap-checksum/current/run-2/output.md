#!/usr/bin/env bash
#
# netshim installer — github.com/acme/netshim
#
# Install (proxy-safe, latest release; cache-buster avoids stale CDN/proxy caching of this script):
#   curl -fsSL "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" | bash
#
# Flags (full detail in --help):
#   --version VERSION   --prefix DIR   --offline TARBALL   --sha256 HASH   --no-verify
#   --build-from-source [env: BUILD_FROM_SOURCE=1]   --force   --quiet   --no-color   --no-gum
#   --uninstall   -h/--help
#
# Every network call this script makes honors HTTPS_PROXY / HTTP_PROXY (NO_PROXY is honored
# natively by curl). Fully airgapped machines: run with --offline /path/to/tarball — this mode
# makes no network calls at all and installs straight from the operator-supplied file.
#
# The downloaded (or offline-supplied) artifact is never trusted without a SHA256 match. If no
# checksum can be obtained, the script fails loudly rather than silently installing unverified
# bytes — bypassing that requires the explicit --no-verify flag.

set -euo pipefail
umask 022

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OWNER="acme"
REPO="netshim"
BINARY_NAME="netshim"

# Used only if version resolution can't reach GitHub at all (tier 4 of resolve_version).
# Bump this on release so a fully network-degraded run still lands on something recent.
FALLBACK_VERSION="0.9.0"

# Update these to match netshim's actual release workflow's OIDC identity before shipping.
COSIGN_ID_RE='^https://github\.com/acme/netshim/\.github/workflows/release\.ya?ml@refs/tags/v.*$'
COSIGN_ISSUER='https://token.actions.githubusercontent.com'

# ---------------------------------------------------------------------------
# Defaults (overridable by flags/env)
# ---------------------------------------------------------------------------

VERSION="${VERSION:-}"
DEST="${PREFIX:-$HOME/.local/bin}"
OFFLINE_TARBALL=""
SHA256_OVERRIDE=""
NO_VERIFY=0
BUILD_FROM_SOURCE_FLAG=0
FORCE=0
QUIET="${QUIET:-0}"
NO_GUM=0
DO_UNINSTALL=0
LOCKFILE="${XDG_CACHE_HOME:-$HOME/.cache}/netshim/install.lock"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

HAS_GUM=0

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [[ "${QUIET:-0}" == 1 && "$level" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "${NO_GUM:-0}" != 1 ]]; then
    gum style --foreground "$color" "$glyph $*"
  elif [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

draw_box() {  # $1=color, rest=lines
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

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

usage() {
  cat <<'EOF'
netshim installer

USAGE
  Install (proxy-safe, latest release):
    curl -fsSL "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" | bash

  Install a specific version:
    curl -fsSL "https://raw.githubusercontent.com/acme/netshim/main/install.sh?$(date +%s)" \
      | bash -s -- --version 1.4.0

  Airgapped install from an operator-supplied tarball (no network calls at all):
    ./install.sh --offline /path/to/netshim_1.4.0_linux_amd64.tar.gz --sha256 <known-good-hash>

FLAGS
  --version VERSION      install a specific release (default: latest)
  --prefix DIR            install directory (default: $HOME/.local/bin, env: PREFIX)
  --offline TARBALL        install from a local tarball; makes zero network calls
  --sha256 HASH             known-good SHA256 to verify the artifact/tarball against
  --no-verify                explicitly skip SHA256/Sigstore verification (NOT recommended;
                              required if a checksum truly cannot be obtained and you still
                              want to proceed anyway — verification never fails silently)
  --build-from-source        consent to cloning the repo and building with a local Go
                              toolchain if no prebuilt artifact is available
                              (env: BUILD_FROM_SOURCE=1, for unattended/non-TTY runs)
  --force                     reinstall even if the requested version is already present
  --quiet                     only print errors
  --no-color                  disable ANSI colors (env: NO_COLOR=1)
  --no-gum                    disable gum-styled output, use plain text/ANSI
  --uninstall                 remove netshim + its shell completions, then exit
  -h, --help                  show this help and exit

ENVIRONMENT
  HTTPS_PROXY / HTTP_PROXY / NO_PROXY   honored on every network call this script makes
                                          (NO_PROXY is read natively by curl)
  PREFIX                                 same as --prefix
  BUILD_FROM_SOURCE=1                    same as --build-from-source
  QUIET=1, NO_COLOR=1                    same as --quiet / --no-color
EOF
}

# ---------------------------------------------------------------------------
# Cleanup / locking
# ---------------------------------------------------------------------------

cleanup() {
  local ec=$?
  [[ -n "${TMP:-}" && -d "$TMP" ]] && rm -rf "$TMP"
  [[ -n "${LOCK_DIR:-}" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR"
  exit "$ec"
}

acquire_lock() {
  local lf="$LOCKFILE" w="${LOCK_WAIT:-2400}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null
    if ! flock -w "$w" 9; then
      err "timed out waiting for the install lock: $lf (another install already running?)"
      exit 1
    fi
    return 0
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"
      continue
    fi
    if (( $(date +%s) - start >= w )); then
      err "timed out waiting for the install lock: $d (another install already running?)"
      exit 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

# ---------------------------------------------------------------------------
# Platform / proxy
# ---------------------------------------------------------------------------

detect_platform() {
  local os arch
  os=$(uname -s | tr 'A-Z' 'a-z')
  arch=$(uname -m)
  case "$arch" in
    x86_64|amd64)   arch=amd64 ;;
    arm64|aarch64)  arch=arm64 ;;
    *) err "unsupported architecture: $arch"; exit 1 ;;
  esac
  case "$os" in
    linux|darwin) : ;;
    *) err "unsupported OS: $os"; exit 1 ;;
  esac
  OS="$os"
  ARCH="$arch"
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — proxy/network config sometimes differs from the Windows host; continuing"
  fi
}

setup_proxy() {
  PROXY_ARGS=()
  if [[ -n "${HTTPS_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
  if [[ ${#PROXY_ARGS[@]} -gt 0 ]]; then
    info "using proxy ${PROXY_ARGS[1]} for all network calls (NO_PROXY honored natively by curl)"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution (CLI/env → GitHub API → GitHub redirect → hardcoded)
# ---------------------------------------------------------------------------

resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  info "resolving latest netshim release..."
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [[ -n "$VERSION" ]] && return 0
  VERSION="$FALLBACK_VERSION"
  warn "could not resolve the latest version from GitHub; using fallback v$VERSION (pass --version to override)"
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

preflight() {
  mkdir -p "$DEST"
  [[ -w "$DEST" ]] || { err "$DEST is not writable"; exit 1; }

  local avail
  avail=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}') || avail=""
  if [[ -n "$avail" && "$avail" -lt 20000 ]]; then
    err "insufficient disk space at $DEST (need at least ~20MB free)"
    exit 1
  fi

  if command -v "$BINARY_NAME" >/dev/null 2>&1; then
    CURRENT_VERSION=$(timeout 1 "$BINARY_NAME" --version 2>/dev/null \
      | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
  fi

  if ! curl -fsSL --connect-timeout 5 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null; then
    warn "cannot reach github.com — check network/proxy settings (HTTPS_PROXY=${HTTPS_PROXY:-unset}, HTTP_PROXY=${HTTP_PROXY:-unset})"
  fi
}

# ---------------------------------------------------------------------------
# Checksum + signature verification
# ---------------------------------------------------------------------------

# Hard fail (not soft-skip) when no hashing tool exists: verification is mandatory
# here unless the operator passed the explicit --no-verify flag.
verify_checksum() {  # $1=file $2=expected
  local file="$1" expected="$2" actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    err "no sha256sum or shasum available; cannot verify the artifact (pass --no-verify to bypass)"
    return 1
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified: $actual"
    return 0
  fi
  err "checksum mismatch: expected $expected, got $actual"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping Sigstore signature check"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle at $2; skipping signature check"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore signature verification FAILED for $1"
  return 1
}

fetch_expected_sha() {  # $1 = artifact basename → prints sha to stdout
  local basename="$1" cs_file="$TMP/checksums.txt" url sha
  if [[ -n "$SHA256_OVERRIDE" ]]; then
    echo "$SHA256_OVERRIDE"
    return 0
  fi
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${REPO}_${VERSION}_checksums.txt" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/${REPO}_checksums.txt"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$cs_file" 2>/dev/null; then
      sha=$(awk -v f="$basename" '$2==f{print $1; exit}' "$cs_file")
      if [[ -n "$sha" ]]; then
        echo "$sha"
        return 0
      fi
    fi
  done
  return 1
}

# ---------------------------------------------------------------------------
# Download / extract / build-from-source
# ---------------------------------------------------------------------------

extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -maxdepth 3 -type f -name "$BINARY_NAME" 2>/dev/null | head -1)
  [[ -n "$bin" ]] || { err "'$BINARY_NAME' binary not found inside $archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

confirm_build_from_source() {
  if [[ "${BUILD_FROM_SOURCE:-0}" == 1 || "$BUILD_FROM_SOURCE_FLAG" == 1 ]]; then
    return 0
  fi
  if [[ -t 0 && -t 1 ]]; then
    local reply
    read -r -p "No prebuilt binary available. Build from source? Requires git + a local Go toolchain. [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]] && return 0
    err "declined to build from source; aborting"
    exit 1
  fi
  err "no prebuilt binary and this run is non-interactive; re-run with --build-from-source or BUILD_FROM_SOURCE=1"
  exit 1
}

build_from_source() {
  command -v git >/dev/null 2>&1 || { err "git is required to build from source"; exit 1; }
  command -v go  >/dev/null 2>&1 || {
    err "no local Go toolchain found. Install Go from https://go.dev/dl/ and re-run, or supply a prebuilt tarball via --offline."
    exit 1
  }
  local repo_dir="$TMP/src"
  info "cloning github.com/$OWNER/$REPO@v$VERSION"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$repo_dir" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$repo_dir"
  ( cd "$repo_dir" && CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.version=$VERSION" \
      -o "$TMP/$BINARY_NAME" "./cmd/$BINARY_NAME" )
  [[ -x "$TMP/$BINARY_NAME" ]] || { err "build failed: binary was not produced"; exit 1; }
  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source"
}

download_and_install() {
  local url base downloaded=0
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${REPO}_${VERSION}_${OS}_${ARCH}.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/${REPO}_${OS}_${ARCH}.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/${REPO}-${OS}-${ARCH}.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      downloaded=1
      break
    fi
  done

  if [[ "$downloaded" != 1 ]]; then
    warn "no prebuilt binary found for ${OS}/${ARCH} v${VERSION} at any known release URL"
    confirm_build_from_source
    build_from_source
    return 0
  fi

  base=$(basename "$url")
  if [[ "$NO_VERIFY" == 1 ]]; then
    warn "--no-verify set: skipping SHA256 checksum and Sigstore signature verification (not recommended)"
  else
    local sha
    sha=$(fetch_expected_sha "$base") || {
      err "could not obtain a SHA256 checksum for $base (checksums.txt unreachable via proxy/network)."
      err "pass --sha256 <known-good-hash>, or the explicit --no-verify flag to bypass verification."
      exit 1
    }
    verify_checksum "$TMP/artifact.tar.gz" "$sha" || exit 1
    verify_sigstore "$TMP/artifact.tar.gz" "$url.sigstore.json" || exit 1
  fi

  extract_and_install "$TMP/artifact.tar.gz"
}

# ---------------------------------------------------------------------------
# Offline / airgap install
# ---------------------------------------------------------------------------

install_offline() {
  [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  mkdir -p "$DEST"
  [[ -w "$DEST" ]] || { err "$DEST is not writable"; exit 1; }

  local base sidecar sha
  base=$(basename "$OFFLINE_TARBALL")
  sidecar="${OFFLINE_TARBALL}.sha256"

  if [[ "$NO_VERIFY" == 1 ]]; then
    warn "--no-verify set: skipping SHA256 checksum verification (not recommended)"
  else
    if [[ -n "$SHA256_OVERRIDE" ]]; then
      sha="$SHA256_OVERRIDE"
    elif [[ -f "$sidecar" ]]; then
      sha=$(awk '{print $1}' "$sidecar")
    else
      err "no checksum available for $base."
      err "pass --sha256 <known-good-hash>, place a ${base}.sha256 file next to the tarball, or pass --no-verify to bypass."
      exit 1
    fi
    verify_checksum "$OFFLINE_TARBALL" "$sha" || exit 1
  fi

  command -v cosign >/dev/null 2>&1 && warn "offline mode: Sigstore verification skipped (no network to fetch the bundle)"
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Completions / PATH
# ---------------------------------------------------------------------------

install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"

  if "$DEST/$BINARY_NAME" completion bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
  else
    rm -f "$bash_dir/$BINARY_NAME"
    warn "could not generate bash completions (binary may not support 'completion bash')"
  fi
  "$DEST/$BINARY_NAME" completion zsh  >"$zsh_dir/_$BINARY_NAME"       2>/dev/null && ok "zsh completions → $zsh_dir/_$BINARY_NAME"  || rm -f "$zsh_dir/_$BINARY_NAME"
  "$DEST/$BINARY_NAME" completion fish >"$fish_dir/$BINARY_NAME.fish"  2>/dev/null && ok "fish completions → $fish_dir/$BINARY_NAME.fish" || rm -f "$fish_dir/$BINARY_NAME.fish"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *) warn "$DEST is not on your PATH. Add: export PATH=\"$DEST:\$PATH\"" ;;
  esac
}

# ---------------------------------------------------------------------------
# Uninstall
# ---------------------------------------------------------------------------

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME"
}

print_uninstall_instructions() {
  cat <<EOF

Uninstall:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  or re-run this script with: --uninstall
EOF
}

print_summary() {
  local verify_status="SHA256 + Sigstore verified"
  [[ "$NO_VERIFY" == 1 ]] && verify_status="SKIPPED (--no-verify)"
  local proxy_status="none"
  [[ ${#PROXY_ARGS[@]:-0} -gt 0 ]] && proxy_status="${PROXY_ARGS[1]}"
  draw_box 42 \
    "netshim installed" \
    "" \
    "version:      ${VERSION:-local (offline tarball)}" \
    "location:     $DEST/$BINARY_NAME" \
    "verification: $verify_status" \
    "proxy:        $proxy_status"
}

# ---------------------------------------------------------------------------
# Arg parsing / main
# ---------------------------------------------------------------------------

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --prefix|--dest) DEST="$2"; shift 2 ;;
      --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
      --sha256) SHA256_OVERRIDE="$2"; shift 2 ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --build-from-source) BUILD_FROM_SOURCE_FLAG=1; shift ;;
      --force) FORCE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "unknown argument: $1"; usage; exit 1 ;;
    esac
  done
}

main() {
  parse_args "$@"

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/netshim-install.XXXXXX")
  trap cleanup EXIT

  command -v gum >/dev/null 2>&1 && [[ -t 1 ]] && HAS_GUM=1
  [[ -n "${NO_COLOR:-}" ]] && NO_GUM=1

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    uninstall
    exit 0
  fi

  detect_platform

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    [[ -n "$VERSION" ]] && warn "--version is ignored in --offline mode (version comes from the supplied tarball)"
    install_offline
  else
    setup_proxy
    resolve_version
    preflight
    acquire_lock
    if [[ -n "${CURRENT_VERSION:-}" && "$CURRENT_VERSION" == "$VERSION" && "$FORCE" != 1 ]]; then
      info "netshim v$VERSION is already installed ($(command -v "$BINARY_NAME")); use --force to reinstall"
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  print_summary
  print_uninstall_instructions
}

main "$@"