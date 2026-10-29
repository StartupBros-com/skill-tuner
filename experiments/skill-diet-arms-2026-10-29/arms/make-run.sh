#!/usr/bin/env bash
# make-run.sh <arm> <task> <rep> - build one neutral run root under /tmp/ws-<hex>/ and print it.
#   arm:  bare | diet | tuner | wfa | re0           (slash-invoked arms, predeclare.md)
#         probe-diet | probe-tuner | probe-wfa | probe-re0 | collide   (no slash; routing probes)
#   task: t1 | t2 | t3 | t4
# Layout: $R/cfg (CLAUDE_CONFIG_DIR, skills under cfg/skills/<name>/), $R/bin/shipit (fake CLI,
# v2 for t3), $R/work (cwd: skills/shipit/SKILL.md for t1-t3, data/ for t4), $R/prompt.txt.
# Appends one line to results/index.tsv with the blinding scan.
set -euo pipefail
arm="$1"; task="$2"; rep="$3"
here="$(cd "$(dirname "$0")" && pwd)"
base="$(cd "$here/.." && pwd)"
repo="$(cd "$base/../.." && pwd)"
SCR="${SCR:-/tmp/hv-skill-diet-1278341}"
hex=$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')
R=/tmp/ws-$hex
mkdir -p "$R/cfg/skills" "$R/work" "$R/bin"

cli=v1; [ "$task" = t3 ] && cli=v2
cp "$base/fixture/shipit.$cli" "$R/bin/shipit"; chmod +x "$R/bin/shipit"
if [ "$task" = t4 ]; then
  cp -r "$base/fixture/data" "$R/work/data"
else
  mkdir -p "$R/work/skills"
  cp -r "$base/fixture/skill" "$R/work/skills/shipit"
fi

install_diet()  { mkdir -p "$R/cfg/skills/skill-diet"; cp -r "$SCR/cand/." "$R/cfg/skills/skill-diet/"; rm -rf "$R/cfg/skills/skill-diet/.git"; }
install_tuner() { mkdir -p "$R/cfg/skills/skill-tuner"; cp "$repo/skills/skill-tuner/SKILL.md" "$repo/skills/skill-tuner/FALSIFIERS.md" "$R/cfg/skills/skill-tuner/"; }
install_wfa()   { mkdir -p "$R/cfg/skills/writing-for-agents/agents"; cp "$SCR/ancestor/SKILL.md" "$SCR/ancestor/SKILL-MECHANICS.md" "$R/cfg/skills/writing-for-agents/"; cp "$SCR/ancestor/agents/openai.yaml" "$R/cfg/skills/writing-for-agents/agents/"; }
install_re0()   { for s in re0 debloat ssotize; do mkdir -p "$R/cfg/skills/$s"; cp "$SCR/contenders/paperthin/skills/depth/$s/SKILL.md" "$R/cfg/skills/$s/" 2>/dev/null || cp "$SCR/contenders/paperthin/skills/breadth/$s/SKILL.md" "$R/cfg/skills/$s/"; done; }

brief=$(cat "$base/fixture/briefs/$task.txt")
case "$arm" in
  bare)        printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  diet)        install_diet;  printf '/skill-diet %s\n' "$brief" > "$R/prompt.txt" ;;
  tuner)       install_tuner; printf '/skill-tuner %s\n' "$brief" > "$R/prompt.txt" ;;
  wfa)         install_wfa;   printf '/writing-for-agents %s\n' "$brief" > "$R/prompt.txt" ;;
  re0)         install_re0;   printf '/re0 %s\n' "$brief" > "$R/prompt.txt" ;;
  probe-diet)  install_diet;  printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  probe-tuner) install_tuner; printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  probe-wfa)   install_wfa;   printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  probe-re0)   install_re0;   printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  collide)     install_diet; install_tuner; install_wfa; printf '%s\n' "$brief" > "$R/prompt.txt" ;;
  *) echo "unknown arm $arm" >&2; exit 2 ;;
esac

# Blinding: harness-authored text and names the arm can see (prompt, run root, two levels of names).
hits=$( { cat "$R/prompt.txt"; echo "$R"; find "$R" -maxdepth 2 -printf '%f\n'; } \
  | grep -o -i -w -E 'eval|evals|test|tests|judge|rubric|score|compare|benchmark|candidate|arena' | sort -u | tr '\n' ' ' || true)
mkdir -p "$base/results"
printf '%s\t%s\t%s\t%s\tblind_hits=[%s]\n' "$arm" "$task" "$rep" "$R" "$hits" >> "$base/results/index.tsv"
echo "$R"
