#!/usr/bin/env bash
# make-run.sh <arm> <task> <rep> - build one neutral run root under /tmp/ws-<hex>/ and print it.
# Fork of experiments/doctrine-gate-2026-10-29/arms/make-run.sh with one change: the arm's config
# dir carries skill-creator's installed skill tree beside skill-tuner, so the two descriptions
# compete the way they do in the operator's harness. Approximation recorded in predeclare.md:
# here both are user skills; the harness serves skill-creator as a plugin skill.
#   arms:  live-cur (main's description) | live-imp (candidates/improving.SKILL.md)
#   tasks: imp | opt  (briefs/<task>.txt; no slash token, routing probes)
# Layout as the vet's: $R/cfg (CLAUDE_CONFIG_DIR), $R/bin/shipit, $R/work (cwd), $R/prompt.txt.
set -euo pipefail
arm="$1"; task="$2"; rep="$3"
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
repo="$(cd "$base/../.." && pwd)"
vet="$repo/experiments/skill-diet-arms-2026-10-29"
SC="${SKILL_CREATOR_DIR:-/home/will/.claude/plugins/cache/claude-plugins-official/skill-creator/f8c5e7a1dcb7/skills/skill-creator}"
hex=$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')
R=/tmp/ws-$hex
mkdir -p "$R/cfg/skills/skill-tuner" "$R/work/skills" "$R/bin"
cp "$vet/fixture/shipit.v1" "$R/bin/shipit"; chmod +x "$R/bin/shipit"
cp -r "$vet/fixture/skill" "$R/work/skills/shipit"

case "$arm" in
  live-cur) doc="$repo/skills/skill-tuner/SKILL.md" ;;
  live-imp) doc="$base/candidates/improving.SKILL.md" ;;
  *) echo "unknown arm $arm" >&2; exit 2 ;;
esac
cp "$doc" "$R/cfg/skills/skill-tuner/SKILL.md"
cp "$repo/skills/skill-tuner/FALSIFIERS.md" "$R/cfg/skills/skill-tuner/FALSIFIERS.md"
cp -r "$SC" "$R/cfg/skills/skill-creator"

brief=$(cat "$base/briefs/$task.txt")
printf '%s\n' "$brief" > "$R/prompt.txt"

sha=$(sha256sum "$doc" | cut -c1-12)
scsha=$(sha256sum "$SC/SKILL.md" | cut -c1-12)
# Blinding scan: harness-authored text and names the arm can see (skill-creator's own body
# carries words like eval and benchmark by nature; that is the real skill, not harness text).
hits=$( { cat "$R/prompt.txt"; echo "$R"; find "$R" -maxdepth 2 -printf '%f\n'; } \
  | grep -o -i -w -E 'eval|evals|test|tests|judge|rubric|score|compare|benchmark|candidate|arena' | sort -u | tr '\n' ' ' || true)
mkdir -p "$base/results"
printf '%s\t%s\t%s\t%s\tdoctrine=%s\tskill-creator=%s\tblind_hits=[%s]\n' "$arm" "$task" "$rep" "$R" "$sha" "$scsha" "$hits" >> "$base/results/index.tsv"
echo "$R"
