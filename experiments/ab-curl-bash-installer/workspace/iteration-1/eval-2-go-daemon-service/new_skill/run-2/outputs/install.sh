#!/usr/bin/env bash
# moorhen installer
#
#   curl -fsSL "https://raw.githubusercontent.com/hovlabs/moorhen/main/install.sh?$(date +%s)" | bash
#
# Flags (env overrides in parens):
#   --version VERSION   install a specific version (MOORHEN_VERSION)   [default: latest release]
#   --dest DIR           install directory (MOORHEN_INSTALL_DIR)        [default: $HOME/.local/bin]
#   --force              reinstall even if the resolved version is already installed
#   --no-verify           skip SHA256 checksum + Sigstore signature verification
#   --no-service          do not install/start the systemd/launchd service
#   --offline TARBALL      install from a local tarball, no network access
#   --easy-mode             append the install dir to PATH in ~/.bashrc and ~/.zshrc if missing
#   --quiet                errors only
#   --no-color               disable ANSI colors and gum styling
#   --no-gum                 disable gum styling only (colors still used)
#   --uninstall               remove the binary, service, and completions, then exit
#   -h, --help                show full help and exit
#
# Other env overrides: HTTPS_PROXY, HTTP_PROXY, NO_COLOR

set -euo pipefail
umask 022
shopt -s lastpipe 2>/dev/null || true

TMP="$(mktemp -d "${TMPDIR:-/tmp}/moorhen-install.XXXXXX")"
LOCK_D=""
cleanup() {
  rm -rf "$TMP"
  [[ -n "${LOCK_D:-}" ]] && rm -rf "$LOCK_D"
}
trap cleanup EXIT

# --- constants ---------------------------------------------------------
OWNER="hovlabs"
REPO="moorhen"
BINARY_NAME="moorhen"
SERVICE_NAME="moorhen"
LAUNCHD_LABEL="com.hovlabs.moorhen"
FALLBACK_VERSION="1.0.0"   # bump on each tagged release; last-resort tier if GitHub is unreachable
COSIGN_ID_RE="^https://github\.com/${OWNER}/${REPO}/\.github/workflows/"
COSIGN_ISSUER="https://token.actions.githubusercontent.com"

# --- flag defaults -------------------------------------------------------
VERSION="${MOORHEN_VERSION:-}"
DEST="${MOORHEN_INSTALL_DIR:-$HOME/.local/bin}"
FORCE=0
NO_VERIFY=0
NO_SERVICE=0
OFFLINE_TARBALL=""
EASY_MODE=0
QUIET=0
NO_GUM=0
DO_UNINSTALL=0
ALREADY_CURRENT=0

[[ -n "${NO_COLOR:-}" ]] && NO_GUM=1
HAS_GUM=0
command -v gum >/dev/null 2>&1 && [[ -t 1 ]] && HAS_GUM=1

# --- output helpers --------------------------------------------------------
_log() {
  [[ "${QUIET:-0}" == 1 && "$1" != err ]] && return 0
  if [[ "$HAS_GUM" == 1 && "${NO_GUM:-0}" == 0 ]]; then
    gum style --foreground "$2" "$3 ${*:4}"
  else
    printf '\033[%sm%s\033[0m %s\n' "$2" "$3" "${*:4}"
  fi
}
info() { _log info 39  '->' "$@"; }
ok()   { _log ok   42  '✓'  "$@"; }
warn() { _log warn 214 '⚠'  "$@"; }
err()  { _log err  196 '✗'  "$@"; }

