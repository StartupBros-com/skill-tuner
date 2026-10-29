#!/usr/bin/env bash
# run-one.sh <run-root> <max-turns> <cap-seconds> - run one arm run (predeclare.md).
# Forked from claude/experiments/teardown-arms-2026-10-26/run-one.sh:
#   - env -i plus an allowlist, so this session's plugin dirs, job paths and settings never reach it;
#   - the fake CLI dir is first on PATH; CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 and a fresh CLAUDE_CONFIG_DIR;
#   - stream-json events land in events.jsonl; extract.py pulls init/result events and tool use;
#   - timeout -k kills a hung run; a watchdog kills a run with no assistant event after 600 s (stall.txt);
#   - exits non-zero when the invocation failed (extract.py's status line is the acceptance signal).
set -uo pipefail
R="$1"; TURNS="$2"; CAP="$3"
here="$(cd "$(dirname "$0")" && pwd)"
MODEL="${ARM_MODEL:-claude-sonnet-5-5}"
cd "$R/work" || exit 1
mkdir -p "$R/xdg-config" "$R/xdg-cache"
PROMPT="$(cat "$R/prompt.txt")"
start=$(date +%s)
timeout -k 30 "$CAP" env -i \
  HOME="$HOME" USER="$USER" LOGNAME="$USER" PATH="$R/bin:$PATH" LANG=C.UTF-8 TERM=dumb SHELL=/bin/bash \
  XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
  XDG_CONFIG_HOME="$R/xdg-config" XDG_CACHE_HOME="$R/xdg-cache" MISE_CONFIG_DIR="$HOME/.config/mise" \
  ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-}" ANTHROPIC_CUSTOM_HEADERS="${ANTHROPIC_CUSTOM_HEADERS:-}" \
  ${ANTHROPIC_API_KEY:+ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"} \
  CLAUDE_CONFIG_DIR="$R/cfg" CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 CLAUDE_CODE_MAX_RETRIES=20 \
  CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1 \
  claude -p "$PROMPT" --model "$MODEL" --max-turns "$TURNS" \
    --output-format stream-json --verbose \
    --allowedTools "Bash,Read,Glob,Grep,Write,Edit" \
    --permission-mode acceptEdits \
  > "$R/events.jsonl" 2> "$R/stderr.txt" &
tp=$!
(
  waited=0
  while [ $waited -lt 600 ]; do
    sleep 10; waited=$((waited + 10))
    kill -0 "$tp" 2>/dev/null || exit 0
    grep -q -F '"type":"assistant"' "$R/events.jsonl" && exit 0
  done
  echo "no assistant event after 600 s" > "$R/stall.txt"
  kill "$tp" 2>/dev/null
) &
wd=$!
wait "$tp"
rc=$?
kill "$wd" 2>/dev/null
end=$(date +%s)
echo "EXIT_CODE=$rc WALL_S=$((end - start)) CAP_S=$CAP MODEL=$MODEL TURNS=$TURNS" >> "$R/stderr.txt"
python3 -I "$here/extract.py" "$R" "$rc"
