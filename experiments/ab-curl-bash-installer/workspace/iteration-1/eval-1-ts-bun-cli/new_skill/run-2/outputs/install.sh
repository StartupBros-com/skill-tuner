#!/usr/bin/env bash
#
# tapwire installer — https://github.com/hovlabs/tapwire
#
# Usage:
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/tapwire/main/install.sh?$(date +%s)" | bash
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/tapwire/main/install.sh?$(date +%s)" | bash -s -- --version 1.2.3
#
# Flags:
#   --version <ver>    Install a specific version (default: latest release)
#   --prefix <dir>     Install directory (default: $HOME/.local/bin, or $TAPWIRE_INSTALL_DIR)
#   --force            Reinstall even if the target version is already present
#   --quiet            Errors only
#   --no-color         Disable ANSI color output
#   --no-gum           Disable gum styling even when gum is installed
#   --no-verify        Skip SHA256/Sigstore verification (not recommended)
#   --offline <path>   Install from a local binary file, no network calls
#   --sha256 <hash>    Expected SHA256 for --offline installs
#   --easy-mode        Append the install dir to PATH via your shell rc file
#   --uninstall        Remove tapwire (and its completions) and exit
#   -h, --help         Show this help and exit
#
# Env:
#   TAPWIRE_INSTALL_DIR      same as --prefix
#   TAPWIRE_VERSION          same as --version
#   HTTPS_PROXY/HTTP_PROXY   proxied network access (NO_PROXY honored natively by curl)
#   NO_COLOR                 disable color (same as --no-color)

set -euo pipefail
umask 022

# --------------------------------------------------------------- constants -
OWNER="hovlabs"
REPO="tapwire"
BINARY_NAME="tapwire"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# ----------------------------------------------------------------- defaults
VERSION="${TAPWIRE_VERSION:-}"
DEST="${TAPWIRE_INSTALL_DIR:-$HOME/.local/bin}"
QUIET=0
FORCE=0
NO_COLOR="${NO_COLOR:-}"
NO_GUM=0
NO_VERIFY=0
OFFLINE_PATH=""
OFFLINE_SHA256=""
EASY_MODE=0
DO_UNINSTALL=0
FROM_SOURCE=0
CURRENT_VERSION=""

PROXY_ARGS=()
if [ -n "${HTTPS_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [ -n "${HTTP_PROXY:-}" ]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi

# ------------------------------------------------------------------ output -
HAS_GUM=0
_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" != 1 ]; then
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
err()  { _log err  196 '✗'  "$@" 1>&2; }
die()  { err "$@"; exit 1; }

# ----------------------------------------------------------------- cleanup -
TMP=""
LOCK_KIND=""
LOCK_DIR=""

release_lock() {
  if [ "$LOCK_KIND" = mkdir ] && [ -n "$LOCK_DIR" ]; then
    rm -rf "$LOCK_DIR"
  fi
}

cleanup() {
  local ec=$?
  [ -n "$TMP" ] && [ -d "$TMP" ] && rm -rf "$TMP"
  release_lock
  exit "$ec"
}

acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || return 1
    flock -w "$w" 9 || return 1
    LOCK_KIND=flock
    return 0
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null) || true
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
  LOCK_KIND=mkdir
  LOCK_DIR="$d"
  return 0
}

# ------------------------------------------------------------------- usage -
usage() {
  cat <<'EOF'
tapwire installer

Usage:
  curl -fsSL "https://raw.githubusercontent.com/hovlabs/tapwire/main/install.sh?$(date +%s)" | bash
  curl -fsSL "https://raw.githubusercontent.com/hovlabs/tapwire/main/install.sh?$(date +%s)" | bash -s -- [flags]

Flags:
  --version <ver>    Install a specific version (default: latest release)
  --prefix <dir>     Install directory (default: $HOME/.local/bin, or $TAPWIRE_INSTALL_DIR)
  --force            Reinstall even if the target version is already present
  --quiet            Errors only
  --no-color         Disable ANSI color output
  --no-gum           Disable gum styling even when gum is installed
  --no-verify        Skip SHA256/Sigstore verification (not recommended)
  --offline <path>   Install from a local binary file, no network calls
  --sha256 <hash>    Expected SHA256 for --offline installs
  --easy-mode        Append the install dir to PATH via your shell rc file
  --uninstall        Remove tapwire (and its completions) and exit
  -h, --help         Show this help and exit

Env:
  TAPWIRE_INSTALL_DIR      same as --prefix
  TAPWIRE_VERSION          same as --version
  HTTPS_PROXY/HTTP_PROXY   proxied network access (NO_PROXY honored natively by curl)
  NO_COLOR                 disable color (same as --no-color)
EOF
}

