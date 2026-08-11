#!/usr/bin/env bash
#
# warpline installer
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/warpline/main/install.sh?$(date +%s)" | bash -s -- [flags]
#
# Flags (see --help for the full list):
#   --version VERSION   --prefix DIR       --quiet            --force
#   --no-color           --no-gum          --build-from-source --no-verify
#   --easy-mode           --offline TARBALL --verify           --uninstall
#
# Env: HTTPS_PROXY / HTTP_PROXY, NO_COLOR, WARPLINE_VERSION, BUILD_FROM_SOURCE=1
#
# warpline release artifacts are Node.js single-executable bundles — no
# separately-installed Node runtime is required to *run* them. Building from
# source (the last-resort fallback) does require Node.js >= 18 + npm.

set -euo pipefail
umask 022

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="warpline"
BINARY_NAME="warpline"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github\\.com/${OWNER}/${REPO}/\\.github/workflows/release\\.ya?ml@refs/tags/v.*$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

DEST="${WARPLINE_INSTALL_DIR:-$HOME/.local/bin}"
LOCKFILE="/tmp/${BINARY_NAME}-install-$(id -u).lock"
HOOK_COMMAND=""   # set to "$DEST/$BINARY_NAME hook pre-tool-use" once DEST is final

VERSION=""
QUIET=0
FORCE=0
DISABLE_COLOR=0
NO_GUM=0
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
NO_VERIFY=0
EASY_MODE=0
OFFLINE_TARBALL=""
DO_UNINSTALL=0
DO_SELF_TEST=0
ALREADY_INSTALLED=0
LOCK_DIR=""
LOCK_FD=""
JSON_TOOL=""
PROXY_ARGS=()

# ---------------------------------------------------------------------------
# Safety prelude: temp dir + cleanup trap, defined before anything can fail
# ---------------------------------------------------------------------------
cleanup() {
  local status=$?
  [[ -n "$LOCK_DIR" && -d "$LOCK_DIR" ]] && rm -rf "$LOCK_DIR" 2>/dev/null || true
  [[ -n "${TMP:-}" && -d "$TMP" ]] && rm -rf "$TMP" 2>/dev/null || true
  return "$status"
}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}.XXXXXX")
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Output helpers — gum-if-TTY, ANSI fallback, honor NO_COLOR + non-TTY
# ---------------------------------------------------------------------------
[[ -n "${NO_COLOR:-}" ]] && DISABLE_COLOR=1
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [[ -t 1 ]] && HAS_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [[ "$QUIET" == 1 && "$level" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "$NO_GUM" != 1 ]]; then
    gum style --foreground "$color" "$glyph $*"
  elif [[ "$DISABLE_COLOR" == 1 || ! -t 1 ]]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

run_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "$secs" "$@"
  else "$@"; fi
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

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
warpline installer

  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash -s -- [flags]

Flags:
  --version VERSION     install a specific version (default: latest)
  --prefix DIR          install directory (default: \$HOME/.local/bin)
  --quiet               only print errors
  --force               reinstall even if the same version is already present
  --no-color            disable ANSI colors
  --no-gum              disable gum styling, use plain ANSI instead
  --build-from-source   consent to building from source with Node.js/npm
  --no-verify           skip checksum/signature verification (not recommended)
  --easy-mode           append \$PREFIX to your shell rc if it's missing from PATH
  --offline TARBALL     install from a local tarball, no network calls at all
  --verify              run a self-test (--version) after installing
  --uninstall           remove the binary + completions, then exit
  -h, --help            show this help

Env:
  HTTPS_PROXY / HTTP_PROXY   proxy for all network calls
  NO_COLOR                   disable ANSI colors
  WARPLINE_VERSION            same as --version
  BUILD_FROM_SOURCE=1         same as --build-from-source (for non-interactive use)
  WARPLINE_INSTALL_DIR         same as --prefix
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --prefix) DEST="$2"; shift 2 ;;
      --quiet) QUIET=1; shift ;;
      --force) FORCE=1; shift ;;
      --no-color) DISABLE_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --build-from-source) BUILD_FROM_SOURCE=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
      --verify) DO_SELF_TEST=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done
  VERSION="${VERSION:-${WARPLINE_VERSION:-}}"
}

