#!/usr/bin/env bash
#
# warpline installer
#
#   curl -fsSL "https://raw.githubusercontent.com/acme/warpline/main/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version X       install a specific version (default: resolved automatically)
#   --dest DIR        install directory (default: ~/.local/bin)
#   --force           reinstall even if the resolved version is already present
#   --quiet           errors only
#   --no-color        disable ANSI styling
#   --no-gum          disable gum styling even if gum is on PATH
#   --no-verify       skip SHA256 + Sigstore verification (not recommended)
#   --offline TARBALL install straight from a local tarball, no network calls
#   --easy-mode       append DEST to PATH in the detected shell rc file
#   --verify          run install + verification self-test and exit
#   -h, --help        show this help and exit
#
# Env: WARPLINE_VERSION, WARPLINE_DEST, HTTPS_PROXY/HTTP_PROXY/NO_PROXY, NO_COLOR
#
set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="warpline"
BINARY_NAME="warpline"
FALLBACK_VERSION="0.1.0"   # last-resort, used only if every resolution tier below fails
COSIGN_ID_RE="^https://github.com/${OWNER}/${REPO}/\.github/workflows/release\.yml@refs/tags/v.*\$"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

DEST="${WARPLINE_DEST:-$HOME/.local/bin}"
VERSION="${WARPLINE_VERSION:-}"
FORCE=0
QUIET=0
NO_GUM=0
NO_VERIFY=0
OFFLINE_TARBALL=""
EASY_MODE=0
SELF_TEST=0
FROM_SOURCE=0

XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BASH_COMPLETION_DIR="${XDG_DATA_HOME}/bash-completion/completions"
ZSH_COMPLETION_DIR="${XDG_DATA_HOME}/zsh/site-functions"
FISH_COMPLETION_DIR="${XDG_DATA_HOME}/fish/vendor_completions.d"

# ---------------------------------------------------------------------------
# output stack — gum-if-TTY, ANSI fallback, honor NO_COLOR/non-TTY; err() is
# never gated by --quiet, since a silent failure is worse than a noisy one.
# ---------------------------------------------------------------------------
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
die()  { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# flags
# ---------------------------------------------------------------------------
show_help() { sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_COLOR=1; NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --verify) SELF_TEST=1; shift ;;
    -h|--help) show_help; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done

# ---------------------------------------------------------------------------
# temp dir + cleanup trap — set up before anything that can fail
# ---------------------------------------------------------------------------
TMP="$(mktemp -d "${TMPDIR:-/tmp}/warpline-install.XXXXXX")"
LOCK_DIR=""
cleanup() {
  rm -rf "$TMP"
  [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR"
}
trap cleanup EXIT

is_valid_json() {
  if command -v jq >/dev/null 2>&1; then jq empty "$1" >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$1" >/dev/null 2>&1
  else return 1
  fi
}

# ---------------------------------------------------------------------------
# proxy — expands to nothing when empty so every curl call stays unconditional
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")
# NO_PROXY is honored natively by curl.

# ---------------------------------------------------------------------------
# platform detection — Node-ecosystem os-arch naming (linux-x64 etc), the
# convention warpline's release workflow bundles under (single-file binaries
# produced by `bun build --compile`). WSL is detected and warned, never blocked.
# ---------------------------------------------------------------------------
OS=""
ARCH=""
TARGET=""
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=linux-x64 ;;
    linux-aarch64)  TARGET=linux-arm64 ;;
    darwin-x86_64)  TARGET=darwin-x64 ;;
    darwin-aarch64) TARGET=darwin-arm64 ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions install to the Linux-side shell config, not Windows"
  fi
}

# ---------------------------------------------------------------------------
# version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                             # 1. flag/env

  if [ -n "$OFFLINE_TARBALL" ]; then VERSION="offline"; return 0; fi

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0                                             # 2. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && return 0                                             # 3. redirect

  VERSION="$FALLBACK_VERSION"                                               # 4/5. hardcoded
  warn "could not resolve latest version from GitHub; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# preflight — disk, perms, network, existing install
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST"
  [ -w "$DEST" ] || die "no write permission on $DEST"

  local avail_kb
  avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    die "less than 50MB free at $DEST; aborting"
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 3 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" \
      || die "no network reachability to github.com (behind a proxy? set HTTPS_PROXY)"
  fi

  CURRENT_VERSION=""
  if [ -x "$DEST/$BINARY_NAME" ]; then
    CURRENT_VERSION=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
  fi
}

