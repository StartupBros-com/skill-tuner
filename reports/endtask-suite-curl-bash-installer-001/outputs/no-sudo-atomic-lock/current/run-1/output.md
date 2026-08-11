#!/usr/bin/env bash
#
# install.sh — installer for bexport (https://github.com/acme/bexport)
#
# Usage:
#   curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" | bash
#
#   # with flags (note the `--`):
#   curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" \
#     | bash -s -- --prefix "$HOME/tools/bin" --force
#
# This installer never requires sudo or elevated privileges. It installs into
# a directory you own (default: $HOME/.local/bin) and is safe to run
# concurrently from multiple CI jobs on the same shared build box: a second
# run waits for (or safely recovers from) a first run's lock, and the binary
# that lands in $PREFIX is never observable half-written — it is built in a
# scratch file and atomically renamed into place.
#
# Flags:
#   --prefix DIR          Install directory (default: $HOME/.local/bin)
#   --version VERSION     Install a specific version instead of latest
#   --force                Reinstall even if the target version is already present
#   --offline TARBALL      Install from a local tarball, no network calls at all
#   --build-from-source   Consent to building from source (needed off a TTY)
#   --no-verify            Skip SHA256 checksum verification (not recommended)
#   --easy-mode            Append $PREFIX to PATH in your shell rc file
#   --verify                Run a self-test against the already-installed binary and exit
#   --uninstall             Remove bexport and its completions, then exit
#   --quiet                 Only print errors
#   --no-color              Disable ANSI color output
#   --no-gum                Disable gum-based output even if gum is installed
#   -h, --help              Show this help and exit
#
# Environment:
#   HTTPS_PROXY / HTTP_PROXY   Proxy used for every network call (NO_PROXY honored by curl)
#   BUILD_FROM_SOURCE=1        Same as --build-from-source, for unattended/non-TTY runs
#   NO_COLOR=1                 Same as --no-color

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="bexport"
BINARY_NAME="bexport"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="https://github.com/${OWNER}/${REPO}/\.github/workflows/.*"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# ---------------------------------------------------------------------------
# Proxy support — passed to every curl call
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# Flag defaults (all set before `set -u` sees anything unassigned)
# ---------------------------------------------------------------------------
PREFIX="${PREFIX:-$HOME/.local/bin}"
VERSION="${VERSION:-}"
FORCE=0
OFFLINE_TARBALL=""
BUILD_FROM_SOURCE_FLAG=0
NO_VERIFY=0
EASY_MODE=0
VERIFY_FLAG=0
UNINSTALL_FLAG=0
QUIET=0
NO_COLOR="${NO_COLOR:-}"
NO_GUM=0
EXISTING_VERSION=""
CHECKSUMS_CACHE=""
LOCK_DIR=""
TMP=""
TARGET=""
OS=""
ARCH=""

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, honors NO_COLOR / non-TTY / --quiet
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [[ -t 1 ]] && HAS_GUM=1

_log() {  # $1=level $2=color $3=glyph  $4..=message
  local level="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" == 1 && "$level" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "$NO_GUM" != 1 && -z "$NO_COLOR" ]]; then
    gum style --foreground "$color" "$glyph $*"
  elif [[ -n "$NO_COLOR" || ! -t 1 ]]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

usage() {
  cat <<EOF
install.sh — installer for bexport ($OWNER/$REPO)

Usage:
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash

Flags:
  --prefix DIR          Install directory (default: \$HOME/.local/bin)
  --version VERSION     Install a specific version instead of latest
  --force                Reinstall even if the target version is already present
  --offline TARBALL      Install from a local tarball, no network calls at all
  --build-from-source   Consent to building from source (needed off a TTY)
  --no-verify            Skip SHA256 checksum verification (not recommended)
  --easy-mode            Append \$PREFIX to PATH in your shell rc file
  --verify                Run a self-test against the already-installed binary and exit
  --uninstall             Remove bexport and its completions, then exit
  --quiet                 Only print errors
  --no-color              Disable ANSI color output
  --no-gum                Disable gum-based output even if gum is installed
  -h, --help              Show this help and exit

No sudo is ever used. bexport installs entirely under a directory you own.
EOF
}