# -------------------------------------------------------------- platform ---
detect_platform() {
  local os arch
  os=$(uname -s | tr 'A-Z' 'a-z')
  arch=$(uname -m)
  case "$arch" in x86_64|amd64) arch=x64 ;; arm64|aarch64) arch=arm64 ;; esac
  ARTIFACT_OS=""
  ARTIFACT_ARCH=""
  case "${os}-${arch}" in
    linux-x64)    ARTIFACT_OS=linux  ; ARTIFACT_ARCH=x64 ;;
    linux-arm64)  ARTIFACT_OS=linux  ; ARTIFACT_ARCH=arm64 ;;
    darwin-arm64) ARTIFACT_OS=darwin ; ARTIFACT_ARCH=arm64 ;;
    *)
      warn "no prebuilt binary for ${os}/${arch}; will build from source"
      FROM_SOURCE=1
      ;;
  esac
  OS="$os"
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — PATH and filesystem-permission quirks are possible; continuing"
  fi
  ARTIFACT_NAME="${BINARY_NAME}-${ARTIFACT_OS:-unknown}-${ARTIFACT_ARCH:-unknown}"
}

# ------------------------------------------------------------------- curl --
curl_fetch() { curl -fsSL --connect-timeout 10 "${PROXY_ARGS[@]}" "$@"; }

