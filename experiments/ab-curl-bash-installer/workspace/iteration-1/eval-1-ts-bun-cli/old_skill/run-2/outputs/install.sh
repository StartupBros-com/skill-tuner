#!/usr/bin/env bash
#
# tapwire installer
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/tapwire/main/install.sh?$(date +%s)" | bash
#
# tapwire ships as standalone binaries (bun build --compile) — no node/bun needed to run it.
# Piping flags through: curl -fsSL .../install.sh | bash -s -- --force
#
# Flags:
#   --version VERSION   install a specific version instead of latest
#   --dest DIR          install directory (default: $HOME/.local/bin)
#   --force             reinstall even if the requested version is already installed
#   --no-verify         skip SHA256 + Sigstore verification (not recommended)
#   --offline FILE       install from a local binary or .tar.gz, no network calls
#   --easy-mode          append the install dir to PATH in your shell rc if missing
#   --quiet              errors only
#   --no-color            disable ANSI colors
#   --no-gum              disable gum styling (plain ANSI fallback)
#   --uninstall           remove tapwire and exit
#   -h, --help            show help and exit
#
# Env vars:
#   TAPWIRE_VERSION, TAPWIRE_INSTALL_DIR, HTTPS_PROXY / HTTP_PROXY / NO_PROXY, NO_COLOR
#
set -euo pipefail
umask 022

# ---- logging ----
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
NO_GUM="${NO_GUM:-0}"
USE_COLOR=1
{ [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; } && USE_COLOR=0
[ -n "${NO_COLOR:-}" ] && NO_GUM=1
QUIET=0

_log() {
  local tag="$1" color="$2" glyph="$3"; shift 3
  [ "${QUIET:-0}" = 1 ] && [ "$tag" != err ] && return 0
  if [ "${HAS_GUM:-0}" = 1 ] && [ "${NO_GUM:-0}" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "${USE_COLOR:-1}" = 1 ]; then
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  else
    printf '%s %s\n' "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  'OK' "$@"; }
warn() { _log warn 214 '!!' "$@"; }
err()  { _log err  196 'XX' "$@" 1>&2; }

# ---- constants ----
OWNER="hovlabs"
REPO="tapwire"
BINARY_NAME="tapwire"
FALLBACK_VERSION="0.1.0"   # bump when cutting a new tapwire release
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/.+"
LOCKFILE="${XDG_CACHE_HOME:-$HOME/.cache}/tapwire-install.lock"

DEST="${TAPWIRE_INSTALL_DIR:-$HOME/.local/bin}"
VERSION="${TAPWIRE_VERSION:-}"
FORCE=0
NO_VERIFY=0
OFFLINE_FILE=""
EASY_MODE=0
DO_UNINSTALL=0

print_help() {
  cat <<EOF
tapwire installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh" | bash -s -- [flags]

Flags:
  --version VERSION   install a specific version instead of latest
  --dest DIR          install directory (default: \$HOME/.local/bin)
  --force             reinstall even if the requested version is already installed
  --no-verify         skip SHA256 + Sigstore verification (not recommended)
  --offline FILE       install from a local binary or .tar.gz, no network calls
  --easy-mode          append the install dir to PATH in your shell rc if missing
  --quiet              errors only
  --no-color            disable ANSI colors
  --no-gum              disable gum styling (plain ANSI fallback)
  --uninstall           remove tapwire and exit
  -h, --help            show this help and exit

Env vars:
  TAPWIRE_VERSION       same as --version
  TAPWIRE_INSTALL_DIR   same as --dest
  HTTPS_PROXY / HTTP_PROXY / NO_PROXY   proxy for all network calls
  NO_COLOR              disable ANSI colors
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --quiet) QUIET=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-color) USE_COLOR=0; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_FILE="$2"; shift 2 ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) err "unknown flag: $1"; print_help; exit 1 ;;
  esac
done