run_with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 1 "$@"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Cleanup — releases the mkdir-fallback lock (flock releases itself on fd
# close at process exit) and removes the scratch dir. No half-installed
# binary is ever left behind because installs land via atomic rename, not
# via cleanup.
# ---------------------------------------------------------------------------
cleanup() {
  local ec=$?
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR"
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP"
  exit "$ec"
}

# ---------------------------------------------------------------------------
# Platform detection — musl preferred on Linux for a static, portable binary
# ---------------------------------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}"; TARGET="" ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — PATH/rc-file detection may need manual adjustment"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — CLI flag/env, GitHub API, redirect, hardcoded fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  if [[ -n "$OFFLINE_TARBALL" ]]; then
    VERSION="$FALLBACK_VERSION"
    return 0
  fi
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  if [[ -n "$VERSION" ]]; then
    info "resolved latest version: $VERSION"
    return 0
  fi
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  if [[ -n "$VERSION" ]]; then
    info "resolved latest version via redirect: $VERSION"
    return 0
  fi
  VERSION="$FALLBACK_VERSION"
  warn "could not resolve latest version from GitHub; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# Checksums — fetched once per run from the release's checksums.txt
# ---------------------------------------------------------------------------
fetch_checksums() {
  [[ -n "$CHECKSUMS_CACHE" ]] && return 0
  local url="https://github.com/$OWNER/$REPO/releases/download/v$VERSION/checksums.txt"
  if curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" "$url" -o "$TMP/checksums.txt" 2>/dev/null; then
    CHECKSUMS_CACHE="$TMP/checksums.txt"
  fi
}

expected_sha_for() {  # $1=filename
  [[ -z "$CHECKSUMS_CACHE" ]] && return 1
  awk -v f="$1" '$2==f || $NF==f {print $1; exit}' "$CHECKSUMS_CACHE"
}

verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0; fi
  if [[ "$a" == "$2" ]]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $a)"; return 1; fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle published for this artifact; skipping"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "signature verified"
  else
    err "Sigstore verification FAILED"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Atomic lock — flock-first, mkdir fallback (no flock on macOS), stale-PID heal.
# Scoped to $PREFIX so concurrent CI jobs targeting different --prefix values
# never block each other, while jobs sharing a prefix serialize correctly.
# ---------------------------------------------------------------------------
acquire_lock() {  # $1=lockfile $2=wait_seconds
  local lf="$1" wait_s="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null
    if flock -w "$wait_s" 9; then
      return 0
    else
      err "timed out after ${wait_s}s waiting for install lock ($lf) — another install may be stuck"
      return 1
    fi
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      warn "clearing stale install lock left by dead process $opid"
      rm -rf "$d"
      continue
    fi
    if (( $(date +%s) - start >= wait_s )); then
      err "timed out after ${wait_s}s waiting for install lock ($d) — another install may be stuck"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
  return 0
}

# ---------------------------------------------------------------------------
# Preflight — no sudo anywhere; only checks against a directory the user owns
# ---------------------------------------------------------------------------
preflight() {
  info "running preflight checks"

  if ! mkdir -p "$PREFIX" 2>/dev/null; then
    err "cannot create install directory: $PREFIX — choose a --prefix you can write to (no sudo is ever used)"
    exit 1
  fi
  if [[ ! -w "$PREFIX" ]]; then
    err "no write permission on $PREFIX — choose a --prefix you own"
    exit 1
  fi

  local avail_kb
  avail_kb=$(df -Pk "$PREFIX" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 20480 ]]; then
    err "less than 20MB free at $PREFIX; aborting"
    exit 1
  fi

  if [[ -x "$PREFIX/$BINARY_NAME" ]]; then
    local cur
    cur=$(run_with_timeout "$PREFIX/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
    if [[ -n "$cur" ]]; then
      EXISTING_VERSION="$cur"
      info "found existing install: $BINARY_NAME $cur"
    fi
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 3 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      warn "network check to github.com failed — check HTTPS_PROXY/HTTP_PROXY, or use --offline TARBALL"
    fi
  fi
}

