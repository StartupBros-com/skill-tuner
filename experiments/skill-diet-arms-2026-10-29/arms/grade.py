"""grade.py <run-root> <task> - deterministic grader for one run (items pinned in predeclare.md).

Reads the final work/skills/shipit/SKILL.md (t1-t3) or runs work/biggest.sh (t4), plus
tools.txt for the events-based items. Writes grade.json into the run root and prints one line.
The answer key lives here and in predeclare.md only; it never enters a run.
"""
import json
import os
import re
import subprocess
import sys

root, task = sys.argv[1], sys.argv[2]
work = os.path.join(root, "work")
skill_path = os.path.join(work, "skills", "shipit", "SKILL.md")


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def tools_field(text, key):
    m = re.search(r"^%s=(.*)$" % re.escape(key), text or "", re.M)
    return m.group(1) if m else ""


skill = read(skill_path)
tools = read(os.path.join(root, "tools.txt")) or ""
items, observed = {}, {}

if skill is not None:
    lines = skill.splitlines()
    rule_lines = [l for l in lines if "shipit check" in l and re.search(r"before|never skip|without", l, re.I)]
    fm = re.search(r"^---\s*\n(.*?)\n---", skill, re.S)
    desc = ""
    if fm:
        m = re.search(r"^description:\s*(.*)$", fm.group(1), re.M)
        desc = m.group(1) if m else ""
    items_all = {
        "D1": len(rule_lines) == 1,
        "D2": "--env" not in skill,
        "D3": not re.search(r"^#+\s*History", skill, re.M) and "forty minutes" not in skill and "make deploy" not in skill,
        "D4": "MAJOR.MINOR.PATCH" not in skill and "incompatible API changes" not in skill,
        "D5": not ("--no-color" in skill and "--timeout <seconds>" in skill),
        "D6": sum(1 for l in lines if re.search(r"dry[- ]?run", l, re.I)) <= 2,
        "D7": "--retries 5" not in skill and "File the failed release id" not in skill,
        "D9": not re.search(r"last week|shipped a broken|broken manifest", skill, re.I),
        "K1": "purge" in skill and "--yes" in skill and bool(re.search(r"irreversib|cannot be undone|can't be undone|can not be undone", skill, re.I)),
        "K2": "no manifest" in skill,
        "K3": "--notes-json" in skill and bool(re.search(r'"items"\s*:\s*\[\s*\{\s*"id"', skill)),
        "K4": bool(re.search(r"releas(e|ing)", desc, re.I)) and bool(re.search(r"roll(ing)?[- ]?back", desc, re.I)),
        "K5": len(rule_lines) >= 1,
        "T3-A": not re.search(r"shipit status", skill),
        "T3-B": "shipit info" in skill,
    }
    observed["bytes"] = len(skill.encode("utf-8"))
    observed["lines"] = len(lines)
    observed["rule_lines"] = len(rule_lines)
    observed["dry_run_lines"] = sum(1 for l in lines if re.search(r"dry[- ]?run", l, re.I))
    observed["env_flag_present"] = "--env" in skill
    try:
        import tiktoken  # noqa: WPS433
        observed["tokens_o200k"] = len(tiktoken.get_encoding("o200k_base").encode(skill))
    except Exception:  # noqa: BLE001
        observed["tokens_o200k"] = None
else:
    items_all = {}
    observed["bytes"] = None

cli_calls = int(tools_field(tools, "cli_calls") or 0)
observed["cli_calls"] = cli_calls
observed["ran_help"] = tools_field(tools, "ran_help") == "yes"
observed["skill_calls"] = tools_field(tools, "skill_calls")
observed["guidance_reads"] = int(tools_field(tools, "guidance_reads") or 0)
observed["fixture_edits"] = int(tools_field(tools, "fixture_edits") or 0)

if task == "t1":
    for k in ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "K1", "K2", "K3", "K4", "K5"):
        items[k] = items_all.get(k, False)
elif task == "t2":
    for k in ("D1", "D9", "K1", "K2", "K3", "K4", "K5"):
        items[k] = items_all.get(k, False)
elif task == "t3":
    for k in ("T3-A", "T3-B", "K1", "K2", "K3", "K4", "K5"):
        items[k] = items_all.get(k, False)
    items["T3-C"] = cli_calls >= 1
elif task == "t4":
    script = os.path.join(work, "biggest.sh")
    items["T4-A"] = os.path.isfile(script)
    out = ""
    if items["T4-A"]:
        try:
            out = subprocess.run(["bash", "biggest.sh"], cwd=work, capture_output=True, text=True, timeout=20).stdout
        except Exception as exc:  # noqa: BLE001
            out = "ERROR %s" % exc
    names = re.findall(r"\b([abcde]\.(?:bin|txt|log|dat|md))\b", out)
    first3 = []
    for n in names:
        if n not in first3:
            first3.append(n)
    first3 = first3[:3]
    items["T4-B"] = first3 == ["b.txt", "d.dat", "a.bin"] and all(s in out for s in ("12000", "8000", "5000"))
    observed["t4_output"] = out[:400]
else:
    sys.exit("unknown task %s" % task)

grade = {"task": task, "items": items, "observed": observed,
         "passed": sum(1 for v in items.values() if v), "total": len(items)}
with open(os.path.join(root, "grade.json"), "w") as fh:
    json.dump(grade, fh, indent=1)
print(os.path.basename(root), task, "%d/%d" % (grade["passed"], grade["total"]),
      " ".join("%s=%d" % (k, int(v)) for k, v in items.items()))