# ---- proxy ----
PROXY_ARGS=()
if [ -n "${HTTPS_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [ -n "${HTTP_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi
# NO_PROXY is honored by curl natively.

# ---- summary box (ASCII-only: minimal containers may lack a UTF-8 locale) ----
draw_box() {  # $1=color, rest=lines
  local color="$1"; shift
  local lines=("$@") max=0 esc s
  esc=$(printf '\033')
  local strip="s/${esc}\\[[0-9;]*m//g"
  for l in "${lines[@]}"; do
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    [ "${#s}" -gt "$max" ] && max=${#s}
  done
  local inner=$((max + 4)) border="" i
  for ((i = 0; i < inner; i++)); do border+="="; done
  if [ "$USE_COLOR" = 1 ] && [ "${HAS_GUM:-0}" = 0 -o "${NO_GUM:-0}" = 1 ]; then
    printf "\033[%sm+%s+\033[0m\n" "$color" "$border"
    for l in "${lines[@]}"; do
      s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
      local pad=$((max - ${#s})) p="" j
      for ((j = 0; j < pad; j++)); do p+=" "; done
      printf "\033[%sm|\033[0m  %b%s  \033[%sm|\033[0m\n" "$color" "$l" "$p" "$color"
    done
    printf "\033[%sm+%s+\033[0m\n" "$color" "$border"
  else
    printf '+%s+\n' "$border"
    for l in "${lines[@]}"; do
      s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
      local pad=$((max - ${#s})) p="" j
      for ((j = 0; j < pad; j++)); do p+=" "; done
      printf '|  %s%s  |\n' "$s" "$p"
    done
    printf '+%s+\n' "$border"
  fi
}

# ---- platform ----
FROM_SOURCE=0
ASSET=""
detect_platform() {
  local os arch
  os=$(uname -s | tr 'A-Z' 'a-z')
  arch=$(uname -m)
  case "$arch" in x86_64|amd64) arch=x64 ;; arm64|aarch64) arch=arm64 ;; esac
  case "${os}-${arch}" in
    linux-x64)    ASSET="tapwire-linux-x64" ;;
    linux-arm64)  ASSET="tapwire-linux-arm64" ;;
    darwin-arm64) ASSET="tapwire-darwin-arm64" ;;
    *) warn "no prebuilt tapwire binary for ${os}/${arch}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$os" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — tapwire should work, but network features may need extra config"
  fi
}

# ---- version resolution ----
# No manifest tier here (unlike a repo-local build script): install.sh runs in an
# arbitrary user directory, so a stray package.json in $PWD must never set VERSION.
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. --version / TAPWIRE_VERSION

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [ -n "$VERSION" ] && return 0                                              # 2. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [ -n "$VERSION" ] && return 0                                              # 3. redirect resolution

  VERSION="$FALLBACK_VERSION"                                                # 4. hardcoded fallback
  warn "could not resolve latest tapwire version from GitHub; falling back to $VERSION"
}

# ---- preflight ----
ALREADY_CURRENT=0
preflight() {
  local parent
  parent=$(dirname "$DEST")
  if [ -d "$DEST" ]; then
    [ -w "$DEST" ] || { err "$DEST is not writable; re-run with --dest <dir> or fix permissions"; exit 1; }
  else
    [ -w "$parent" ] || { err "cannot create $DEST (parent $parent is not writable)"; exit 1; }
  fi

  local avail
  avail=$(df -Pk "$parent" 2>/dev/null | tail -1 | tr -s ' ' | cut -d' ' -f4)
  if [ -n "$avail" ] && [[ "$avail" =~ ^[0-9]+$ ]] && [ "$avail" -lt 51200 ]; then
    err "insufficient disk space near $DEST (need ~50MB, have $((avail / 1024))MB)"; exit 1
  fi

  if [ -x "$DEST/$BINARY_NAME" ]; then
    local cur=""
    if command -v timeout >/dev/null 2>&1; then
      cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | head -1) || true
    else
      cur=$("$DEST/$BINARY_NAME" --version 2>/dev/null | head -1) || true
    fi
    [ -n "$cur" ] && info "existing install found: $cur"
    case "$cur" in
      *"$VERSION"*) [ "$FORCE" != 1 ] && ALREADY_CURRENT=1 ;;
    esac
  fi

  if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
    warn "network check to github.com failed; continuing (may be transient or a proxy/firewall issue)"
  fi
}

