#!/usr/bin/env bash
#
# warpline installer
# ===================
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/warpline/main/install.sh?$(date +%s)" | bash
#
# Flags (pass after `-s --` when piping):
#   --version VERSION   install a specific version           (default: latest)
#   --dest DIR           install directory                     (default: ~/.local/bin, /usr/local/bin if root)
#   --quiet               errors only
#   --force                reinstall even if the target version is already present
#   --no-color               disable ANSI color output
#   --no-gum                  disable gum styling even if gum is installed
#   --no-verify                 skip SHA256 / Sigstore verification (not recommended)
#   --offline TARBALL              install from a local tarball, no network calls at all
#   --easy-mode                      append a PATH export to your shell rc if $DEST isn't on PATH
#   --uninstall                        remove the warpline binary, completions and share dir
#   --verify                             run a post-install self-test and exit
#   -h, --help                             show this help
#
# Example:
#   curl -fsSL "https://raw.githubusercontent.com/acme/warpline/main/install.sh?$(date +%s)" \
#     | bash -s -- --version 1.4.0 --dest "$HOME/bin"
#
set -euo pipefail
umask 022

OWNER="acme"
REPO="warpline"
BINARY_NAME="warpline"
FALLBACK_VERSION="0.1.0"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"
COSIGN_ID_RE="https://github.com/${OWNER}/${REPO}/.github/workflows/release.yml@refs/tags/v.*"

CLAUDE_SETTINGS="$HOME/.claude/settings.json"
# Codex CLI's upstream config is ~/.codex/config.toml; this installer instead reads/writes
# ~/.codex/config.json with the same hooks.pre_tool_use array shape, to keep the merge on the
# jq/python3-JSON-only path (no sed/awk, no TOML writer). If your Codex build only honors
# config.toml, port this block by hand.
CODEX_SETTINGS="$HOME/.codex/config.json"

VERSION=""
DEST=""
QUIET=0
FORCE=0
NO_COLOR_FLAG=0
NO_GUM=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
DO_UNINSTALL=0
DO_VERIFY_SELFTEST=0

PROXY_ARGS=()
AGENTS=()
LOCK_MODE=""
LOCK_PATH=""
TMP=""
HOOK_CMD=""

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  DEST_DEFAULT="/usr/local/bin"
else
  DEST_DEFAULT="$HOME/.local/bin"
fi

HAS_GUM=0
if command -v gum >/dev/null 2>&1 && [[ -t 1 ]]; then
  HAS_GUM=1
fi

_log() {
  local color="$1" symbol="$2"; shift 2
  local kind="$symbol" msg="$*"
  if [[ "$QUIET" == 1 && "$symbol" != "✗" ]]; then
    return 0
  fi
  if [[ "$HAS_GUM" == 1 && "$NO_GUM" != 1 ]]; then
    gum style --foreground "$color" "$symbol $msg"
  elif [[ "$NO_COLOR_FLAG" == 1 || -n "${NO_COLOR:-}" || ! -t 1 ]]; then
    printf '%s %s\n' "$symbol" "$msg"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$symbol" "$msg"
  fi
}
info() { _log 39  '->' "$@"; }
ok()   { _log 42  '✓'  "$@"; }
warn() { _log 214 '⚠'  "$@"; }
err()  { _log 196 '✗'  "$@"; }

