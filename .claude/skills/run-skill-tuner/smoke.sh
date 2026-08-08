#!/usr/bin/env bash
# Drive skill-tuner's CLI end to end.
#
# The wrinkle that shapes this script: running this app for real spends
# money. Every eval subcommand shells out to `claude -p`, so a smoke test
# that exercised the whole surface would bill the person running it. Most of
# the CLI is reachable without spending anything -- verify and compare make
# zero model calls by design, the suite runs on a fake adapter, and the
# refuse-to-spend guards are observable precisely because they fire *before*
# the first call. That free surface is the default.
#
#   ./smoke.sh          free: ~10s, $0.00, no network
#   ./smoke.sh --live   adds one real probe against a scratch document (~$0.20)
#
# Run from the repo root. Exits non-zero on the first failure.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO" || exit 1
SCRIPTS="skills/skill-tuner/scripts"
LIVE=0
[ "${1:-}" = "--live" ] && LIVE=1

pass=0; fail=0
ok()   { printf '  \033[32mok\033[0m   %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  \033[31mFAIL\033[0m %s\n     %s\n' "$1" "${2:-}"; fail=$((fail+1)); }
step() { printf '\n\033[1m%s\033[0m\n' "$1"; }

# --------------------------------------------------------------------------
step "environment"
# --------------------------------------------------------------------------
bash "$SCRIPTS/doctor.sh" >/tmp/st-doctor.$$ 2>&1 \
  && ok "doctor.sh: environment ready" \
  || bad "doctor.sh exited non-zero" "$(tail -3 /tmp/st-doctor.$$)"
rm -f /tmp/st-doctor.$$

# --------------------------------------------------------------------------
step "unit suite (fake adapter — never calls a model)"
# --------------------------------------------------------------------------
# Two traps here. The suite must run from the scripts dir, because tests
# import sibling modules by bare name. And do not tail the output: unittest
# writes its verdict to stderr while the tests themselves print cost
# estimates to stdout, so the last few interleaved lines are usually noise.
# Match against the whole capture.
out=$(cd "$SCRIPTS" && python3 -m unittest discover tests 2>&1)
grep -q '^OK$' <<<"$out" && ok "$(grep -oE 'Ran [0-9]+ tests' <<<"$out")" \
  || bad "unit suite red" "$(grep -E '^(FAIL|ERROR)' <<<"$out" | head -3)"

python3 scripts/check_stdlib_only.py >/dev/null 2>&1 \
  && ok "shipped runner imports stdlib only (R7)" \
  || bad "third-party import in the shipped runner" "$(python3 scripts/check_stdlib_only.py 2>&1 | tail -3)"

# --------------------------------------------------------------------------
step "refuse-to-spend guards (observable because they fire before the call)"
# --------------------------------------------------------------------------
# API-key auth with no budget must refuse. Under subscription auth there is
# no dollar figure to cap, so the guard correctly does not fire -- skip
# rather than fail, or this check would depend on how the box is logged in.
auth=$(python3 -c "import sys;sys.path.insert(0,'$SCRIPTS');import tune;print(tune.detect_auth_mode())")
if [ "$auth" = "api-key" ]; then
  # Capture first, then match. Under `set -o pipefail` a pipeline inherits
  # the failure of ANY stage, and this CLI exits non-zero *by design* when it
  # refuses -- so `tune.py ... | grep -q` reports false even when grep found
  # the line. Every check below matches against a captured string for the
  # same reason.
  unmetered=$(python3 "$SCRIPTS/tune.py" probe --target README.md </dev/null 2>&1)
  if grep -q "refusing to run without --budget-usd" <<<"$unmetered"; then
    ok "unmetered run refused before any call (AE3)"
  else
    bad "unmetered run was not refused" "auth=$auth"
  fi
else
  ok "unmetered guard skipped (auth=$auth, no dollar cost to cap)"
fi

# Non-interactive without --yes must abort after printing the estimate.
est=$(python3 "$SCRIPTS/tune.py" probe --target README.md --budget-usd 1 </dev/null 2>&1)
grep -q "Planned probe calls" <<<"$est" \
  && ok "prints a cost estimate before spending (R8)" \
  || bad "no pre-flight estimate" "$est"
