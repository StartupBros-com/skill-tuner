#!/usr/bin/env bash
# skill-tuner preflight doctor (Unit 6): pro-gate-style ok/warn/blocking
# checks to run before a live eval so a missing `claude` CLI or a broken
# repo layout fails fast and legibly instead of mid-battery. Warnings are
# informational -- they never block a run; only a "blocking" finding does.
set -uo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." >/dev/null 2>&1 && pwd)"

blocking=0

ok()   { printf '  \xe2\x9c\x93 %s\n' "$1"; }
warn() { printf '  ! %s\n' "$1"; }
fail() { printf '  \xe2\x9c\x97 %s\n' "$1"; blocking=1; }

echo "skill-tuner doctor"
echo "==================="

# --------------------------------------------------------------------------
# 1. claude CLI on PATH
# --------------------------------------------------------------------------
echo
echo "claude CLI"
claude_present=0
if command -v claude >/dev/null 2>&1; then
  ok "claude found on PATH: $(command -v claude)"
  claude_present=1
else
  fail "claude not found on PATH -- install/auth the Claude Code CLI before running evals"
fi

# --------------------------------------------------------------------------
# 2. claude --help mentions the two flags the adapter's command line relies
#    on (--setting-sources, --output-format). Warn (never block) when this
#    can't be determined -- a --help wording change is not the same class
#    of failure as claude being entirely absent.
# --------------------------------------------------------------------------
if [ "$claude_present" -eq 1 ]; then
  help_output="$(claude --help 2>&1)"
  help_status=$?
  if [ "$help_status" -ne 0 ] || [ -z "$help_output" ]; then
    warn "could not run 'claude --help' to check adapter flags (not determinable)"
  else
    missing_flags=()
    for flag in "--setting-sources" "--output-format"; do
      if ! grep -qF -- "$flag" <<<"$help_output"; then
        missing_flags+=("$flag")
      fi
    done
    if [ "${#missing_flags[@]}" -eq 0 ]; then
      ok "claude --help mentions --setting-sources and --output-format"
    else
      warn "claude --help does not mention: ${missing_flags[*]} (adapter command may not match this claude version)"
    fi
  fi
else
  warn "--setting-sources/--output-format check skipped (claude not determinable)"
fi

# --------------------------------------------------------------------------
# 3. python3 >= 3.9 (tune.py/routing_parity.py/probe.py syntax and typing
#    features assume it)
# --------------------------------------------------------------------------
echo
echo "python3"
if command -v python3 >/dev/null 2>&1; then
  py_version="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)"
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    ok "python3 ${py_version} >= 3.9"
  else
    fail "python3 ${py_version:-unknown} is older than the required 3.9"
  fi
else
  fail "python3 not found on PATH"
fi

# --------------------------------------------------------------------------
# 4. repo layout sane: plugin.json parses, SKILL.md present
# --------------------------------------------------------------------------
echo
echo "repo layout"
plugin_json="${REPO_ROOT}/.claude-plugin/plugin.json"
if [ -f "$plugin_json" ]; then
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$plugin_json" >/dev/null 2>&1; then
    ok "plugin.json present and parses: ${plugin_json}"
  else
    fail "plugin.json present but does not parse as JSON: ${plugin_json}"
  fi
else
  fail "plugin.json missing: ${plugin_json}"
fi

skill_md="${REPO_ROOT}/skills/skill-tuner/SKILL.md"
if [ -f "$skill_md" ]; then
  ok "SKILL.md present: ${skill_md}"
else
  fail "SKILL.md missing: ${skill_md}"
fi

# --------------------------------------------------------------------------
echo
if [ "$blocking" -eq 1 ]; then
  printf 'Result: BLOCKING -- fix the \xe2\x9c\x97 items above before running live evals.\n'
  exit 1
fi
echo "Result: OK (any ! warnings above are non-blocking)."
exit 0
