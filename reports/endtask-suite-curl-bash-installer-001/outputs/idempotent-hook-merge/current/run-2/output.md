#!/usr/bin/env bash
#
# warpline installer
# ===================
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/warpline/main/install.sh?$(date +%s)" | bash
#
# Flags (pass after `--`, e.g. `curl ... | bash -s -- --quiet`):
#   --version VERSION       install a specific version (default: latest)
#   --prefix DIR            install directory (default: $HOME/.local/bin)
#   --force                 reinstall even if the same version is present
#   --quiet                 only print errors
#   --no-color              disable ANSI colors
#   --no-gum                don't use gum for output even if installed
#   --no-verify             skip SHA256 checksum verification (not recommended)
#   --build-from-source     consent to installing a toolchain and building
#                           from source, non-interactively (also: BUILD_FROM_SOURCE=1)
#   --offline TARBALL       install from a local tarball, no network calls
#   --easy-mode             append $PREFIX to PATH in your shell rc if missing
#   --uninstall             remove warpline and its completions, then exit
#   --verify                run a post-install self-test and exit
#   -h, --help              show this help and exit
#
# Env vars honored: HTTPS_PROXY, HTTP_PROXY, NO_PROXY, NO_COLOR, BUILD_FROM_SOURCE
#
set -euo pipefail
umask 022

OWNER="acme"
REPO="warpline"
BINARY_NAME="warpline"
FALLBACK_VERSION="0.1.0"
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION=""
PREFIX=""
DEST=""
FORCE=0
QUIET=0
NO_GUM=0
NO_VERIFY=0
BUILD_FROM_SOURCE="${BUILD_FROM_SOURCE:-0}"
OFFLINE_TARBALL=""
EASY_MODE=0
DO_UNINSTALL=0
DO_VERIFY_ONLY=0
FROM_SOURCE=0
AGENT_CONFIG_FAILS=()

TMP=""
LOCKFD_HELD=0
LOCK_MKDIR=""

cleanup() {
  local ec=$?
  if [[ -n "$LOCK_MKDIR" && -d "$LOCK_MKDIR" ]]; then rm -rf "$LOCK_MKDIR"; fi
  if [[ -n "$TMP" && -d "$TMP" ]]; then rm -rf "$TMP"; fi
  exit "$ec"
}
trap cleanup EXIT

# ---------------------------------------------------------------- output ---
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

usage() {
  sed -n '2,29p' "$0" | sed 's/^# \{0,1\}//'
}

# -------------------------------------------------------------- arg parse --
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version) VERSION="$2"; shift 2 ;;
      --prefix) PREFIX="$2"; shift 2 ;;
      --force) FORCE=1; shift ;;
      --quiet) QUIET=1; shift ;;
      --no-color) NO_COLOR=1; shift ;;
      --no-gum) NO_GUM=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --build-from-source) BUILD_FROM_SOURCE=1; shift ;;
      --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      --verify) DO_VERIFY_ONLY=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done
  PREFIX="${PREFIX:-$HOME/.local/bin}"
  DEST="$PREFIX"
  HOOK_COMMAND="$DEST/$BINARY_NAME hook pre-tool-use"
}

# -------------------------------------------------------------- platform ---
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x64 ;; arm64|aarch64) ARCH=arm64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x64)    TARGET=linux-x64-musl ;;
    linux-arm64)  TARGET=linux-arm64-musl ;;
    darwin-x64)   TARGET=darwin-x64 ;;
    darwin-arm64) TARGET=darwin-arm64 ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — if Claude Code or Codex CLI run on the Windows side rather than in this WSL distro, their settings files won't be under \$HOME here; rerun this installer from the same environment the agent runs in."
  fi
}

