"""aggregate.py - per (arm, brief): runs, skill-tuner hits, skill-creator hits, spend, from results/runs.tsv.

Reads only the run ledger this experiment wrote. A hit is a Skill tool call naming the skill
(the skill_calls line extract.py writes); the opt brief is keyed as correct for either skill,
so both counts are printed and no verdict is derived from it here.
"""
import json
import pathlib
import re
import sys

base = pathlib.Path(__file__).resolve().parent.parent
rows = []
for line in (base / "results" / "runs.tsv").read_text(encoding="utf-8").splitlines():
    arm, task, rep, root, status, calls = line.split("\t")
    m = re.search(r"cost=([0-9.]+)", status)
    cost = float(m.group(1)) if m else 0.0
    calls_json = calls.split("=", 1)[1] if "=" in calls else "[]"
    try:
        skill_calls = json.loads(calls_json)
    except json.JSONDecodeError:
        skill_calls = []
    rows.append((arm, task, int(rep), status.split()[0], cost, skill_calls))

groups = {}
for arm, task, rep, ok, cost, skill_calls in rows:
    g = groups.setdefault((arm, task), {"n": 0, "ok": 0, "tuner": 0, "creator": 0, "cost": 0.0, "reps": []})
    g["n"] += 1
    g["ok"] += ok == "ok"
    g["tuner"] += any("skill-tuner" in c for c in skill_calls)
    g["creator"] += any("skill-creator" in c for c in skill_calls)
    g["cost"] += cost
    g["reps"].append((rep, skill_calls))

print("arm\tbrief\truns\tok\tskill-tuner\tskill-creator\tspend")
for (arm, task), g in sorted(groups.items()):
    print(f"{arm}\t{task}\t{g['n']}\t{g['ok']}\t{g['tuner']}/{g['n']}\t{g['creator']}/{g['n']}\t${g['cost']:.2f}")
print(f"total\t\t{len(rows)}\t\t\t\t${sum(r[4] for r in rows):.2f}")
if "--reps" in sys.argv:
    for (arm, task), g in sorted(groups.items()):
        for rep, skill_calls in sorted(g["reps"]):
            print(f"  {arm} {task} rep{rep}: {skill_calls}")
