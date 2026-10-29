#!/usr/bin/env bash
# job.sh <arm> <task> <rep> [max-turns] [cap-seconds] - build + run one routing run; appends to results/runs.tsv.
# run-one.sh and extract.py are the skill-diet vet's, unchanged. No grader: the measurement is
# the skill_calls line (which skills the run invoked), not the edit's quality.
set -uo pipefail
arm="$1"; task="$2"; rep="$3"; turns="${4:-10}"; cap="${5:-600}"
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
repo="$(cd "$base/../.." && pwd)"
vet="$repo/experiments/skill-diet-arms-2026-10-29/arms"
R=$(bash "$here/make-run.sh" "$arm" "$task" "$rep") || { echo "make-run failed $arm $task $rep" >&2; exit 2; }
bash "$vet/run-one.sh" "$R" "$turns" "$cap" > "$R/run.log" 2>&1
rc=$?
status=$(head -1 "$R/status.txt" 2>/dev/null || echo "error no-status")
calls=$(grep -m1 '^skill_calls=' "$R/tools.txt" 2>/dev/null || echo 'skill_calls=?')
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$arm" "$task" "$rep" "$R" "$status" "$calls" >> "$base/results/runs.tsv"
echo "$arm $task $rep $R :: $status :: $calls"
exit $rc