# ---------------------------------------------------------------- proxy ----
PROXY_ARGS=()
setup_proxy() {
  if [[ -n "${HTTPS_PROXY:-}" ]]; then PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

# ------------------------------------------------------------- version -----
resolve_version() {
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"
}

installed_version() {
  [[ -x "$DEST/$BINARY_NAME" ]] || return 1
  timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
}

# ------------------------------------------------------------- preflight ---
preflight() {
  mkdir -p "$DEST"
  [[ -w "$DEST" ]] || { err "no write permission on $DEST"; exit 1; }

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [[ -n "$avail_kb" && "$avail_kb" -lt 51200 ]]; then
    err "less than 50MB free at $DEST"; exit 1
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      warn "no network reachability to github.com — proceeding anyway (may fail downstream)"
    fi
  fi

  local existing
  existing=$(installed_version || true)
  if [[ -n "$existing" ]]; then
    info "found existing $BINARY_NAME v$existing at $DEST/$BINARY_NAME"
  fi
}

# ---------------------------------------------------------------- lock -----
acquire_lock() {
  local lf="${TMPDIR:-/tmp}/warpline-install-$(id -u).lock" w=2400
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null || { err "cannot open lockfile $lf"; exit 1; }
    if ! flock -w "$w" 9; then err "timed out waiting for install lock ($lf)"; exit 1; fi
    LOCKFD_HELD=1
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    if (( $(date +%s) - start >= w )); then err "timed out waiting for install lock ($d)"; exit 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_MKDIR="$d"
}

# ------------------------------------------------------- checksum/sigstore-
verify_checksum() {  # $1=file $2=expected (may be empty)
  [[ "$NO_VERIFY" == 1 ]] && { warn "checksum verification skipped (--no-verify)"; return 0; }
  if [[ -z "$2" ]]; then warn "no checksum available for this artifact; skipping"; return 0; fi
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0
  fi
  if [[ "$a" == "$2" ]]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $a)"; return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature verification"; return 0; }
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle for this artifact; skipping"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
  else
    err "Sigstore verification FAILED for $1"
    return 1
  fi
}

fetch_expected_sha() {  # $1=artifact filename
  local sums
  sums=$(curl -fsSL "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/checksums.txt" 2>/dev/null) || { echo ""; return 0; }
  echo "$sums" | grep "$1" | awk '{print $1}' | head -1
}

# -------------------------------------------------------------- install ----
extract_and_install() {  # $1=archive path
  local extract_dir="$TMP/extracted"
  mkdir -p "$extract_dir"
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$extract_dir" ;;
    *.tar.xz) tar -xJf "$1" -C "$extract_dir" ;;
    *.zip) unzip -q "$1" -d "$extract_dir" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin; bin=$(find "$extract_dir" -type f -name "$BINARY_NAME" | head -1)
  [[ -n "$bin" ]] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  chmod +x "$bin" 2>/dev/null || true
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME v$VERSION -> $DEST/$BINARY_NAME"
}

download_and_install() {
  local artifact="$REPO-v$VERSION-$TARGET.tar.gz"
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$artifact"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url
  for url in "${urls[@]}"; do
    local out="$TMP/artifact.tar.gz"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$out" 2>/dev/null; then
      local fname; fname=$(basename "$url")
      local expected; expected=$(fetch_expected_sha "$fname")
      if verify_checksum "$out" "$expected" && verify_sigstore "$out" "$url.sigstore.json"; then
        extract_and_install "$out" && return 0
      fi
      rm -f "$out"
    fi
  done
  warn "no prebuilt binary could be downloaded/verified"
  confirm_build_from_source
  build_from_source
}

confirm_build_from_source() {
  [[ "$BUILD_FROM_SOURCE" == 1 ]] && return 0
  if [[ -t 0 && -t 1 ]]; then
    printf '\033[33m?\033[0m No verified prebuilt binary is available. Build %s from source? This installs/uses git + Node.js (>=18) + npm. [y/N] ' "$BINARY_NAME"
    read -r reply
    if [[ "$reply" =~ ^[Yy]$ ]]; then BUILD_FROM_SOURCE=1; return 0; fi
    err "aborting. Rerun with --build-from-source or BUILD_FROM_SOURCE=1 to consent non-interactively."
    exit 1
  else
    err "no prebuilt binary and not running in a terminal; rerun with --build-from-source or BUILD_FROM_SOURCE=1 to consent to installing a toolchain and building from source."
    exit 1
  fi
}

