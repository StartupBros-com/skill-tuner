"""aggregate.py - turn results/runs.tsv + per-run grade.json into cases, paired-json files,
compare verdicts and results/summary.md (rules pinned in predeclare.md).

Usage: python3 -I aggregate.py <experiment-dir> <scratch-dir>
  <scratch-dir> is the cwd for `tune.py compare` (it writes reports/compare_log.jsonl relative to cwd).
Rep 0 rows are smoke runs and are ignored. Only status `ok` rows count as valid reps.
Copies each valid run's SKILL.md, reply.txt, tools.txt, status.txt, grade.json and the init skills
list into results/runs/<arm>-<task>-<rep>/ so the record survives /tmp.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

exp = os.path.abspath(sys.argv[1])
scratch = os.path.abspath(sys.argv[2])
repo = os.path.abspath(os.path.join(exp, "..", ".."))
tune = os.path.join(repo, "skills", "skill-tuner", "scripts", "tune.py")
res = os.path.join(exp, "results")
os.makedirs(os.path.join(res, "runs"), exist_ok=True)
os.makedirs(scratch, exist_ok=True)

ARMS = ["bare", "diet", "tuner", "wfa", "re0"]
TASKS = ["t1", "t2", "t3", "t4"]

rows = []
with open(os.path.join(res, "runs.tsv")) as fh:
    for line in fh:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 6:
            continue
        arm, task, rep, root, status, graded = parts[:6]
        if rep == "0":
            continue
        rows.append(dict(arm=arm, task=task, rep=int(rep), root=root, status=status, ok=status.startswith("ok")))

# ---------- per-run records ----------
grades = {}  # (arm, task, rep) -> grade dict
probe_rows = []
for r in rows:
    key = (r["arm"], r["task"], r["rep"])
    dest = os.path.join(res, "runs", "%s-%s-%d" % key)
    os.makedirs(dest, exist_ok=True)
    for name in ("reply.txt", "tools.txt", "status.txt", "grade.json", "stall.txt"):
        src = os.path.join(r["root"], name)
        if os.path.exists(src):
            shutil.copy(src, dest)
    sk = os.path.join(r["root"], "work", "skills", "shipit", "SKILL.md")
    if os.path.exists(sk):
        shutil.copy(sk, os.path.join(dest, "SKILL.md"))
    bs = os.path.join(r["root"], "work", "biggest.sh")
    if os.path.exists(bs):
        shutil.copy(bs, os.path.join(dest, "biggest.sh"))
    init = os.path.join(r["root"], "init.json")
    if os.path.exists(init):
        try:
            d = json.load(open(init)) or {}
            with open(os.path.join(dest, "init-skills.json"), "w") as fh:
                json.dump({"skills": d.get("skills"), "model": d.get("model"),
                           "claude_code_version": d.get("claude_code_version")}, fh, indent=1)
        except ValueError:
            pass
    if r["arm"].startswith("probe-") or r["arm"] == "collide":
        tools = open(os.path.join(r["root"], "tools.txt")).read() if os.path.exists(os.path.join(r["root"], "tools.txt")) else ""
        m = re.search(r"^skill_calls=(.*)$", tools, re.M)
        calls = json.loads(m.group(1)) if m else []
        gr = re.search(r"^guidance_reads=(\d+)", tools, re.M)
        probe_rows.append(dict(arm=r["arm"], task=r["task"], rep=r["rep"], ok=r["ok"], skill_calls=calls,
                               guidance_reads=int(gr.group(1)) if gr else 0, root=r["root"]))
        continue
    if r["ok"] and os.path.exists(os.path.join(r["root"], "grade.json")):
        grades[key] = json.load(open(os.path.join(r["root"], "grade.json")))

# ---------- validity per arm x task ----------
valid = defaultdict(list)
for (arm, task, rep), g in grades.items():
    valid[(arm, task)].append(rep)
excluded_tasks = set()
for task in TASKS:
    for arm in ARMS:
        if len(valid[(arm, task)]) < 2:
            excluded_tasks.add(task)

# ---------- cases ----------
items_by_task = defaultdict(set)
for (arm, task, rep), g in grades.items():
    items_by_task[task].update(g["items"].keys())
case_scores = {}  # case -> {arm: score}
case_n = {}
for task in TASKS:
    if task in excluded_tasks:
        continue
    for item in sorted(items_by_task[task]):
        case = "%s/%s" % (task, item)
        sc = {}
        for arm in ARMS:
            reps = valid[(arm, task)]
            vals = [grades[(arm, task, rep)]["items"].get(item, False) for rep in reps]
            sc[arm] = sum(1 for v in vals if v) / len(vals) if vals else None
            case_n[(case, arm)] = len(vals)
        case_scores[case] = sc
retained = {c: s for c, s in case_scores.items() if len(set(s.values())) > 1}
dropped = {c: s for c, s in case_scores.items() if len(set(s.values())) <= 1}

# ---------- paired-json + compare ----------
pj = os.path.join(scratch, "paired")
os.makedirs(pj, exist_ok=True)
for arm in ARMS:
    with open(os.path.join(pj, "%s.json" % arm), "w") as fh:
        json.dump({c: s[arm] for c, s in retained.items()}, fh, indent=1)
pairs = [("bare", "diet"), ("bare", "tuner"), ("bare", "wfa"), ("bare", "re0"),
         ("tuner", "diet"), ("wfa", "diet"), ("re0", "diet")]
verdicts = {}
os.makedirs(os.path.join(res, "compare"), exist_ok=True)
for base, cand in pairs:
    cmd = [sys.executable, tune, "compare", "--paired-json", "--baseline", os.path.join(pj, "%s.json" % base),
           "--candidate", os.path.join(pj, "%s.json" % cand), "--delta", "0.10"]
    p = subprocess.run(cmd, cwd=scratch, capture_output=True, text=True)
    out = p.stdout + ("\n[stderr]\n" + p.stderr if p.stderr.strip() else "")
    with open(os.path.join(res, "compare", "%s-vs-%s.md" % (cand, base)), "w") as fh:
        fh.write(out)
    m = re.search(r"\*\*Verdict: (\w+)\*\*", out)
    md = re.search(r"mean difference: ([+-][0-9.]+)", out)
    ci = re.search(r"95% CI: \[([^\]]+)\]", out)
    rec = re.search(r"case record: (.*)", out)
    verdicts[(cand, base)] = dict(verdict=m.group(1) if m else "ERROR rc=%d" % p.returncode,
                                  mean=md.group(1) if md else "?", ci=ci.group(1) if ci else "?",
                                  record=rec.group(1).strip() if rec else "?")

# ---------- pass rates and normalized gain ----------
def arm_rate(arm, cases):
    vals = [case_scores[c][arm] for c in cases if case_scores[c][arm] is not None]
    return sum(vals) / len(vals) if vals else None

lines = []
lines.append("# Results summary (generated by arms/aggregate.py)\n")
lines.append("Valid reps per arm x task (status ok, rep 0 smoke runs excluded):\n")
lines.append("| arm | " + " | ".join(TASKS) + " |")
lines.append("| --- | " + " | ".join("---" for _ in TASKS) + " |")
for arm in ARMS:
    lines.append("| %s | " % arm + " | ".join(str(len(valid[(arm, t)])) for t in TASKS) + " |")
if excluded_tasks:
    lines.append("\nTasks excluded for every arm (an arm had < 2 valid reps): %s\n" % ", ".join(sorted(excluded_tasks)))
failed = [r for r in rows if not r["ok"] and not r["arm"].startswith("probe-") and r["arm"] != "collide"]
lines.append("\nFailed or missing arm runs: %d" % len(failed))
for r in failed:
    lines.append("- %s %s rep%d %s: %s" % (r["arm"], r["task"], r["rep"], r["root"], r["status"]))

lines.append("\n## Cases\n")
lines.append("%d cases scored, %d retained (differ between arms), %d dropped (identical in every arm).\n" % (
    len(case_scores), len(retained), len(dropped)))
lines.append("| case | " + " | ".join(ARMS) + " | kept |")
lines.append("| --- | " + " | ".join("---" for _ in ARMS) + " | --- |")
for c in sorted(case_scores):
    s = case_scores[c]
    lines.append("| %s | " % c + " | ".join("%.2f" % s[a] if s[a] is not None else "-" for a in ARMS) + " | %s |" % ("yes" if c in retained else "no"))

lines.append("\n## Pass rates on retained cases and normalized gain over bare\n")
lines.append("| arm | pass rate (retained) | pass rate (all) | normalized gain vs bare | T4 pass rate |")
lines.append("| --- | --- | --- | --- | --- |")
bare_r = arm_rate("bare", retained)
for arm in ARMS:
    r_ret = arm_rate(arm, retained)
    r_all = arm_rate(arm, case_scores)
    t4 = arm_rate(arm, [c for c in case_scores if c.startswith("t4/")])
    gain = "-"
    if arm != "bare" and r_ret is not None and bare_r is not None and bare_r < 1:
        gain = "%+.2f" % ((r_ret - bare_r) / (1 - bare_r))
    lines.append("| %s | %s | %s | %s | %s |" % (
        arm, "%.2f" % r_ret if r_ret is not None else "-", "%.2f" % r_all if r_all is not None else "-", gain,
        "%.2f" % t4 if t4 is not None else "-"))

lines.append("\n## Paired verdicts (tune.py compare --paired-json, delta 0.10, retained cases)\n")
lines.append("| candidate vs baseline | verdict | mean diff | 95% CI | case record |")
lines.append("| --- | --- | --- | --- | --- |")
for (cand, base), v in verdicts.items():
    lines.append("| %s vs %s | %s | %s | %s | %s |" % (cand, base, v["verdict"], v["mean"], v["ci"], v["record"]))

lines.append("\n## Observed, not scored\n")
lines.append("| arm | task | rep | bytes | tokens | cli_calls | ran_help | guidance_reads | env flag left | cost |")
lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
for (arm, task, rep) in sorted(grades):
    g = grades[(arm, task, rep)]
    o = g["observed"]
    st = next((r["status"] for r in rows if (r["arm"], r["task"], r["rep"]) == (arm, task, rep)), "")
    cost = re.search(r"cost=([0-9.]+)", st)
    lines.append("| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s |" % (
        arm, task, rep, o.get("bytes"), o.get("tokens_o200k"), o.get("cli_calls"), o.get("ran_help"),
        o.get("guidance_reads"), o.get("env_flag_present"), "%.3f" % float(cost.group(1)) if cost else "?"))

lines.append("\n## Routing and collision probes (no slash token)\n")
lines.append("| probe | task | rep | ok | Skill calls | guidance reads |")
lines.append("| --- | --- | --- | --- | --- | --- |")
for p in sorted(probe_rows, key=lambda x: (x["arm"], x["task"], x["rep"])):
    lines.append("| %s | %s | %d | %s | %s | %d |" % (p["arm"], p["task"], p["rep"], "yes" if p["ok"] else "no",
                                                   json.dumps(p["skill_calls"]), p["guidance_reads"]))

with open(os.path.join(res, "summary.md"), "w") as fh:
    fh.write("\n".join(lines) + "\n")
with open(os.path.join(res, "cases.json"), "w") as fh:
    json.dump({"case_scores": case_scores, "retained": sorted(retained), "dropped": sorted(dropped),
               "verdicts": {"%s-vs-%s" % k: v for k, v in verdicts.items()},
               "excluded_tasks": sorted(excluded_tasks)}, fh, indent=1)
print("\n".join(lines[:60]))
print("... summary written to", os.path.join(res, "summary.md"))
