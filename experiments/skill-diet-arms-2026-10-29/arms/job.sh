#!/usr/bin/env bash
# job.sh <arm> <task> <rep> [max-turns] [cap-seconds] - one build + run + grade; appends to results/runs.tsv.
set -uo pipefail
arm="$1"; task="$2"; rep="$3"; turns="${4:-40}"; cap="${5:-900}"
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
R=$(bash "$here/make-run.sh" "$arm" "$task" "$rep") || { echo "make-run failed $arm $task $rep" >&2; exit 2; }
bash "$here/run-one.sh" "$R" "$turns" "$cap" > "$R/run.log" 2>&1
rc=$?
status=$(head -1 "$R/status.txt" 2>/dev/null || echo "error no-status")
graded="-"
case "$arm" in
  probe-*|collide) ;;
  *) graded=$(python3 -I "$here/grade.py" "$R" "$task" 2>&1 | tail -1) ;;
esac
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$arm" "$task" "$rep" "$R" "$status" "$graded" >> "$base/results/runs.tsv"
echo "$arm $task $rep $R :: $status :: $graded"
exit $rc