# ---------------------------------------------------------------------------
# atomic lock — flock-first, mkdir spinlock fallback (macOS has no flock),
# stale-PID self-heal. Braced exec so we don't clobber the caller's stderr.
# ---------------------------------------------------------------------------
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-120}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    [ $(( $(date +%s) - start )) -ge "$w" ] && return 1
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

# ---------------------------------------------------------------------------
# checksum + Sigstore — the asymmetry is the point: missing tool warns and
# continues; tool present + bad signature hard-fails.
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected_sha256
  [ "$NO_VERIFY" = 1 ] && { warn "--no-verify: skipping checksum"; return 0; }
  local actual
  if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then actual=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool found; skipping checksum"; return 0
  fi
  if [ "$actual" = "$2" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch (want $2, got $actual)"; return 1
  fi
}

verify_sigstore() {  # $1=file $2=bundle_url
  [ "$NO_VERIFY" = 1 ] && return 0
  command -v cosign >/dev/null 2>&1 || { warn "cosign absent; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no Sigstore bundle published; skipping"; return 0; }
  if cosign verify-blob --bundle "$TMP/sig.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" >/dev/null 2>&1; then
    ok "signature verified"
  else
    err "Sigstore verification FAILED"; return 1
  fi
}

# ---------------------------------------------------------------------------
# download → extract → install. install -m 0755 beats cp+chmod: no window
# where a partially-permissioned binary is visible on $PATH.
# ---------------------------------------------------------------------------
extract_and_install() {  # $1=archive
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$1" -C "$TMP" ;;
    *.zip) unzip -q "$1" -d "$TMP" ;;
    *) die "unrecognized archive format: $1" ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || die "binary not found inside archive"
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

download_and_install() {
  if [ -n "$OFFLINE_TARBALL" ]; then
    [ -f "$OFFLINE_TARBALL" ] || die "--offline tarball not found: $OFFLINE_TARBALL"
    extract_and_install "$OFFLINE_TARBALL"
    return 0
  fi

  local sha_url artifact_sha=""
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      artifact_sha=$(curl -fsSL "${PROXY_ARGS[@]}" "${url}.sha256" 2>/dev/null | awk '{print $1}') || true
      if [ -n "$artifact_sha" ]; then
        verify_checksum "$TMP/artifact.tar.gz" "$artifact_sha" || { rm -f "$TMP/artifact.tar.gz"; continue; }
      else
        warn "no published checksum for $url; proceeding unverified"
      fi
      verify_sigstore "$TMP/artifact.tar.gz" "${url}.sigstore.json" || { rm -f "$TMP/artifact.tar.gz"; continue; }
      extract_and_install "$TMP/artifact.tar.gz"
      return 0
    fi
  done

  warn "no prebuilt binary available; building from source"
  build_from_source
}

# ---------------------------------------------------------------------------
# build-from-source fallback — warpline is TypeScript, so the fallback chain
# is node/npm (not rustup/cargo): clone → npm ci → npm run build → locate
# the built entrypoint named in package.json's "bin" field.
# ---------------------------------------------------------------------------
build_from_source() {
  command -v git >/dev/null 2>&1 || die "git required to build from source"
  command -v node >/dev/null 2>&1 || die "node (>=18) required to build from source; install it and re-run"
  command -v npm >/dev/null 2>&1 || die "npm required to build from source"
  timeout 1 node -e 'process.exit(parseInt(process.versions.node) >= 18 ? 0 : 1)' \
    || die "node >=18 required (found $(timeout 1 node -v 2>/dev/null))"

  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || die "failed to clone $OWNER/$REPO"

  ( cd "$src" && npm ci --no-audit --no-fund && npm run build ) \
    || die "build failed"

  local bin_rel
  if command -v jq >/dev/null 2>&1; then
    bin_rel=$(jq -r '.bin | if type == "object" then .[keys[0]] else . end' "$src/package.json")
  else
    bin_rel=$(python3 -c "import json;d=json.load(open('$src/package.json'));b=d.get('bin');print(b if isinstance(b,str) else list(b.values())[0])")
  fi
  [ -n "$bin_rel" ] && [ -f "$src/$bin_rel" ] || die "could not locate built entrypoint in package.json's bin field"

  install -m 0755 "$src/$bin_rel" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# completions — XDG paths, not hardcoded rc-file guesses
# ---------------------------------------------------------------------------
install_completions() {
  mkdir -p "$BASH_COMPLETION_DIR" "$ZSH_COMPLETION_DIR" "$FISH_COMPLETION_DIR"
  "$DEST/$BINARY_NAME" completions bash > "$BASH_COMPLETION_DIR/$BINARY_NAME" 2>/dev/null \
    && ok "bash completions → $BASH_COMPLETION_DIR/$BINARY_NAME" \
    || warn "bash completions unavailable"
  "$DEST/$BINARY_NAME" completions zsh > "$ZSH_COMPLETION_DIR/_$BINARY_NAME" 2>/dev/null \
    && ok "zsh completions → $ZSH_COMPLETION_DIR/_$BINARY_NAME" \
    || warn "zsh completions unavailable"
  "$DEST/$BINARY_NAME" completions fish > "$FISH_COMPLETION_DIR/$BINARY_NAME.fish" 2>/dev/null \
    && ok "fish completions → $FISH_COMPLETION_DIR/$BINARY_NAME.fish" \
    || warn "fish completions unavailable"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on PATH"
  if [ "$EASY_MODE" = 1 ]; then
    local rc=""
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      */fish) rc="$HOME/.config/fish/config.fish" ;;
    esac
    if [ -n "$rc" ]; then
      printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
      ok "added $DEST to PATH in $rc (restart your shell)"
    fi
  else
    info "add this to your shell rc, or re-run with --easy-mode: export PATH=\"$DEST:\$PATH\""
  fi
}

