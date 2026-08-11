---
name: curl-bash-installer
description: >-
  Write a production-grade `curl | bash` installer (install.sh one-liner) for a CLI tool —
  platform→target-triple detection, version-resolution fallback chain, checksum + Sigstore
  verification, atomic locking, build-from-source fallback, shell completions, AI-agent
  hook auto-config, and uninstall. Use when creating install.sh, a curl-pipe-bash installer,
  or a one-liner install for a Rust/TS/Go CLI. Self-contained (real bash inline).
---

<!-- Distilled 2026-07-04 from the retired 30-file `installer-workmanship` skill, whose method was to
     study-and-emulate two upstream install.sh exemplars that don't exist on this machine. This version
     is self-contained: real snippets inline, no external line-refs. Locking + OS-detection re-anchored
     on the operator's own ~/SITES/pro-gate/lib/pro-gate-lib.sh (production flock-first/mkdir-fallback).
     Agent auto-config + draw_box + uninstall: references/PATTERNS.md -->

# curl | bash Installer

> **Core principle.** An installer runs on a stranger's machine, once, unattended, piped from the
> internet into `bash`. It must fail loudly and early, verify what it downloads, never corrupt an
> existing install, work behind a corporate proxy and in an airgap, and leave the machine either fully
> installed or untouched — never half. Reference exemplar for real cross-platform locking/OS-detection:
> `~/SITES/pro-gate/lib/pro-gate-lib.sh`.

## The 14 non-negotiables

1. **Fail-safe prelude** — `set -euo pipefail`; `umask 022`; `trap cleanup EXIT` right after temp-dir creation; `shopt -s lastpipe 2>/dev/null` if you pipe into `read`.
2. **Documented curl one-liner** — header comment shows `curl -fsSL ".../install.sh?$(date +%s)" | bash` (cache-buster) and lists every flag.
3. **Proxy support** — `HTTPS_PROXY`→`HTTP_PROXY`→`PROXY_ARGS=(--proxy …)` array, passed to *every* curl call.
4. **Platform detection** — OS+arch → Rust target triple (prefer `musl` on Linux for static portability); WSL detected and *warned*, never blocked.
5. **Preflight** — disk space (`df -Pk`), write perms, existing-install version, network reachability; fail early with a clear message.
6. **Atomic locking** — `flock`-first with `mkdir` spinlock fallback (macOS has no `flock`), stale-PID self-heal via `kill -0`.
7. **Checksum** — SHA256, dual-tool (`sha256sum` then `shasum -a 256`); skip only on explicit `--no-verify`.
8. **Signature** — Sigstore/cosign: **soft-skip** if `cosign` absent, **hard-fail** if present and verification fails.
9. **Build-from-source fallback** — last download tier: `rustup` (if needed) → `git clone --depth 1` → `cargo build --release`.
10. **Shell completions** — bash/zsh/fish into XDG paths, not hardcoded rc-file guesses.
11. **`--offline TARBALL`** airgap mode — no network calls, install straight from a local tarball.
12. **Final summary** — one box: what changed, backup locations, per-component status.
13. **Uninstall instructions** — printed at the end of every run (binary path, completions, hooks).
14. **Flags** — `--quiet` (errors only), `--force` (reinstall over existing), `--no-color`/`--no-gum`, all in `--help`.

## Build plan

```
Scaffold   1. header + curl one-liner + full flag list   2. safety prelude   3. constants + flag parser + --help
Core       4. platform→triple (+WSL warn)   5. proxy→PROXY_ARGS   6. version resolution (5-tier)
           7. artifact URL + 4-tier download fallback   8. preflight   9. acquire lock (stale-PID heal)
           10. download→extract→locate binary   11. verify SHA256 + Sigstore   12. install -m 0755; release lock; cleanup
Integrate  13. completions (XDG)   14. PATH check (--easy-mode appends rc)   15. service (systemd/launchd) if daemon
           16. detect installed AI agents   17. configure hooks/skills idempotently (JSON-merge + timestamped backup)
Polish     18. --offline / --verify self-test   19. final summary box   20. uninstall instructions
```

## Core snippets (real, self-contained)

**Platform → Rust triple (+ WSL warn).** Prefer `musl` on Linux — static, no glibc skew.
```bash
detect_platform() {
  OS=$(uname -s | tr 'A-Z' 'a-z'); ARCH=$(uname -m)
  case "$ARCH" in x86_64|amd64) ARCH=x86_64 ;; arm64|aarch64) ARCH=aarch64 ;; esac
  case "${OS}-${ARCH}" in
    linux-x86_64)   TARGET=x86_64-unknown-linux-musl ;;
    linux-aarch64)  TARGET=aarch64-unknown-linux-musl ;;
    darwin-x86_64)  TARGET=x86_64-apple-darwin ;;
    darwin-aarch64) TARGET=aarch64-apple-darwin ;;
    *) warn "no prebuilt for ${OS}/${ARCH}; building from source"; FROM_SOURCE=1 ;;
  esac
  [[ "$OS" == linux ]] && grep -qi microsoft /proc/version 2>/dev/null && warn "WSL detected — some features may need extra config"
}
```

