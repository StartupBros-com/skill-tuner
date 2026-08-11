#!/usr/bin/env bash
#
# bexport installer — https://github.com/acme/bexport
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" | bash
#
# Never requires sudo. Installs into --prefix (default: $HOME/.local/bin), a directory
# every regular user owns on a shared build server. Safe to invoke from several CI jobs
# on the same box at the same time: concurrent runs serialize on a lock under --prefix,
# a run that dies leaves a lock the next run detects and clears automatically, and the
# binary is written to a same-directory temp file and moved into place with a single
# atomic rename — it is never observable half-written.
#
# Flags:
#   --prefix DIR       install directory (default: $HOME/.local/bin)
#   --version VER      install a specific version instead of latest
#   --force            reinstall even if that version is already present
#   --offline TARBALL  install from a local release tarball, no network at all
#   --no-verify        skip SHA256 / Sigstore verification (not recommended)
#   --easy-mode        append a PATH export to ~/.bashrc / ~/.zshrc if needed
#   --quiet            only print errors
#   --no-color         disable ANSI colors
#   --no-gum           disable gum styling even if gum is installed
#   --uninstall        remove the installed binary + completions, then exit
#   -h, --help         show help and exit

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------- constants --

OWNER="acme"
REPO="bexport"
BINARY_NAME="bexport"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/\.github/workflows/release\.ya?ml@refs/tags/v.*\$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

TMP=""
LOCKFILE=""
LOCK_MODE=""
LOCK_MKDIR_PATH=""

# ------------------------------------------------------------- output stack --

HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {  # $1=color $2=glyph $3=level, rest=message
  local color="$1" glyph="$2" lvl="$3"; shift 3
  [ "${QUIET:-0}" = 1 ] && [ "$lvl" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM:-0}" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log 39  '->' info "$@"; }
ok()   { _log 42  '✓'  ok   "$@"; }
warn() { _log 214 '⚠'  warn "$@"; }
err()  { _log 196 '✗'  err  "$@"; }

draw_box() {  # $1=title, rest=lines
  local title="$1"; shift
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM:-0}" = 0 ]; then
    gum style --border rounded --border-foreground 212 --padding "1 2" --bold "$title" "" "$@"
    return 0
  fi
  local width=64 line
  line=$(printf '%*s' "$width" '' | tr ' ' '-')
  printf '+%s+\n' "$line"
  printf '| %-*s |\n' $((width - 2)) "$title"
  printf '+%s+\n' "$line"
  local l
  for l in "$@"; do printf '| %-*s |\n' $((width - 2)) "$l"; done
  printf '+%s+\n' "$line"
}

run_timeout() {  # $1=seconds, rest=cmd  (falls back to running it uncapped if `timeout` is absent, e.g. stock macOS)
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "$secs" "$@"; else "$@"; fi
}

usage() {
  cat <<'EOF'
bexport installer

USAGE:
  curl -fsSL "https://raw.githubusercontent.com/acme/bexport/main/install.sh?$(date +%s)" | bash -s -- [FLAGS]

  # or, after downloading:
  ./install.sh [FLAGS]

FLAGS:
  --prefix DIR       install directory (default: $HOME/.local/bin). No sudo is ever
                     used; pick any directory you own — this is designed for shared
                     build servers where regular users have no root.
  --version VER      install a specific version instead of latest (e.g. --version 1.4.0)
  --force            reinstall even if that version is already present
  --offline TARBALL  install from a local release tarball, no network calls at all
  --no-verify        skip SHA256 / Sigstore verification (not recommended)
  --easy-mode        append a PATH export to ~/.bashrc / ~/.zshrc if PREFIX isn't on PATH
  --quiet            only print errors
  --no-color         disable ANSI colors
  --no-gum           disable gum styling even if gum is installed
  --uninstall        remove the installed binary and completions, then exit
  -h, --help         show this help and exit

ENVIRONMENT:
  HTTPS_PROXY / HTTP_PROXY   used for every network call this script makes
  NO_COLOR                   same effect as --no-color
  XDG_DATA_HOME               where shell completions are installed

CONCURRENCY:
  Safe to run from multiple CI jobs on the same box at once. A second run waits on
  a lock at $PREFIX/.bexport-install.lock, and automatically clears that lock if the
  process that held it has died, instead of racing the first run. The binary itself
  is written to a temp file next to the destination and moved into place with a
  single atomic rename, so it is never visible half-written.
EOF
}

