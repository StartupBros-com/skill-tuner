#!/usr/bin/env bash
#
# octoparse installer
#
#   curl -fsSL "https://get.octoparse.dev/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION        Install a specific version (default: resolved automatically)
#   --dest DIR                Install directory (default: $HOME/.local/bin)
#   --force                   Reinstall even if the version is already present
#   --quiet                   Errors only
#   --no-color                 Disable ANSI color output
#   --no-gum                    Disable gum styling even if gum is present
#   --no-verify                 Skip SHA256/Sigstore verification (not recommended)
#   --offline TARBALL          Install from a local tarball, no network calls at all
#   --build-from-source        Allow installing a Rust toolchain and building from source
#   --easy-mode                 Append the install dir to PATH via your shell rc file
#   --uninstall                 Remove the octoparse binary, completions, and agent hooks
#   -h, --help                    Show this help and exit
#
# Environment variables (all optional):
#   VERSION                    Same as --version
#   DEST                       Same as --dest
#   HTTPS_PROXY / HTTP_PROXY / NO_PROXY   Standard proxy vars, honored on every network call
#   NO_COLOR                   Same as --no-color
#   ALLOW_BUILD_FROM_SOURCE=1  Same as --build-from-source (for unattended/CI use)
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

OWNER="acme"
REPO="octoparse"
BINARY_NAME="octoparse"
COSIGN_ID_RE='https://github\.com/acme/octoparse/\.github/workflows/release\.yml@.*'
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
FALLBACK_VERSION="0.1.0"

VERSION="${VERSION:-}"
DEST="${DEST:-$HOME/.local/bin}"
FORCE=0
QUIET="${QUIET:-0}"
NO_COLOR="${NO_COLOR:-}"
NO_GUM="${NO_GUM:-0}"
NO_VERIFY=0
OFFLINE_TARBALL=""
BUILD_FROM_SOURCE_OK=0
[[ "${ALLOW_BUILD_FROM_SOURCE:-0}" == 1 ]] && BUILD_FROM_SOURCE_OK=1
EASY_MODE=0
DO_UNINSTALL=0
FROM_SOURCE=0

# ---------------------------------------------------------------- output ---
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && NO_GUM=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "${QUIET:-0}" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM:-0}" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=60
  printf '\n┌─ %s %s┐\n' "$title" "$(printf '─%.0s' $(seq 1 $((width - ${#title} - 4))))"
  for l in "${lines[@]}"; do printf '│ %s\n' "$l"; done
  printf '└%s┘\n\n' "$(printf '─%.0s' $(seq 1 $width))"
}

# ------------------------------------------------------------------ help ---
usage() {
  sed -n '2,29p' "$0" | sed 's/^# \{0,1\}//'
}

# ------------------------------------------------------------------ args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --build-from-source) BUILD_FROM_SOURCE_OK=1; shift ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) err "unknown flag: $1"; usage; exit 1 ;;
  esac
done

# --------------------------------------------------------------- cleanup ---
TMP=""
cleanup() {
  [[ -n "$TMP" && -d "$TMP" ]] && rm -rf "$TMP"
  [[ -n "${LOCK_DIR:-}" && -d "${LOCK_DIR:-}" ]] && rm -rf "$LOCK_DIR"
}
trap cleanup EXIT
TMP="$(mktemp -d "${TMPDIR:-/tmp}/octoparse-install.XXXXXX")"

# -------------------------------------------------------------- platform ---
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *)
      warn "no prebuilt binary for ${OS}/${ARCH}"
      FROM_SOURCE=1
      ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions and PATH setup may need extra manual config"
  fi
}

# ----------------------------------------------------------------- proxy ---
PROXY_ARGS=()
[[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ------------------------------------------------------------- resolve v ---
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"
}

# ------------------------------------------------------------- preflight ---
get_installed_version() {
  [[ -x "$DEST/$BINARY_NAME" ]] || return 1
  timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}'
}

preflight() {
  local parent
  parent=$(dirname "$DEST")
  mkdir -p "$DEST" 2>/dev/null || true
  [[ -w "$DEST" ]] || { err "no write permission for $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$parent" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    err "less than 50MB free at $DEST — aborting"
    exit 1
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      err "cannot reach github.com — check network/proxy, or use --offline TARBALL"
      exit 1
    fi
  fi

  local installed
  installed=$(get_installed_version || true)
  if [[ -n "$installed" && "$installed" == "$VERSION" && "$FORCE" != 1 ]]; then
    ok "octoparse $VERSION already installed at $DEST/$BINARY_NAME"
    ALREADY_INSTALLED=1
  fi
}

# ------------------------------------------------------------------ lock ---
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
  fi
  LOCK_DIR="${lf}.d"
  local start; start=$(date +%s)
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    local opid; opid=$(cat "$LOCK_DIR/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$LOCK_DIR"; continue
    fi
    (( $(date +%s) - start >= w )) && { err "timed out waiting for install lock"; return 1; }
    sleep 2
  done
  echo $$ > "$LOCK_DIR/pid"
}

# -------------------------------------------------------------- checksum ---
verify_checksum() {  # $1=file $2=expected
  local a
  if [[ -z "$2" ]]; then warn "no checksum available; skipping"; return 0; fi
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0
  fi
  if [[ "$a" == "$2" ]]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $a)"; return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign absent; skipping signature check"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle found; skipping"; return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null; then
    ok "signature verified"
  else
    err "Sigstore verification FAILED"; return 1
  fi
}