build_from_source() {
  info "building $BINARY_NAME from source"
  command -v git >/dev/null 2>&1 || { err "git is required to build from source"; exit 1; }
  command -v node >/dev/null 2>&1 || { err "Node.js >=18 is required to build from source"; exit 1; }
  local nodever; nodever=$(timeout 1 node --version 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/')
  [[ -n "$nodever" && "$nodever" -ge 18 ]] || warn "Node.js >=18 recommended; found v$(timeout 1 node --version 2>/dev/null)"

  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && npm ci --silent && npm run build --silent )

  local bin
  bin=$(find "$src" -maxdepth 4 -type f -name "$BINARY_NAME" -perm -u+x 2>/dev/null | head -1)
  if [[ -z "$bin" ]]; then
    bin=$(find "$src/dist" "$src/bin" -maxdepth 2 -type f 2>/dev/null | head -1)
  fi
  [[ -n "$bin" ]] || { err "build finished but no binary found"; exit 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source -> $DEST/$BINARY_NAME"
}

# --------------------------------------------------------------- offline ---
offline_install() {
  [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  local sidecar="${OFFLINE_TARBALL}.sha256"
  local expected=""
  [[ -f "$sidecar" ]] && expected=$(awk '{print $1}' "$sidecar")
  verify_checksum "$OFFLINE_TARBALL" "$expected" || exit 1
  extract_and_install "$OFFLINE_TARBALL"
}

# ------------------------------------------------------------ completions --
install_completions() {
  [[ -x "$DEST/$BINARY_NAME" ]] || return 0
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null \
    && ok "bash completions -> $bash_dir/$BINARY_NAME" || warn "bash completions unavailable"
  "$DEST/$BINARY_NAME" completions zsh > "$zsh_dir/_$BINARY_NAME" 2>/dev/null \
    && ok "zsh completions -> $zsh_dir/_$BINARY_NAME" || warn "zsh completions unavailable"
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null \
    && ok "fish completions -> $fish_dir/$BINARY_NAME.fish" || warn "fish completions unavailable"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [[ "$EASY_MODE" == 1 ]]; then
    local rc=""
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      *) rc="$HOME/.profile" ;;
    esac
    if ! grep -qF "$DEST" "$rc" 2>/dev/null; then
      printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
      ok "added $DEST to PATH in $rc (restart your shell)"
    fi
  else
    warn "$DEST is not on your PATH — add it, or rerun with --easy-mode"
  fi
}

# ---------------------------------------------------------- json helpers ---
jsonvalid() {  # $1=file
  if command -v jq >/dev/null 2>&1; then jq empty "$1" >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then python3 -c 'import json,sys;json.load(open(sys.argv[1]))' "$1" >/dev/null 2>&1
  else return 1
  fi
}

# ----------------------------------------------------------- agent hooks ---
detect_agents() {
  AGENTS_FOUND=()
  [[ -d "$HOME/.claude" ]] && AGENTS_FOUND+=(claude)
  if [[ -d "$HOME/.codex" ]] || command -v codex >/dev/null 2>&1; then
    AGENTS_FOUND+=(codex)
  fi
  if [[ ${#AGENTS_FOUND[@]} -eq 0 ]]; then
    info "no supported AI agent found (Claude Code, Codex CLI) — skipping hook config"
  fi
}

merge_claude_hook() {  # $1=settings file
  local f="$1" tmp="$TMP/claude-settings.$$.json" bak="" merge_ok=1
  if [[ -f "$f" ]]; then
    bak="${f}.bak.$(date +%s)"
    cp "$f" "$bak"
  else
    mkdir -p "$(dirname "$f")"
    echo '{}' > "$f"
  fi

  if command -v jq >/dev/null 2>&1; then
    jq --arg cmd "$HOOK_COMMAND" '
      .hooks //= {} | .hooks.PreToolUse //= [] |
      if ([.hooks.PreToolUse[]?.hooks[]?.command] | index($cmd)) == null
      then .hooks.PreToolUse += [{"matcher":"*","hooks":[{"type":"command","command":$cmd}]}]
      else . end
    ' "$f" > "$tmp" 2>/dev/null || merge_ok=0
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$f" "$tmp" "$HOOK_COMMAND" 2>/dev/null <<'PY' || merge_ok=0
import json, sys
src, dst, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src) as fh:
    data = json.load(fh)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
already = any(
    h.get("command") == cmd
    for entry in pre
    for h in entry.get("hooks", [])
)
if not already:
    pre.append({"matcher": "*", "hooks": [{"type": "command", "command": cmd}]})
with open(dst, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
PY
  else
    warn "neither jq nor python3 found; skipping Claude Code hook config"
    return 0
  fi

  if [[ "$merge_ok" == 1 && -s "$tmp" ]] && jsonvalid "$tmp"; then
    mv "$tmp" "$f"
    ok "Claude Code pre-tool-use hook configured -> $f"
  else
    err "hook merge failed; left $f untouched$( [[ -n "$bak" ]] && printf ' (unmodified copy at %s)' "$bak" )"
    rm -f "$tmp"
    return 1
  fi
}

merge_codex_hook() {  # $1=config file
  local f="$1" tmp="$TMP/codex-config.$$.json" bak="" merge_ok=1
  if [[ -f "$f" ]]; then
    bak="${f}.bak.$(date +%s)"
    cp "$f" "$bak"
  else
    mkdir -p "$(dirname "$f")"
    echo '{}' > "$f"
  fi

  if command -v jq >/dev/null 2>&1; then
    jq --arg cmd "$HOOK_COMMAND" '
      .hooks //= {} | .hooks.pre_tool_use //= [] |
      if (.hooks.pre_tool_use | index($cmd)) == null
      then .hooks.pre_tool_use += [$cmd]
      else . end
    ' "$f" > "$tmp" 2>/dev/null || merge_ok=0
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$f" "$tmp" "$HOOK_COMMAND" 2>/dev/null <<'PY' || merge_ok=0
import json, sys
src, dst, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src) as fh:
    data = json.load(fh)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("pre_tool_use", [])
if cmd not in pre:
    pre.append(cmd)
with open(dst, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
PY
  else
    warn "neither jq nor python3 found; skipping Codex CLI hook config"
    return 0
  fi

  if [[ "$merge_ok" == 1 && -s "$tmp" ]] && jsonvalid "$tmp"; then
    mv "$tmp" "$f"
    ok "Codex CLI pre-tool-use hook configured -> $f"
  else
    err "hook merge failed; left $f untouched$( [[ -n "$bak" ]] && printf ' (unmodified copy at %s)' "$bak" )"
    rm -f "$tmp"
    return 1
  fi
}

configure_agents() {
  detect_agents
  local a
  for a in "${AGENTS_FOUND[@]:-}"; do
    [[ -z "$a" ]] && continue
    case "$a" in
      claude) merge_claude_hook "$HOME/.claude/settings.json" || AGENT_CONFIG_FAILS+=("claude") ;;
      codex)  merge_codex_hook  "$HOME/.codex/config.json"    || AGENT_CONFIG_FAILS+=("codex")  ;;
    esac
  done
}

# --------------------------------------------------------------- summary ---
draw_box() {  # $1=color, rest=lines
  local color="$1"; shift; local lines=("$@") max=0 esc; esc=$(printf '\033'); local strip="s/${esc}\\[[0-9;]*m//g"
  local l s
  for l in "${lines[@]}"; do
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    (( ${#s} > max )) && max=${#s}
  done
  local inner=$((max+4)) border="" i
  for ((i=0;i<inner;i++)); do border+="═"; done
  printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
  for l in "${lines[@]}"; do
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    local pad=$((max-${#s})) p="" j
    for ((j=0;j<pad;j++)); do p+=" "; done
    printf "\033[%sm║\033[0m  %b%s  \033[%sm║\033[0m\n" "$color" "$l" "$p" "$color"
  done
  printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
}

print_summary() {
  local color=42
  [[ ${#AGENT_CONFIG_FAILS[@]} -gt 0 ]] && color=214
  local agents_line="none detected"
  [[ ${#AGENTS_FOUND[@]:-0} -gt 0 ]] && agents_line="${AGENTS_FOUND[*]}"
  local lines=(
    "warpline v$VERSION installed"
    "binary:      $DEST/$BINARY_NAME"
    "agents seen: $agents_line"
  )
  if [[ ${#AGENT_CONFIG_FAILS[@]} -gt 0 ]]; then
    lines+=("hook config FAILED for: ${AGENT_CONFIG_FAILS[*]} (see warnings above)")
  fi
  [[ "$QUIET" != 1 ]] && draw_box "$color" "${lines[@]}"
}

print_uninstall_instructions() {
  [[ "$QUIET" == 1 ]] && return 0
  cat <<EOF

Uninstall:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  Agent hooks are left in place — remove the "$HOOK_COMMAND" entry from
  ~/.claude/settings.json or ~/.codex/config.json manually if desired.
  (Or rerun this installer with --uninstall.)
EOF
}

do_uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "uninstalled $BINARY_NAME. Agent hooks left in place — remove from settings.json/config.json manually if desired."
}

# ----------------------------------------------------------- self-test -----
run_verify() {
  local fails=0
  if [[ -x "$DEST/$BINARY_NAME" ]]; then
    ok "binary present and executable: $DEST/$BINARY_NAME"
  else
    err "binary missing: $DEST/$BINARY_NAME"; fails=1
  fi
  if timeout 1 "$DEST/$BINARY_NAME" --version >/dev/null 2>&1; then
    ok "binary runs (--version)"
  else
    err "binary failed to run"; fails=1
  fi
  if [[ -f "$HOME/.claude/settings.json" ]] && grep -qF "$HOOK_COMMAND" "$HOME/.claude/settings.json" 2>/dev/null; then
    ok "Claude Code hook present"
  fi
  if [[ -f "$HOME/.codex/config.json" ]] && grep -qF "$HOOK_COMMAND" "$HOME/.codex/config.json" 2>/dev/null; then
    ok "Codex CLI hook present"
  fi
  [[ "$fails" == 0 ]] && { ok "self-test passed"; return 0; } || { err "self-test failed"; return 1; }
}

# ------------------------------------------------------------------ main ---
main() {
  parse_args "$@"
  TMP=$(mktemp -d)

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    do_uninstall
    exit 0
  fi

  if [[ "$DO_VERIFY_ONLY" == 1 ]]; then
    run_verify
    exit $?
  fi

  setup_proxy
  detect_platform

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    resolve_version
    preflight
    acquire_lock
    offline_install
  else
    resolve_version
    preflight
    acquire_lock

    local existing
    existing=$(installed_version || true)
    if [[ -n "$existing" && "$existing" == "$VERSION" && "$FORCE" != 1 ]]; then
      info "$BINARY_NAME v$VERSION already installed — skipping download (use --force to reinstall)"
    elif [[ "$FROM_SOURCE" == 1 ]]; then
      confirm_build_from_source
      build_from_source
    else
      download_and_install
    fi
  fi

  install_completions
  check_path
  configure_agents

  print_summary
  print_uninstall_instructions
}

main "$@"