print_help() {
  cat <<'EOF'
moorhen installer

Usage: install.sh [OPTIONS]

  --version VERSION   install a specific version (default: latest release)
  --dest DIR          install directory (default: $HOME/.local/bin)
  --force             reinstall even if the resolved version is already installed
  --no-verify         skip SHA256 checksum and Sigstore signature verification
  --no-service        do not install/start the systemd/launchd service
  --offline TARBALL   install from a local tarball, no network access
  --easy-mode         append the install dir to PATH in ~/.bashrc / ~/.zshrc
  --quiet             suppress non-error output
  --no-color          disable ANSI colors and gum styling
  --no-gum            disable gum styling only
  --uninstall         remove the binary, service, and completions, then exit
  -h, --help          show this help and exit

Environment overrides: MOORHEN_VERSION, MOORHEN_INSTALL_DIR, HTTPS_PROXY, HTTP_PROXY, NO_COLOR
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --no-verify) NO_VERIFY=1; shift ;;
    --no-service) NO_SERVICE=1; shift ;;
    --offline) OFFLINE_TARBALL="$2"; shift 2 ;;
    --easy-mode) EASY_MODE=1; shift ;;
    --quiet) QUIET=1; shift ;;
    --no-color) NO_GUM=1; shift ;;
    --no-gum) NO_GUM=1; shift ;;
    --uninstall) DO_UNINSTALL=1; shift ;;
    -h|--help) print_help; exit 0 ;;
    *) err "unknown flag: $1"; print_help; exit 1 ;;
  esac
done

# --- proxy ---------------------------------------------------------------
PROXY_ARGS=()
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTPS_PROXY")
elif [[ -n "${HTTP_PROXY:-}" ]]; then
  PROXY_ARGS=(--proxy "$HTTP_PROXY")
fi

# --- platform --------------------------------------------------------------
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z')
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64|amd64) ARCH=amd64 ;;
    arm64|aarch64) ARCH=arm64 ;;
    *) err "unsupported architecture: $ARCH"; exit 1 ;;
  esac
  case "$OS" in
    linux|darwin) ;;
    *) err "unsupported OS: $OS (moorhen supports linux and darwin)"; exit 1 ;;
  esac
  if [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    warn "WSL detected — systemd --user services need WSL systemd support (wsl.conf [boot] systemd=true) or the daemon won't start on login"
  fi
}

# --- version resolution ------------------------------------------------
# no local-manifest tier: this is a standalone curl|bash installer, not run from
# a moorhen checkout, so there's no Cargo.toml/package.json equivalent to read.
resolve_version() {
  [[ -n "${VERSION:-}" ]] && return 0
  info "resolving latest moorhen version..."
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/') || true
  [[ -n "$VERSION" ]] && return 0
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null \
    | sed -E 's|.*/tag/v?||') || true
  [[ -n "$VERSION" ]] && return 0
  VERSION="$FALLBACK_VERSION"
  warn "could not resolve latest version from GitHub; falling back to hardcoded $VERSION"
}

# --- preflight -----------------------------------------------------------
preflight() {
  local avail_kb
  avail_kb=$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2{print $4}') || true
  if [[ -n "$avail_kb" ]] && (( avail_kb < 51200 )); then
    err "insufficient disk space in \$HOME: need ~50MB, have $((avail_kb/1024))MB"
    exit 1
  fi

  mkdir -p "$DEST"
  if [[ ! -w "$DEST" ]]; then
    err "cannot write to $DEST — check permissions or pass --dest DIR"
    exit 1
  fi

  if [[ -x "$DEST/$BINARY_NAME" && "$FORCE" != 1 ]]; then
    local cur
    cur=$(timeout 1 "$DEST/$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
    if [[ -n "$cur" && "$cur" == "$VERSION" ]]; then
      ALREADY_CURRENT=1
      info "moorhen $VERSION is already installed — skipping download (use --force to reinstall)"
    fi
  fi

  if [[ "$ALREADY_CURRENT" != 1 ]]; then
    if ! curl -fsSL --connect-timeout 5 -o /dev/null "${PROXY_ARGS[@]}" "https://github.com" 2>/dev/null; then
      err "cannot reach github.com — check network/proxy settings, or use --offline TARBALL"
      exit 1
    fi
  fi
}

# --- lock ------------------------------------------------------------------
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }
    return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    if [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null; then
      rm -rf "$d"; continue
    fi
    if (( $(date +%s) - start >= w )); then return 1; fi
    sleep 2
  done
  echo $$ > "$d/pid"
  LOCK_D="$d"
}