# --------------------------------------------------------------- extract ---
extract_and_install() {  # $1=archive
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$1" -C "$TMP" ;;
    *.zip) unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------- build from source ---
# Building from source means installing a Rust toolchain if one isn't already
# present — a big, surprising thing to do to someone's machine. We only do it
# with explicit consent: an interactive prompt when a human is watching, or a
# flag/env var the caller set on purpose when unattended.
build_from_source() {
  if [[ "$BUILD_FROM_SOURCE_OK" != 1 ]]; then
    if [[ -t 0 && -t 1 ]]; then
      warn "No prebuilt binary for ${OS:-this platform}/${ARCH:-}."
      warn "Building from source will install a Rust toolchain (via rustup) if one isn't already present."
      read -r -p "Proceed with installing a Rust toolchain and building from source? [y/N] " reply
      case "$reply" in
        y|Y|yes|YES) BUILD_FROM_SOURCE_OK=1 ;;
        *) err "aborted — declined to install a Rust toolchain"; exit 1 ;;
      esac
    else
      err "No prebuilt binary for ${OS:-this platform}/${ARCH:-}, and building from source would install a Rust toolchain unattended."
      err "Refusing to do that without explicit consent."
      err "Re-run with --build-from-source, or set ALLOW_BUILD_FROM_SOURCE=1, to allow it."
      exit 1
    fi
  fi

  if ! command -v cargo >/dev/null 2>&1; then
    info "installing Rust toolchain via rustup (minimal profile)..."
    curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --profile minimal --no-modify-path
    # shellcheck disable=SC1091
    source "$HOME/.cargo/env"
  fi

  info "cloning $OWNER/$REPO..."
  local clone_args=(--depth 1)
  [[ -n "$VERSION" ]] && clone_args+=(--branch "v$VERSION")
  git clone "${clone_args[@]}" "https://github.com/$OWNER/$REPO.git" "$TMP/src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$TMP/src"

  info "building (cargo build --release)..."
  ( cd "$TMP/src" && cargo build --release )
  local bin="$TMP/src/target/release/$BINARY_NAME"
  [[ -x "$bin" ]] || { err "build failed: $bin not found"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# ------------------------------------------------------------- download ---
download_and_install() {
  if [[ "$FROM_SOURCE" == 1 ]]; then
    build_from_source
    return
  fi

  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url artifact sha bundle_url
  for url in "${urls[@]}"; do
    artifact="$TMP/artifact.tar.gz"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$artifact" 2>/dev/null; then
      if [[ "$NO_VERIFY" != 1 ]]; then
        sha=$(curl -fsSL "${PROXY_ARGS[@]}" "$url.sha256" 2>/dev/null | awk '{print $1}')
        verify_checksum "$artifact" "$sha" || { rm -f "$artifact"; continue; }
        bundle_url="$url.sigstore.json"
        verify_sigstore "$artifact" "$bundle_url" || { rm -f "$artifact"; continue; }
      else
        warn "skipping verification (--no-verify)"
      fi
      extract_and_install "$artifact" && return 0
    fi
  done

  warn "no prebuilt binary could be downloaded"
  build_from_source
}

# ---------------------------------------------------------- completions ---
install_completions() {
  local xdg_data="${XDG_DATA_HOME:-$HOME/.local/share}"
  command -v "$BINARY_NAME" >/dev/null 2>&1 || return 0
  local bash_dir="$xdg_data/bash-completion/completions"
  local zsh_dir="$xdg_data/zsh/site-functions"
  local fish_dir="$xdg_data/fish/vendor_completions.d"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null \
    && ok "bash completions → $bash_dir/$BINARY_NAME" || true
  "$DEST/$BINARY_NAME" completions zsh > "$zsh_dir/_$BINARY_NAME" 2>/dev/null \
    && ok "zsh completions → $zsh_dir/_$BINARY_NAME" || true
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null \
    && ok "fish completions → $fish_dir/$BINARY_NAME.fish" || true
}

# ---------------------------------------------------------------- PATH -----
path_check() {
  case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
      warn "$DEST is not on your PATH"
      if [[ "$EASY_MODE" == 1 ]]; then
        local rc="$HOME/.bashrc"
        [[ -n "${ZSH_VERSION:-}" ]] && rc="$HOME/.zshrc"
        echo "export PATH=\"$DEST:\$PATH\"" >> "$rc"
        ok "appended PATH export to $rc (restart your shell)"
      else
        info "add this to your shell rc, or re-run with --easy-mode:"
        info "  export PATH=\"$DEST:\$PATH\""
      fi
      ;;
  esac
}

# ------------------------------------------------------------ agent hooks --
merge_json_hook() {  # $1=config_file $2=hook_json_snippet_file
  local cfg="$1" snippet="$2"
  if command -v jq >/dev/null 2>&1; then
    jq -s '.[0] * .[1]' "$cfg" "$snippet" > "$cfg.tmp" && mv "$cfg.tmp" "$cfg"
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$cfg" "$snippet" <<'PY'
import json, sys
cfg_path, snippet_path = sys.argv[1], sys.argv[2]
with open(cfg_path) as f: cfg = json.load(f)
with open(snippet_path) as f: snippet = json.load(f)
def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            merge(a[k], v)
        else:
            a[k] = v
merge(cfg, snippet)
with open(cfg_path, "w") as f: json.dump(cfg, f, indent=2)
PY
  else
    warn "neither jq nor python3 available; skipping hook config for $cfg"
    return 1
  fi
}

configure_agent_hooks() {
  local agents=(
    "Claude Code:$HOME/.claude/settings.json"
    "Codex:$HOME/.codex/config.json"
    "Gemini:$HOME/.gemini/settings.json"
    "Cursor:$HOME/.cursor/mcp.json"
  )
  local entry name cfg dir
  for entry in "${agents[@]}"; do
    name="${entry%%:*}"; cfg="${entry#*:}"; dir=$(dirname "$cfg")
    [[ -d "$dir" ]] || continue
    [[ -f "$cfg" ]] || echo '{}' > "$cfg"
    if grep -q '"octoparse"' "$cfg" 2>/dev/null; then
      info "$name already configured for octoparse; leaving as-is"
      continue
    fi
    cp "$cfg" "$cfg.bak.$(date +%s)"
    cat > "$TMP/hook.json" <<EOF
{"hooks":{"octoparse":{"command":"$DEST/$BINARY_NAME","args":["hook"]}}}
EOF
    if merge_json_hook "$cfg" "$TMP/hook.json"; then
      ok "configured $name hook ($cfg)"
    else
      cp "$cfg.bak."* "$cfg" 2>/dev/null || true
    fi
  done
}

# ------------------------------------------------------------ uninstall ---
print_uninstall_instructions() {
  draw_box "uninstall octoparse" \
    "rm -f \"$DEST/$BINARY_NAME\"" \
    "rm -f \"${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME\"" \
    "rm -f \"${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME\"" \
    "rm -f \"${XDG_DATA_HOME:-$HOME/.local/share}/fish/vendor_completions.d/$BINARY_NAME.fish\"" \
    "remove the \"octoparse\" hook entry from any agent config listed above" \
    "or re-run this script with --uninstall to do all of the above automatically"
}

do_uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/fish/vendor_completions.d/$BINARY_NAME.fish"
  local agents=(
    "$HOME/.claude/settings.json"
    "$HOME/.codex/config.json"
    "$HOME/.gemini/settings.json"
    "$HOME/.cursor/mcp.json"
  )
  local cfg
  for cfg in "${agents[@]}"; do
    [[ -f "$cfg" ]] || continue
    if grep -q '"octoparse"' "$cfg" 2>/dev/null; then
      cp "$cfg" "$cfg.bak.$(date +%s)"
      if command -v jq >/dev/null 2>&1; then
        jq 'del(.hooks.octoparse)' "$cfg" > "$cfg.tmp" && mv "$cfg.tmp" "$cfg"
      elif command -v python3 >/dev/null 2>&1; then
        python3 - "$cfg" <<'PY'
import json, sys
p = sys.argv[1]
with open(p) as f: cfg = json.load(f)
cfg.get("hooks", {}).pop("octoparse", None)
with open(p, "w") as f: json.dump(cfg, f, indent=2)
PY
      fi
      ok "removed octoparse hook from $cfg"
    fi
  done
  ok "octoparse uninstalled"
  exit 0
}