usage() {
  cat <<'EOF'
warpline installer

  curl -fsSL "https://raw.githubusercontent.com/acme/warpline/main/install.sh?$(date +%s)" | bash

Flags:
  --version VERSION   install a specific version (default: latest)
  --dest DIR          install directory (default: ~/.local/bin, /usr/local/bin if root)
  --quiet             errors only
  --force             reinstall even if the target version is already present
  --no-color          disable ANSI color output
  --no-gum            disable gum styling even if gum is installed
  --no-verify         skip SHA256 / Sigstore verification (not recommended)
  --offline TARBALL   install from a local tarball, no network calls at all
  --easy-mode         append a PATH export to your shell rc if needed
  --uninstall         remove warpline (leaves agent hook entries; instructions are printed)
  --verify            run a post-install self-test and exit
  -h, --help          show this help
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version)
        [[ $# -ge 2 ]] || { err "missing value for --version"; exit 1; }
        VERSION="$2"; shift 2 ;;
      --dest)
        [[ $# -ge 2 ]] || { err "missing value for --dest"; exit 1; }
        DEST="$2"; shift 2 ;;
      --quiet)     QUIET=1; shift ;;
      --force)     FORCE=1; shift ;;
      --no-color)  NO_COLOR_FLAG=1; shift ;;
      --no-gum)    NO_GUM=1; shift ;;
      --no-verify) NO_VERIFY=1; shift ;;
      --offline)
        [[ $# -ge 2 ]] || { err "missing value for --offline"; exit 1; }
        OFFLINE_TARBALL="$2"; shift 2 ;;
      --easy-mode) EASY_MODE=1; shift ;;
      --uninstall) DO_UNINSTALL=1; shift ;;
      --verify)    DO_VERIFY_SELFTEST=1; shift ;;
      -h|--help)   usage; exit 0 ;;
      *) err "unknown flag: $1"; usage; exit 1 ;;
    esac
  done
}

setup_proxy() {
  PROXY_ARGS=()
  if [[ -n "${HTTPS_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTPS_PROXY")
  elif [[ -n "${HTTP_PROXY:-}" ]]; then
    PROXY_ARGS=(--proxy "$HTTP_PROXY")
  fi
}

cleanup() {
  if [[ -n "${TMP:-}" && -d "${TMP:-}" ]]; then
    rm -rf "$TMP"
  fi
  if [[ "$LOCK_MODE" == "mkdir" && -n "$LOCK_PATH" ]]; then
    rm -rf "$LOCK_PATH"
  fi
  exec 9>&- 2>/dev/null || true
}

detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)  ARCH=x64 ;;
    arm64|aarch64) ARCH=arm64 ;;
    *) err "unsupported architecture: $ARCH"; exit 1 ;;
  esac
  case "$OS" in
    linux|darwin) : ;;
    *) err "unsupported OS: $OS"; exit 1 ;;
  esac
  TARGET="${OS}-${ARCH}"
  if [[ "$OS" == "linux" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — install proceeds normally, but double-check hook paths if you also run agents on the Windows side"
  fi
}

resolve_version() {
  if [[ -n "$VERSION" ]]; then
    return 0
  fi

  if [[ -f "package.json" ]]; then
    local pkg_name=""
    pkg_name=$(grep -m1 '"name"' package.json 2>/dev/null | sed -E 's/.*"name"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/') || true
    if [[ "$pkg_name" == "$REPO" ]]; then
      VERSION=$(grep -m1 '"version"' package.json | sed -E 's/.*"version"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/') || true
    fi
  fi
  if [[ -n "$VERSION" ]]; then
    info "version from local package.json: $VERSION"
    return 0
  fi

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  if [[ -n "$VERSION" ]]; then
    info "version from GitHub API: $VERSION"
    return 0
  fi

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  if [[ -n "$VERSION" && "$VERSION" != *"releases/latest"* ]]; then
    info "version from redirect: $VERSION"
    return 0
  fi

  VERSION="$FALLBACK_VERSION"
  warn "could not resolve latest version from GitHub; falling back to $FALLBACK_VERSION"
}

preflight() {
  local avail=""
  avail=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}') || true
  if [[ -z "$avail" ]]; then
    avail=$(df -Pk "$(dirname "$DEST")" 2>/dev/null | awk 'NR==2{print $4}') || true
  fi
  if [[ -n "$avail" ]] && (( avail < 51200 )); then
    err "less than 50MB free near $DEST; aborting"
    exit 1
  fi

  if ! mkdir -p "$DEST" 2>/dev/null; then
    err "cannot create $DEST"
    exit 1
  fi
  if [[ ! -w "$DEST" ]]; then
    err "$DEST is not writable"
    exit 1
  fi

  if [[ -z "$OFFLINE_TARBALL" ]]; then
    if ! curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" 2>/dev/null; then
      err "no network reachability to github.com (use --offline TARBALL for an airgapped install)"
      exit 1
    fi
  fi
}