# ---- atomic lock ----
# flock-first with mkdir spinlock fallback (no flock on macOS). Brace-scope the exec:
# a bare `exec 9>f 2>/dev/null` permanently redirects the *caller's* stderr to /dev/null.
acquire_lock() {
  local lf="$1" w="${2:-300}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || { err "cannot open lock file $lf"; exit 1; }
    flock -w "$w" 9 || { err "could not acquire lock on $lf (another install may be running)"; exit 1; }
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    if [ $(( $(date +%s) - start )) -ge "$w" ]; then err "timed out waiting for lock $d"; exit 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  trap 'rm -rf "'"$d"'"; cleanup' EXIT
}

# ---- checksum + signature ----
verify_checksum() {  # $1=file $2=expected_sha256
  local file="$1" expected="$2" actual
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no sha256sum/shasum found; skipping checksum verification"
    return 0
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $(basename "$file") (want $expected, got $actual)"
  return 1
}

fetch_expected_sha() {  # $1=asset filename
  local url sums=""
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/SHA256SUMS" \
    "https://github.com/$OWNER/$REPO/releases/download/$VERSION/SHA256SUMS" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/SHA256SUMS"; do
    sums=$(curl -fsSL "${PROXY_ARGS[@]}" "$url" 2>/dev/null) && [ -n "$sums" ] && break
  done
  [ -n "$sums" ] || { warn "could not fetch SHA256SUMS"; return 1; }
  printf '%s\n' "$sums" | grep -E "[[:space:]]\*?${1}\$" | cut -d' ' -f1 | head -1
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle published for this release; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore signature verification FAILED for $(basename "$1")"
  return 1
}

# ---- download (4-tier) ----
download_and_install() {
  local asset="$ASSET" expected=""
  if [ "$NO_VERIFY" != 1 ]; then
    expected=$(fetch_expected_sha "$asset" || true)
  fi
  local url
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$asset" \
    "https://github.com/$OWNER/$REPO/releases/download/$VERSION/$asset" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$asset"; do
    info "trying $url"
    curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/$BINARY_NAME" 2>/dev/null || continue

    if [ "$NO_VERIFY" = 1 ]; then
      warn "--no-verify: skipping checksum and signature verification"
    else
      if [ -n "$expected" ]; then
        verify_checksum "$TMP/$BINARY_NAME" "$expected" || { rm -f "$TMP/$BINARY_NAME"; continue; }
      else
        warn "no SHA256SUMS entry for $asset; proceeding unverified"
      fi
      verify_sigstore "$TMP/$BINARY_NAME" \
        "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/${asset}.sigstore.json" \
        || { rm -f "$TMP/$BINARY_NAME"; continue; }
    fi

    install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
    ok "installed $BINARY_NAME $VERSION -> $DEST/$BINARY_NAME"
    return 0
  done
  return 1
}

