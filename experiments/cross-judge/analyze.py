#!/usr/bin/env python3
"""Analyze blind cross-model adjudications (adjudicate.py output).

Reports per-leg confirm rates with a Fisher exact test for cross-leg
symmetry. The question of record: does a non-Claude judge endorse
claude-confirmed findings at a rate that (a) is high enough for the
findings to count as real, and (b) does not differ between doctrine legs —
a leg-asymmetric confirm rate would mean the doctrine's measured advantage
is partly a claude-family artifact. Stdlib only, $0.
"""
import argparse
import json
import math
import pathlib
import sys
from collections import Counter

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "skills/skill-tuner/scripts"
sys.path.insert(0, str(SCRIPTS))
import compare  # noqa: E402  (bootstrap_ci_95, exact_sign_test_p — the shipped stats)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """2x2 table [[a,b],[c,d]] — sum of hypergeometric probabilities <= observed."""
    n = a + b + c + d
    row1, col1 = a + b, a + c

    def p_of(x: int) -> float:
        return (math.comb(col1, x) * math.comb(n - col1, row1 - x)
                / math.comb(n, row1))

    lo, hi = max(0, row1 + col1 - n), min(row1, col1)
    p_obs = p_of(a)
    return min(1.0, sum(p_of(x) for x in range(lo, hi + 1)
                        if p_of(x) <= p_obs * (1 + 1e-9)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("adjudications", help="adjudications.jsonl")
    args = ap.parse_args()

    rows = [json.loads(ln) for ln in open(args.adjudications)]
    errors = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    legs = sorted({r["leg"] for r in rows})

    print(f"{len(rows)} adjudications ({len(errors)} errors excluded)")
    qp_missing = [r for r in rows if not r["quote_present"]]
    if qp_missing:
        print(f"!! judge reports quote absent for {len(qp_missing)}: "
              + ", ".join(r["id"] for r in qp_missing))

    counts = {}
    for leg in legs:
        sub = [r for r in rows if r["leg"] == leg]
        conf = sum(r["genuine"] for r in sub)
        counts[leg] = (conf, len(sub) - conf)
        print(f"  {leg:10s} confirmed {conf}/{len(sub)} "
              f"({conf / len(sub):.0%})")

    if len(legs) == 2:
        (a, b), (c, d) = counts[legs[0]], counts[legs[1]]
        p = fisher_exact_two_sided(a, b, c, d)
        print(f"  symmetry: Fisher exact two-sided p = {p:.3f} "
              f"({'no leg asymmetry detected' if p >= 0.05 else 'LEG ASYMMETRY'})")

    print("\nrefuted findings by rule (which doctrine rules does the "
          "cross-judge push back on):")
    refuted = Counter((r["leg"], r["rule"]) for r in rows if not r["genuine"])
    for (leg, rule), n in refuted.most_common():
        print(f"  {n}  {leg:10s} {rule}")

    if len(legs) == 2:
        base, cand = legs[0], legs[1]  # alphabetical: incumbent, v3
        skills = sorted({r["skill"] for r in rows})
        per = {(leg, s): 0 for leg in legs for s in skills}
        for r in rows:
            if r["genuine"]:
                per[(r["leg"], r["skill"])] += 1
        diffs = [float(per[(cand, s)] - per[(base, s)]) for s in skills]
        mean = sum(diffs) / len(diffs)
        lo, hi = compare.bootstrap_ci_95(diffs)
        won = sum(d > 0 for d in diffs)
        lost = sum(d < 0 for d in diffs)
        p = compare.exact_sign_test_p(won, lost)
        print(f"\npaired re-verdict on cross-judge-confirmed findings only "
              f"({cand} - {base}, n={len(diffs)} docs):")
        print(f"  mean {mean:+.3f}/doc  bootstrap CI [{lo:+.2f}, {hi:+.2f}]  "
              f"{won}W/{lost}L/{len(diffs) - won - lost}T  sign p={p:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