# --------------------------------------------------------------- version ---
resolve_version() {
  [ -n "$VERSION" ] && return 0
  # No manifest tier here: this script runs standalone via curl|bash, not from
  # inside a tapwire checkout, so a stray package.json in $PWD could resolve
  # the wrong version.
  VERSION=$(curl_fetch "https://api.github.com/repos/${OWNER}/${REPO}/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  if [ -n "$VERSION" ]; then
    info "resolved latest version via GitHub API: $VERSION"
    return 0
  fi
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/${OWNER}/${REPO}/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||') || true
  if [ -n "$VERSION" ]; then
    info "resolved latest version via redirect: $VERSION"
    return 0
  fi
  VERSION="$FALLBACK_VERSION"
  warn "could not resolve latest version from GitHub; falling back to ${VERSION} (pass --version to override)"
}

# -------------------------------------------------------------- verify -----
verify_checksum() {  # $1=file $2=expected
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
  err "checksum mismatch (want ${expected}, got ${actual})"
  return 1
}

verify_sigstore() {  # $1=file $2=bundle_url
  local file="$1" bundle_url="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  if ! curl_fetch "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle at ${bundle_url}; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
       --certificate-identity-regexp "$COSIGN_ID_RE" \
       --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED"
  return 1
}

# ------------------------------------------------------------- download ----
download_and_install() {
  local base url expected
  BASE_URLS=(
    "https://github.com/${OWNER}/${REPO}/releases/download/v${VERSION}"
    "https://github.com/${OWNER}/${REPO}/releases/download/${VERSION}"
    "https://github.com/${OWNER}/${REPO}/releases/latest/download"
  )
  for base in "${BASE_URLS[@]}"; do
    url="${base}/${ARTIFACT_NAME}"
    info "trying ${url}"
    if ! curl_fetch "$url" -o "$TMP/${ARTIFACT_NAME}" 2>/dev/null; then
      continue
    fi

    if [ "$NO_VERIFY" = 1 ]; then
      warn "--no-verify set; skipping checksum verification"
    else
      if ! curl_fetch "${base}/SHA256SUMS" -o "$TMP/SHA256SUMS" 2>/dev/null; then
        warn "no SHA256SUMS at ${base}; trying next source"
        continue
      fi
      expected=$(awk -v n="$ARTIFACT_NAME" '$2==n{print $1}' "$TMP/SHA256SUMS")
      if [ -z "$expected" ]; then
        warn "${ARTIFACT_NAME} not listed in SHA256SUMS at ${base}; trying next source"
        continue
      fi
      if ! verify_checksum "$TMP/${ARTIFACT_NAME}" "$expected"; then
        die "checksum verification FAILED for ${ARTIFACT_NAME} from ${base} — possible corruption or tampering, aborting"
      fi
    fi

    if ! verify_sigstore "$TMP/${ARTIFACT_NAME}" "${base}/${ARTIFACT_NAME}.sigstore.json"; then
      die "Sigstore signature verification FAILED for ${ARTIFACT_NAME} — aborting"
    fi

    install -m 0755 "$TMP/${ARTIFACT_NAME}" "$DEST/${BINARY_NAME}"
    ok "installed ${BINARY_NAME} ${VERSION} → ${DEST}/${BINARY_NAME}"
    return 0
  done
  return 1
}

# --------------------------------------------------------- build-from-source
build_from_source() {
  info "building from source (requires git + bun; neither is needed after this)"
  local build_dir="$TMP/src"
  command -v git >/dev/null 2>&1 || die "git is required to build from source but was not found"

  if ! command -v bun >/dev/null 2>&1; then
    info "bun not found; installing bun temporarily to build tapwire"
    curl -fsSL "${PROXY_ARGS[@]}" https://bun.sh/install | bash || die "failed to install bun"
    export PATH="$HOME/.bun/bin:$PATH"
    command -v bun >/dev/null 2>&1 || die "bun installation did not put 'bun' on PATH"
  fi

  git clone --depth 1 --branch "v${VERSION}" "https://github.com/${OWNER}/${REPO}.git" "$build_dir" 2>/dev/null \
    || git clone --depth 1 "https://github.com/${OWNER}/${REPO}.git" "$build_dir" \
    || die "git clone of ${OWNER}/${REPO} failed"

  (
    cd "$build_dir"
    bun install --frozen-lockfile
    bun run build 2>/dev/null || bun run compile 2>/dev/null || bun build . --compile --outfile "$BINARY_NAME"
  ) || die "build from source failed"

  local built=""
  built=$(find "$build_dir" -maxdepth 3 -type f -name "$BINARY_NAME" -perm -u+x 2>/dev/null | head -1)
  [ -n "$built" ] && [ -f "$built" ] || die "build succeeded but the ${BINARY_NAME} binary was not found in ${build_dir}"

  install -m 0755 "$built" "$DEST/$BINARY_NAME"
  ok "built and installed ${BINARY_NAME} from source → ${DEST}/${BINARY_NAME}"
}

# -------------------------------------------------------------- preflight --
preflight() {
  local need_kb=204800 avail_kb parent
  parent="$DEST"
  [ -d "$parent" ] || parent=$(dirname "$DEST")
  avail_kb=$(df -Pk "$parent" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt "$need_kb" ] 2>/dev/null; then
    die "not enough disk space at ${parent} (have ${avail_kb}KB, need ~${need_kb}KB)"
  fi

  mkdir -p "$DEST" 2>/dev/null || die "cannot create install dir: ${DEST}"
  [ -w "$DEST" ] || die "install dir not writable: ${DEST} (try --prefix, or fix permissions)"

  if [ -x "$DEST/$BINARY_NAME" ]; then
    CURRENT_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) || true
    [ -n "$CURRENT_VERSION" ] && info "found existing install: ${BINARY_NAME} ${CURRENT_VERSION}"
  fi

  curl -fsSL -o /dev/null --connect-timeout 5 "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null \
    || warn "network reachability check to github.com failed; downloads may fail"
}

# ------------------------------------------------------------ completions --
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  if ! timeout 1 "$bin" completions bash >/dev/null 2>&1; then
    warn "this build of ${BINARY_NAME} does not support shell completions; skipping"
    return 0
  fi
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$bin" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$bin" completions zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$bin" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "installed shell completions (bash/zsh/fish)"
}

# ------------------------------------------------------------------- path --
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [ "$EASY_MODE" = 1 ]; then
    local rc marker="# added by tapwire installer"
    case "${SHELL:-}" in
      */zsh)  rc="$HOME/.zshrc" ;;
      */fish) rc="$HOME/.config/fish/config.fish" ;;
      *)      rc="$HOME/.bashrc" ;;
    esac
    if [ -f "$rc" ] && grep -qF "$marker" "$rc" 2>/dev/null; then
      info "PATH already configured in ${rc}"
    else
      mkdir -p "$(dirname "$rc")"
      {
        echo ""
        echo "$marker"
        if [ "$rc" = "$HOME/.config/fish/config.fish" ]; then
          echo "set -gx PATH \"$DEST\" \$PATH"
        else
          echo "export PATH=\"$DEST:\$PATH\""
        fi
      } >> "$rc"
      ok "added ${DEST} to PATH in ${rc} (restart your shell or run: source ${rc})"
    fi
  else
    warn "${DEST} is not on PATH; re-run with --easy-mode or add it manually:"
    warn "  export PATH=\"${DEST}:\$PATH\""
  fi
}

