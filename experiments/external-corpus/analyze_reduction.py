#!/usr/bin/env python3
"""Paired per-doc defect reduction: original external skills vs their fixed
scratch copies, both probed under the same doctrine/model/cap.

Reduction is confirmed-findings-before minus confirmed-findings-after per
document. Positive mean = fewer verified defects after fixing. Bootstrap CI
and exact sign test come from the shipped compare module — the same stats
that gate every other claim in this repo. $0.
"""
import argparse
import json
import pathlib
import sys
from collections import Counter

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "skills/skill-tuner/scripts"
sys.path.insert(0, str(SCRIPTS))
import compare  # noqa: E402


def per_doc(report_path: str) -> Counter:
    r = json.load(open(report_path))
    return Counter(f["target_file"].rsplit("/", 2)[-2]
                   for f in r["probe"]["confirmed_findings"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", nargs="+", required=True,
                    help="original-corpus report.json paths")
    ap.add_argument("--after", required=True,
                    help="fixed-corpus report.json path")
    ap.add_argument("--docs", required=True,
                    help="comma-separated doc names in the fixed run")
    args = ap.parse_args()

    before = Counter()
    for p in args.before:
        before.update(per_doc(p))
    after = per_doc(args.after)
    docs = args.docs.split(",")

    reductions = []
    print("doc                  before  after  reduction")
    for d in docs:
        r = before.get(d, 0) - after.get(d, 0)
        reductions.append(float(r))
        print(f"{d:20s} {before.get(d, 0):5d} {after.get(d, 0):6d}  {r:+d}")

    mean = sum(reductions) / len(reductions)
    lo, hi = compare.bootstrap_ci_95(reductions)
    won = sum(r > 0 for r in reductions)
    lost = sum(r < 0 for r in reductions)
    p = compare.exact_sign_test_p(won, lost)
    print(f"\nmean reduction {mean:+.2f} defects/doc, bootstrap 95% CI "
          f"[{lo:+.2f}, {hi:+.2f}], {won}W/{lost}L/"
          f"{len(reductions) - won - lost}T, sign p={p:.3f}")
    verdict = ("defect reduction confirmed" if lo > 0
               else "reduction not resolved at n")
    print(f"verdict: {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