# ---------------------------------------------------------------------------
# Build-from-source fallback — requires explicit consent (TTY prompt, or
# --build-from-source / BUILD_FROM_SOURCE=1 off a TTY)
# ---------------------------------------------------------------------------
confirm_build_from_source() {
  if [[ "$BUILD_FROM_SOURCE_FLAG" == 1 || "${BUILD_FROM_SOURCE:-0}" == 1 ]]; then
    return 0
  fi
  if [[ -t 0 && -t 1 ]]; then
    local reply
    read -r -p "No prebuilt binary for $TARGET. Build from source? This may install rustup/cargo under \$HOME. [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]] && return 0
    err "aborted: no prebuilt binary and build-from-source declined"
    exit 1
  fi
  err "no prebuilt binary for this platform and not running interactively; re-run with --build-from-source or BUILD_FROM_SOURCE=1 to allow building from source"
  exit 1
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    warn "cargo not found; installing rustup toolchain under \$HOME (no sudo)"
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --no-modify-path
    # shellcheck disable=SC1091
    source "$HOME/.cargo/env"
  fi
  local src_dir="$TMP/src" clone_args
  clone_args=(--depth 1 "https://github.com/$OWNER/$REPO.git" "$src_dir")
  [[ -n "$VERSION" ]] && clone_args=(--depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src_dir")
  git clone "${clone_args[@]}"
  ( cd "$src_dir" && cargo build --release )
  local bin="$src_dir/target/release/$BINARY_NAME"
  [[ -x "$bin" ]] || { err "build succeeded but binary not found at $bin"; return 1; }
  atomic_install "$bin"
}

# ---------------------------------------------------------------------------
# Atomic install — build the file in a scratch name in the SAME directory,
# then rename into place. Rename on a POSIX filesystem is atomic, so the
# final path is either the old binary or the fully-written new one — never
# a partial write, regardless of how many installers race on this box.
# ---------------------------------------------------------------------------
atomic_install() {  # $1=source binary path
  local src="$1" tmp_dest
  mkdir -p "$PREFIX"
  tmp_dest="$PREFIX/.${BINARY_NAME}.tmp.$$"
  install -m 0755 "$src" "$tmp_dest"
  mv -f "$tmp_dest" "$PREFIX/$BINARY_NAME"
  ok "installed $BINARY_NAME v$VERSION → $PREFIX/$BINARY_NAME"
}

extract_and_install() {  # $1=archive
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -type f -name "$BINARY_NAME" | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  chmod +x "$bin"
  atomic_install "$bin"
}

# ---------------------------------------------------------------------------
# Download — 4-tier URL fallback, checksum required by default, Sigstore
# soft-skip/hard-fail, then source-build as the last resort
# ---------------------------------------------------------------------------
download_and_install() {
  if [[ -z "$TARGET" ]]; then
    warn "no prebuilt binary for this platform"
    confirm_build_from_source
    build_from_source
    return $?
  fi

  fetch_checksums

  local candidates=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url fname
  for url in "${candidates[@]}"; do
    fname=$(basename "$url")
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      if [[ "$NO_VERIFY" == 1 ]]; then
        warn "--no-verify set; skipping checksum verification"
      else
        local expected
        expected=$(expected_sha_for "$fname" || true)
        if [[ -z "$expected" ]]; then
          err "no published checksum for $fname; refusing to install unverified binary (pass --no-verify to override)"
          return 1
        fi
        verify_checksum "$TMP/artifact.tar.gz" "$expected" || return 1
      fi
      verify_sigstore "$TMP/artifact.tar.gz" "$url.sigstore.json" || return 1
      extract_and_install "$TMP/artifact.tar.gz"
      return 0
    fi
  done

  warn "no prebuilt binary available for $TARGET (all mirrors failed); falling back to source build"
  confirm_build_from_source
  build_from_source
}

install_offline() {
  info "offline mode: installing from $OFFLINE_TARBALL (no network calls)"
  [[ -f "$OFFLINE_TARBALL" ]] || { err "tarball not found: $OFFLINE_TARBALL"; exit 1; }
  if [[ "$NO_VERIFY" != 1 ]]; then
    warn "offline mode has no checksums.txt to verify against; skipping checksum check (pass --no-verify to silence this)"
  fi
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Completions — XDG paths, not hardcoded rc-file guesses
# ---------------------------------------------------------------------------
install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"

  if "$PREFIX/$BINARY_NAME" completions bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
  else
    warn "could not generate bash completions"
    rm -f "$bash_dir/$BINARY_NAME"
  fi
  if "$PREFIX/$BINARY_NAME" completions zsh >"$zsh_dir/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  else
    rm -f "$zsh_dir/_$BINARY_NAME"
  fi
  if "$PREFIX/$BINARY_NAME" completions fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions → $fish_dir/$BINARY_NAME.fish"
  else
    rm -f "$fish_dir/$BINARY_NAME.fish"
  fi
}

# ---------------------------------------------------------------------------
# PATH check — never assume $PREFIX is on PATH
# ---------------------------------------------------------------------------
path_check() {
  case ":$PATH:" in
    *":$PREFIX:"*) return 0 ;;
  esac
  if [[ "$EASY_MODE" == 1 ]]; then
    local rc
    rc="$HOME/.$(basename "${SHELL:-bash}")rc"
    [[ -f "$rc" ]] || rc="$HOME/.profile"
    printf '\nexport PATH="%s:$PATH"\n' "$PREFIX" >> "$rc"
    ok "added $PREFIX to PATH in $rc (restart your shell, or: source $rc)"
  else
    warn "$PREFIX is not on your PATH. Add it manually, or re-run with --easy-mode."
  fi
}

