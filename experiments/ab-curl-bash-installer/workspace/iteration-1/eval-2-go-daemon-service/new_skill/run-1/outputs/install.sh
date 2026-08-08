#!/usr/bin/env bash
#
# moorhen installer — installs the moorhen agent binary and registers it as a
# background service (systemd --user on Linux, launchd agent on macOS).
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/moorhen/main/install.sh?$(date +%s)" | bash
#
# Flags (see also: install.sh --help):
#   -v, --version VERSION   install a specific release (default: latest)
#   -d, --dest DIR          install directory (default: $HOME/.local/bin)
#   -f, --force             reinstall even if the requested version is already installed
#   -q, --quiet             errors only
#       --no-color          disable ANSI colors (plain output)
#       --no-gum            disable gum styling even if installed
#       --no-verify         skip SHA256 / Sigstore verification (not recommended)
#       --no-service        skip installing/starting the background service
#       --offline TARBALL   install from a local tarball, no network calls
#       --easy-mode         append the install dir to PATH in your shell rc if missing
#       --verify             run installer self-diagnostics only, no changes made
#       --uninstall         remove moorhen, its service, and completions
#   -h, --help              show this help and exit
#
set -euo pipefail
umask 022

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OWNER="hovlabs"
REPO="moorhen"
BINARY_NAME="moorhen"
SERVICE_NAME="moorhen"                 # systemd --user unit: moorhen.service
SERVICE_LABEL="com.hovlabs.moorhen"    # launchd label / plist filename
FALLBACK_VERSION="1.0.0"               # last-resort version if all resolution tiers fail
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

VERSION="${MOORHEN_VERSION:-}"
DEST="${MOORHEN_INSTALL_DIR:-$HOME/.local/bin}"
QUIET=0
FORCE=0
NO_VERIFY=0
NO_SERVICE=0
NO_GUM=0
PLAIN=0
OFFLINE_TARBALL=""
EASY_MODE=0
VERIFY_ONLY=0
DO_UNINSTALL=0
FROM_SOURCE=0
ALREADY_INSTALLED=0

[ -n "${NO_COLOR:-}" ] && PLAIN=1
[ -t 1 ] || PLAIN=1

TMP=""
LOCKFILE=""
LOCK_HELD=0

# ---------------------------------------------------------------------------
# Output stack — gum-if-TTY, ANSI fallback, plain fallback. Honors NO_COLOR /
# non-TTY / --quiet. err() is never gated by --quiet.
# ---------------------------------------------------------------------------
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [ -t 1 ] && HAS_GUM=1

_log() {
  local level="$1" color="$2" glyph="$3"; shift 3
  [ "$QUIET" = 1 ] && [ "$level" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "$NO_GUM" = 0 ] && [ "$PLAIN" = 0 ]; then
    gum style --foreground "$color" "$glyph $*"
  elif [ "$PLAIN" = 1 ]; then
    printf '%s %s\n' "$glyph" "$*"
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
# Flag parsing
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
moorhen installer

Usage: install.sh [options]

  -v, --version VERSION   install a specific release (default: latest)
  -d, --dest DIR          install directory (default: \$HOME/.local/bin)
  -f, --force             reinstall even if requested version is already installed
  -q, --quiet             errors only
      --no-color          disable ANSI colors (plain output)
      --no-gum            disable gum styling even if installed
      --no-verify         skip SHA256 / Sigstore verification (not recommended)
      --no-service        skip installing/starting the background service
      --offline TARBALL   install from a local tarball, no network calls
      --easy-mode         append the install dir to PATH in your shell rc if missing
      --verify             run installer self-diagnostics only, no changes made
      --uninstall         remove moorhen, its service, and completions
  -h, --help              show this help and exit
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    -v|--version) VERSION="$2"; shift 2 ;;
    -d|--dest) DEST="$2"; shift 2 ;;
    -f|--force) FORCE=1; shift ;;
    -q|--quiet) QUIET=1; shift ;;
    --no-color) PLAIN=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --no-service) NO_SERVICE=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --verify) VERIFY_ONLY=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown flag: $1 (see --help)" ;;
  esac
