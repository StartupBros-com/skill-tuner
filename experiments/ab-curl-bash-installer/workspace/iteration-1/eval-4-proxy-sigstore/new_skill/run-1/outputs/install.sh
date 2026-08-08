#!/usr/bin/env bash
#
# pgshim installer — https://github.com/hovlabs/pgshim
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash -s -- [flags]
#
# Flags:
#   --version VERSION   Install a specific version (default: latest)
#   --prefix DIR        Install directory (default: /usr/local/bin if writable, else ~/.local/bin)
#   --force             Reinstall even if the requested version is already installed
#   --no-verify         Skip SHA256 / Sigstore verification (NOT recommended)
#   --offline TARBALL   Install from a local tarball, no network access
#   --easy-mode         Append the install dir to PATH in your shell rc if missing
#   --uninstall         Remove pgshim and its shell completions
#   --quiet             Print errors only
#   --no-color          Disable ANSI colors
#   --no-gum            Disable gum styling even if gum is installed
#   -h, --help          Show help and exit
#
# Env vars:
#   PGSHIM_VERSION             same as --version
#   HTTPS_PROXY / HTTP_PROXY   used for every network call (corporate proxy support)
#   NO_COLOR                   same as --no-color
#
set -euo pipefail
umask 022

OWNER="hovlabs"
REPO="pgshim"
BINARY_NAME="pgshim"
FALLBACK_VERSION="0.1.0"  # last known-good; only used if every version-resolution tier fails
COSIGN_ID_RE='^https://github\.com/hovlabs/pgshim/\.github/workflows/release\.ya?ml@refs/tags/v.*$'
COSIGN_ISSUER='https://token.actions.githubusercontent.com'

VERSION="${PGSHIM_VERSION:-}"
PREFIX=""
DEST=""
FORCE=0
NO_VERIFY=0
QUIET=0
NO_GUM=0
OFFLINE_TARBALL=""
EASY_MODE=0
UNINSTALL=0
TMP=""
LOCK_FD_HELD=0
LOCK_DIR=""
ALREADY_CURRENT=0
INSTALLED_VERSION=""
FROM_SOURCE=0
: "${NO_COLOR:=}"

HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" == 1 && "$level" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "$NO_GUM" == 0 && -z "${NO_COLOR:-}" ]]; then
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
err()  { _log err  196 '✗'  "$@" >&2; }

print_help() {
  cat <<'EOF'
pgshim installer

  curl -fsSL "https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh?$(date +%s)" | bash -s -- [flags]

Flags:
  --version VERSION   Install a specific version (default: latest)
  --prefix DIR        Install directory (default: /usr/local/bin if writable, else ~/.local/bin)
  --force             Reinstall even if the requested version is already installed
  --no-verify         Skip SHA256 / Sigstore verification (NOT recommended)
  --offline TARBALL   Install from a local tarball, no network access
  --easy-mode         Append the install dir to PATH in your shell rc if missing
  --uninstall         Remove pgshim and its shell completions
  --quiet             Print errors only
  --no-color          Disable ANSI colors
  --no-gum            Disable gum styling even if gum is installed
  -h, --help          Show this help and exit

Env vars:
  PGSHIM_VERSION             same as --version
  HTTPS_PROXY / HTTP_PROXY   used for every network call
  NO_COLOR                   same as --no-color
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version)
        [[ $# -ge 2 ]] || { err "--version requires a value"; exit 1; }
        VERSION="$2"; shift 2 ;;
      --version=*) VERSION="${1#*=}"; shift ;;
      --prefix)
        [[ $# -ge 2 ]] || { err "--prefix requires a value"; exit 1; }
        PREFIX="$2"; shift 2 ;;
      --prefix=*) PREFIX="${1#*=}"; shift ;;
      --offline)
        [[ $# -ge 2 ]] || { err "--offline requires a tarball path"; exit 1; }
        OFFLINE_TARBALL="$2"; shift 2 ;;
      --offline=*) OFFLINE_TARBALL="${1#*=}"; shift ;;
      --force) FORCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --uninstall) UNINSTALL=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      -h|--help) print_help; exit 0 ;;
      *) err "unknown flag: $1"; print_help; exit 1 ;;
    esac
  done
}

