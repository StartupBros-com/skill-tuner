#!/usr/bin/env bash
#
# bexport installer — github.com/acme/bexport
#
# Usage (default: installs into $HOME/.local/bin, no sudo required anywhere):
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" | bash
#
# With flags (flags after `--` are passed through to the script):
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" \
#     | bash -s -- --prefix "$HOME/tools/bin" --version 1.4.0
#
# Flags:
#   --prefix DIR      Install directory (default: $HOME/.local/bin). Never requires sudo.
#   --version VER     Install a specific version instead of resolving latest.
#   --force           Reinstall even if the resolved version is already present.
#   --no-verify       Skip SHA256 checksum AND Sigstore signature verification.
#   --offline TARBALL Install from a local tarball; no network calls at all.
#   --easy-mode       Append PREFIX to PATH in your shell rc file if it's missing.
#   --quiet           Only print errors.
#   --no-color        Disable ANSI colors (also honors NO_COLOR env var).
#   --no-gum          Disable gum styling even if installed (ANSI fallback).
#   -h, --help        Show this help and exit.
#
# Env vars honored: HTTPS_PROXY, HTTP_PROXY, NO_PROXY (native to curl), NO_COLOR.
#
# This installer is designed for shared, no-sudo build servers: every artifact it
# writes lives under $PREFIX (or XDG user dirs under $HOME), and the final binary
# is written via install-to-tempfile + atomic rename so a concurrent reader never
# observes a partially-written binary, and a concurrent installer run waits on
# (or safely recovers from) a lock instead of racing.

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="bexport"
BINARY_NAME="bexport"
FALLBACK_VERSION="1.0.0"   # last known-good release; bump when cutting new releases
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/\.github/workflows/release\.ya?ml@refs/tags/v.*\$"

PREFIX="${PREFIX:-$HOME/.local/bin}"
VERSION="${VERSION:-}"
FORCE=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
QUIET=0
NO_COLOR="${NO_COLOR:-}"
NO_GUM=0

TMP=""
LOCK_FD=""
LOCK_DIR_HELD=""

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR / --quiet / non-TTY
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ] && [ -z "$NO_COLOR" ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ -t 1 ] && [ -z "$NO_COLOR" ]; then
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  else
    printf '%s %s\n' "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" 1>&2; }

die() { err "$@"; exit 1; }

draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=${#title}
  local l
  for l in "${lines[@]}"; do (( ${#l} > width )) && width=${#l}; done
  width=$((width + 2))
  local bar; bar=$(printf '─%.0s' $(seq 1 "$width"))
  printf '┌%s┐\n' "$bar"
  printf '│ %-*s│\n' "$((width - 1))" "$title"
  printf '├%s┤\n' "$bar"
  for l in "${lines[@]}"; do printf '│ %-*s│\n' "$((width - 1))" "$l"; done
  printf '└%s┘\n' "$bar"
}

# ---------------------------------------------------------------------------
# Cleanup — single EXIT trap covers temp dir + whichever lock strategy was used
# ---------------------------------------------------------------------------
cleanup() {
  local status=$?
  [ -n "$TMP" ] && [ -d "$TMP" ] && rm -rf "$TMP"
  if [ -n "$LOCK_DIR_HELD" ] && [ -d "$LOCK_DIR_HELD" ]; then
    rm -rf "$LOCK_DIR_HELD"
  fi
  return "$status"
}

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --prefix)     PREFIX="$2"; shift 2 ;;
      --prefix=*)   PREFIX="${1#*=}"; shift ;;
      --version)    VERSION="$2"; shift 2 ;;
      --version=*)  VERSION="${1#*=}"; shift ;;
      --force)      FORCE=1; shift ;;
      --no-verify)  NO_VERIFY=1; shift ;;
      --offline)    OFFLINE_TARBALL="$2"; shift 2 ;;
      --offline=*)  OFFLINE_TARBALL="${1#*=}"; shift ;;
      --easy-mode)  EASY_MODE=1; shift ;;
      --quiet)      QUIET=1; shift ;;
      --no-color)   NO_COLOR=1; shift ;;
      --no-gum)     NO_GUM=1; shift ;;
      -h|--help)    usage ;;
      *) die "unknown flag: $1 (see --help)" ;;
    esac
  done
  # Expand ~ and make absolute so lock/mv paths are unambiguous.
  PREFIX="${PREFIX/#\~/$HOME}"
  case "$PREFIX" in /*) ;; *) PREFIX="$PWD/$PREFIX" ;; esac
}

# ---------------------------------------------------------------------------
# Proxy support — array expands to nothing when unset, so every curl call
# stays unconditional and NO_PROXY is still honored natively by curl.
# ---------------------------------------------------------------------------
PROXY_ARGS=()
setup_proxy() {
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

# ---------------------------------------------------------------------------
# Platform → Rust target triple (musl preferred on Linux for static portability)
# ---------------------------------------------------------------------------
OS=""; ARCH=""; TARGET=""; FROM_SOURCE=0
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)   ARCH=x86_64 ;;
    arm64|aarch64)  ARCH=aarch64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = "linux" ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — filesystem perms under /mnt/* can behave oddly; a native Linux path (e.g. \$HOME) is recommended"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. flag/env

  if [ -f Cargo.toml ]; then                                                 # 2. local manifest
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/' || true)           # 3. GitHub API
  [ -n "$VERSION" ] && return 0

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||' || true)                                        # 4. redirect
  [ -n "$VERSION" ] && return 0

  VERSION="$FALLBACK_VERSION"                                                # 5. hardcoded
  warn "could not resolve latest version over the network; falling back to pinned v$VERSION"
}

# ---------------------------------------------------------------------------
# Preflight — disk space, write perms, existing install, network reachability
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$PREFIX" || die "cannot create $PREFIX (no sudo is used — check ownership/perms of a parent dir)"

  local probe="$PREFIX/.bexport-write-test.$$"
  ( : > "$probe" ) 2>/dev/null || die "$PREFIX is not writable by $(id -un) — pass a different --prefix"
  rm -f "$probe"

  local avail_kb
  avail_kb=$(df -Pk "$PREFIX" | awk 'NR==2 {print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    die "less than 50MB free at $PREFIX ($((avail_kb / 1024))MB available)"
  fi

  if [ -x "$PREFIX/$BINARY_NAME" ]; then
    local existing
    existing=$(timeout 1 "$PREFIX/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    [ -n "$existing" ] && info "existing install detected: $BINARY_NAME $existing"
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    if ! curl -fsSL --connect-timeout 5 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null; then
      die "no network reachability to github.com — check your connection/proxy, or use --offline TARBALL"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Atomic lock — flock-first with mkdir spinlock fallback (macOS has no flock),
# stale-PID self-heal so a crashed prior run can't wedge every future run.
# All state lives under $PREFIX, which is always user-owned — no sudo needed.
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$PREFIX/.${BINARY_NAME}.install.lock"
  local wait_s=1200

  if command -v flock >/dev/null 2>&1; then
    exec 9>>"$lf" 2>/dev/null || die "cannot open lockfile $lf"
    info "waiting for install lock..."
    if ! flock -w "$wait_s" 9; then
      die "timed out after ${wait_s}s waiting for install lock ($lf) — is another install stuck?"
    fi
    LOCK_FD=9
    return 0
  fi

  warn "flock unavailable; using mkdir spinlock fallback"
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then
      warn "clearing stale lock left by dead pid $opid"
      rm -rf "$d"
      continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$wait_s" ]; then
      die "timed out after ${wait_s}s waiting for install lock ($d) — is another install stuck?"
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR_HELD="$d"
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected-sha256 (may be empty)
  [ "$NO_VERIFY" = 1 ] && { warn "--no-verify: skipping checksum"; return 0; }
  if [ -z "$2" ]; then
    warn "no checksum available for this artifact; skipping (use --no-verify to silence)"
    return 0
  fi
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no sha256sum/shasum available; skipping checksum"
    return 0
  fi
  if [ "$actual" = "$2" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $2, got $actual)"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  [ "$NO_VERIFY" = 1 ] && { warn "--no-verify: skipping Sigstore check"; return 0; }
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore signature check"
    return 0
  fi
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle at $2; skipping"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED for $1"
  return 1
}

# ---------------------------------------------------------------------------
# Extract + atomically install: build the final binary in a sibling tempfile
# in the SAME directory as the target, then `mv` it into place. A rename
# within one filesystem is atomic, so no reader — including another CI job
# invoking bexport mid-install — ever observes a partially-written binary.
# ---------------------------------------------------------------------------
extract_and_install() {  # $1=archive path
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$1" -C "$TMP" ;;
    *.zip)          unzip -q "$1" -d "$TMP" ;;
    *) die "unrecognized archive format: $1" ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || die "binary '$BINARY_NAME' not found inside archive"

  local staged="$PREFIX/.${BINARY_NAME}.$$.tmp"
  install -m 0755 "$bin" "$staged"
  mv -f "$staged" "$PREFIX/$BINARY_NAME"
  ok "installed $BINARY_NAME → $PREFIX/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Download — 4-tier URL fallback, each tier verified before install; falls
# through to source build if every prebuilt tier fails.
# ---------------------------------------------------------------------------
download_and_install() {
  local url sha_url sig_url expected_sha artifact="$TMP/artifact.tar.gz"

  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  do
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      sha_url="${url}.sha256"
      expected_sha=$(curl -fsSL "${PROXY_ARGS[@]}" "$sha_url" 2>/dev/null | awk '{print $1}' || true)
      if verify_checksum "$artifact" "$expected_sha"; then
        sig_url="${url}.sigstore.json"
        if verify_sigstore "$artifact" "$sig_url"; then
          extract_and_install "$artifact"
          return 0
        fi
      fi
      rm -f "$artifact"
    fi
  done

  warn "no verifiable prebuilt binary available; building from source"
  build_from_source
}

# ---------------------------------------------------------------------------
# Build-from-source fallback — last tier. rustup installs into $HOME/.cargo,
# so this stays sudo-free too.
# ---------------------------------------------------------------------------
build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    info "cargo not found; installing rustup (user-local, no sudo)"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --no-modify-path \
      || die "rustup install failed"
    # shellcheck disable=SC1091
    source "$HOME/.cargo/env"
  fi
  command -v git >/dev/null 2>&1 || die "git is required to build from source"

  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || die "git clone of $OWNER/$REPO failed"

  ( cd "$src" && cargo build --release ) || die "cargo build failed"

  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || die "build succeeded but $bin was not produced"

  local staged="$PREFIX/.${BINARY_NAME}.$$.tmp"
  install -m 0755 "$bin" "$staged"
  mv -f "$staged" "$PREFIX/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $PREFIX/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Offline install — no network calls at all; verifies against a sidecar
# checksum only if one sits next to the tarball locally.
# ---------------------------------------------------------------------------
install_offline() {
  [ -f "$OFFLINE_TARBALL" ] || die "--offline tarball not found: $OFFLINE_TARBALL"
  local sha=""
  [ -f "${OFFLINE_TARBALL}.sha256" ] && sha=$(awk '{print $1}' "${OFFLINE_TARBALL}.sha256")
  verify_checksum "$OFFLINE_TARBALL" "$sha" || die "checksum verification failed for $OFFLINE_TARBALL"
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Shell completions — XDG user paths only, no rc-file guessing, no sudo.
# ---------------------------------------------------------------------------
install_completions() {
  local bin="$PREFIX/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  timeout 1 "$bin" completions bash >/dev/null 2>&1 || { warn "binary has no 'completions' subcommand; skipping"; return 0; }

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"

  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$bin" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null && ok "bash completions → $bash_dir/$BINARY_NAME"
  "$bin" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null && ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  "$bin" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null && ok "fish completions → $fish_dir/$BINARY_NAME.fish"

  if [ "$zsh_dir" != "" ]; then
    warn "zsh completions require '$zsh_dir' to be on your \$fpath (e.g. fpath+=($zsh_dir) before compinit)"
  fi
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$PREFIX:"*) return 0 ;;
  esac
  warn "$PREFIX is not on your PATH"
  if [ "$EASY_MODE" = 1 ]; then
    local rc=""
    case "${SHELL:-}" in
      */zsh)  rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      *)      rc="$HOME/.profile" ;;
    esac
    printf '\nexport PATH="%s:$PATH"\n' "$PREFIX" >> "$rc"
    ok "appended PATH export to $rc — restart your shell or 'source $rc'"
  else
    info "add this to your shell rc, or re-run with --easy-mode:"
    info "  export PATH=\"$PREFIX:\$PATH\""
  fi
}

