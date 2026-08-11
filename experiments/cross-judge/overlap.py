#!/usr/bin/env python3
"""Match recall-probe findings against claude's raw finding set (confirmed +
refuted) for the sampled docs; emit the novel ones for claude adjudication.

Overlap = token-overlap >= 0.5 between the two findings' target quotes
(intersection over the smaller set). Coarse, but the point is to separate
"re-found the same defect" from "found something new"; borderline cases
land novel and the claude adjudication pass decides if they're real.
"""
import argparse
import json
import re


def norm_tokens(s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", re.sub(r"\s+", " ", s).strip().lower()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True,
                    help="banked leg report.json (claude raw findings)")
    ap.add_argument("--recall", required=True, help="recall_probe.jsonl")
    ap.add_argument("--novel-out", required=True)
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()

    rep = json.load(open(args.report))
    rows = [json.loads(ln) for ln in open(args.recall)]
    docs = {r["doc"] for r in rows}
    claude_raw = {d: [] for d in docs}
    for kind in ("confirmed_findings", "refuted_findings"):
        for f in rep["probe"][kind]:
            d = f["target_file"].rsplit("/", 2)[-2]
            if d in claude_raw:
                claude_raw[d].append({"quote": f["target_quote"], "kind": kind})

    novel, overlapping = [], []
    for row in rows:
        for i, f in enumerate(row["findings"]):
            gq = norm_tokens(f["target_quote"])
            best, best_score = None, 0.0
            for cf in claude_raw[row["doc"]]:
                cq = norm_tokens(cf["quote"])
                score = len(gq & cq) / max(1, min(len(gq), len(cq)))
                if score > best_score:
                    best, best_score = cf, score
            rec = {"id": f"{row['doc']}-g{i:02d}", "doc": row["doc"], **f,
                   "best_overlap": round(best_score, 2),
                   "matched_kind": (best["kind"]
                                    if best and best_score >= args.threshold
                                    else None)}
            (overlapping if rec["matched_kind"] else novel).append(rec)

    total = sum(len(r["findings"]) for r in rows)
    print(f"claude raw on sampled docs: "
          f"{sum(len(v) for v in claude_raw.values())}")
    print(f"probe findings: {total} | overlapping {len(overlapping)} "
          f"| novel {len(novel)}")
    for kind in ("confirmed_findings", "refuted_findings"):
        n = sum(1 for r in overlapping if r["matched_kind"] == kind)
        print(f"  overlaps hitting claude {kind}: {n}")
    json.dump(novel, open(args.novel_out, "w"), indent=1)
    print(f"novel by doc:",
          {d: sum(1 for r in novel if r['doc'] == d) for d in sorted(docs)})
    return 0


if __name__ == "__main__":
    sys_exit = main()
    raise SystemExit(sys_exit)