resolve_prefix() {
  if [[ -z "$PREFIX" ]]; then
    if [[ -w /usr/local/bin ]]; then
      PREFIX="/usr/local/bin"
    else
      PREFIX="$HOME/.local/bin"
    fi
  fi
  DEST="$PREFIX"
}

PROXY_ARGS=()
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [[ -n "${HTTP_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi
# NO_PROXY is honored natively by curl; PROXY_ARGS is passed to every curl call below.

detect_platform() {
  FROM_SOURCE=0
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)  ARCH=x86_64 ;;
    arm64|aarch64) ARCH=aarch64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — some networking/proxy config may need extra attention; continuing"
  fi
}

resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] && return 0
  VERSION="$FALLBACK_VERSION"
  warn "could not resolve latest version from GitHub; falling back to hardcoded $VERSION"
}

preflight() {
  local avail_kb
  avail_kb=$(df -Pk "${TMPDIR:-/tmp}" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ "$avail_kb" =~ ^[0-9]+$ ]] && (( avail_kb < 51200 )); then
    err "less than 50MB free in ${TMPDIR:-/tmp} (have ${avail_kb}KB); aborting"
    exit 1
  fi

  mkdir -p "$PREFIX" 2>/dev/null || true
  if [[ ! -w "$PREFIX" ]]; then
    err "install prefix '$PREFIX' is not writable (pass --prefix or fix permissions)"
    exit 1
  fi

  if [[ -x "$DEST/$BINARY_NAME" ]]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [[ -n "$cur" ]]; then
      INSTALLED_VERSION="$cur"
      [[ "$INSTALLED_VERSION" == "$VERSION" && "$FORCE" != 1 ]] && ALREADY_CURRENT=1
    fi
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      err "cannot reach github.com — check network/proxy settings (HTTPS_PROXY=${HTTPS_PROXY:-unset}, HTTP_PROXY=${HTTP_PROXY:-unset})"
      exit 1
    fi
  fi
}

acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || { err "cannot open lockfile $lf"; return 1; }
    if flock -w "$w" 9; then LOCK_FD_HELD=1; return 0; fi
    err "timed out waiting for install lock ($lf)"
    return 1
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null && { rm -rf "$d"; continue; }
    if (( $(date +%s) - start >= w )); then
      err "timed out waiting for install lock ($d)"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
  return 0
}
release_lock() {
  [[ "$LOCK_FD_HELD" == 1 ]] && exec 9>&- 2>/dev/null || true
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR"
}

cleanup() {
  local ec=$?
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP"
  release_lock
  exit $ec
}

fetch_and_verify_checksum() {  # $1=downloaded file  $2=artifact URL (companion lives at $2.sha256)
  local file="$1" url="$2"
  if [[ "$NO_VERIFY" == 1 ]]; then
    warn "checksum verification skipped (--no-verify)"
    return 0
  fi
  local sumfile="$TMP/artifact.sha256"
  if ! curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" -o "$sumfile" 2>/dev/null; then
    err "could not download checksum file (${url}.sha256)"
    return 1
  fi
  local expected; expected=$(awk '{print $1; exit}' "$sumfile")
  [[ -n "$expected" ]] || { err "checksum file is empty or malformed"; return 1; }
  local actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no SHA256 tool (sha256sum/shasum) found; skipping checksum verification"
    return 0
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $(basename "$file") (want $expected, got $actual)"
  return 1
}