# ---------------------------------------------------------------------------
# Final summary + uninstall instructions
# ---------------------------------------------------------------------------
print_summary() {
  local installed_version
  installed_version=$(timeout 1 "$PREFIX/$BINARY_NAME" --version 2>/dev/null || echo "unknown")
  draw_box "bexport install complete" \
    "binary:      $PREFIX/$BINARY_NAME" \
    "version:     $installed_version" \
    "completions: bash-completion / zsh site-functions / fish (XDG, under \$HOME)" \
    "lock:        $PREFIX/.${BINARY_NAME}.install.lock (released)"
  echo
  info "To uninstall:"
  info "  rm -f \"$PREFIX/$BINARY_NAME\""
  info "  rm -f \"\${XDG_DATA_HOME:-\$HOME/.local/share}/bash-completion/completions/$BINARY_NAME\""
  info "  rm -f \"\${XDG_DATA_HOME:-\$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME\""
  info "  rm -f \"\${XDG_CONFIG_HOME:-\$HOME/.config}/fish/completions/$BINARY_NAME.fish\""
  info "  rm -f \"$PREFIX/.${BINARY_NAME}.install.lock\""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"
  TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")
  trap cleanup EXIT

  setup_proxy
  detect_platform

  if [ -n "$OFFLINE_TARBALL" ]; then
    preflight
    acquire_lock
    install_offline
    install_completions
    check_path
    print_summary
    return 0
  fi

  resolve_version
  preflight
  acquire_lock

  if [ -x "$PREFIX/$BINARY_NAME" ] && [ "$FORCE" = 0 ]; then
    local existing
    existing=$(timeout 1 "$PREFIX/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [ "$existing" = "$VERSION" ]; then
      ok "$BINARY_NAME $VERSION is already installed at $PREFIX — skipping download (use --force to reinstall)"
      install_completions
      check_path
      print_summary
      return 0
    fi
  fi

  if [ "$FROM_SOURCE" = 1 ]; then
    build_from_source
  else
    download_and_install
  fi

  install_completions
  check_path
  print_summary
}

main "$@"