#!/usr/bin/env bash
# batch.sh [parallelism] - the 60 arm runs (5 arms x 4 tasks x 3 reps), interleaved by rep then task
# so no arm gets a time-of-day block to itself. Then probes.sh runs the 27 routing/collision runs.
set -uo pipefail
P="${1:-6}"
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
mkdir -p "$base/results"
jobs="$base/results/jobs.txt"
: > "$jobs"
for rep in 1 2 3; do
  for task in t1 t2 t3 t4; do
    for arm in bare diet tuner wfa re0; do
      echo "$arm $task $rep" >> "$jobs"
    done
  done
done
echo "batch start $(date -u +%FT%TZ) jobs=$(wc -l < "$jobs") P=$P" >> "$base/results/batch.log"
xargs -P "$P" -L 1 bash "$here/job.sh" < "$jobs" >> "$base/results/batch.log" 2>&1
echo "batch end $(date -u +%FT%TZ)" >> "$base/results/batch.log"
# routing + collision probes (no slash token), 10 turns, 600 s cap
probes="$base/results/probe-jobs.txt"
: > "$probes"
for rep in 1 2 3; do
  for task in t1 t4; do
    for arm in probe-diet probe-tuner probe-wfa probe-re0; do
      echo "$arm $task $rep 10 600" >> "$probes"
    done
  done
  echo "collide t1 $rep 10 600" >> "$probes"
done
echo "probes start $(date -u +%FT%TZ) jobs=$(wc -l < "$probes")" >> "$base/results/batch.log"
xargs -P "$P" -L 1 bash "$here/job.sh" < "$probes" >> "$base/results/batch.log" 2>&1
echo "probes end $(date -u +%FT%TZ)" >> "$base/results/batch.log"
echo BATCH_DONE >> "$base/results/batch.log"