acquire_lock() {
  local lf="$1" w="${2:-1200}"
  if command -v flock >/dev/null 2>&1; then
    if ! { exec 9>>"$lf"; } 2>/dev/null; then
      err "cannot open lockfile $lf"
      return 1
    fi
    if flock -w "$w" 9; then
      LOCK_MODE="flock"
      return 0
    fi
    err "timed out waiting for lock $lf"
    return 1
  fi

  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid=""
    if [[ -f "$d/pid" ]]; then
      opid=$(cat "$d/pid" 2>/dev/null) || true
    fi
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"
      continue
    fi
    if (( $(date +%s) - start >= w )); then
      err "timed out waiting for lock $d"
      return 1
    fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_MODE="mkdir"
  LOCK_PATH="$d"
  return 0
}

existing_version() {
  if [[ ! -x "$DEST/$BINARY_NAME" ]]; then
    return 1
  fi
  local v=""
  v=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1) || true
  if [[ -z "$v" ]]; then
    return 1
  fi
  printf '%s' "$v"
}

verify_checksum() {
  local file="$1" expected="$2" actual=""
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    warn "no sha256sum/shasum available; skipping checksum verification"
    return 0
  fi
  if [[ "$actual" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $(basename "$file") (want $expected, got $actual)"
  return 1
}

verify_sigstore() {
  local file="$1" bundle_url="$2"
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore verification (soft-skip)"
    return 0
  fi
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/sig.json" 2>/dev/null; then
    warn "no Sigstore bundle at $bundle_url; skipping signature verification"
    return 0
  fi
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$file" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore verification FAILED for $(basename "$file") — cosign is installed, so this is a hard failure"
  return 1
}

extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) err "unrecognized archive format: $archive"; return 1 ;;
  esac
  local bin=""
  bin=$(find "$TMP" -maxdepth 4 -type f -name "$BINARY_NAME" | head -1) || true
  if [[ -z "$bin" ]]; then
    err "binary '$BINARY_NAME' not found inside $archive"
    return 1
  fi
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
  return 0
}

build_from_source() {
  if ! command -v node >/dev/null 2>&1; then
    err "node not found; cannot build from source. Install Node.js >= 18 and retry, or use --offline"
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    err "npm not found; cannot build from source"
    exit 1
  fi
  if ! command -v git >/dev/null 2>&1; then
    err "git not found; cannot build from source"
    exit 1
  fi

  local src="$TMP/src"
  info "cloning $OWNER/$REPO@v$VERSION for a source build..."
  if ! git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null; then
    if ! git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"; then
      err "git clone failed"
      exit 1
    fi
  fi

  if ! ( cd "$src" && npm ci --silent && npm run build --silent ); then
    err "source build failed"
    exit 1
  fi

  local share_dir="$HOME/.local/share/$REPO/$VERSION"
  mkdir -p "$share_dir"
  cp -r "$src/dist" "$share_dir/dist"
  if [[ -d "$src/node_modules" ]]; then
    cp -r "$src/node_modules" "$share_dir/node_modules"
  fi

  cat > "$DEST/$BINARY_NAME" <<EOF
#!/usr/bin/env bash
exec node "$share_dir/dist/cli.js" "\$@"
EOF
  chmod 0755 "$DEST/$BINARY_NAME"
  ok "built from source → $DEST/$BINARY_NAME"
}

download_and_install() {
  local candidates=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
  )
  local url sha
  for url in "${candidates[@]}"; do
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      if [[ "$NO_VERIFY" != 1 ]]; then
        sha=$(curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" 2>/dev/null | awk '{print $1}') || true
        if [[ -n "$sha" ]]; then
          if ! verify_checksum "$TMP/artifact.tar.gz" "$sha"; then
            rm -f "$TMP/artifact.tar.gz"
            continue
          fi
        else
          warn "no checksum published for this artifact; proceeding unverified (pass --no-verify to silence)"
        fi
        if ! verify_sigstore "$TMP/artifact.tar.gz" "${url}.sigstore.json"; then
          err "aborting install: signature verification failed and cosign is present"
          exit 1
        fi
      fi
      if extract_and_install "$TMP/artifact.tar.gz"; then
        return 0
      fi
      rm -f "$TMP/artifact.tar.gz"
    fi
  done
  warn "no prebuilt binary available for $TARGET; building from source"
  build_from_source
}

