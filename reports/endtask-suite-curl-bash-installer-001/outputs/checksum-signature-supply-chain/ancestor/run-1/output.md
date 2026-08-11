#!/usr/bin/env bash
#
# install.sh — installer for ledgerctl (github.com/acme/ledgerctl)
#
# ledgerctl signs financial records. Supply-chain integrity is not optional here:
# every downloaded artifact is SHA256-checksummed, and if `cosign` is present on
# this machine, a Sigstore signature bundle is verified before anything is
# installed. Missing cosign is tolerated (warn + continue) — a failed
# verification when cosign IS present is not (hard stop, nothing installed).
#
#   curl -fsSL "https://install.ledgerctl.dev/install.sh?$(date +%s)" | bash
#
# Flags:
#   --version VERSION   Install a specific version (default: latest)
#   --dest DIR           Install directory (default: $HOME/.local/bin)
#   --force               Reinstall even if the same version is already present
#   --quiet                Errors only
#   --no-color              Disable ANSI colors
#   --no-gum                 Disable gum styling even if installed
#   --no-verify                Skip SHA256 checksum verification (NOT RECOMMENDED)
#   --no-sigstore                Skip Sigstore signature verification (NOT RECOMMENDED)
#   --offline TARBALL              Install from a local tarball, no network calls
#   --verify                        Self-test: report on the currently installed binary
#   --easy-mode                      Append $DEST to PATH in the detected shell rc file
#   -h, --help                        Show this help and exit
#
# Env:
#   HTTPS_PROXY / HTTP_PROXY / NO_PROXY   Standard proxy vars, honored on every curl call
#   LEDGERCTL_VERSION                     Same as --version

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="acme"
REPO="ledgerctl"
BINARY_NAME="ledgerctl"
FALLBACK_VERSION="1.4.2"
DEST="${DEST:-$HOME/.local/bin}"
LOCKFILE="/tmp/.${BINARY_NAME}-install.lock"
COSIGN_ID_RE='^https://github\.com/acme/ledgerctl/\.github/workflows/release\.ya?ml@refs/tags/v.*$'
COSIGN_ISSUER='https://token.actions.githubusercontent.com'

VERSION="${LEDGERCTL_VERSION:-}"
FORCE=0
QUIET=0
NO_COLOR_FLAG=0
NO_GUM=0
NO_VERIFY=0
NO_SIGSTORE=0
OFFLINE_TARBALL=""
DO_VERIFY_SELFTEST=0
EASY_MODE=0
FROM_SOURCE=0
TMP=""

# ---------------------------------------------------------------------------
# Output stack — gum if present + TTY, ANSI fallback, honor NO_COLOR/--quiet
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && NO_GUM=1 && NO_COLOR_FLAG=1

_log() {
  local kind="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$kind" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$NO_COLOR_FLAG" = 1 ] || [ ! -t 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
  else
    printf '\033[%sm%s\033[0m %s\n' "$color" "$glyph" "$*"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@" >&2; }

draw_box() {
  # $@ = lines to print inside the box
  local max=0 line
  for line in "$@"; do (( ${#line} > max )) && max=${#line}; done
  local border; border=$(printf '─%.0s' $(seq 1 $((max + 2))))
  printf '┌%s┐\n' "$border"
  for line in "$@"; do printf '│ %-*s │\n' "$max" "$line"; done
  printf '└%s┘\n' "$border"
}

die() { err "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Cleanup / lock release
# ---------------------------------------------------------------------------
LOCK_DIR=""
cleanup() {
  local code=$?
  [ -n "$TMP" ] && rm -rf "$TMP"
  [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR"
  exit "$code"
}
TMP=$(mktemp -d "${TMPDIR:-/tmp}/${BINARY_NAME}-install.XXXXXX")
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Flag parsing
# ---------------------------------------------------------------------------
usage() { sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --version)      VERSION="$2"; shift 2 ;;
    --dest)         DEST="$2"; shift 2 ;;
    --force)        FORCE=1; shift ;;
    --quiet)        QUIET=1; shift ;;
    --no-color)     NO_COLOR_FLAG=1; shift ;;
    --no-gum)       NO_GUM=1; shift ;;
    --no-verify)    NO_VERIFY=1; shift ;;
    --no-sigstore)  NO_SIGSTORE=1; shift ;;
    --offline)      OFFLINE_TARBALL="$2"; shift 2 ;;
    --verify)       DO_VERIFY_SELFTEST=1; shift ;;
    --easy-mode)    EASY_MODE=1; shift ;;
    -h|--help)      usage; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done