verify_sigstore() {  # $1=downloaded file  $2=artifact URL (bundle lives at $2.sigstore.json)
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping Sigstore signature verification"; return 0; }
  local bundle="$TMP/artifact.sigstore.json"
  if ! curl -fsSL "${PROXY_ARGS[@]}" "${2}.sigstore.json" -o "$bundle" 2>/dev/null; then
    warn "no Sigstore bundle at ${2}.sigstore.json; skipping signature check"
    return 0
  fi
  if cosign verify-blob \
      --bundle "$bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore signature verification FAILED for $(basename "$1") — refusing to install"
  return 1
}

atomic_install_binary() {  # $1=source binary path
  local src="$1" tmp_dest="$DEST/.$BINARY_NAME.tmp.$$"
  install -m 0755 "$src" "$tmp_dest"
  mv -f "$tmp_dest" "$DEST/$BINARY_NAME"
}

extract_and_install() {  # $1=archive path
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; exit 1 ;;
  esac
  local bin; bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found inside archive"; exit 1; }
  atomic_install_binary "$bin"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      info "installing a minimal Rust toolchain via rustup"
      rustup toolchain install stable --profile minimal >/dev/null
    else
      info "no Rust toolchain found; bootstrapping via rustup.rs"
      curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable >/dev/null
      # shellcheck disable=SC1091
      source "$HOME/.cargo/env"
    fi
  fi
  command -v git >/dev/null 2>&1 || { err "git is required to build from source"; exit 1; }
  local src="$TMP/src"
  if ! git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null; then
    rm -rf "$src"
    git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  fi
  ( cd "$src" && cargo build --release )
  local bin="$src/target/release/$BINARY_NAME"
  [[ -x "$bin" ]] || { err "build succeeded but binary not found at $bin"; exit 1; }
  atomic_install_binary "$bin"
  ok "built and installed $BINARY_NAME → $DEST/$BINARY_NAME (from source)"
}

download_and_install() {
  if [[ "$FROM_SOURCE" == 1 ]]; then
    build_from_source
    return $?
  fi
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
  )
  local url found=0
  for url in "${urls[@]}"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      found=1
      break
    fi
  done
  if [[ "$found" != 1 ]]; then
    warn "no prebuilt binary found for $TARGET; building from source"
    build_from_source
    return $?
  fi
  if ! fetch_and_verify_checksum "$TMP/artifact.tar.gz" "$url"; then
    err "aborting install — downloaded artifact failed checksum verification"
    exit 1
  fi
  if ! verify_sigstore "$TMP/artifact.tar.gz" "$url"; then
    err "aborting install — downloaded artifact failed Sigstore signature verification"
    exit 1
  fi
  extract_and_install "$TMP/artifact.tar.gz"
}

install_offline() {
  local archive="$OFFLINE_TARBALL"
  [[ -f "$archive" ]] || { err "offline tarball not found: $archive"; exit 1; }
  if [[ "$NO_VERIFY" == 1 ]]; then
    warn "checksum/signature verification skipped (--no-verify)"
  else
    if [[ -f "${archive}.sha256" ]]; then
      local expected actual
      expected=$(awk '{print $1; exit}' "${archive}.sha256")
      if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum "$archive" | cut -d' ' -f1)
      elif command -v shasum >/dev/null 2>&1; then
        actual=$(shasum -a 256 "$archive" | cut -d' ' -f1)
      else
        warn "no SHA256 tool found; skipping checksum verification"
        expected=""
      fi
      if [[ -n "$expected" && "$actual" != "$expected" ]]; then
        err "checksum mismatch for offline tarball (want $expected, got $actual)"
        exit 1
      fi
      [[ -n "$expected" ]] && ok "SHA256 verified (offline)"
    else
      warn "no ${archive}.sha256 found next to tarball; skipping checksum verification"
    fi
    if command -v cosign >/dev/null 2>&1; then
      if [[ -f "${archive}.sigstore.json" ]]; then
        if cosign verify-blob --bundle "${archive}.sigstore.json" \
            --certificate-identity-regexp "$COSIGN_ID_RE" \
            --certificate-oidc-issuer "$COSIGN_ISSUER" "$archive" >/dev/null 2>&1; then
          ok "Sigstore signature verified (offline)"
        else
          err "Sigstore signature verification FAILED for offline tarball — refusing to install"
          exit 1
        fi
      else
        warn "no ${archive}.sigstore.json found next to tarball; skipping signature check"
      fi
    else
      warn "cosign not found; skipping Sigstore signature verification"
    fi
  fi
  extract_and_install "$archive"
}