install_completions() {
  if [[ ! -x "$DEST/$BINARY_NAME" ]]; then
    return 0
  fi
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"

  if timeout 1 "$DEST/$BINARY_NAME" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null; then
    ok "bash completions → $bash_dir/$BINARY_NAME"
  else
    rm -f "$bash_dir/$BINARY_NAME"
    warn "bash completions unavailable"
  fi
  if timeout 1 "$DEST/$BINARY_NAME" completion zsh > "$zsh_dir/_$BINARY_NAME" 2>/dev/null; then
    ok "zsh completions → $zsh_dir/_$BINARY_NAME"
  else
    rm -f "$zsh_dir/_$BINARY_NAME"
    warn "zsh completions unavailable"
  fi
  if timeout 1 "$DEST/$BINARY_NAME" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null; then
    ok "fish completions → $fish_dir/$BINARY_NAME.fish"
  else
    rm -f "$fish_dir/$BINARY_NAME.fish"
    warn "fish completions unavailable"
  fi
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on your PATH"
  if [[ "$EASY_MODE" == 1 ]]; then
    local rc="$HOME/.bashrc"
    if [[ -n "${ZSH_VERSION:-}" ]]; then
      rc="$HOME/.zshrc"
    fi
    echo "export PATH=\"$DEST:\$PATH\"" >> "$rc"
    ok "appended PATH export to $rc (restart your shell, or re-source it)"
  else
    info "add this to your shell rc: export PATH=\"$DEST:\$PATH\"  (or re-run with --easy-mode)"
  fi
}

detect_agents() {
  AGENTS=()
  if [[ -d "$HOME/.claude" ]] || command -v claude >/dev/null 2>&1; then
    AGENTS+=(claude)
  fi
  if [[ -d "$HOME/.codex" ]] || command -v codex >/dev/null 2>&1; then
    AGENTS+=(codex)
  fi
}

# Validates $2 as JSON, backs up $1, atomically writes $3 only if it differs from $2, and
# restores the backup if the write fails partway. Called by both agent hook configurators
# so the idempotency / backup / rollback logic lives in exactly one place.
_json_apply() {
  local target="$1" before="$2" after="$3" label="$4"

  if [[ "$before" == "$after" ]]; then
    ok "$label hook already present in $target; skipping (idempotent)"
    return 0
  fi

  if command -v jq >/dev/null 2>&1; then
    if ! printf '%s' "$after" | jq empty >/dev/null 2>&1; then
      err "$label merge produced invalid JSON; leaving $target untouched"
      return 1
    fi
  else
    if ! printf '%s' "$after" | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1; then
      err "$label merge produced invalid JSON; leaving $target untouched"
      return 1
    fi
  fi

  local backup="${target}.bak.$(date +%s)"
  cp "$target" "$backup"

  if printf '%s\n' "$after" > "$target.tmp.$$" && mv "$target.tmp.$$" "$target"; then
    ok "$label hook configured → $target (backup: $backup)"
    return 0
  fi
  err "failed writing $target; restoring from $backup"
  cp "$backup" "$target"
  return 1
}

_python_merge_claude() {
  python3 - "$1" "$2" <<'PY'
import json, sys
target, cmd = sys.argv[1], sys.argv[2]
with open(target) as f:
    data = json.load(f)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
found = any(
    h.get("command") == cmd
    for entry in pre
    for h in entry.get("hooks", [])
)
if not found:
    pre.append({"matcher": "*", "hooks": [{"type": "command", "command": cmd}]})
print(json.dumps(data, indent=2))
PY
}

_python_merge_codex() {
  python3 - "$1" "$2" <<'PY'
import json, sys
target, cmd = sys.argv[1], sys.argv[2]
with open(target) as f:
    data = json.load(f)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("pre_tool_use", [])
if cmd not in pre:
    pre.append(cmd)
print(json.dumps(data, indent=2))
PY
}