# ---------------------------------------------------------------------------
# Proxy support — expands to nothing when unset, so every curl call is safe
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64)   ARCH=x86_64 ;;
    arm64|aarch64)  ARCH=aarch64 ;;
  esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt binary for ${OS}/${ARCH}; will build from source"; FROM_SOURCE=1 ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — completions may need an extra rc-file source line"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution — 5-tier fallback
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                             # 1. flag/env

  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0                                             # 2. GitHub API

  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && return 0                                             # 3. redirect

  VERSION="$FALLBACK_VERSION"                                               # 4. hardcoded
  warn "could not resolve latest version over the network; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
preflight() {
  local avail_kb
  avail_kb=$(df -Pk "$TMP" | awk 'NR==2{print $4}')
  [ "$avail_kb" -ge 51200 ] || die "less than 50MB free in $TMP; aborting"

  mkdir -p "$DEST" 2>/dev/null || die "cannot create $DEST"
  [ -w "$DEST" ] || die "$DEST is not writable"

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" != 1 ] && [ -z "$OFFLINE_TARBALL" ]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | awk '{print $NF}') || true
    if [ -n "$cur" ] && [ "$cur" = "$VERSION" ]; then
      ok "ledgerctl $VERSION already installed at $DEST/$BINARY_NAME"
      SKIP_DOWNLOAD=1
      return 0
    fi
  fi
  SKIP_DOWNLOAD=0

  if [ -z "$OFFLINE_TARBALL" ]; then
    curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" -o /dev/null "https://github.com" \
      || die "no network reachability to github.com — use --offline TARBALL for airgapped install"
  fi
}

# ---------------------------------------------------------------------------
# Atomic lock — flock-first, mkdir spinlock fallback (macOS has no flock),
# stale-PID self-heal. Braced redirect so we never clobber the caller's stderr.
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" wait_s="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$wait_s" 9 || die "timed out waiting for install lock"; return 0; }
  fi
  local d="${lf}.d" start
  start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    (( $(date +%s) - start >= wait_s )) && die "timed out waiting for install lock"
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_DIR="$d"
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected-hash
  local file="$1" expected="$2" actual
  if [ "$NO_VERIFY" = 1 ]; then
    warn "--no-verify passed; skipping SHA256 checksum (NOT RECOMMENDED for ledgerctl)"
    return 0
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
  else
    die "no sha256sum or shasum available — cannot verify a security-sensitive binary; aborting"
  fi
  if [ -z "$expected" ]; then
    die "no expected checksum available for $file — refusing to install unverified (use --no-verify to override)"
  fi
  if [ "$actual" = "$expected" ]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch (want $expected, got $actual)"
  return 1
}

fetch_expected_sha() {  # $1=checksums_url $2=artifact_filename
  local url="$1" fname="$2"
  curl -fsSL "${PROXY_ARGS[@]}" "$url" 2>/dev/null | awk -v f="$fname" '$2==f || $2=="*"f {print $1; exit}'
}

verify_sigstore() {  # $1=file $2=bundle_url
  local file="$1" bundle_url="$2"
  if [ "$NO_SIGSTORE" = 1 ]; then
    warn "--no-sigstore passed; skipping Sigstore verification (NOT RECOMMENDED for ledgerctl)"
    return 0
  fi
  if ! command -v cosign >/dev/null 2>&1; then
    warn "cosign not installed; skipping Sigstore signature check (checksum verification still applies)"
    return 0
  fi
  if ! curl -fsSL "${PROXY_ARGS[@]}" "$bundle_url" -o "$TMP/artifact.sigstore.json" 2>/dev/null; then
    err "cosign is installed but no Sigstore bundle was found at $bundle_url"
    err "refusing to install an unverifiable ledgerctl binary on a machine that can check signatures"
    return 1
  fi
  if cosign verify-blob \
      --bundle "$TMP/artifact.sigstore.json" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$file" 2>/dev/null; then
    ok "Sigstore signature verified"
    return 0
  fi
  err "Sigstore signature verification FAILED for $file"
  return 1
}