# ---------------------------------------------------------------------------
# AI-agent hook auto-config — idempotent by construction: every merge first
# strips any existing warpline-tagged entry, then appends exactly one fresh
# one, so re-running the installer never produces duplicates. Original file
# is only overwritten after the merged result is validated as JSON, and only
# after a timestamped backup is taken — a bad merge leaves the original
# untouched and the run continues (agent config is best-effort, not fatal).
# ---------------------------------------------------------------------------
configure_claude_hook() {
  local file="$HOME/.claude/settings.json"
  [ -d "$HOME/.claude" ] || command -v claude >/dev/null 2>&1 || return 0
  info "configuring Claude Code pre-tool-use hook ($file)"

  mkdir -p "$HOME/.claude"
  [ -f "$file" ] || echo '{}' > "$file"
  if ! is_valid_json "$file"; then
    warn "$file is not valid JSON; backing it up and starting fresh"
    cp "$file" "$file.bak.$(date +%s)"
    echo '{}' > "$file"
  fi

  local hook_cmd="$DEST/$BINARY_NAME hook pre-tool-use"
  local tmp; tmp="$TMP/claude-settings.json"

  if command -v jq >/dev/null 2>&1; then
    jq --arg cmd "$hook_cmd" '
      .hooks //= {} |
      .hooks.PreToolUse //= [] |
      .hooks.PreToolUse |= (
        map(select(((.hooks // [{}])[0].command // "") | contains("warpline") | not))
        + [{matcher: "*", hooks: [{type: "command", command: $cmd}]}]
      )
    ' "$file" > "$tmp" 2>/dev/null || { warn "jq merge failed; leaving $file untouched"; return 0; }
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$file" "$tmp" "$hook_cmd" <<'PYEOF' || { warn "python3 merge failed; leaving file untouched"; return 0; }
import json, sys
src, dst, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src) as f:
    data = json.load(f)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
pre[:] = [e for e in pre if "warpline" not in ((e.get("hooks") or [{}])[0].get("command", ""))]
pre.append({"matcher": "*", "hooks": [{"type": "command", "command": cmd}]})
with open(dst, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
  else
    warn "neither jq nor python3 found; skipping Claude Code hook config"
    return 0
  fi

  if is_valid_json "$tmp"; then
    cp "$file" "$file.bak.$(date +%s)"
    mv "$tmp" "$file"
    ok "Claude Code hook configured"
  else
    err "hook merge produced invalid JSON; leaving $file untouched"
  fi
}

configure_codex_hook() {
  local file="$HOME/.codex/config.json"
  [ -d "$HOME/.codex" ] || command -v codex >/dev/null 2>&1 || return 0
  info "configuring Codex CLI pre-tool-use hook ($file)"
  # NOTE: Codex's hook schema is assumed (flat "hooks" array keyed by "id") —
  # confirm against the installed Codex version's actual config surface and
  # adjust the jq filter / python block below if it differs. Kept soft-fail
  # (warn, not die) for exactly this reason.

  mkdir -p "$HOME/.codex"
  [ -f "$file" ] || echo '{}' > "$file"
  if ! is_valid_json "$file"; then
    warn "$file is not valid JSON; backing it up and starting fresh"
    cp "$file" "$file.bak.$(date +%s)"
    echo '{}' > "$file"
  fi

  local hook_cmd="$DEST/$BINARY_NAME hook pre-tool-use"
  local tmp; tmp="$TMP/codex-config.json"

  if command -v jq >/dev/null 2>&1; then
    jq --arg cmd "$hook_cmd" '
      .hooks //= [] |
      .hooks |= (
        map(select(.id != "warpline-pre-tool-use"))
        + [{id: "warpline-pre-tool-use", event: "pre-tool-use", command: $cmd}]
      )
    ' "$file" > "$tmp" 2>/dev/null || { warn "jq merge failed; leaving $file untouched"; return 0; }
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "$file" "$tmp" "$hook_cmd" <<'PYEOF' || { warn "python3 merge failed; leaving file untouched"; return 0; }
import json, sys
src, dst, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src) as f:
    data = json.load(f)
hooks = data.setdefault("hooks", [])
hooks[:] = [e for e in hooks if e.get("id") != "warpline-pre-tool-use"]
hooks.append({"id": "warpline-pre-tool-use", "event": "pre-tool-use", "command": cmd})
with open(dst, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
  else
    warn "neither jq nor python3 found; skipping Codex CLI hook config"
    return 0
  fi

  if is_valid_json "$tmp"; then
    cp "$file" "$file.bak.$(date +%s)"
    mv "$tmp" "$file"
    ok "Codex CLI hook configured"
  else
    err "hook merge produced invalid JSON; leaving $file untouched"
  fi
}

configure_agent_hooks() {
  configure_claude_hook
  configure_codex_hook
}

# ---------------------------------------------------------------------------
# final summary box
# ---------------------------------------------------------------------------
draw_box() {
  local title="$1"; shift
  local lines=("$@") width=0 l
  for l in "$title" "${lines[@]}"; do [ ${#l} -gt "$width" ] && width=${#l}; done
  width=$((width + 2))
  local bar; bar=$(printf '─%.0s' $(seq 1 "$width"))
  printf '┌%s┐\n' "$bar"
  printf '│ %-*s│\n' "$width" "$title"
  printf '├%s┤\n' "$bar"
  for l in "${lines[@]}"; do printf '│ %-*s│\n' "$width" "$l"; done
  printf '└%s┘\n' "$bar"
}

print_summary() {
  draw_box "warpline $VERSION installed" \
    "binary:       $DEST/$BINARY_NAME" \
    "completions:  $BASH_COMPLETION_DIR, $ZSH_COMPLETION_DIR, $FISH_COMPLETION_DIR" \
    "claude hook:  $HOME/.claude/settings.json (backups: *.bak.<timestamp>)" \
    "codex hook:   $HOME/.codex/config.json (backups: *.bak.<timestamp>)"
  echo
  info "uninstall: rm $DEST/$BINARY_NAME"
  info "           rm $BASH_COMPLETION_DIR/$BINARY_NAME $ZSH_COMPLETION_DIR/_$BINARY_NAME $FISH_COMPLETION_DIR/$BINARY_NAME.fish"
  info "           remove the warpline-tagged entry from ~/.claude/settings.json and ~/.codex/config.json"
}

# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------
run_self_test() {
  timeout 1 "$DEST/$BINARY_NAME" --version >/dev/null 2>&1 || die "self-test: binary did not run"
  is_valid_json "$HOME/.claude/settings.json" 2>/dev/null || warn "self-test: Claude settings not present/valid (may be expected)"
  ok "self-test passed"
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
main() {
  detect_platform
  resolve_version
  preflight

  if [ "$FORCE" = 0 ] && [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" = "$VERSION" ]; then
    ok "warpline $VERSION already installed at $DEST/$BINARY_NAME"
  else
    acquire_lock "${TMPDIR:-/tmp}/warpline-install.lock" 120 \
      || die "another warpline install is already running; try again shortly"
    download_and_install
    install_completions
    check_path
  fi

  # agent hook config always re-runs, even on the short-circuit path above —
  # it's idempotent, and a version bump shouldn't require a --force just to
  # pick up a hook config change.
  configure_agent_hooks

  [ "$SELF_TEST" = 1 ] && run_self_test

  print_summary
}

main "$@"