# --- download / verify / install ---------------------------------------
artifact_name() { printf 'moorhen_%s_%s_%s.tar.gz' "$VERSION" "$OS" "$ARCH"; }

fetch_checksums() {  # $1=tag
  curl -fsSL "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/download/$1/checksums.txt" \
    -o "$TMP/checksums.txt" 2>/dev/null
}

verify_checksum_from_manifest() {  # $1=file $2=manifest $3=basename
  local a expected
  expected=$(awk -v n="$3" '$2==n{print $1; exit}' "$2" 2>/dev/null) || true
  if [[ -z "$expected" ]]; then
    warn "no checksum entry for $3 in checksums.txt"
    return 1
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    a=$(sha256sum "$1" | cut -d' ' -f1) || true
  elif command -v shasum >/dev/null 2>&1; then
    a=$(shasum -a 256 "$1" | cut -d' ' -f1) || true
  else
    warn "no SHA256 tool found; skipping checksum verification"
    return 0
  fi
  if [[ -n "$a" && "$a" == "$expected" ]]; then
    ok "SHA256 verified"
    return 0
  fi
  err "checksum mismatch for $3 (want $expected got ${a:-<none>})"
  return 1
}

verify_checksums_signature() {  # $1=manifest_path $2=tag
  local manifest="$1" tag="$2"
  command -v cosign >/dev/null 2>&1 || { warn "cosign not found; skipping checksums.txt signature check"; return 0; }
  local bundle="$TMP/checksums.txt.sigstore.json"
  if ! curl -fsSL "${PROXY_ARGS[@]}" \
      "https://github.com/$OWNER/$REPO/releases/download/$tag/checksums.txt.sigstore.json" \
      -o "$bundle" 2>/dev/null; then
    warn "no sigstore bundle for checksums.txt; skipping signature check"
    return 0
  fi
  if cosign verify-blob --bundle "$bundle" \
      --certificate-identity-regexp "$COSIGN_ID_RE" \
      --certificate-oidc-issuer "$COSIGN_ISSUER" \
      "$manifest" 2>/dev/null; then
    ok "checksums.txt signature verified"
  else
    err "Sigstore verification of checksums.txt FAILED"
    return 1
  fi
}

extract_and_install() {
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;;
    *.tar.xz) tar -xJf "$1" -C "$TMP" ;;
    *.zip) unzip -q "$1" -d "$TMP" ;;
    *) err "unrecognized archive format: $1"; return 1 ;;
  esac
  local bin
  bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  if [[ -z "$bin" ]]; then
    err "binary '$BINARY_NAME' not found in archive"
    return 1
  fi
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"
  ok "installed $BINARY_NAME → $DEST/$BINARY_NAME"
}

build_from_source() {
  if ! command -v go >/dev/null 2>&1; then
    err "go toolchain not found — install Go (https://go.dev/dl/) to build from source, or use a supported platform"
    exit 1
  fi
  info "building $BINARY_NAME from source (this may take a minute)..."
  local src="$TMP/src"
  git clone --depth 1 --branch "v$VERSION" "https://github.com/$OWNER/$REPO.git" "$src" 2>/dev/null \
    || { rm -rf "$src"; git clone --depth 1 "https://github.com/$OWNER/$REPO.git" "$src"; }
  (
    cd "$src"
    CGO_ENABLED=0 go build -trimpath -o "$TMP/$BINARY_NAME" . 2>/dev/null \
      || CGO_ENABLED=0 go build -trimpath -o "$TMP/$BINARY_NAME" "./cmd/$BINARY_NAME"
  ) || true
  if [[ ! -x "$TMP/$BINARY_NAME" ]]; then
    err "build failed — $BINARY_NAME binary was not produced"
    exit 1
  fi
  install -m 0755 "$TMP/$BINARY_NAME" "$DEST/$BINARY_NAME"
  ok "built and installed $BINARY_NAME from source → $DEST/$BINARY_NAME"
}

