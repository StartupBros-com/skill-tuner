#!/usr/bin/env python3
"""Paired comparison of two probe runs (Unit 9.6). Python 3 stdlib only.

The swap gate used to be one line: `confirmed(candidate) >= confirmed(
incumbent)` on raw totals. That rule cannot express "we could not tell", so
it always answers, and on a noisy measurement roughly half those answers are
luck. It demonstrably was: the same two doctrines failed that rule at n=1 on
a margin of 2 and passed it at n=6 on a margin of 2.

This module pairs the two runs by document -- the only comparison that
controls for documents simply differing in how many defects they contain --
and reports the difference with an interval around it. The verdict is one of:

- ``better``        the 95% interval excludes zero on the high side
- ``worse``         the interval excludes zero on the low side
- ``not_worse``     the interval's lower bound sits above -delta, i.e. any
                    regression is smaller than the margin you declared
                    tolerable (a non-inferiority claim, not an equality one)
- ``inconclusive``  none of the above: the run does not license a claim

``delta`` is the non-inferiority margin, in confirmed findings per document,
and it is an argument rather than a constant because it is a judgment about
what regression would matter, not a fact about the data.

When a run is inconclusive, ``n_for_delta`` estimates the document count that
would have resolved it at the observed variance -- so "collect more" is a
number, not a shrug.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

# Two-tailed 95% critical values. A t-table beats pulling in scipy for one
# number, and beats pretending n=6 is normal: at 5 degrees of freedom the
# correct multiplier is 2.571, not 1.96, and using the latter would narrow
# every small-sample interval by a quarter.
_T95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056,
    27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
}
_T95_LARGE = 1.96

MIN_DOCUMENTS = 3


class ComparisonError(ValueError):
    """Raised when two runs cannot be honestly compared: different documents,
    too few of them, or a different model behind each side."""


def t_critical_95(df: int) -> float:
    if df < 1:
        raise ComparisonError("need at least two documents to form an interval")
    return _T95.get(df, _T95_LARGE)


def n_to_resolve(
    mean: float, sd: float, delta: float, *, max_n: int = 500
) -> int | None:
    """Smallest document count at which a non-inferiority claim would clear,
    holding the observed mean and spread.

    The bound is ``mean - t*sd/sqrt(n) > -delta``, so how much data it takes
    depends on where the point estimate already sits, not on the spread
    alone. Sizing from spread alone can return a number *below* the n already
    collected -- which reads as "gather fewer documents" and is nonsense.
    That is what the first version of this did: n=16, verdict inconclusive,
    and it advised 12.

    Returns None when ``mean`` is already at or past ``-delta``: no sample
    size rescues a point estimate that is itself worse than the margin, and
    printing a number would promise otherwise.
    """
    if mean <= -delta:
        return None
    if sd <= 0:
        return 3
    for candidate in range(3, max_n + 1):
        if mean - t_critical_95(candidate - 1) * sd / math.sqrt(candidate) > -delta:
            return candidate
    return None


def _per_target(report: Mapping[str, Any]) -> dict[str, int]:
    probe = report.get("probe")
    if not isinstance(probe, Mapping):
        raise ComparisonError("report has no probe block")
    rows = probe.get("per_target") or []
    if not rows:
        raise ComparisonError("report has no per_target breakdown to pair on")
    return {str(row["target_file"]): int(row["findings_confirmed"]) for row in rows}


def _manifest_field(report: Mapping[str, Any], key: str) -> Any:
    manifest = report.get("manifest")
    return manifest.get(key) if isinstance(manifest, Mapping) else None


def compare_probe_reports(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    delta: float = 1.0,
    exclude: Sequence[str] = (),
) -> dict[str, Any]:
    """Pair two probe reports by document and judge the difference.

    ``exclude`` drops documents from **both** sides, matched on path suffix.
    Its purpose is a banked baseline whose input has since drifted: excluding
    the one document that moved keeps every other pair honest for the price of
    one document, where re-measuring the baseline costs a whole leg. It
    applies symmetrically by construction, because an exclusion that could hit
    one side would be a way to delete losing documents.
    """
    base_counts = _per_target(baseline)
    cand_counts = _per_target(candidate)

    excluded: list[str] = []
    if exclude:
        def dropped(name: str) -> bool:
            return any(pattern and pattern in name for pattern in exclude)

        excluded = sorted({n for n in {**base_counts, **cand_counts} if dropped(n)})
        base_counts = {k: v for k, v in base_counts.items() if not dropped(k)}
        cand_counts = {k: v for k, v in cand_counts.items() if not dropped(k)}

    if set(base_counts) != set(cand_counts):
        only_base = sorted(set(base_counts) - set(cand_counts))
        only_cand = sorted(set(cand_counts) - set(base_counts))
        raise ComparisonError(
            "runs measured different documents; pairing by position would "
            f"compare unrelated things. baseline-only={only_base} "
            f"candidate-only={only_cand}"
        )

    documents = sorted(base_counts)
    if len(documents) < MIN_DOCUMENTS:
        raise ComparisonError(
            f"need at least {MIN_DOCUMENTS} documents to say anything; got {len(documents)}"
        )

    warnings: list[str] = []
    if excluded:
        warnings.append(
            f"excluded from both sides: {', '.join(excluded)}"
        )
    base_model = _manifest_field(baseline, "model_pin")
    cand_model = _manifest_field(candidate, "model_pin")
    if base_model and cand_model and base_model != cand_model:
        raise ComparisonError(
            f"runs used different model pins ({base_model} vs {cand_model}); "
            "the difference would measure the models, not the doctrines"
        )

    base_cli = _manifest_field(baseline, "cli_version")
    cand_cli = _manifest_field(candidate, "cli_version")
    if base_cli and cand_cli and base_cli != cand_cli:
        warnings.append(
            f"runs used different claude CLI versions ({base_cli} vs {cand_cli}); "
            "the doctrine's own time-relative rule says these are not directly comparable"
        )
    if not _manifest_field(baseline, "run_id") or not _manifest_field(candidate, "run_id"):
        warnings.append(
            "at least one run predates provenance recording; its inputs and model cannot be verified"
        )

    diffs = [cand_counts[name] - base_counts[name] for name in documents]
    n = len(diffs)
    mean_diff = statistics.mean(diffs)
    sd = statistics.stdev(diffs) if n > 1 else 0.0
    se = sd / math.sqrt(n) if sd else 0.0
    half = t_critical_95(n - 1) * se
    ci_low, ci_high = mean_diff - half, mean_diff + half

    if ci_low > 0:
        verdict = "better"
    elif ci_high < 0:
        verdict = "worse"
    elif ci_low > -delta:
        verdict = "not_worse"
    else:
        verdict = "inconclusive"

    n_for_delta = n_to_resolve(mean_diff, sd, delta) if verdict == "inconclusive" else n

    return {
        "verdict": verdict,
        "delta": delta,
        "documents": documents,
        "excluded": excluded,
        "n": n,
        "baseline_total": sum(base_counts.values()),
        "candidate_total": sum(cand_counts.values()),
        "per_document": [
            {
                "target_file": name,
                "baseline": base_counts[name],
                "candidate": cand_counts[name],
                "diff": cand_counts[name] - base_counts[name],
            }
            for name in documents
        ],
        "mean_diff": mean_diff,
        "sd": sd,
        "se": se,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "documents_won": sum(1 for d in diffs if d > 0),
        "documents_lost": sum(1 for d in diffs if d < 0),
        "documents_tied": sum(1 for d in diffs if d == 0),
        # What the pre-U9 gate would have concluded, kept so a reader can see
        # exactly which claim the old rule was making.
        "passes_legacy_count_rule": sum(cand_counts.values()) >= sum(base_counts.values()),
        "n_for_delta": n_for_delta,
        "warnings": warnings,
    }


def load_report(path: Path) -> dict[str, Any]:
    report_path = path / "report.json" if path.is_dir() else path
    return json.loads(report_path.read_text(encoding="utf-8"))


def render(result: Mapping[str, Any]) -> str:
    lines = [
        "# Paired probe comparison",
        "",
        f"**Verdict: {result['verdict']}**  (non-inferiority margin delta = "
        f"{result['delta']:.2f} findings/document)",
        "",
        f"- totals: candidate {result['candidate_total']} vs baseline {result['baseline_total']} "
        f"across {result['n']} documents",
        f"- mean difference: {result['mean_diff']:+.3f} findings/document "
        f"(sd {result['sd']:.3f}, se {result['se']:.3f})",
        f"- 95% CI: [{result['ci_low']:+.2f}, {result['ci_high']:+.2f}]",
        f"- document record: {result['documents_won']} won, "
        f"{result['documents_lost']} lost, {result['documents_tied']} tied",
        f"- the pre-U9 raw-count rule would say: "
        f"{'PASS' if result['passes_legacy_count_rule'] else 'FAIL'}",
    ]
    if result["verdict"] == "inconclusive":
        needed = result["n_for_delta"]
        if needed is None:
            lines.append(
                "- no sample size resolves this: the point estimate itself is "
                "at or past the margin, so more documents would confirm a "
                "regression rather than clear one"
            )
        else:
            lines.append(
                f"- to clear the margin at this mean and spread you would need "
                f"about {needed} documents ({needed - result['n']:+d} on this run)"
            )
    lines.append("")
    lines.append("| Document | baseline | candidate | diff |")
    lines.append("| --- | --- | --- | --- |")
    for row in result["per_document"]:
        name = Path(row["target_file"]).parent.name or row["target_file"]
        lines.append(
            f"| {name} | {row['baseline']} | {row['candidate']} | {row['diff']:+d} |"
        )
    if result["warnings"]:
        lines.append("")
        lines.append("### Warnings")
        lines.append("")
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)