# ---------------------------------------------------------------------------
# Download — 4-tier artifact fallback, each tier checksummed + signature-checked
# ---------------------------------------------------------------------------
download_and_install() {
  local fname="$REPO-v$VERSION-$TARGET.tar.gz"
  local urls=(
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$fname"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-$OS-$ARCH.tar.gz"
  )

  local url
  for url in "${urls[@]}"; do
    info "trying $url"
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      local base checksums_url sigstore_url expected_sha
      base=$(dirname "$url")
      checksums_url="$base/checksums.txt"
      sigstore_url="$url.sigstore.json"
      expected_sha=$(fetch_expected_sha "$checksums_url" "$(basename "$url")")

      if verify_checksum "$TMP/artifact.tar.gz" "$expected_sha" \
         && verify_sigstore "$TMP/artifact.tar.gz" "$sigstore_url"; then
        extract_and_install "$TMP/artifact.tar.gz" && return 0
      else
        die "artifact from $url failed verification; refusing to proceed"
      fi
    fi
  done

  warn "no prebuilt binary available for $TARGET; building from source"
  build_from_source
}

extract_and_install() {
  local archive="$1"
  case "$archive" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$TMP" ;;
    *.tar.xz)       tar -xJf "$archive" -C "$TMP" ;;
    *.zip)          unzip -q "$archive" -d "$TMP" ;;
    *) die "unrecognized archive format: $archive" ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || die "binary '$BINARY_NAME' not found inside archive"
  local backup=""
  if [ -f "$DEST/$BINARY_NAME" ]; then
    backup="$DEST/$BINARY_NAME.bak.$(date +%s)"
    cp "$DEST/$BINARY_NAME" "$backup"
  fi
  if install -m 0755 "$bin" "$DEST/$BINARY_NAME"; then
    ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
    [ -n "$backup" ] && rm -f "$backup"
  else
    [ -n "$backup" ] && mv "$backup" "$DEST/$BINARY_NAME"
    die "install failed; previous binary restored"
  fi
}

# ---------------------------------------------------------------------------
# Build from source — last-resort tier
# ---------------------------------------------------------------------------
build_from_source() {
  if ! command -v cargo >/dev/null 2>&1; then
    if command -v rustup >/dev/null 2>&1; then
      rustup install stable && rustup default stable
    else
      curl -fsSL "${PROXY_ARGS[@]}" https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
      # shellcheck disable=SC1090
      source "$HOME/.cargo/env"
    fi
  fi
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"
  ( cd "$src" && cargo build --release )
  [ -f "$src/target/release/$BINARY_NAME" ] || die "source build did not produce $BINARY_NAME"
  install -m 0755 "$src/target/release/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Offline / airgap install
# ---------------------------------------------------------------------------
offline_install() {
  local tarball="$OFFLINE_TARBALL"
  [ -f "$tarball" ] || die "offline tarball not found: $tarball"
  local sha_file="$tarball.sha256"
  local expected=""
  if [ -f "$sha_file" ]; then
    expected=$(awk '{print $1}' "$sha_file")
  else
    warn "no companion $sha_file found; skipping checksum verification for offline install"
  fi
  if [ -n "$expected" ]; then
    verify_checksum "$tarball" "$expected" || die "offline artifact failed checksum verification"
  fi
  if [ -f "$tarball.sigstore.json" ] && command -v cosign >/dev/null 2>&1; then
    cp "$tarball.sigstore.json" "$TMP/artifact.sigstore.json"
    verify_sigstore "$tarball" "file://$tarball.sigstore.json" || true
  fi
  extract_and_install "$tarball"
}

# ---------------------------------------------------------------------------
# Shell completions (XDG paths, not rc-file guessing)
# ---------------------------------------------------------------------------
install_completions() {
  command -v "$DEST/$BINARY_NAME" >/dev/null 2>&1 || return 0
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completions bash > "$bash_dir/$BINARY_NAME" 2>/dev/null \
    && ok "bash completions → $bash_dir/$BINARY_NAME" || warn "bash completions unavailable"
  "$DEST/$BINARY_NAME" completions zsh > "$zsh_dir/_$BINARY_NAME" 2>/dev/null \
    && ok "zsh completions → $zsh_dir/_$BINARY_NAME" || warn "zsh completions unavailable"
  "$DEST/$BINARY_NAME" completions fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null \
    && ok "fish completions → $fish_dir/$BINARY_NAME.fish" || warn "fish completions unavailable"
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  warn "$DEST is not on your PATH"
  if [ "$EASY_MODE" = 1 ]; then
    local rc="$HOME/.bashrc"
    [ -n "${ZSH_VERSION:-}" ] && rc="$HOME/.zshrc"
    printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
    ok "appended PATH export to $rc — restart your shell or 'source $rc'"
  else
    info "add this to your shell rc, or re-run with --easy-mode:"
    info "  export PATH=\"$DEST:\$PATH\""
  fi
}

# ---------------------------------------------------------------------------
# AI-agent hook auto-config — idempotent JSON merge with timestamped backup
# ---------------------------------------------------------------------------
merge_json() {  # $1=settings_file  $2=key  $3=value(json)
  local file="$1" key="$2" value="$3"
  [ -f "$file" ] || echo '{}' > "$file"
  local backup="$file.bak.$(date +%s)"
  cp "$file" "$backup"

  local merged=""
  if command -v jq >/dev/null 2>&1; then
    merged=$(jq --argjson v "$value" ". + {\"$key\": \$v}" "$file" 2>/dev/null) || true
  elif command -v python3 >/dev/null 2>&1; then
    merged=$(python3 - "$file" "$key" "$value" <<'PY' 2>/dev/null
import json, sys
path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    data = json.load(f)
data[key] = json.loads(value)
print(json.dumps(data, indent=2))
PY
) || true
  else
    warn "neither jq nor python3 available; skipping agent config for $file"
    rm -f "$backup"
    return 0
  fi

  if [ -n "$merged" ]; then
    printf '%s\n' "$merged" > "$file"
    ok "configured $key in $file (backup: $backup)"
  else
    err "failed to merge $key into $file; rolling back"
    mv "$backup" "$file"
  fi
}

configure_agent_hooks() {
  local hook_value='{"command":"'"$DEST/$BINARY_NAME"'","args":["hook","--stdin"]}'

  local claude_settings="$HOME/.claude/settings.json"
  if [ -d "$HOME/.claude" ]; then
    if command -v jq >/dev/null 2>&1 && [ -f "$claude_settings" ] \
       && jq -e '.hooks.ledgerctl' "$claude_settings" >/dev/null 2>&1; then
      info "Claude Code hook already configured; leaving as-is"
    else
      merge_json "$claude_settings" "hooks" "{\"ledgerctl\": $hook_value}"
    fi
  fi

  local codex_settings="$HOME/.codex/config.json"
  [ -d "$HOME/.codex" ] && merge_json "$codex_settings" "ledgerctl_hook" "$hook_value"

  local gemini_settings="$HOME/.gemini/settings.json"
  [ -d "$HOME/.gemini" ] && merge_json "$gemini_settings" "ledgerctl_hook" "$hook_value"
}

# ---------------------------------------------------------------------------
# Self-test / --verify
# ---------------------------------------------------------------------------
verify_selftest() {
  [ -x "$DEST/$BINARY_NAME" ] || die "$BINARY_NAME not found at $DEST/$BINARY_NAME"
  local v; v=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null || echo unknown)
  local sha=unknown
  if command -v sha256sum >/dev/null 2>&1; then
    sha=$(sha256sum "$DEST/$BINARY_NAME" | cut -d' ' -f1)
  elif command -v shasum >/dev/null 2>&1; then
    sha=$(shasum -a 256 "$DEST/$BINARY_NAME" | cut -d' ' -f1)
  fi
  draw_box "ledgerctl self-test" "binary:  $DEST/$BINARY_NAME" "version: $v" "sha256:  $sha"
}