grep -q "confirmation required" <<<"$est" \
  && ok "aborts non-interactively without --yes" \
  || bad "did not abort without --yes" "$est"

strays=$(find reports -maxdepth 1 -type d -empty 2>/dev/null | wc -l)
[ "$strays" -eq 0 ] \
  && ok "a refused pre-flight leaves no run directory behind" \
  || bad "$strays empty run dir(s) left by refused runs" "$(find reports -maxdepth 1 -type d -empty | head -3)"

# --------------------------------------------------------------------------
step "verify — re-checks a banked run, zero model calls"
# --------------------------------------------------------------------------
run=$(find reports -mindepth 2 -maxdepth 2 -name report.json 2>/dev/null \
        | head -1 | xargs -r dirname | xargs -r basename)
if [ -z "$run" ]; then
  bad "no banked run under reports/ to verify" ""
else
  v=$(python3 "$SCRIPTS/tune.py" verify "$run" 2>&1); rc=$?
  # rc=1 means DRIFTED, which is a real answer and not a failure of the
  # tool. Treat "it produced a verdict" as the success condition.
  if grep -qE "No drift|DRIFTED|no manifest" <<<"$v"; then
    ok "verify $run -> $(grep -oE 'No drift|DRIFTED|no manifest' <<<"$v" | head -1) (exit $rc)"
  else
    bad "verify produced no verdict" "$v"
  fi
fi

# --------------------------------------------------------------------------
step "compare — paired verdict from banked reports, zero model calls"
# --------------------------------------------------------------------------
if [ -d reports/swapgate3-probe-incumbent ] && [ -d reports/swapgate5-probe-doctrine-v2 ]; then
  c=$(python3 "$SCRIPTS/tune.py" compare \
        --baseline swapgate3-probe-incumbent \
        --candidate swapgate5-probe-doctrine-v2 \
        --exclude design-drift 2>&1)
  grep -q "Verdict:" <<<"$c" \
    && ok "compare -> $(grep -oE 'Verdict: [a-z_]+' <<<"$c")" \
    || bad "compare produced no verdict" "$c"
  # The interval is the whole point; a verdict without one is the bug this
  # tool exists to prevent.
  grep -q "95% CI" <<<"$c" && ok "verdict carries a confidence interval" \
    || bad "verdict has no interval" "$c"
else
  ok "compare skipped (banked swapgate reports not present)"
fi

# Fewer than 3 cases must refuse rather than produce a meaningless interval.
r=$(python3 - <<'PY' 2>&1
import sys; sys.path.insert(0, "skills/skill-tuner/scripts")
import compare
try:
    compare.compare_paired({"a": 1}, {"a": 2}, delta=1.0)
    print("NO-REFUSAL")
except compare.ComparisonError as exc:
    print("refused:", exc)
PY
)
grep -q "^refused:" <<<"$r" && ok "refuses to judge fewer than 3 cases" \
  || bad "judged too few cases" "$r"

# --------------------------------------------------------------------------
step "reader matches skill-creator's own (skipped when not installed)"
# --------------------------------------------------------------------------
d=$(python3 scripts/validate_skillcreator_reader.py 2>&1 | tail -1)
grep -qE "same values|not installed" <<<"$d" && ok "$d" \
  || bad "reader disagrees with skill-creator" "$d"

# --------------------------------------------------------------------------
if [ "$LIVE" = "1" ]; then
step "LIVE probe (spends ~\$0.20)"
# --------------------------------------------------------------------------
  t=$(mktemp -d)/target.md
  printf '%s\n' '---' 'name: smoke' 'description: Scratch doc for the smoke test.' '---' \
    '' '## Rules' '' '- Never skip validation.' '- Verify the output.' > "$t"
  l=$(python3 "$SCRIPTS/tune.py" probe --target "$t" \
        --run-id "smoke-$(date +%s)" --yes --budget-usd 2 2>&1 | tail -2)
  grep -q "findings_confirmed=" <<<"$l" \
    && ok "live probe: $(grep -oE 'findings_confirmed=[0-9]+ refuted_count=[0-9]+ spent=\$[0-9.]+' <<<"$l")" \
    || bad "live probe produced no result" "$l"
fi

printf '\n\033[1m%d passed, %d failed\033[0m\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