configure_claude_hook() {
  local target="$CLAUDE_SETTINGS"
  mkdir -p "$(dirname "$target")"
  if [[ ! -f "$target" ]]; then
    echo '{}' > "$target"
  fi

  if command -v jq >/dev/null 2>&1; then
    if ! jq empty "$target" >/dev/null 2>&1; then
      err "$target is not valid JSON; refusing to touch it — fix manually and re-run"
      return 1
    fi
  elif command -v python3 >/dev/null 2>&1; then
    if ! python3 -c "import json; json.load(open('$target'))" >/dev/null 2>&1; then
      err "$target is not valid JSON; refusing to touch it — fix manually and re-run"
      return 1
    fi
  else
    warn "neither jq nor python3 found; cannot safely edit $target — skipping Claude Code hook"
    return 1
  fi

  local before after
  before=$(cat "$target")

  if command -v jq >/dev/null 2>&1; then
    after=$(jq --arg cmd "$HOOK_CMD" --arg matcher '*' '
      .hooks = (.hooks // {}) |
      .hooks.PreToolUse = (
        (.hooks.PreToolUse // []) as $existing
        | if any($existing[]?.hooks[]?; .command == $cmd)
          then $existing
          else $existing + [{"matcher": $matcher, "hooks": [{"type": "command", "command": $cmd}]}]
          end
      )
    ' "$target") || { err "jq merge failed for $target"; return 1; }
  else
    after=$(_python_merge_claude "$target" "$HOOK_CMD") || { err "python3 merge failed for $target"; return 1; }
  fi

  _json_apply "$target" "$before" "$after" "Claude Code"
}

configure_codex_hook() {
  local target="$CODEX_SETTINGS"
  mkdir -p "$(dirname "$target")"
  if [[ ! -f "$target" ]]; then
    echo '{}' > "$target"
  fi

  if command -v jq >/dev/null 2>&1; then
    if ! jq empty "$target" >/dev/null 2>&1; then
      err "$target is not valid JSON; refusing to touch it — fix manually and re-run"
      return 1
    fi
  elif command -v python3 >/dev/null 2>&1; then
    if ! python3 -c "import json; json.load(open('$target'))" >/dev/null 2>&1; then
      err "$target is not valid JSON; refusing to touch it — fix manually and re-run"
      return 1
    fi
  else
    warn "neither jq nor python3 found; cannot safely edit $target — skipping Codex CLI hook"
    return 1
  fi

  local before after
  before=$(cat "$target")

  if command -v jq >/dev/null 2>&1; then
    after=$(jq --arg cmd "$HOOK_CMD" '
      .hooks = (.hooks // {}) |
      .hooks.pre_tool_use = (
        (.hooks.pre_tool_use // []) as $existing
        | if any($existing[]?; . == $cmd) then $existing else $existing + [$cmd] end
      )
    ' "$target") || { err "jq merge failed for $target"; return 1; }
  else
    after=$(_python_merge_codex "$target" "$HOOK_CMD") || { err "python3 merge failed for $target"; return 1; }
  fi

  _json_apply "$target" "$before" "$after" "Codex CLI"
}

self_test() {
  info "running self-test..."
  local v=""
  v=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null) || true
  if [[ -n "$v" ]]; then
    ok "binary runs: $v"
  else
    err "binary did not respond to --version"
  fi

  if [[ -f "$CLAUDE_SETTINGS" ]] && command -v jq >/dev/null 2>&1; then
    if jq -e --arg cmd "$HOOK_CMD" \
        '[.hooks.PreToolUse[]?.hooks[]? | select(.command==$cmd)] | length > 0' \
        "$CLAUDE_SETTINGS" >/dev/null 2>&1; then
      ok "Claude Code hook present in $CLAUDE_SETTINGS"
    fi
  fi
  if [[ -f "$CODEX_SETTINGS" ]] && command -v jq >/dev/null 2>&1; then
    if jq -e --arg cmd "$HOOK_CMD" \
        '[.hooks.pre_tool_use[]? | select(.==$cmd)] | length > 0' \
        "$CODEX_SETTINGS" >/dev/null 2>&1; then
      ok "Codex CLI hook present in $CODEX_SETTINGS"
    fi
  fi
}

draw_box() {
  local title="$1"; shift
  local lines=("$@")
  local width=${#title}
  local l
  for l in "${lines[@]}"; do
    if (( ${#l} > width )); then width=${#l}; fi
  done
  width=$((width + 2))
  local border
  border=$(printf '─%.0s' $(seq 1 "$width"))
  printf '\n┌%s┐\n' "$border"
  printf '│ %-*s │\n' "$width" "$title"
  printf '├%s┤\n' "$border"
  for l in "${lines[@]}"; do
    printf '│ %-*s │\n' "$width" "$l"
  done
  printf '└%s┘\n\n' "$border"
}

print_summary() {
  local lines=("binary:      $DEST/$BINARY_NAME (v$VERSION)")
  lines+=("completions: bash/zsh/fish under XDG dirs")
  if [[ ${#AGENTS[@]} -gt 0 ]]; then
    lines+=("agent hooks: ${AGENTS[*]}")
  else
    lines+=("agent hooks: none detected")
  fi
  draw_box "warpline v$VERSION installed" "${lines[@]}"
}

print_uninstall_instructions() {
  cat <<EOF
Uninstall:
  rm -f "$DEST/$BINARY_NAME"
  rm -rf "$HOME/.local/share/$REPO"
  rm -f "\${XDG_DATA_HOME:-\$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "\${XDG_DATA_HOME:-\$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "\${XDG_CONFIG_HOME:-\$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  # then remove the "$HOOK_CMD" entry from:
  #   $CLAUDE_SETTINGS
  #   $CODEX_SETTINGS
Or re-run:
  curl -fsSL "https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh?\$(date +%s)" | bash -s -- --uninstall
EOF
}

uninstall() {
  info "uninstalling $BINARY_NAME..."
  local dest="${DEST:-$DEST_DEFAULT}"
  rm -f "$dest/$BINARY_NAME"
  rm -rf "$HOME/.local/share/$REPO"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  ok "binary and completions removed"
  info "agent hook entries in $CLAUDE_SETTINGS / $CODEX_SETTINGS were left in place — remove the \"$BINARY_NAME hook pre-tool-use\" entry by hand if desired"
  exit 0
}

main() {
  parse_args "$@"
  setup_proxy

  if [[ "$DO_UNINSTALL" == 1 ]]; then
    uninstall
  fi

  TMP=$(mktemp -d "${TMPDIR:-/tmp}/${REPO}-install.XXXXXX")
  trap cleanup EXIT

  detect_platform
  if [[ -z "$DEST" ]]; then
    DEST="$DEST_DEFAULT"
  fi
  HOOK_CMD="$DEST/$BINARY_NAME hook pre-tool-use"

  if [[ -n "$OFFLINE_TARBALL" ]]; then
    if [[ ! -f "$OFFLINE_TARBALL" ]]; then
      err "no such file: $OFFLINE_TARBALL"
      exit 1
    fi
    if [[ -z "$VERSION" ]]; then
      VERSION="offline"
    fi
  else
    resolve_version
  fi

  preflight

  local lockdir="${XDG_STATE_HOME:-$HOME/.local/state}/$REPO"
  mkdir -p "$lockdir"
  if ! acquire_lock "$lockdir/install.lock" 1200; then
    err "another $REPO install appears to be running; try again later"
    exit 1
  fi

  local current=""
  current=$(existing_version) || true
  if [[ -n "$current" && "$current" == "$VERSION" && "$FORCE" != 1 && -z "$OFFLINE_TARBALL" ]]; then
    ok "$REPO v$VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
  else
    if [[ -n "$OFFLINE_TARBALL" ]]; then
      if [[ "$NO_VERIFY" != 1 ]]; then
        warn "offline mode: skipping checksum/Sigstore verification (no network to fetch expected hashes)"
      fi
      if ! extract_and_install "$OFFLINE_TARBALL"; then
        err "offline install failed"
        exit 1
      fi
    else
      download_and_install
    fi
  fi

  install_completions
  check_path

  detect_agents
  if [[ ${#AGENTS[@]} -eq 0 ]]; then
    info "no supported AI agent (Claude Code, Codex CLI) detected; skipping hook configuration"
  else
    local a
    for a in "${AGENTS[@]}"; do
      if [[ "$a" == "claude" ]]; then
        configure_claude_hook || warn "Claude Code hook configuration failed; $CLAUDE_SETTINGS left untouched"
      fi
      if [[ "$a" == "codex" ]]; then
        configure_codex_hook || warn "Codex CLI hook configuration failed; $CODEX_SETTINGS left untouched"
      fi
    done
  fi

  if [[ "$DO_VERIFY_SELFTEST" == 1 ]]; then
    self_test
  fi

  print_summary
  print_uninstall_instructions
}

main "$@"