# -------------------------------------------------------------------- main --
main() {
  [[ "$DO_UNINSTALL" == 1 ]] && do_uninstall

  detect_platform

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
    preflight
    acquire_lock "$TMP/../octoparse-install.lock" || { err "could not acquire install lock"; exit 1; }
    if [[ "$NO_VERIFY" != 1 && -f "$OFFLINE_TARBALL.sha256" ]]; then
      verify_checksum "$OFFLINE_TARBALL" "$(awk '{print $1}' "$OFFLINE_TARBALL.sha256")" || exit 1
    fi
    extract_and_install "$OFFLINE_TARBALL"
  else
    resolve_version
    preflight
    if [[ "${ALREADY_INSTALLED:-0}" != 1 ]]; then
      acquire_lock "${DEST}/.octoparse-install.lock" || { err "could not acquire install lock"; exit 1; }
      download_and_install
    fi
  fi

  install_completions
  path_check
  configure_agent_hooks

  draw_box "octoparse install summary" \
    "version:   ${VERSION:-source build}" \
    "binary:    $DEST/$BINARY_NAME" \
    "backups:   any *.bak.<timestamp> files next to modified agent configs" \
    "status:    $( [[ "${ALREADY_INSTALLED:-0}" == 1 ]] && echo 'already up to date' || echo 'installed' )"

  print_uninstall_instructions
}

main "$@"