# --------------------------------------------------------------- arg parser --

parse_args() {
  PREFIX="${PREFIX:-$HOME/.local/bin}"
  VERSION="${VERSION:-}"
  FORCE=0; QUIET=0; NO_GUM=0; NO_VERIFY=0; EASY_MODE=0; UNINSTALL=0
  OFFLINE_TARBALL=""

  while [ $# -gt 0 ]; do
    case "$1" in
      --prefix)     PREFIX="$2"; shift 2 ;;
      --version)    VERSION="$2"; shift 2 ;;
      --force)      FORCE=1; shift ;;
      --offline)    OFFLINE_TARBALL="$2"; shift 2 ;;
      --no-verify)  NO_VERIFY=1; shift ;;
      --easy-mode)  EASY_MODE=1; shift ;;
      --quiet)      QUIET=1; shift ;;
      --no-color)   NO_COLOR=1; shift ;;
      --no-gum)     NO_GUM=1; shift ;;
      --uninstall)  UNINSTALL=1; shift ;;
      -h|--help)    usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done

  PREFIX="${PREFIX%/}"
  [ -n "${NO_COLOR:-}" ] && NO_GUM=1
}

# -------------------------------------------------------------------- proxy --

build_proxy_args() {
  PROXY_ARGS=()
  if [ -n "${HTTPS_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [ -n "${HTTP_PROXY:-}" ]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
  # NO_PROXY is honored by curl natively; nothing to do here.
}

# --------------------------------------------------------------- detection --

detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)   ARCH=x86_64 ;;
    arm64|aarch64)  ARCH=aarch64 ;;
  esac
  FROM_SOURCE=0
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — install will proceed normally, but PATH setup may need extra care in your Windows terminal profile"
  fi
}

# --------------------------------------------------------------- preflight --

preflight() {
  local avail_kb
  avail_kb=$(df -Pk "$PREFIX" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    err "less than 50MB free at $PREFIX ($((avail_kb / 1024))MB available)"
    exit 1
  fi

  CURRENT_VERSION=""
  if [ -x "$PREFIX/$BINARY_NAME" ]; then
    CURRENT_VERSION=$(run_timeout 1 "$PREFIX/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    [ -n "$CURRENT_VERSION" ] && info "found existing install: v$CURRENT_VERSION"
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://api.github.com" 2>/dev/null \
      || warn "network check to github.com failed — will still try, or rerun with --offline TARBALL"
  fi
}

# ---------------------------------------------------------- version/verify --

resolve_version() {
  [ -n "$VERSION" ] && return 0                                                     # 1. flag/env

  if [ -f Cargo.toml ]; then
    VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  fi
  [ -n "$VERSION" ] && return 0                                                     # 2. local manifest

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                                     # 3. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  if [ -n "$VERSION" ]; then return 0; fi                                           # 4. redirect

  VERSION="$FALLBACK_VERSION"                                                       # 5. hardcoded
  warn "could not resolve latest version; falling back to v$VERSION"
}

fetch_sidecar() {  # $1=base url  $2=suffix  -> prints local path on stdout, or nothing
  local url="$1$2" out="$TMP/$(basename "$1")$2"
  if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$out" 2>/dev/null && [ -s "$out" ]; then
    echo "$out"
    return 0
  fi
  rm -f "$out"
  return 1
}

verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then
    a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else
    warn "no SHA256 tool available; skipping checksum"
    return 0
  fi
  if [ "$a" = "$2" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $2, got $a)"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  local bundle="$TMP/sig.json"
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$bundle" 2>/dev/null || { warn "no Sigstore bundle published; skipping"; return 0; }
  if cosign verify-blob --bundle "$bundle" \
       --certificate-identity-regexp "$COSIGN_ID_RE" \
       --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED for $1"
  return 1
}

# ---------------------------------------------------- atomic lock (no sudo) --

acquire_lock() {  # $1=lockfile $2=wait_seconds
  local lf="$1" w="${2:-2400}"

  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    if flock -w "$w" 9; then
      LOCK_MODE="flock"
      return 0
    fi
    exec 9>&- 2>/dev/null || true
    return 1
  fi

  # macOS/others without flock: mkdir spinlock with stale-PID self-heal.
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then
      warn "clearing stale install lock left by dead process $opid"
      rm -rf "$d"
      continue
    fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_MKDIR_PATH="$d"
  LOCK_MODE="mkdir"
  return 0
}

release_lock() {
  case "$LOCK_MODE" in
    flock) exec 9>&- 2>/dev/null || true ;;
    mkdir) [ -n "$LOCK_MKDIR_PATH" ] && rm -rf "$LOCK_MKDIR_PATH" ;;
  esac
  LOCK_MODE=""
}