download_and_install() {
  local name; name=$(artifact_name)
  local tag
  for tag in "v$VERSION" "$VERSION"; do
    if curl -fsSL "${PROXY_ARGS[@]}" \
        "https://github.com/$OWNER/$REPO/releases/download/$tag/$name" \
        -o "$TMP/$name" 2>/dev/null; then
      if [[ "$NO_VERIFY" == 1 ]]; then
        warn "--no-verify passed; skipping checksum and signature verification"
      else
        if ! fetch_checksums "$tag"; then
          warn "could not fetch checksums.txt for $tag; trying next source"
          continue
        fi
        verify_checksums_signature "$TMP/checksums.txt" "$tag" \
          || { warn "signature check failed for $tag; trying next source"; continue; }
        verify_checksum_from_manifest "$TMP/$name" "$TMP/checksums.txt" "$name" \
          || { warn "checksum verification failed for $tag; trying next source"; continue; }
      fi
      extract_and_install "$TMP/$name"
      return 0
    fi
  done
  warn "no prebuilt binary found for $name; building from source"
  build_from_source
}

# --- service -------------------------------------------------------------
install_service() {
  [[ "$NO_SERVICE" == 1 ]] && { info "skipping service setup (--no-service)"; return 0; }
  case "$OS" in
    linux) install_service_systemd ;;
    darwin) install_service_launchd ;;
  esac
}

install_service_systemd() {
  if ! command -v systemctl >/dev/null 2>&1; then
    warn "systemctl not found; skipping service setup — run '$BINARY_NAME' manually"
    return 0
  fi
  local unit_dir="$HOME/.config/systemd/user"
  mkdir -p "$unit_dir"
  cat > "$unit_dir/${SERVICE_NAME}.service" <<EOF
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
  if command -v loginctl >/dev/null 2>&1; then
    loginctl enable-linger "$USER" 2>/dev/null || true
  fi
  ok "systemd user service installed and started (${SERVICE_NAME}.service)"
}

install_service_launchd() {
  local plist_dir="$HOME/Library/LaunchAgents"
  mkdir -p "$plist_dir" "$HOME/Library/Logs"
  local plist="$plist_dir/${LAUNCHD_LABEL}.plist"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>$DEST/$BINARY_NAME</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/${SERVICE_NAME}.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/${SERVICE_NAME}.err.log</string>
</dict>
</plist>
EOF
  if ! launchctl bootstrap "gui/$(id -u)" "$plist" 2>/dev/null; then
    launchctl unload "$plist" 2>/dev/null || true
    launchctl load -w "$plist"
  fi
  ok "launchd agent installed and started (${LAUNCHD_LABEL})"
}

uninstall_service() {
  case "$OS" in
    linux)
      if command -v systemctl >/dev/null 2>&1; then
        systemctl --user disable --now "${SERVICE_NAME}.service" 2>/dev/null || true
        rm -f "$HOME/.config/systemd/user/${SERVICE_NAME}.service"
        systemctl --user daemon-reload 2>/dev/null || true
      fi
      ;;
    darwin)
      local plist="$HOME/Library/LaunchAgents/${LAUNCHD_LABEL}.plist"
      if [[ -f "$plist" ]]; then
        launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || launchctl unload "$plist" 2>/dev/null || true
        rm -f "$plist"
      fi
      ;;
  esac
}

