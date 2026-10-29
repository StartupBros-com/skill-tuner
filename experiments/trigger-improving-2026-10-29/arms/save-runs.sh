#!/usr/bin/env bash
# save-runs.sh - copy each run's durable records out of its /tmp root into results/runs/<arm>-<task>-<rep>/.
# Saved: status.txt (status + cost), tools.txt (skill_calls), reply.txt, init.json (what the arm could see,
# including the skills list), and the final fixture SKILL.md.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
while IFS=$'\t' read -r arm task rep root status calls; do
  [ -d "$root" ] || { echo "missing root $root ($arm $task $rep)"; continue; }
  dst="$base/results/runs/$arm-$task-$rep"
  mkdir -p "$dst"
  for f in status.txt tools.txt reply.txt init.json stall.txt; do
    [ -f "$root/$f" ] && cp "$root/$f" "$dst/$f"
  done
  [ -f "$root/work/skills/shipit/SKILL.md" ] && cp "$root/work/skills/shipit/SKILL.md" "$dst/SKILL.md"
  echo "saved $dst"
done < "$base/results/runs.tsv"