cleanup() {
  local ec=$?
  release_lock
  [ -n "$TMP" ] && rm -rf "$TMP" 2>/dev/null
  exit $ec
}

# ------------------------------------------------------- atomic install --

# Stages into a temp file in the *same directory* as the destination, then
# renames into place. Same-filesystem rename is atomic: readers/writers of
# $PREFIX/$BINARY_NAME see either the old file or the fully-written new one,
# never a partial write — this is what makes concurrent installs safe.
stage_install() {  # $1=path to built/extracted binary
  local src="$1" stage
  stage=$(mktemp "$PREFIX/.${BINARY_NAME}.XXXXXX")
  cp "$src" "$stage"
  chmod 0755 "$stage"
  mv -f "$stage" "$PREFIX/$BINARY_NAME"
  ok "installed $BINARY_NAME → $PREFIX/$BINARY_NAME"
}

extract_and_install() {  # $1=archive path
  local archive="$1" dir bin
  dir=$(mktemp -d "$TMP/extract.XXXXXX")
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$dir" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$dir" ;;
    *.zip)          unzip -q "$archive" -d "$dir" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  bin=$(find "$dir" -type f -name "$BINARY_NAME" | head -1)
  [ -n "$bin" ] || { err "binary not found inside archive"; return 1; }
  chmod +x "$bin" 2>/dev/null || true
  stage_install "$bin"
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup toolchain install stable --profile minimal
    else
      warn "no cargo/rustup found; installing rustup into \$HOME/.cargo (no sudo)"
      curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable
      # shellcheck disable=SC1090
      . "$HOME/.cargo/env"
    fi
  fi
  command -v cargo >/dev/null 2>&1 || { err "cargo still unavailable; cannot build from source"; exit 1; }

  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )

  local bin="$src/target/release/$BINARY_NAME"
  [ -x "$bin" ] || { err "build succeeded but binary not found at $bin"; exit 1; }
  stage_install "$bin"
}

download_and_install() {
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url artifact shafile expected

  if [ "$FROM_SOURCE" = 1 ]; then
    warn "no prebuilt target for this platform; building from source"
    build_from_source
    return
  fi

  for url in "${urls[@]}"; do
    artifact="$TMP/artifact.tar.gz"
    curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null || continue

    if [ "$NO_VERIFY" != 1 ]; then
      expected=""
      shafile=$(fetch_sidecar "$url" ".sha256" || true)
      if [ -n "$shafile" ]; then
        expected=$(awk '{print $1}' "$shafile")
        verify_checksum "$artifact" "$expected" || { warn "checksum failed for $url, trying next source"; continue; }
      else
        warn "no .sha256 sidecar published for this artifact; skipping checksum"
      fi
      verify_sigstore "$artifact" "$url.sigstore" || { warn "signature failed for $url, trying next source"; continue; }
    fi

    extract_and_install "$artifact" && return 0
  done

  warn "no prebuilt binary could be downloaded for $TARGET; building from source"
  build_from_source
}

# -------------------------------------------------------------- completions --

install_completions() {
  local bin="$PREFIX/$BINARY_NAME"
  command -v "$bin" >/dev/null 2>&1 || return 0
  run_timeout 1 "$bin" --help 2>/dev/null | grep -qi completions || return 0

  local data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
  local bash_dir="$data_home/bash-completion/completions"
  local zsh_dir="$data_home/zsh/site-functions"
  local fish_dir="$data_home/fish/vendor_completions.d"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || true

  local shell dest tmp
  for shell in bash zsh fish; do
    case "$shell" in
      bash) dest="$bash_dir/$BINARY_NAME" ;;
      zsh)  dest="$zsh_dir/_$BINARY_NAME" ;;
      fish) dest="$fish_dir/$BINARY_NAME.fish" ;;
    esac
    tmp=$(mktemp "${dest}.XXXXXX")
    if "$bin" completions "$shell" >"$tmp" 2>/dev/null; then
      mv -f "$tmp" "$dest"
      ok "installed $shell completions → $dest"
    else
      rm -f "$tmp"
    fi
  done
}