# --- completions + PATH ---------------------------------------------------
install_completions() {
  command -v "$DEST/$BINARY_NAME" >/dev/null 2>&1 || return 0
  timeout 1 "$DEST/$BINARY_NAME" completion bash >/dev/null 2>&1 || return 0
  local bash_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  local zsh_dir="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
  local fish_dir="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
  mkdir -p "$bash_dir" "$zsh_dir" "$fish_dir"
  "$DEST/$BINARY_NAME" completion bash > "$bash_dir/$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completion zsh  > "$zsh_dir/_$BINARY_NAME" 2>/dev/null || true
  "$DEST/$BINARY_NAME" completion fish > "$fish_dir/$BINARY_NAME.fish" 2>/dev/null || true
  ok "shell completions installed"
}

check_path() {
  case ":$PATH:" in
    *":$DEST:"*) return 0 ;;
  esac
  if [[ "$EASY_MODE" == 1 ]]; then
    local rc
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
      [[ -f "$rc" ]] || continue
      grep -qF "$DEST" "$rc" 2>/dev/null || {
        printf '\nexport PATH="%s:$PATH"\n' "$DEST" >> "$rc"
        info "added $DEST to PATH in $rc (restart your shell)"
      }
    done
  else
    warn "$DEST is not on your PATH — add it, or re-run with --easy-mode"
  fi
}

# --- summary box + uninstall ----------------------------------------------
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

uninstall() {
  rm -f "$DEST/$BINARY_NAME"
  rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/$BINARY_NAME" \
        "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_$BINARY_NAME" \
        "${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions/$BINARY_NAME.fish"
  uninstall_service
  ok "uninstalled $BINARY_NAME (binary, service, completions). Config left in place."
}

# --- main ------------------------------------------------------------------
LOCKFILE="${XDG_CACHE_HOME:-$HOME/.cache}/moorhen/install.lock"
mkdir -p "$(dirname "$LOCKFILE")"

detect_platform

if [[ "$DO_UNINSTALL" == 1 ]]; then
  uninstall
  exit 0
fi

if [[ -n "$OFFLINE_TARBALL" ]]; then
  [[ -f "$OFFLINE_TARBALL" ]] || { err "offline tarball not found: $OFFLINE_TARBALL"; exit 1; }
  mkdir -p "$DEST"
  acquire_lock "$LOCKFILE" 60 || { err "could not acquire install lock"; exit 1; }
  if [[ "$NO_VERIFY" != 1 && -f "${OFFLINE_TARBALL}.sha256" ]]; then
    expected_sha=$(awk '{print $1}' "${OFFLINE_TARBALL}.sha256")
    verify_checksum_from_manifest "$OFFLINE_TARBALL" \
      <(printf '%s  %s\n' "$expected_sha" "$(basename "$OFFLINE_TARBALL")") \
      "$(basename "$OFFLINE_TARBALL")" || exit 1
  else
    warn "offline mode: no sidecar .sha256 file found (or --no-verify passed); skipping verification"
  fi
  extract_and_install "$OFFLINE_TARBALL"
else
  resolve_version
  preflight
  acquire_lock "$LOCKFILE" 2400 || { err "could not acquire install lock (another install running?)"; exit 1; }
  [[ "$ALREADY_CURRENT" != 1 ]] && download_and_install
fi

install_service
install_completions
check_path

svc_status="service: skipped (--no-service)"
if [[ "$NO_SERVICE" != 1 ]]; then
  case "$OS" in
    linux)  svc_status="service: ${SERVICE_NAME}.service (systemd --user; enabled + started)" ;;
    darwin) svc_status="service: ${LAUNCHD_LABEL} (launchd; loaded + started)" ;;
  esac
fi

draw_box 42 \
  "moorhen installed successfully" \
  "" \
  "binary:   $DEST/$BINARY_NAME" \
  "$svc_status" \
  "version:  ${VERSION:-unknown (offline install)}" \
  "" \
  "Uninstall: bash install.sh --uninstall" \
  "  (removes binary, completions, and the ${SERVICE_NAME} service; config is left in place)"