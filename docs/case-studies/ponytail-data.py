#!/usr/bin/env python3
"""Build the paired series for the Ponytail case study from the maintainer's
published corrected benchmark (DietrichGebert/ponytail,
benchmarks/results/2026-06-18-agentic.md): 12 real-repo tasks, LOC =
git-diff added lines, mean of n=4 Claude-Code-Haiku-4.5 runs per cell,
baseline arm vs ponytail arm. Transcribed 2026-08-10; verify against the
source before re-publishing. Writes reduction series (absolute LOC and
percent) against null-of-zero baselines for `tune.py compare --paired-json`.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (task, baseline LOC, ponytail LOC)
ROWS = [
    ("date-picker-frontend", 404, 23),
    ("color-picker-frontend", 287, 23),
    ("file-dropzone-frontend", 251, 95),
    ("multi-step-wizard-frontend", 571, 312),
    ("star-rating-frontend", 103, 70),
    ("command-palette-frontend", 268, 233),
    ("archive-item-backend", 175, 116),
    ("search-items-backend", 44, 44),
    ("export-csv-backend", 36, 33),
    ("bulk-delete-backend", 33, 26),
    ("duplicate-item-backend", 24, 23),
    ("count-items-backend", 21, 17),
]

abs_reduction = {t: float(b - p) for t, b, p in ROWS}
pct_reduction = {t: round(100.0 * (b - p) / b, 2) for t, b, p in ROWS}
zeros = {t: 0.0 for t, _, _ in ROWS}

(HERE / "ponytail-reduction-loc.json").write_text(json.dumps(abs_reduction, indent=2) + "\n")
(HERE / "ponytail-reduction-pct.json").write_text(json.dumps(pct_reduction, indent=2) + "\n")
(HERE / "ponytail-null-zero.json").write_text(json.dumps(zeros, indent=2) + "\n")

total_base = sum(b for _, b, _ in ROWS)
total_pony = sum(p for _, _, p in ROWS)
print(f"totals: baseline {total_base} LOC, ponytail {total_pony} LOC "
      f"({100*(total_base-total_pony)/total_base:.1f}% reduction of totals)")
print(f"per-task pct reductions: {sorted(pct_reduction.values())}")
