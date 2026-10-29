"""read-routing.py - print the banked routing-parity verdict, both conditions' scores, the per-case
picture for every reject case (how many trials each condition routed to skill-tuner), and spend.

Reads reports/trigger-improving-routing/{report.json,trials.jsonl} only. The two planted negatives
(shared__near_miss__1 and __2) are skill-creator's stated jobs; predeclare.md refuses the land if the
candidate routes either to skill-tuner in more trials than the original does.
"""
import collections
import json
import pathlib
import sys

repo = pathlib.Path(__file__).resolve().parents[3]
run = repo / "reports" / (sys.argv[1] if len(sys.argv) > 1 else "trigger-improving-routing")
report = json.load(open(run / "report.json", encoding="utf-8"))
rp = report["routing_parity"]
print("verdict:", rp["verdict"], "| failing_case_ids:", rp.get("failing_case_ids"))
for cond, s in rp["scores"].items():
    print(f"  {cond:9s} accuracy {s['correct']}/{s['total']} ({s['accuracy']:.0%})  "
          f"near-miss rejection {s['near_miss_correct']}/{s['near_miss_total']} ({s['near_miss_accuracy']:.0%})  "
          f"failing {s.get('failing_case_ids')}")
conds = report["conditions"]
total_cost = sum(c["total_cost_usd"] for c in conds.values())
total_trials = sum(c["trials"] for c in conds.values())
print(f"spend: ${total_cost:.2f} over {total_trials} calls")

# Which neutral id was skill-tuner in each trial? The manifest records id assignment per condition
# when neutral_ids is on; fall back to the trials' own correctness via the report's case table.
battery = json.load(open(repo / "configs" / "trigger-improving-routing-battery.json", encoding="utf-8"))
kinds = {c["case_id"]: c["kind"] for c in battery}
rows = [json.loads(l) for l in open(run / "trials.jsonl", encoding="utf-8") if l.strip()]
by_case = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    by_case[r["case_id"]][r["condition"]].append(r["response"])
print("\nper-case answers (response id per trial; the target's neutral id is the one obvious cases pick):")
for case_id in [c["case_id"] for c in battery]:
    conds_answers = by_case.get(case_id, {})
    line = "  ".join(f"{cond}: {','.join(a or '-' for a in ans)}" for cond, ans in sorted(conds_answers.items()))
    print(f"  {kinds[case_id]:17s} {case_id:26s} {line}")
m = report.get("manifest") or {}
dirty = [i for i in m.get("inputs", []) if i.get("dirty")]
print(f"\nmanifest inputs: {len(m.get('inputs', []))}, dirty: {len(dirty)}")