# ---------------------------------------------------------------------------
# Platform + proxy
# ---------------------------------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64) ARCH=x64 ;;
    arm64|aarch64) ARCH=arm64 ;;
  esac
  case "$OS" in
    linux|darwin) : ;;
    *) warn "no prebuilt artifact naming for OS '$OS'; will fall back to source build" ;;
  esac
  PLATFORM="${OS}-${ARCH}"
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions and PATH setup may need extra config"
  fi
}

setup_proxy() {
  PROXY_ARGS=()
  if [[ -n "${HTTPS_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
  # NO_PROXY is honored by curl natively on every call below.
}

# ---------------------------------------------------------------------------
# Version resolution — 4-tier fallback (flag/env → local manifest → GitHub
# API → hardcoded last-known-good)
# ---------------------------------------------------------------------------
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  if [[ -f package.json ]]; then
    VERSION=$(grep -m1 '"version"' package.json | sed -E 's/.*"([0-9][^"]*)".*/\1/' || true)
  fi
  [[ -n "$VERSION" ]] && return 0
  if [[ -z "$OFFLINE_TARBALL" ]]; then
    VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
      "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
      | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/' || true)
    [[ -n "$VERSION" ]] && return 0
    VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
      "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||' || true)
  fi
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
  local avail_kb
  avail_kb=$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" ]] && (( avail_kb < 51200 )); then
    err "less than 50MB free under \$HOME; aborting"
    exit 1
  fi

  mkdir -p "$DEST" 2>/dev/null || { err "cannot create install dir $DEST"; exit 1; }
  [[ -w "$DEST" ]] || { err "no write permission on $DEST"; exit 1; }
  HOOK_COMMAND="$DEST/$BINARY_NAME hook pre-tool-use"

  if [[ -x "$DEST/$BINARY_NAME" && "$FORCE" != 1 ]]; then
    local cur
    cur=$(run_timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}' || true)
    if [[ -n "$cur" && "$cur" == "$VERSION" ]]; then
      ALREADY_INSTALLED=1
      ok "warpline $VERSION already installed at $DEST/$BINARY_NAME"
    fi
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null \
      || warn "network check to github.com failed; downloads may fail (proxy? airgap? try --offline)"
  fi
}

# ---------------------------------------------------------------------------
# Atomic lock — flock-first, mkdir spinlock fallback (macOS has no flock),
# stale-PID self-heal
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  # brace-scoped so a failed exec doesn't leak a permanent stderr redirect
  # onto the rest of the script.
  if command -v flock >/dev/null 2>&1 && { exec 9>>"$lf"; } 2>/dev/null; then
    LOCK_FD=9
    flock -w "$w" 9
    return $?
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid
    opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"; continue
    fi
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

# ---------------------------------------------------------------------------
# Checksum + Sigstore — missing tool warns and continues; tool present with a
# bad result hard-fails.
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0; fi
  [[ "$a" == "$2" ]] && { ok "SHA256 verified"; return 0; } || { err "checksum mismatch (want $2 got $a)"; return 1; }
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no Sigstore bundle published; skipping"; return 0; }
  cosign verify-blob --bundle "$TMP/sig.json" --certificate-identity-regexp "$COSIGN_ID_RE" \
    --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null && ok "signature verified" \
    || { err "Sigstore verification FAILED"; return 1; }
}

# ---------------------------------------------------------------------------
# Download → verify → extract, 4-tier artifact URL fallback → source build
# ---------------------------------------------------------------------------
extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -type f -name "$BINARY_NAME" 2>/dev/null | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  chmod +x "$bin" 2>/dev/null || true
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

download_and_install() {
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$PLATFORM.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$PLATFORM.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$OS-$ARCH.tar.gz"
  )
  local url
  for url in "${urls[@]}"; do
    info "trying artifact: $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      if [[ "$NO_VERIFY" == 1 ]]; then
        warn "--no-verify set; skipping checksum + signature"
      else
        local sha
        sha=$(curl -fsSL "${PROXY_ARGS[@]}" "$url.sha256" 2>/dev/null | awk '{print $1}' || true)
        if [[ -z "$sha" ]]; then
          warn "no checksum published for this artifact; skipping checksum"
        elif ! verify_checksum "$TMP/artifact.tar.gz" "$sha"; then
          rm -f "$TMP/artifact.tar.gz"; continue
        fi
        verify_sigstore "$TMP/artifact.tar.gz" "$url.sigstore.json" || { rm -f "$TMP/artifact.tar.gz"; continue; }
      fi
      extract_and_install "$TMP/artifact.tar.gz" && return 0
    fi
    rm -f "$TMP/artifact.tar.gz"
  done
  warn "no prebuilt binary available for $PLATFORM; falling back to a source build"
  confirm_build_from_source
  build_from_source
}