done

# ---------------------------------------------------------------------------
# Proxy support. dcurl wraps every network call so PROXY_ARGS is applied
# uniformly; routing through a helper (rather than inlining
# "${PROXY_ARGS[@]}" at each call site) avoids the classic bash <4.4
# "unbound variable" trap when `set -u` expands a zero-element array
# (still bash 3.2 on stock macOS).
# ---------------------------------------------------------------------------
PROXY_ARGS=()
[ -n "${HTTPS_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[ -z "${HTTPS_PROXY:-}" ] && [ -n "${HTTP_PROXY:-}" ] && PROXY_ARGS=(--proxy "$HTTP_PROXY")

dcurl() {
  if [ "${#PROXY_ARGS[@]}" -gt 0 ]; then
    curl "${PROXY_ARGS[@]}" "$@"
  else
    curl "$@"
  fi
}

# NO_PROXY is honored by curl natively.

with_timeout() {  # portable wrapper: stock macOS ships no `timeout`
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Temp dir + cleanup trap
# ---------------------------------------------------------------------------
TMP="$(mktemp -d "${TMPDIR:-/tmp}/moorhen-install.XXXXXX")"
cleanup() {
  local ec=$?
  [ "$LOCK_HELD" = 1 ] && release_lock "$LOCKFILE"
  rm -rf "$TMP"
  exit "$ec"
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Platform detection — Go build targets (goreleaser default GOOS/GOARCH
# names). Go binaries are statically linked already, so there's no
# musl/gnu split to worry about the way there is for Rust/cgo builds.
# ---------------------------------------------------------------------------
detect_platform() {
  OS="$(uname -s | tr 'A-Z' 'a-z')"
  local m; m="$(uname -m)"
  case "$m" in
    x86_64|amd64) ARCH=amd64 ;;
    arm64|aarch64) ARCH=arm64 ;;
    *) die "unsupported architecture: $m" ;;
  esac
  case "$OS" in
    linux|darwin) : ;;
    *) die "unsupported OS: $OS (moorhen supports linux and darwin)" ;;
  esac
  if [ "$OS" = linux ] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — the systemd --user service requires systemd enabled for this distro (see /etc/wsl.conf)"
  fi
}