**Proxy array** — expands to nothing when empty, so every curl call stays unconditional:
```bash
PROXY_ARGS=()
[[ -n "${HTTPS_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTPS_PROXY")
[[ -z "${HTTPS_PROXY:-}" && -n "${HTTP_PROXY:-}" ]] && PROXY_ARGS=(--proxy "$HTTP_PROXY")
# curl -fsSL "${PROXY_ARGS[@]}" "$url"    (NO_PROXY is honored by curl natively)
```

**Version resolution — 5-tier fallback:**
```bash
resolve_version() {
  [[ -n "$VERSION" ]] && return 0                                          # 1. CLI flag/env
  [[ -f Cargo.toml ]] && VERSION=$(awk -F\" '/^version[[:space:]]*=/{print $2; exit}' Cargo.toml)
  [[ -z "$VERSION" && -f package.json ]] && VERSION=$(grep -m1 '"version"' package.json | sed -E 's/.*"([0-9][^"]*)".*/\1/')
  [[ -n "$VERSION" ]] && return 0                                          # 2. manifest
  VERSION=$(curl -fsSL --connect-timeout 5 "${PROXY_ARGS[@]}" \
    "https://api.github.com/repos/$OWNER/$REPO/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"v?([^"]+)".*/\1/')
  [[ -n "$VERSION" ]] && return 0                                          # 3. GitHub API
  VERSION=$(curl -fsSL -o /dev/null -w '%{url_effective}' "${PROXY_ARGS[@]}" \
    "https://github.com/$OWNER/$REPO/releases/latest" 2>/dev/null | sed -E 's|.*/tag/v?||')
  [[ -n "$VERSION" ]] || VERSION="$FALLBACK_VERSION"                       # 4. redirect  5. hardcoded
}
```

**Download — 4-tier fallback → source:**
```bash
download_and_install() {
  for url in \
    "https://github.com/$OWNER/$REPO/releases/download/v$VERSION/$REPO-v$VERSION-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$TARGET.tar.gz" \
    "https://github.com/$OWNER/$REPO/releases/latest/download/$REPO-$OS-$ARCH.tar.gz"; do
    if curl -fsSL "${PROXY_ARGS[@]}" "$url" -o "$TMP/artifact.tar.gz" 2>/dev/null; then
      verify_checksum "$TMP/artifact.tar.gz" "$EXPECTED_SHA" && extract_and_install "$TMP/artifact.tar.gz" && return 0
    fi
  done
  warn "no prebuilt binary; building from source"; rm -rf "$TMP"; build_from_source   # rm: no temp leak
}
```

**Checksum + Sigstore** — the asymmetry is the point: *missing tool = warn+continue; tool present + bad sig = hard fail.*
```bash
verify_checksum() {  # $1=file $2=expected
  local a
  if command -v sha256sum >/dev/null 2>&1; then a=$(sha256sum "$1" | cut -d' ' -f1)
  elif command -v shasum  >/dev/null 2>&1; then a=$(shasum -a 256 "$1" | cut -d' ' -f1)
  else warn "no SHA256 tool; skipping checksum"; return 0; fi
  [[ "$a" == "$2" ]] && { ok "SHA256 verified"; return 0; } || { err "checksum mismatch (want $2 got $a)"; return 1; }
}
verify_sigstore() {  # $1=file $2=bundle_url
  command -v cosign >/dev/null 2>&1 || { warn "cosign absent; skipping signature check"; return 0; }
  curl -fsSL "${PROXY_ARGS[@]}" "$2" -o "$TMP/sig.json" 2>/dev/null || { warn "no sigstore bundle; skipping"; return 0; }
  cosign verify-blob --bundle "$TMP/sig.json" --certificate-identity-regexp "$COSIGN_ID_RE" \
    --certificate-oidc-issuer "$COSIGN_ISSUER" "$1" 2>/dev/null && ok "signature verified" || { err "Sigstore verification FAILED"; return 1; }
}
```