confirm_build_from_source() {
  [[ "$BUILD_FROM_SOURCE" == 1 ]] && return 0
  # curl | bash means stdin IS the script; a plain `read` would consume script
  # bytes instead of prompting the user, so we go through /dev/tty explicitly.
  if [[ -r /dev/tty ]]; then
    printf '\033[214m⚠\033[0m No prebuilt binary for %s. Build from source with Node.js/npm? [y/N] ' "$PLATFORM" > /dev/tty
    local reply
    read -r reply < /dev/tty
    if [[ "$reply" =~ ^[Yy]$ ]]; then BUILD_FROM_SOURCE=1; return 0; fi
    err "declined source build; aborting"
    exit 1
  fi
  err "no prebuilt binary and no TTY available; re-run with --build-from-source or BUILD_FROM_SOURCE=1"
  exit 1
}

build_from_source() {
  command -v node >/dev/null 2>&1 || { err "Node.js not found; install Node.js >= 18 first, then re-run with --build-from-source"; exit 1; }
  command -v npm  >/dev/null 2>&1 || { err "npm not found; install Node.js >= 18 (bundles npm) first"; exit 1; }
  command -v git  >/dev/null 2>&1 || { err "git not found; required to build from source"; exit 1; }

  local node_major
  node_major=$(node -e 'console.log(process.versions.node.split(".")[0])' 2>/dev/null || echo 0)
  if (( node_major < 18 )); then
    err "Node.js >= 18 required (found $(node -v 2>/dev/null))"
    exit 1
  fi

  info "cloning $OWNER/$REPO@v$VERSION and building..."
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || { err "git clone failed"; exit 1; }
  ( cd "$src" && npm ci --no-audit --no-fund && npm run build ) \
    || { err "build failed"; exit 1; }

  local bin
  bin=$(find "$src/dist" "$src/bin" -maxdepth 3 -type f -name "$BINARY_NAME*" 2>/dev/null | head -1)
  [[ -n "$bin" ]] || { err "built binary not found under dist/ or bin/"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Completions (XDG paths) + PATH check
# ---------------------------------------------------------------------------
install_completions() {
  local bin="$DEST/$BINARY_NAME"
  [[ -x "$bin" ]] || return 0
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || true

  if run_timeout 1 "$bin" completions bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
  else
    rm -f "$bash_dir/$BINARY_NAME"; warn "bash completions unavailable"
  fi
  if run_timeout 1 "$bin" completions zsh >"$zsh_dir/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  else
    rm -f "$zsh_dir/_$BINARY_NAME"; warn "zsh completions unavailable"
  fi
  if run_timeout 1 "$bin" completions fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions → $fish_dir/$BINARY_NAME.fish"
  else
    rm -f "$fish_dir/$BINARY_NAME.fish"; warn "fish completions unavailable"
  fi
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on your PATH"
  if [[ "$EASY_MODE" == 1 ]]; then
    local rc="$HOME/.bashrc"
    [[ -n "${ZSH_VERSION:-}" ]] && rc="$HOME/.zshrc"
    if ! grep -qF "$DEST" "$rc" 2>/dev/null; then
      printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
      ok "added $DEST to PATH in $rc (restart your shell, or source it)"
    fi
  else
    info "add this to your shell rc: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
  fi
}

# ---------------------------------------------------------------------------
# Agent hook config — Claude Code (~/.claude/settings.json) and Codex CLI
# (~/.codex/config.json). Idempotent by construction: every merge first
# strips any existing hook entry that runs $HOOK_COMMAND, then re-adds
# exactly one — so five runs in a row still leave exactly one entry, and a
# --prefix change updates the command path instead of duplicating it.
# Never edited with sed/awk; jq if present, else python3's json module,
# else skipped with a warning. Always: timestamped backup before writing,
# and the merged output is JSON-validated before it replaces the original —
# on any failure the backup is restored and the original file is untouched.
# ---------------------------------------------------------------------------
detect_json_tool() {
  if command -v jq >/dev/null 2>&1; then JSON_TOOL=jq
  elif command -v python3 >/dev/null 2>&1; then JSON_TOOL=python3
  else JSON_TOOL=""; fi
}

json_is_valid() {
  if [[ "$JSON_TOOL" == jq ]]; then
    jq empty "$1" >/dev/null 2>&1
  else
    python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$1" >/dev/null 2>&1
  fi
}

configure_claude_hook() {
  local file="$HOME/.claude/settings.json"
  mkdir -p "$(dirname "$file")" 2>/dev/null || { err "cannot create $(dirname "$file")"; return 1; }
  [[ -f "$file" ]] || echo '{}' > "$file"

  detect_json_tool
  if [[ -z "$JSON_TOOL" ]]; then
    warn "neither jq nor python3 found; cannot safely edit $file — skipping Claude Code hook"
    return 1
  fi

  if ! json_is_valid "$file"; then
    local corrupt="${file}.corrupt.$(date +%s)"
    cp "$file" "$corrupt"
    warn "$file is not valid JSON; backed up to $corrupt and starting fresh"
    echo '{}' > "$file"
  fi

  local backup="${file}.bak.$(date +%s)"
  cp "$file" "$backup" || { err "backup of $file failed; skipping Claude Code hook"; return 1; }

  local tmp="$TMP/claude-settings.json"
  if [[ "$JSON_TOOL" == jq ]]; then
    jq --arg cmd "$HOOK_COMMAND" '
      .hooks //= {} |
      .hooks.PreToolUse //= [] |
      .hooks.PreToolUse |= [ .[] | select((.hooks // []) | any(.command == $cmd) | not) ] |
      .hooks.PreToolUse += [{"matcher": "*", "hooks": [{"type": "command", "command": $cmd}]}]
    ' "$file" > "$tmp" 2>/dev/null || true
  else
    python3 - "$file" "$HOOK_COMMAND" > "$tmp" <<'PYEOF'
import json, sys
file, cmd = sys.argv[1], sys.argv[2]
with open(file) as f:
    data = json.load(f)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
pre[:] = [g for g in pre if not any(h.get("command") == cmd for h in g.get("hooks", []))]
pre.append({"matcher": "*", "hooks": [{"type": "command", "command": cmd}]})
print(json.dumps(data, indent=2))
PYEOF
  fi

  if [[ -s "$tmp" ]] && json_is_valid "$tmp"; then
    mv "$tmp" "$file"
    ok "configured Claude Code pre-tool-use hook → $file (backup: $backup)"
    return 0
  fi
  err "failed to merge Claude Code hook config; leaving $file untouched (backup: $backup)"
  return 1
}

configure_codex_hook() {
  # Codex CLI's config schema is less standardized than Claude Code's; this
  # targets ~/.codex/config.json with a hooks.pre_tool_use array. Re-verify
  # against current Codex CLI docs before relying on this in production.
  local file="$HOME/.codex/config.json"
  mkdir -p "$(dirname "$file")" 2>/dev/null || { err "cannot create $(dirname "$file")"; return 1; }
  [[ -f "$file" ]] || echo '{}' > "$file"

  detect_json_tool
  if [[ -z "$JSON_TOOL" ]]; then
    warn "neither jq nor python3 found; cannot safely edit $file — skipping Codex CLI hook"
    return 1
  fi

  if ! json_is_valid "$file"; then
    local corrupt="${file}.corrupt.$(date +%s)"
    cp "$file" "$corrupt"
    warn "$file is not valid JSON; backed up to $corrupt and starting fresh"
    echo '{}' > "$file"
  fi

  local backup="${file}.bak.$(date +%s)"
  cp "$file" "$backup" || { err "backup of $file failed; skipping Codex CLI hook"; return 1; }

  local tmp="$TMP/codex-config.json"
  if [[ "$JSON_TOOL" == jq ]]; then
    jq --arg cmd "$HOOK_COMMAND" '
      .hooks //= {} |
      .hooks.pre_tool_use //= [] |
      .hooks.pre_tool_use |= [ .[] | select(.command != $cmd) ] |
      .hooks.pre_tool_use += [{"command": $cmd}]
    ' "$file" > "$tmp" 2>/dev/null || true
  else
    python3 - "$file" "$HOOK_COMMAND" > "$tmp" <<'PYEOF'
import json, sys
file, cmd = sys.argv[1], sys.argv[2]
with open(file) as f:
    data = json.load(f)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("pre_tool_use", [])
pre[:] = [h for h in pre if h.get("command") != cmd]
pre.append({"command": cmd})
print(json.dumps(data, indent=2))
PYEOF
  fi

  if [[ -s "$tmp" ]] && json_is_valid "$tmp"; then
    mv "$tmp" "$file"
    ok "configured Codex CLI pre-tool-use hook → $file (backup: $backup)"
    return 0
  fi
  err "failed to merge Codex CLI hook config; leaving $file untouched (backup: $backup)"
  return 1
}

configure_agent_hooks() {
  local configured=0
  if [[ -d "$HOME/.claude" ]] || command -v claude >/dev/null 2>&1; then
    configure_claude_hook && configured=1
  else
    info "Claude Code not detected; skipping its hook"
  fi
  if [[ -d "$HOME/.codex" ]] || command -v codex >/dev/null 2>&1; then
    configure_codex_hook && configured=1
  else
    info "Codex CLI not detected; skipping its hook"
  fi
  [[ "$configured" == 1 ]] || warn "no supported AI agent detected; no hooks were installed"
}

# ---------------------------------------------------------------------------
# Self-test, uninstall, summary
# ---------------------------------------------------------------------------
self_test() {
  if run_timeout 3 "$DEST/$BINARY_NAME" --version >/dev/null 2>&1; then
    ok "self-test passed: $BINARY_NAME --version runs"
  else
    err "self-test failed: $DEST/$BINARY_NAME --version did not run"
    exit 1
  fi
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME. Agent hooks were left in place — remove them from"
  info "  ~/.claude/settings.json and/or ~/.codex/config.json manually if desired"
  info "  (backups of those files are named *.bak.<timestamp> next to each)."
}

print_summary() {
  [[ "$QUIET" == 1 ]] && return 0
  local v claude_state codex_state
  v=$(run_timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null || echo "$VERSION")
  if [[ -f "$HOME/.claude/settings.json" ]] && grep -qF "$HOOK_COMMAND" "$HOME/.claude/settings.json" 2>/dev/null; then
    claude_state="configured"
  else
    claude_state="skipped"
  fi
  if [[ -f "$HOME/.codex/config.json" ]] && grep -qF "$HOOK_COMMAND" "$HOME/.codex/config.json" 2>/dev/null; then
    codex_state="configured"
  else
    codex_state="skipped"
  fi
  draw_box 42 \
    "\033[1mwarpline installed\033[0m" \
    "" \
    "binary:   $DEST/$BINARY_NAME ($v)" \
    "claude:   $claude_state" \
    "codex:    $codex_state" \
    "backups:  *.bak.<timestamp> next to any edited agent config"
}

print_uninstall_hint() {
  [[ "$QUIET" == 1 ]] && return 0
  info "to uninstall: curl -fsSL https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh | bash -s -- --uninstall"
  info "  (removes $DEST/$BINARY_NAME + shell completions; agent hooks are left in place)"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  parse_args "$@"

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    uninstall
    exit 0
  fi

  detect_platform
  setup_proxy
  resolve_version
  [[ "$QUIET" != 1 ]] && info "installing $BINARY_NAME v$VERSION for $PLATFORM"

  preflight
  acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock"; exit 1; }

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    [[ -f "$OFFLINE_TARBALL" ]] || { err "--offline file not found: $OFFLINE_TARBALL"; exit 1; }
    if [[ "$NO_VERIFY" != 1 && -f "$OFFLINE_TARBALL.sha256" ]]; then
      verify_checksum "$OFFLINE_TARBALL" "$(awk '{print $1}' "$OFFLINE_TARBALL.sha256")" \
        || { err "checksum mismatch on offline tarball"; exit 1; }
    else
      warn "no local .sha256 next to $OFFLINE_TARBALL; skipping checksum in offline mode"
    fi
    extract_and_install "$OFFLINE_TARBALL" || { err "offline install failed"; exit 1; }
  elif [[ "$ALREADY_INSTALLED" == 1 && "$FORCE" != 1 ]]; then
    info "skipping download (already at v$VERSION); re-checking agent hooks anyway"
  else
    download_and_install
  fi

  install_completions
  check_path
  configure_agent_hooks

  [[ "$DO_SELF_TEST" == 1 ]] && self_test

  print_summary
  print_uninstall_hint
}

main "$@"