# ---------------------------------------------------------------------------
# Version resolution
# ---------------------------------------------------------------------------
resolve_version() {
  [ -n "$VERSION" ] && return 0                                              # 1. flag/env

  if [ -n "$OFFLINE_TARBALL" ]; then
    VERSION="$FALLBACK_VERSION"                                             # offline: version is just a label
    return 0
  fi

  VERSION=$(dcurl -fsSL --connect-timeout 5 \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [ -n "$VERSION" ] && return 0                                              # 2. GitHub API

  VERSION=$(dcurl -fsSL -o /dev/null -w '%{url_effective}' \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [ -n "$VERSION" ] && return 0                                              # 3. redirect

  VERSION="$FALLBACK_VERSION"                                                # 4. hardcoded
  warn "could not resolve latest version from GitHub; falling back to $VERSION"
}

# ---------------------------------------------------------------------------
# Preflight — disk, perms, existing install, network
# ---------------------------------------------------------------------------
preflight() {
  mkdir -p "$DEST" 2>/dev/null || die "cannot create install dir: $DEST"
  [ -w "$DEST" ] || die "no write permission on install dir: $DEST"

  local avail_kb; avail_kb=$(df -Pk "$DEST" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail_kb" ] && [ "$avail_kb" -lt 51200 ]; then
    die "less than 50MB free at $DEST ($((avail_kb/1024))MB available)"
  fi

  if [ -x "$DEST/$BINARY_NAME" ] && [ "$FORCE" = 0 ]; then
    local current
    current=$(with_timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
    if [ -n "$current" ] && [ "$current" = "$VERSION" ]; then
      ALREADY_INSTALLED=1
      info "moorhen $VERSION already installed at $DEST/$BINARY_NAME (use --force to reinstall)"
    fi
  fi

  if [ -z "$OFFLINE_TARBALL" ]; then
    dcurl -fsSL -o /dev/null --connect-timeout 5 "https://github.com" \
      || die "cannot reach github.com — check network/proxy, or use --offline TARBALL"
  fi
}

# ---------------------------------------------------------------------------
# Atomic locking — flock-first, mkdir spinlock fallback (macOS has no
# flock), stale-PID self-heal.
# ---------------------------------------------------------------------------
acquire_lock() {
  local lf="$1" w="${2:-2400}"
  LOCKFILE="$lf"
  mkdir -p "$(dirname "$lf")" 2>/dev/null || true
  if command -v flock >/dev/null 2>&1; then
    if { exec 9>>"$lf"; } 2>/dev/null; then
      flock -w "$w" 9 && LOCK_HELD=1
      return $?
    fi
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [ -n "$opid" ] && ! kill -0 "$opid" 2>/dev/null; then rm -rf "$d"; continue; fi
    local now; now=$(date +%s)
    [ $((now - start)) -ge "$w" ] && return 1
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_HELD=1
}
release_lock() {
  local lf="$1"
  command -v flock >/dev/null 2>&1 && { exec 9>&- ; } 2>/dev/null || true
  rm -rf "${lf}.d" 2>/dev/null || true
  LOCK_HELD=0
}

# ---------------------------------------------------------------------------
# Checksum + Sigstore verification. The asymmetry is the point: a missing
# tool warns and continues; a present tool with a bad signature hard-fails.
# ---------------------------------------------------------------------------
verify_checksum() {  # $1=file $2=expected
  [ "$NO_VERIFY" = 1 ] && { warn "checksum verification skipped (--no-verify)"; return 0; }
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no sha256sum/shasum found; skipping checksum"; return 0
  fi
  if [ "$a" = "$2" ]; then ok "SHA256 verified"; return 0
  else err "checksum mismatch for $1 (want $2, got $a)"; return 1
  fi
}

checksum_for() {  # $1=filename $2=checksums.txt path
  awk -v f="$1" '$2==f{print $1; found=1} END{exit !found}' "$2"
}

verify_sigstore() {  # $1=checksums.txt path $2=release tag (e.g. v1.2.3)
  [ "$NO_VERIFY" = 1 ] && return 0
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping signature check"; return 0; }
  local base="https://github.com/$OWNER/$REPO/releases/download/$2"
  dcurl -fsSL "$base/checksums.txt.pem" -o "$TMP/checksums.txt.pem" 2>/dev/null \
    || { warn "no Sigstore cert published for $2; skipping"; return 0; }
  dcurl -fsSL "$base/checksums.txt.sig" -o "$TMP/checksums.txt.sig" 2>/dev/null \
    || { warn "no Sigstore signature published for $2; skipping"; return 0; }
  if cosign verify-blob \
      --certificate "$TMP/checksums.txt.pem" \
      --signature "$TMP/checksums.txt.sig" \
      --certificate-identity-regexp "^https://github.com/$OWNER/$REPO/.*@refs/tags/$2\$" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$1" >/dev/null 2>&1; then
    ok "Sigstore signature verified"
  else
    err "Sigstore verification FAILED for checksums.txt (release may be compromised)"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Extract + install (atomic — install -m 0755 beats cp && chmod, no
# wrong-perms window)
# ---------------------------------------------------------------------------
extract_and_install() {
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$1" -C "$TMP" ;;
    *.zip) unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin; bin=$(find "$TMP" -maxdepth 3 -name "$BINARY_NAME" -type f | head -1)
  [ -n "$bin" ] || { err "binary '$BINARY_NAME' not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME $VERSION → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Build-from-source fallback (last download tier)
# ---------------------------------------------------------------------------
build_from_source() {
  FROM_SOURCE=1
  command -v git >/dev/null 2>&1 || die "git not found; cannot build from source (install git or use a supported platform)"
  command -v go  >/dev/null 2>&1 || die "go toolchain not found; install Go 1.21+ or use a supported platform"
  info "building $BINARY_NAME from source (v$VERSION)"
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src" \
    || die "git clone failed"
  local pkg="."
  [ -d "$src/cmd/$BINARY_NAME" ] && pkg="./cmd/$BINARY_NAME"
  ( cd "$src" && CGO_ENABLED=0 go build -trimpath -o "$TMP/$BINARY_NAME" "$pkg" ) \
    || die "go build failed"
  [ -x "$TMP/$BINARY_NAME" ] || die "build did not produce a binary"
  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

# ---------------------------------------------------------------------------
# Download — tries tag naming with and without the "v" prefix, verifying
# each candidate (checksum + optional Sigstore) before install. A failed
# candidate is discarded, not trusted; falls through to build-from-source.
# ---------------------------------------------------------------------------
download_and_install() {
  local artifact="${REPO}_${VERSION}_${OS}_${ARCH}.tar.gz"
  local tag_candidates=("v$VERSION" "$VERSION")
  local tag base_url expected

  for tag in "${tag_candidates[@]}"; do
    base_url="https://github.com/$OWNER/$REPO/releases/download/$tag"
    info "trying $base_url/$artifact"
    dcurl -fsSL "$base_url/$artifact" -o "$TMP/artifact.tar.gz" 2>/dev/null || continue

    if [ "$NO_VERIFY" = 1 ]; then
      warn "verification skipped (--no-verify)"
      extract_and_install "$TMP/artifact.tar.gz" && return 0
      continue
    fi

    if ! dcurl -fsSL "$base_url/checksums.txt" -o "$TMP/checksums.txt" 2>/dev/null; then
      warn "no checksums.txt at $tag; skipping this release candidate"
      continue
    fi
    verify_sigstore "$TMP/checksums.txt" "$tag" || return 1
    expected=$(checksum_for "$artifact" "$TMP/checksums.txt") \
      || { warn "$artifact not listed in checksums.txt at $tag; skipping"; continue; }
    verify_checksum "$TMP/artifact.tar.gz" "$expected" || return 1
    extract_and_install "$TMP/artifact.tar.gz" && return 0
  done

  warn "no verified prebuilt binary available; building from source"
  build_from_source
}

# ---------------------------------------------------------------------------
# Airgap mode — no network calls, install straight from a local tarball
# ---------------------------------------------------------------------------
install_offline() {
  [ -f "$OFFLINE_TARBALL" ] || die "--offline tarball not found: $OFFLINE_TARBALL"
  info "installing from local tarball (offline, no network calls)"
  if [ "$NO_VERIFY" = 0 ]; then
    local sums; sums="$(dirname "$OFFLINE_TARBALL")/checksums.txt"
    if [ -f "$sums" ]; then
      local expected; expected=$(checksum_for "$(basename "$OFFLINE_TARBALL")" "$sums") || true
      if [ -n "$expected" ]; then
        verify_checksum "$OFFLINE_TARBALL" "$expected" || die "checksum verification failed"
      else
        warn "$(basename "$OFFLINE_TARBALL") not listed in $sums; skipping checksum"
      fi
    else
      warn "no checksums.txt alongside offline tarball; skipping checksum"
    fi
  fi
  extract_and_install "$OFFLINE_TARBALL"
}

# ---------------------------------------------------------------------------
# Shell completions (XDG paths, not hardcoded rc-file guesses)
# ---------------------------------------------------------------------------
install_completions() {
  [ -x "$DEST/$BINARY_NAME" ] || return 0

  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir" 2>/dev/null || true

  if with_timeout 1 "$DEST/$BINARY_NAME" completion bash >"$bash_dir/$BINARY_NAME" 2>/dev/null; then
    with_timeout 1 "$DEST/$BINARY_NAME" completion zsh  >"$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
    with_timeout 1 "$DEST/$BINARY_NAME" completion fish >"$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
    ok "shell completions installed (bash/zsh/fish)"
  else
    warn "binary does not support 'completion' subcommand; skipping"
    rm -f "$bash_dir/$BINARY_NAME"
  fi
}

# ---------------------------------------------------------------------------
# PATH check
# ---------------------------------------------------------------------------
check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [ "$EASY_MODE" = 1 ]; then
    local rc=""
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      *) rc="$HOME/.profile" ;;
    esac
    local line="export PATH=\"$DEST:\$PATH\""
    if [ -f "$rc" ] && grep -qF "$line" "$rc" 2>/dev/null; then
      info "PATH already configured in $rc"
    else
      printf '\n# added by moorhen installer\n%s\n' "$line" >> "$rc"
      ok "added $DEST to PATH in $rc (restart your shell or: source $rc)"
    fi
  else
    warn "$DEST is not on PATH — add it manually, or re-run with --easy-mode"
  fi
}

# ---------------------------------------------------------------------------
# Background service — systemd --user on Linux, launchd agent on macOS.
# Started immediately and enabled at login on both.
# ---------------------------------------------------------------------------
install_service() {
  [ "$NO_SERVICE" = 1 ] && { info "skipping service setup (--no-service)"; return 0; }
  case "$OS" in
    linux) install_service_systemd ;;
    darwin) install_service_launchd ;;
  esac
}

install_service_systemd() {
  command -v systemctl >/dev/null 2>&1 || { warn "systemctl not found; skipping service setup"; return 0; }
  local unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  local unit="$unit_dir/${SERVICE_NAME}.service"
  cat > "$unit" <<EOF
[Unit]
Description=moorhen agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$DEST/$BINARY_NAME
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now "${SERVICE_NAME}.service"
  ok "systemd --user service installed and started (${SERVICE_NAME}.service)"
}

install_service_launchd() {
  local dir="$HOME/Library/LaunchAgents"
  mkdir -p "$dir" "$HOME/Library/Logs"
  local plist="$dir/${SERVICE_LABEL}.plist"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$SERVICE_LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$DEST/$BINARY_NAME</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/${BINARY_NAME}.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/${BINARY_NAME}.err.log</string>
</dict>
</plist>
EOF
  launchctl unload "$plist" >/dev/null 2>&1 || true
  launchctl load -w "$plist"
  ok "launchd agent installed and started ($SERVICE_LABEL)"
}

# uninstall_service is defined only when a systemd/launchd service was
# installed — uninstall() guards it with declare -F, or set -e would kill
# the uninstall between deleting the binary and reporting success.
uninstall_service() {
  case "$OS" in
    linux)
      if command -v systemctl >/dev/null 2>&1; then
        systemctl --user disable --now "${SERVICE_NAME}.service" >/dev/null 2>&1 || true
        rm -f "$HOME/.config/systemd/user/${SERVICE_NAME}.service"
        systemctl --user daemon-reload >/dev/null 2>&1 || true
      fi
      ;;
    darwin)
      local plist="$HOME/Library/LaunchAgents/${SERVICE_LABEL}.plist"
      if [ -f "$plist" ]; then
        launchctl unload "$plist" >/dev/null 2>&1 || true
        rm -f "$plist"
      fi
      ;;
  esac
}

# ---------------------------------------------------------------------------
# Final summary box
# ---------------------------------------------------------------------------
draw_box() {  # $1=color, rest=lines
  local color="$1"; shift
  local lines=("$@") stripped=() max=0 esc; esc=$(printf '\033')
  local strip="s/${esc}\\[[0-9;]*m//g"
  local l s
  for l in "${lines[@]}"; do
    s=$(printf '%b' "$l" | LC_ALL=C sed "$strip")
    stripped+=("$s")
    [ "${#s}" -gt "$max" ] && max=${#s}
  done
  local inner=$((max + 4)) i idx=0
  if [ "$PLAIN" = 1 ]; then
    local border=""; for ((i = 0; i < inner; i++)); do border+="-"; done
    printf '+%s+\n' "$border"
    for l in "${lines[@]}"; do
      s="${stripped[$idx]}"; idx=$((idx + 1))
      printf '|  %s%*s  |\n' "$s" $((max - ${#s})) ''
    done
    printf '+%s+\n' "$border"
  else
    local border=""; for ((i = 0; i < inner; i++)); do border+="═"; done
    printf "\033[%sm╔%s╗\033[0m\n" "$color" "$border"
    for l in "${lines[@]}"; do
      s="${stripped[$idx]}"; idx=$((idx + 1))
      printf "\033[%sm║\033[0m  %b%*s  \033[%sm║\033[0m\n" "$color" "$l" $((max - ${#s})) '' "$color"
    done
    printf "\033[%sm╚%s╝\033[0m\n" "$color" "$border"
  fi
}

print_uninstall_instructions() {
  info "to uninstall: curl -fsSL \"https://raw.githubusercontent.com/$OWNER/$REPO/main/install.sh\" | bash -s -- --uninstall"
  info "  or manually: rm $DEST/$BINARY_NAME"
  case "$OS" in
    linux) info "  and: systemctl --user disable --now ${SERVICE_NAME}.service && rm ~/.config/systemd/user/${SERVICE_NAME}.service" ;;
    darwin) info "  and: launchctl unload ~/Library/LaunchAgents/${SERVICE_LABEL}.plist && rm ~/Library/LaunchAgents/${SERVICE_LABEL}.plist" ;;
  esac
  info "  agent hooks/config, if any, are left in place — remove manually if desired"
}

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  if declare -F uninstall_service >/dev/null; then uninstall_service; fi
  ok "uninstalled $BINARY_NAME (binary, completions, service)"
}

self_test() {
  info "platform: $OS/$ARCH"
  local tool
  for tool in curl tar install; do
    command -v "$tool" >/dev/null 2>&1 && ok "$tool found" || err "$tool MISSING (required)"
  done
  for tool in sha256sum shasum cosign flock git go systemctl launchctl gum; do
    command -v "$tool" >/dev/null 2>&1 && ok "$tool found (optional)" || warn "$tool not found (optional)"
  done
  if [ -d "$DEST" ]; then
    [ -w "$DEST" ] && ok "install dir writable: $DEST" || err "install dir not writable: $DEST"
  else
    local parent; parent=$(dirname "$DEST")
    [ -w "$parent" ] && ok "install dir does not exist yet but parent is writable: $DEST" || err "cannot create install dir: $DEST"
  fi
  if [ -z "$OFFLINE_TARBALL" ]; then
    dcurl -fsSL -o /dev/null --connect-timeout 5 https://github.com \
      && ok "network reachable" || warn "cannot reach github.com"
  fi
  info "self-test complete (no changes made)"
}

final_summary() {
  local lines=()
  lines+=("\033[1mmoorhen $VERSION\033[0m")
  lines+=("binary:      $DEST/$BINARY_NAME")
  if [ "$FROM_SOURCE" = 1 ]; then
    lines+=("source:      built from source")
  elif [ -n "$OFFLINE_TARBALL" ]; then
    lines+=("source:      local tarball (offline)")
  else
    lines+=("source:      release tarball ($OS/$ARCH)")
  fi
  if [ "$NO_SERVICE" = 1 ]; then
    lines+=("service:     skipped (--no-service)")
  elif [ "$OS" = linux ]; then
    lines+=("service:     systemd --user (${SERVICE_NAME}.service) — running, enabled at login")
  else
    lines+=("service:     launchd (${SERVICE_LABEL}) — running, enabled at login")
  fi
  lines+=("completions: bash/zsh/fish (if supported by the binary)")
  draw_box 42 "${lines[@]}"
  print_uninstall_instructions
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if [ "$DO_UNINSTALL" = 1 ]; then
    detect_platform
    uninstall
    exit 0
  fi

  detect_platform

  if [ "$VERIFY_ONLY" = 1 ]; then
    self_test
    exit 0
  fi

  resolve_version
  preflight
  acquire_lock "$DEST/.${BINARY_NAME}.lock" || die "could not acquire install lock (another install running?)"

  if [ -n "$OFFLINE_TARBALL" ]; then
    install_offline
  elif [ "$ALREADY_INSTALLED" = 1 ]; then
    info "reusing existing install; re-applying completions/service configuration"
  else
    download_and_install || die "installation failed"
  fi

  install_completions
  check_path
  install_service
  final_summary
}

main