install_completions() {
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  if "$DEST/$BINARY_NAME" completions bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
  else
    warn "could not generate bash completions"
  fi
  if "$DEST/$BINARY_NAME" completions zsh >"$zsh_dir/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  else
    warn "could not generate zsh completions"
  fi
  if "$DEST/$BINARY_NAME" completions fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions → $fish_dir/$BINARY_NAME.fish"
  else
    warn "could not generate fish completions"
  fi
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
      warn "$DEST is not on your PATH"
      if [[ "$EASY_MODE" == 1 ]]; then
        local rc; rc="$( [[ -n "${ZSH_VERSION:-}" ]] && echo "$HOME/.zshrc" || echo "$HOME/.bashrc" )"
        printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
        ok "added $DEST to PATH in $rc (restart your shell)"
      else
        info "add to your shell rc: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

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

print_summary() {
  [[ "$QUIET" == 1 ]] && return 0
  local ver; ver=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}')
  [[ -z "$ver" ]] && ver="${VERSION:-unknown}"
  local checksum_status="SHA256 verified"
  [[ "$NO_VERIFY" == 1 ]] && checksum_status="skipped (--no-verify)"
  local sig_status="skipped (cosign not found)"
  command -v cosign >/dev/null 2>&1 && sig_status="Sigstore verified (or skipped if no bundle published)"
  [[ "$NO_VERIFY" == 1 ]] && sig_status="skipped (--no-verify)"
  local path_status="(on PATH)"
  case ":$PATH:" in *":$DEST:"*) ;; *) path_status="(NOT on PATH — see warning above)" ;; esac
  draw_box 42 \
    "pgshim installed" \
    "" \
    "binary:      $DEST/$BINARY_NAME" \
    "version:     $ver" \
    "target:      ${TARGET:-built from source}" \
    "checksum:    $checksum_status" \
    "signature:   $sig_status" \
    "completions: bash/zsh/fish (XDG paths)" \
    "prefix:      $DEST $path_status"
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  # uninstall_service is only defined when a systemd/launchd service was installed; guard it
  # so `set -e` can't kill the uninstall between deleting the binary and reporting success.
  if declare -F uninstall_service >/dev/null; then uninstall_service; fi
  ok "uninstalled $BINARY_NAME and its shell completions from $DEST"
}

print_uninstall() {
  [[ "$QUIET" == 1 ]] && return 0
  info "uninstall: curl -fsSL \"https://raw.githubusercontent.com/hovlabs/pgshim/main/install.sh\" | bash -s -- --uninstall"
  info "  or manually: rm -f \"$DEST/$BINARY_NAME\" plus the completion files listed above"
}

main() {
  parse_args "$@"
  VERSION="${VERSION#v}"
  resolve_prefix

  if [[ "$UNINSTALL" == 1 ]]; then
    uninstall
    exit 0
  fi

  detect_platform
  [[ -z "$OFFLINE_TARBALL" ]] && resolve_version
  preflight

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/pgshim-install.XXXXXX")
  trap cleanup EXIT

  local lockdir="${XDG_CACHE_HOME:-$HOME/.cache}/pgshim"
  mkdir -p "$lockdir"
  acquire_lock "$lockdir/install.lock" 2400 || exit 1

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    install_offline
  elif [[ "$ALREADY_CURRENT" == 1 ]]; then
    ok "pgshim $VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
  else
    download_and_install
  fi

  install_completions
  check_path
  print_summary
  print_uninstall
}

main "$@"