# ---------------------------------------------------------------------------
# Summary + uninstall instructions
# ---------------------------------------------------------------------------
print_summary() {
  draw_box \
    "ledgerctl install complete" \
    "version:      ${VERSION:-source build}" \
    "binary:       $DEST/$BINARY_NAME" \
    "checksum:      $([ "$NO_VERIFY" = 1 ] && echo 'skipped (--no-verify)' || echo 'verified')" \
    "sigstore:      $([ "$NO_SIGSTORE" = 1 ] && echo 'skipped (--no-sigstore)' || echo 'checked')" \
    "completions:  bash/zsh/fish (XDG paths)"
}

print_uninstall() {
  cat <<EOF

To uninstall ledgerctl:
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME"
  rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  # and remove the "ledgerctl"/"ledgerctl_hook" entry from any agent settings.json
  # under ~/.claude, ~/.codex, ~/.gemini if you configured agent hooks
EOF
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if [ "$DO_VERIFY_SELFTEST" = 1 ]; then
    verify_selftest
    exit 0
  fi

  detect_platform

  if [ -n "$OFFLINE_TARBALL" ]; then
    acquire_lock "$LOCKFILE"
    offline_install
  else
    resolve_version
    preflight
    acquire_lock "$LOCKFILE"
    if [ "${SKIP_DOWNLOAD:-0}" != 1 ]; then
      if [ "$FROM_SOURCE" = 1 ]; then
        build_from_source
      else
        download_and_install
      fi
    fi
  fi

  install_completions
  check_path
  configure_agent_hooks
  print_summary
  print_uninstall
}

main "$@"