self_test() {
  [[ -x "$PREFIX/$BINARY_NAME" ]] || { err "$BINARY_NAME is not installed at $PREFIX"; exit 1; }
  local v
  v=$(run_with_timeout "$PREFIX/$BINARY_NAME" --version 2>/dev/null) || { err "$BINARY_NAME --version failed to run"; exit 1; }
  ok "self-test passed: $v"
}

# ---------------------------------------------------------------------------
# Final summary box
# ---------------------------------------------------------------------------
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
# Uninstall — printed at the end of every run; preserves config
# ---------------------------------------------------------------------------
uninstall() {
  rm -f "$PREFIX/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME from $PREFIX"
}

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --prefix)               PREFIX="$2"; shift 2 ;;
      --prefix=*)              PREFIX="${1#*=}"; shift ;;
      --version)               VERSION="$2"; shift 2 ;;
      --version=*)              VERSION="${1#*=}"; shift ;;
      --force)                  FORCE=1; shift ;;
      --offline)                 OFFLINE_TARBALL="$2"; shift 2 ;;
      --offline=*)                OFFLINE_TARBALL="${1#*=}"; shift ;;
      --build-from-source)        BUILD_FROM_SOURCE_FLAG=1; shift ;;
      --no-verify)                  NO_VERIFY=1; shift ;;
      --easy-mode)                   EASY_MODE=1; shift ;;
      --verify)                       VERIFY_FLAG=1; shift ;;
      --uninstall)                     UNINSTALL_FLAG=1; shift ;;
      --quiet)                          QUIET=1; shift ;;
      --no-color)                        NO_COLOR=1; shift ;;
      --no-gum)                           NO_GUM=1; shift ;;
      -h|--help)                           usage; exit 0 ;;
      *) err "unknown flag: $1 (see --help)"; exit 1 ;;
    esac
  done
  PREFIX="${PREFIX/#\~/$HOME}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
parse_args "$@"

if [[ "$UNINSTALL_FLAG" == 1 ]]; then
  uninstall
  exit 0
fi

if [[ "$VERIFY_FLAG" == 1 ]]; then
  self_test
  exit 0
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/bexport-install.XXXXXX")
trap cleanup EXIT

detect_platform
preflight

LOCKFILE="$PREFIX/.${BINARY_NAME}-install.lock"
acquire_lock "$LOCKFILE" 2400 || exit 1

resolve_version

if [[ -n "$OFFLINE_TARBALL" ]]; then
  install_offline
elif [[ -n "$EXISTING_VERSION" && "$EXISTING_VERSION" == "$VERSION" && "$FORCE" != 1 ]]; then
  ok "$BINARY_NAME $VERSION already installed at $PREFIX — skipping download (use --force to reinstall)"
else
  download_and_install
fi

install_completions
path_check

draw_box 42 \
  "bexport install complete" \
  "" \
  "binary:      $PREFIX/$BINARY_NAME" \
  "version:     $VERSION" \
  "prefix:      $PREFIX (no sudo used)" \
  "completions: bash/zsh/fish (XDG dirs)"

echo
info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall --prefix \"$PREFIX\""
info "  (removes: $PREFIX/$BINARY_NAME and its shell completions; agent/shell hooks, if any, are left in place)"