**Atomic lock** — from your own `pro-gate-lib.sh` (flock-first, mkdir fallback, stale-PID heal). Note the brace-scoping: a bare `exec 9>f 2>/dev/null` permanently redirects the *caller's* stderr — brace it.
```bash
acquire_lock() {  # $1=lockfile $2=wait_s
  local lf="$1" w="${2:-2400}"
  if command -v flock >/dev/null 2>&1; then
    { exec 9>>"$lf"; } 2>/dev/null && { flock -w "$w" 9; return $?; }; return 0
  fi
  local d="${lf}.d" start; start=$(date +%s)
  while ! mkdir "$d" 2>/dev/null; do
    local opid; opid=$(cat "$d/pid" 2>/dev/null || true)
    [[ -n "$opid" ]] && ! kill -0 "$opid" 2>/dev/null && { rm -rf "$d"; continue; }
    (( $(date +%s) - start >= w )) && return 1; sleep 2
  done
  echo $$ > "$d/pid"; trap 'rm -rf "'"$d"'"' EXIT
}
```

**Install (atomic) + output stack.** `install -m 0755` beats `cp && chmod` (no wrong-perms window).
```bash
extract_and_install() {
  case "$1" in *.tar.gz|*.tgz) tar -xzf "$1" -C "$TMP" ;; *.tar.xz) tar -xJf "$1" -C "$TMP" ;; *.zip) unzip -q "$1" -d "$TMP" ;; esac
  local bin; bin=$(find "$TMP" -name "$BINARY_NAME" -type f | head -1)
  [[ -n "$bin" ]] || { err "binary not found in archive"; return 1; }
  install -m 0755 "$bin" "$DEST/$BINARY_NAME"; ok "installed $BINARY_NAME → $DEST"
}
# gum-if-TTY, ANSI fallback, honor NO_COLOR + non-TTY; err() never gated by --quiet
HAS_GUM=0; command -v gum >/dev/null && [ -t 1 ] && HAS_GUM=1
[ -n "${NO_COLOR:-}" ] && NO_GUM=1
_log() { [ "${QUIET:-0}" = 1 ] && [ "$1" != err ] && return 0
  if [ "$HAS_GUM" = 1 ] && [ "${NO_GUM:-0}" = 0 ]; then gum style --foreground "$2" "$3 ${*:4}"
  else printf '\033[%sm%s\033[0m %s\n' "$2" "$3" "${*:4}"; fi; }
info() { _log info 39 '->' "$@"; }
ok()   { _log ok   42 '✓'  "$@"; }
warn() { _log warn 214 '⚠' "$@"; }
err()  { _log err  196 '✗' "$@"; }
```

## Agent auto-config, draw_box, uninstall/service

If the CLI plugs into AI agents (Claude Code / Codex / Gemini / Cursor), the installer should detect which
are present and wire its hook into their settings **idempotently** — grep-for-already → timestamped backup →
`jq`-or-Python3 merge → roll back on failure. The full detection + JSON-merge-with-backup pattern (the
load-bearing reusable piece), the `draw_box` implementation, and the uninstall/service snippets are in
[references/PATTERNS.md](references/PATTERNS.md).

## Anti-patterns

- **Skipping checksum verification** — supply-chain risk; always verify SHA256.
- **`gnu` target on Linux** — not portable; use `musl` (static).
- **Editing settings/JSON without a backup**, or with `sed`/`awk` — `cp file file.bak.$(date +%s)` first, merge with `jq`/Python3.
- **Assuming `~/.local/bin` is on PATH** — check `:$PATH:`, offer to fix, don't assume.
- **Hard-failing on optional features** (missing cosign/gum) — warn and continue.
- **`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback.
- **Raw unstyled output** — route through `info/ok/warn/err`; honor `NO_COLOR`/non-TTY so piped/CI output has no ANSI.
- **`<tool> --version` with no timeout** — wrap in `timeout 1` (some CLIs hang).
- **Ignoring proxy env** — `PROXY_ARGS` on every curl call.

## Pre-ship checklist

- [ ] `set -euo pipefail` + `umask 022` + `trap cleanup EXIT`; `--help` documents every flag
- [ ] platform covers linux/darwin × x86_64/aarch64; WSL warned not blocked
- [ ] preflight (disk/perms/network/existing); atomic lock with stale-PID heal
- [ ] SHA256 (dual tool) + Sigstore (soft-skip / hard-fail); build-from-source fallback works
- [ ] completions (bash/zsh/fish, XDG); agent hooks idempotent (re-run = no dup hooks)
- [ ] proxy on every network call; final summary box + uninstall printed
- [ ] tested: `--quiet` (errors only), `--no-color`/`--no-gum` (ANSI fallback), `--offline <tarball>` (no network)
- [ ] version-already-installed short-circuits download but STILL re-runs agent config (idempotent, not a full no-op)
