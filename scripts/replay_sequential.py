#!/usr/bin/env python3
"""Retrospective sequential replay of the banked doctrine gates.

For each banked candidate leg, feed its per-document diffs against the
banked incumbent baseline through compare.sequential_decision in the order
the documents were actually probed, and report where the mSPRT would have
stopped, what it would have said, and what the skipped documents cost in
the real run. Zero model calls: this consumes only banked report.json data.

Repo-maintenance tool; not shipped with the skill. Python 3 stdlib only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "skills" / "skill-tuner" / "scripts"))

import compare  # noqa: E402

REPORTS = Path(__file__).resolve().parents[1] / "reports"
BASELINE = "swapgate3-probe-incumbent"
CANDIDATES = [
    ("swapgate3-probe-candidate", "v1"),
    ("swapgate4-probe-ablated", "v1-ablated"),
    ("swapgate5-probe-doctrine-v2", "v2"),
    ("swapgate6-probe-doctrine-v3", "v3"),
    ("swapgate7-probe-doctrine-v3.1", "v3.1"),
]
DELTA = 1.0


def per_target_rows(run: str) -> list[dict]:
    report = json.loads((REPORTS / run / "report.json").read_text())
    return report["probe"]["per_target"]


def main() -> None:
    base_counts = {r["target_file"]: r["findings_confirmed"]
                   for r in per_target_rows(BASELINE)}
    print(f"baseline: {BASELINE} | delta={DELTA} alpha=0.05 "
          f"sigma0={compare.SEQUENTIAL_SIGMA0}\n")
    print("| gate | full-leg verdict | seq stop | seq verdict | agree | "
          "calls saved | $ saved (est) |")
    print("| --- | --- | --- | --- | --- | --- | --- |")

    for run, label in CANDIDATES:
        rows = [r for r in per_target_rows(run) if r["target_file"] in base_counts]
        diffs: list[float] = []
        stop_at, stop_verdict = None, None
        for row in rows:  # report order == probe order
            diffs.append(float(row["findings_confirmed"]
                               - base_counts[row["target_file"]]))
            decision = compare.sequential_decision(diffs, delta=DELTA)
            if decision["stop"]:
                stop_at, stop_verdict = decision["n"], decision["stop"]
                break

        full = compare.compare_paired(
            {r["target_file"]: float(base_counts[r["target_file"]]) for r in rows},
            {r["target_file"]: float(r["findings_confirmed"]) for r in rows},
            delta=DELTA,
        )
        full_verdict = full["verdict"] + (
            " (regression confirmed)" if full.get("regression_confirmed")
            and full["verdict"] == "inconclusive" else ""
        )

        if stop_at is None:
            print(f"| {label} | {full_verdict} | never (ran all {len(rows)}) "
                  f"| undecided | n/a | 0 | $0.00 |")
            continue

        skipped = rows[stop_at:]
        calls_saved = sum(r["probe_calls"] + r["verify_calls"] for r in skipped)
        trials = json.loads((REPORTS / run / "report.json").read_text())
        cost_rows = []
        trials_path = REPORTS / run / "trials.jsonl"
        for line in trials_path.read_text().splitlines():
            cost_rows.append(json.loads(line))
        total_cost = sum(r.get("cost_usd") or 0 for r in cost_rows)
        total_calls = len(cost_rows)
        dollars_saved = total_cost * calls_saved / total_calls if total_calls else 0.0
        # Sequential-vs-full agreement: not_worse and better both pass the
        # gate; worse and inconclusive-with-regression both fail it.
        seq_pass = stop_verdict in ("better", "not_worse")
        full_pass = full["verdict"] in ("better", "not_worse")
        agree = "PASS-agree" if seq_pass == full_pass else "DISAGREE"
        print(f"| {label} | {full_verdict} | n={stop_at}/{len(rows)} "
              f"| {stop_verdict} | {agree} | {calls_saved}/{total_calls} "
              f"| ${dollars_saved:.2f} |")


if __name__ == "__main__":
    main()