# --------------------------------------------------------------- box/print -
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
  local mode="$1" installed_version
  installed_version=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | head -1) || true
  [ "$QUIET" = 1 ] && return 0
  draw_box 42 \
    "tapwire installed" \
    "" \
    "binary:   ${DEST}/${BINARY_NAME}" \
    "version:  ${installed_version:-$VERSION}" \
    "mode:     ${mode}" \
    "verified: $([ "$NO_VERIFY" = 1 ] && echo 'skipped (--no-verify)' || echo 'SHA256 + Sigstore (if available)')"
}

print_uninstall_hint() {
  [ "$QUIET" = 1 ] && return 0
  info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/${OWNER}/${REPO}/main/install.sh\" | bash -s -- --uninstall"
  info "  (or delete ${DEST}/${BINARY_NAME} and its completion files directly)"
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  if declare -F uninstall_service >/dev/null; then uninstall_service; fi
  ok "uninstalled ${BINARY_NAME}. PATH/rc entries left in place — remove manually if desired."
}

# -------------------------------------------------------------------- main -
main() {
  detect_platform
  resolve_version

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/tapwire-install.XXXXXX")
  trap cleanup EXIT

  if [ -n "$OFFLINE_PATH" ]; then
    [ -f "$OFFLINE_PATH" ] || die "--offline path not found: $OFFLINE_PATH"
    mkdir -p "$DEST"
    [ -w "$DEST" ] || die "install dir not writable: $DEST"
    if [ "$NO_VERIFY" != 1 ] && [ -n "$OFFLINE_SHA256" ]; then
      verify_checksum "$OFFLINE_PATH" "$OFFLINE_SHA256" || die "checksum verification failed for offline artifact"
    elif [ "$NO_VERIFY" != 1 ]; then
      warn "no --sha256 given for --offline install; skipping checksum verification"
    fi
    install -m 0755 "$OFFLINE_PATH" "$DEST/$BINARY_NAME"
    ok "installed ${BINARY_NAME} from local file → ${DEST}/${BINARY_NAME}"
    install_completions
    check_path
    print_summary "offline"
    print_uninstall_hint
    return 0
  fi

  preflight

  if [ "$FORCE" != 1 ] && [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" = "$VERSION" ]; then
    info "${BINARY_NAME} ${VERSION} already installed; skipping download (use --force to reinstall)"
  else
    local lockfile="${XDG_CACHE_HOME:-$HOME/.cache}/tapwire/install.lock"
    acquire_lock "$lockfile" 2400 || die "could not acquire install lock (another install running?)"

    if [ "$FROM_SOURCE" = 1 ]; then
      build_from_source
    else
      if ! download_and_install; then
        warn "no prebuilt binary found for ${ARTIFACT_NAME}; falling back to build from source"
        build_from_source
      fi
    fi
  fi

  install_completions
  check_path
  print_summary "network"
  print_uninstall_hint
}

# --------------------------------------------------------------- flag parse
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --version=*) VERSION="${1#*=}"; shift ;;
    --prefix) DEST="$2"; shift 2 ;;
    --prefix=*) DEST="${1#*=}"; shift ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_PATH="$2"; shift 2 ;;
    --offline=*) OFFLINE_PATH="${1#*=}"; shift ;;
    --sha256) OFFLINE_SHA256="$2"; shift 2 ;;
    --sha256=*) OFFLINE_SHA256="${1#*=}"; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done

[ -n "$NO_COLOR" ] && NO_GUM=1
HAS_GUM=0
if [ "$NO_GUM" != 1 ] && command -v gum >/dev/null 2>&1 && [ -t 1 ]; then
  HAS_GUM=1
fi

if [ "$DO_UNINSTALL" = 1 ]; then
  uninstall
  exit 0
fi

main