# ---- build from source (bun, build-only — not required to run tapwire) ----
build_from_source() {
  warn "building from source: needs ~200MB for the bun toolchain (build-only, removed after install is not automatic)"
  if ! command -v bun >/dev/null 2>&1; then
    info "bun not found; installing it temporarily to build tapwire"
    curl -fsSL "${PROXY_ARGS[@]}" https://bun.sh/install | bash || { err "failed to install bun"; exit 1; }
    export PATH="$HOME/.bun/bin:$PATH"
  fi
  command -v git >/dev/null 2>&1 || { err "git is required to build tapwire from source"; exit 1; }

  export https_proxy="${HTTPS_PROXY:-${https_proxy:-}}" http_proxy="${HTTP_PROXY:-${http_proxy:-}}"
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || { err "git clone of $OWNER/$REPO failed"; exit 1; }

  ( cd "$src" && bun install && bun run build ) || { err "build from source failed"; exit 1; }

  local bin="" f
  for f in "$src"/dist/"$BINARY_NAME"* "$src"/"$BINARY_NAME"* "$src"/bin/"$BINARY_NAME"*; do
    [ -f "$f" ] && [ -x "$f" ] && { bin="$f"; break; }
  done
  [ -n "$bin" ] || { err "build succeeded but $BINARY_NAME binary was not found in $src"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source -> $DEST/$BINARY_NAME"
}

# ---- offline mode ----
install_from_offline() {
  [ -f "$OFFLINE_FILE" ] || { err "--offline file not found: $OFFLINE_FILE"; exit 1; }
  info "installing from local file (no network calls): $OFFLINE_FILE"
  local src="$OFFLINE_FILE"
  case "$OFFLINE_FILE" in
    *.tar.gz|*.tgz)
      tar -xzf "$OFFLINE_FILE" -C "$TMP"
      src=""
      local f
      for f in "$TMP/$BINARY_NAME" "$TMP"/*/"$BINARY_NAME" "$TMP"/"$BINARY_NAME"*; do
        [ -f "$f" ] && { src="$f"; break; }
      done
      ;;
  esac
  [ -n "$src" ] && [ -f "$src" ] || { err "could not locate $BINARY_NAME binary in $OFFLINE_FILE"; exit 1; }
  if [ "$NO_VERIFY" != 1 ]; then
    warn "offline mode: no SHA256SUMS available to verify against; pass --no-verify to silence this"
  fi
  mkdir -p "$DEST"
  install -m 0755 "$src" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME -> $DEST/$BINARY_NAME"
}

# ---- completions ----
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [ -x "$bin" ] || return 0
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || { warn "could not create completion dirs; skipping"; return 0; }

  if "$bin" completions bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions -> $bash_dir/$BINARY_NAME"
  else
    rm -f "$bash_dir/$BINARY_NAME"
  fi
  if "$bin" completions zsh >"$zsh_dir/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions -> $zsh_dir/_$BINARY_NAME"
  else
    rm -f "$zsh_dir/_$BINARY_NAME"
  fi
  if "$bin" completions fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions -> $fish_dir/$BINARY_NAME.fish"
  else
    rm -f "$fish_dir/$BINARY_NAME.fish"
  fi
}

# ---- PATH check ----
PATH_OK=1
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) PATH_OK=1 ;;
    *)
      PATH_OK=0
      warn "$DEST is not on your PATH"
      if [ "$EASY_MODE" = 1 ]; then
        local rc
        case "${SHELL:-}" in
          */zsh) rc="$HOME/.zshrc" ;;
          */bash) rc="$HOME/.bashrc" ;;
          */fish) rc="$HOME/.config/fish/config.fish" ;;
          *) rc="$HOME/.profile" ;;
        esac
        printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
        ok "added $DEST to PATH in $rc (restart your shell or: source $rc)"
        PATH_OK=1
      else
        info "add to your shell rc: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
      fi
      ;;
  esac
}

# ---- uninstall ----
uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME"
}

# ---- summary ----
print_summary() {
  local ver=""
  if command -v timeout >/dev/null 2>&1; then
    ver=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | head -1)
  else
    ver=$("$DEST/$BINARY_NAME" --version 2>/dev/null | head -1)
  fi
  local path_line="PATH:    ok"
  [ "$PATH_OK" = 1 ] || path_line="PATH:    not on PATH — see warning above"
  draw_box 42 \
    "tapwire installed" \
    "binary:  $DEST/$BINARY_NAME" \
    "version: ${ver:-unknown}" \
    "$path_line" \
    "" \
    "uninstall: curl -fsSL https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh | bash -s -- --uninstall"
}

# ---- main ----
TMP=""
cleanup() { [ -n "$TMP" ] && rm -rf "$TMP"; }
trap cleanup EXIT
TMP=$(mktemp -d "${TMPDIR:-/tmp}/tapwire-install.XXXXXX")

if [ "$DO_UNINSTALL" = 1 ]; then
  uninstall
  exit 0
fi

if [ -n "$OFFLINE_FILE" ]; then
  install_from_offline
else
  detect_platform
  resolve_version
  preflight
  acquire_lock "$LOCKFILE" 300
  mkdir -p "$DEST"

  if [ "$ALREADY_CURRENT" = 1 ]; then
    info "$BINARY_NAME $VERSION already installed; skipping download (re-checking completions and PATH)"
  elif [ "$FROM_SOURCE" = 1 ]; then
    build_from_source
  else
    download_and_install || { warn "all prebuilt download tiers failed"; build_from_source; }
  fi
fi

install_completions
check_path
print_summary