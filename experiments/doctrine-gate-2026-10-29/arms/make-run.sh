#!/usr/bin/env bash
# make-run.sh <arm> <task> <rep> - build one neutral run root under /tmp/ws-<hex>/ and print it.
# Reuses the skill-diet vet's fixture (fake shipit CLI, planted skill, briefs); only the
# installed skill-tuner document varies by arm.
#   arms:  live-orig | live-cand           no slash token; routing probes (description test)
#          tuner-current | tuner-c68 | tuner-c69a | tuner-combined   slash-invoked /skill-tuner
#   tasks: t1 | t2
# Layout as the vet's: $R/cfg (CLAUDE_CONFIG_DIR), $R/bin/shipit, $R/work (cwd), $R/prompt.txt.
set -euo pipefail
arm="$1"; task="$2"; rep="$3"
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
repo="$(cd "$base/../.." && pwd)"
vet="$repo/experiments/skill-diet-arms-2026-10-29"
hex=$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')
R=/tmp/ws-$hex
mkdir -p "$R/cfg/skills/skill-tuner" "$R/work/skills" "$R/bin"
cp "$vet/fixture/shipit.v1" "$R/bin/shipit"; chmod +x "$R/bin/shipit"
cp -r "$vet/fixture/skill" "$R/work/skills/shipit"

case "$arm" in
  live-orig|tuner-current) doc="$repo/skills/skill-tuner/SKILL.md" ;;
  live-cand)               doc="$base/candidates/desc-only.SKILL.md" ;;
  tuner-c68)               doc="$base/candidates/c68.SKILL.md" ;;
  tuner-c69a)              doc="$base/candidates/c69a.SKILL.md" ;;
  tuner-combined)          doc="$base/candidates/combined.SKILL.md" ;;
  *) echo "unknown arm $arm" >&2; exit 2 ;;
esac
cp "$doc" "$R/cfg/skills/skill-tuner/SKILL.md"
cp "$repo/skills/skill-tuner/FALSIFIERS.md" "$R/cfg/skills/skill-tuner/FALSIFIERS.md"

brief=$(cat "$vet/fixture/briefs/$task.txt")
case "$arm" in
  live-*)  printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  tuner-*) printf '/skill-tuner %s\n' "$brief" > "$R/prompt.txt" ;;
esac

sha=$(sha256sum "$doc" | cut -c1-12)
# Blinding scan: harness-authored text and names the arm can see.
hits=$( { cat "$R/prompt.txt"; echo "$R"; find "$R" -maxdepth 2 -printf '%f\n'; } \
  | grep -o -i -w -E 'eval|evals|test|tests|judge|rubric|score|compare|benchmark|candidate|arena' | sort -u | tr '\n' ' ' || true)
mkdir -p "$base/results"
printf '%s\t%s\t%s\t%s\tdoctrine=%s\tblind_hits=[%s]\n' "$arm" "$task" "$rep" "$R" "$sha" "$hits" >> "$base/results/index.tsv"
echo "$R"