# ------------------------------------------------------------------- PATH --

check_path() {
  case ":$PATH:" in
    *":$PREFIX:"*) return 0 ;;
  esac
  warn "$PREFIX is not on your PATH"
  if [ "$EASY_MODE" = 1 ]; then
    local rc
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
      [ -f "$rc" ] || continue
      grep -qF "# added by bexport installer" "$rc" 2>/dev/null && continue
      { echo ''; echo '# added by bexport installer'; echo "export PATH=\"$PREFIX:\$PATH\""; } >> "$rc"
      info "appended PATH export to $rc"
    done
  else
    info "add this to your shell profile: export PATH=\"$PREFIX:\$PATH\""
  fi
}

# --------------------------------------------------------------- uninstall --

do_uninstall() {
  local data_home="${XDG_DATA_HOME:-$HOME/.local/share}" removed=0 f
  for f in "$PREFIX/$BINARY_NAME" \
           "$data_home/bash-completion/completions/$BINARY_NAME" \
           "$data_home/zsh/site-functions/_$BINARY_NAME" \
           "$data_home/fish/vendor_completions.d/$BINARY_NAME.fish"; do
    if [ -e "$f" ]; then
      rm -f "$f"
      ok "removed $f"
      removed=1
    fi
  done
  [ "$removed" = 1 ] || info "nothing to remove under $PREFIX"
  info "if you used --easy-mode, remove the '# added by bexport installer' block from your shell rc file(s) by hand"
  exit 0
}

print_uninstall() {
  local data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
  cat <<EOF

To uninstall: rerun this script with --uninstall, or manually:
  rm -f "$PREFIX/$BINARY_NAME"
  rm -f "$data_home/bash-completion/completions/$BINARY_NAME"
  rm -f "$data_home/zsh/site-functions/_$BINARY_NAME"
  rm -f "$data_home/fish/vendor_completions.d/$BINARY_NAME.fish"
EOF
}

# ----------------------------------------------------------------------- main --

main() {
  parse_args "$@"
  detect_platform
  build_proxy_args

  mkdir -p "$PREFIX" 2>/dev/null \
    || { err "cannot create $PREFIX (this installer never uses sudo — pick a --prefix you own)"; exit 1; }
  [ -w "$PREFIX" ] || { err "$PREFIX is not writable — pick a different --prefix"; exit 1; }

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")
  trap cleanup EXIT

  LOCKFILE="$PREFIX/.${BINARY_NAME}-install.lock"
  info "acquiring install lock at $LOCKFILE ..."
  acquire_lock "$LOCKFILE" 2400 \
    || { err "timed out waiting for the install lock — another install may be stuck; if you're sure nothing is running, remove $LOCKFILE(.d) by hand"; exit 1; }

  if [ "$UNINSTALL" = 1 ]; then
    do_uninstall
  fi

  preflight

  if [ -n "$OFFLINE_TARBALL" ]; then
    [ -f "$OFFLINE_TARBALL" ] || { err "--offline file not found: $OFFLINE_TARBALL"; exit 1; }
    extract_and_install "$OFFLINE_TARBALL"
  else
    resolve_version
    if [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" = "$VERSION" ] && [ "$FORCE" != 1 ]; then
      info "bexport v$VERSION already installed at $PREFIX/$BINARY_NAME — skipping download"
    else
      download_and_install
    fi
  fi

  # Completions and PATH setup still run even when the download was skipped
  # above, so a re-run of an already-installed version isn't a full no-op.
  install_completions
  check_path

  draw_box "bexport installed" \
    "binary:      $PREFIX/$BINARY_NAME" \
    "version:     $("$PREFIX/$BINARY_NAME" --version 2>/dev/null || echo unknown)" \
    "completions: bash/zsh/fish under \$XDG_DATA_HOME, if published by this build" \
    "lock:        $LOCKFILE (released)"

  print_uninstall
}

main "$@"