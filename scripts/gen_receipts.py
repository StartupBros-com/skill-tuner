#!/usr/bin/env python3
"""Generate skill-tuner's README Receipts section from live report.json
files (Unit 6). Python 3 standard library only.

This is a repo-maintenance tool, not part of the bundled skill under
skills/skill-tuner/ -- it never ships, and it never touches the eval
runner's adapter path. It reads the report.json written by a completed
`tune.py routing-parity` run and a completed `tune.py probe` run and prints
the markdown block meant to sit between the README's
``<!-- receipts:start -->`` / ``<!-- receipts:end -->`` markers. It never
writes README.md itself, so pasting the output in stays a deliberate,
reviewable step.

Usage:
    python3 scripts/gen_receipts.py \\
        --routing-report reports/receipts-routing-001/report.json \\
        --probe-report reports/receipts-probe-001/report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_routing_section(report: dict[str, Any], run_id: str) -> list[str]:
    rp = report["routing_parity"]
    lines = [
        f"### Routing-parity — `{run_id}`",
        "",
        "| Condition | Accuracy | Near-miss rejection |",
        "| --- | --- | --- |",
    ]
    for condition, score in rp["scores"].items():
        lines.append(
            f"| {condition} | {score['correct']}/{score['total']} ({score['accuracy']:.1%}) "
            f"| {score['near_miss_correct']}/{score['near_miss_total']} ({score['near_miss_accuracy']:.1%}) |"
        )
    lines.append("")
    lines.append(f"**Verdict: {rp['verdict']}**")
    if rp["failing_case_ids"]:
        lines.append("")
        lines.append(f"Failing case ids: {', '.join(rp['failing_case_ids'])}")
    lines.append("")
    return lines


# A receipts block leads with numbers; the findings themselves are evidence
# for the number, not the README's payload. Six targets can confirm a dozen
# findings whose issue text runs to several screens, which buries the result
# it is supposed to support -- so preview a few and point at the full report.
FINDING_PREVIEW_LIMIT = 3
ISSUE_PREVIEW_CHARS = 180


def _shorten(text: str, limit: int = ISSUE_PREVIEW_CHARS) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1].rstrip() + "…"


def render_probe_section(report: dict[str, Any], run_id: str) -> list[str]:
    probe = report["probe"]
    targets = probe.get("target_files") or [probe["target_file"]]
    verify_trials = probe.get("verify_trials", 1)

    headline = (
        f"**findings_confirmed: {probe['findings_confirmed']}** "
        f"(refuted: {probe['refuted_count']}, targets: {len(targets)}, "
        f"probe calls: {probe['probe_calls']}, verify calls: {probe['verify_calls']}"
    )
    if verify_trials > 1:
        headline += f" at {verify_trials} skeptics per finding"
    headline += ")"

    lines = [f"### Marginal-value probe — `{run_id}`", "", headline, ""]

    if probe.get("halted_on_budget"):
        lines.append(
            "> Partial run: the budget cap halted this battery before every "
            "target was probed. Not a verdict on the full target set."
        )
        lines.append("")

    per_target = probe.get("per_target") or []
    if len(targets) > 1 and per_target:
        lines.append("| Target | confirmed | refuted |")
        lines.append("| --- | --- | --- |")
        for entry in per_target:
            name = Path(entry["target_file"]).parent.name or entry["target_file"]
            lines.append(
                f"| {name} | {entry['findings_confirmed']} | {entry['refuted_count']} |"
            )
        lines.append("")

    findings = probe["confirmed_findings"]
    if findings:
        for finding in findings[:FINDING_PREVIEW_LIMIT]:
            lines.append(f"- **{_shorten(finding['rule'], 90)}**: {_shorten(finding['issue'])}")
        remaining = len(findings) - FINDING_PREVIEW_LIMIT
        if remaining > 0:
            lines.append(
                f"- …and {remaining} more, with quotes and proposed fixes, in "
                f"`reports/{run_id}/report.md`"
            )
    else:
        lines.append("No confirmed findings on this pass.")
    lines.append("")
    return lines


def render_receipts(routing_report: dict[str, Any], routing_run_id: str, probe_report: dict[str, Any], probe_run_id: str) -> str:
    lines: list[str] = []
    lines.extend(render_routing_section(routing_report, routing_run_id))
    lines.extend(render_probe_section(probe_report, probe_run_id))
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--routing-report", type=Path, required=True, help="path to a routing-parity report.json")
    parser.add_argument("--routing-run-id", default=None, help="defaults to the report's parent directory name")
    parser.add_argument("--probe-report", type=Path, required=True, help="path to a probe report.json")
    parser.add_argument("--probe-run-id", default=None, help="defaults to the report's parent directory name")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    routing_run_id = args.routing_run_id or args.routing_report.resolve().parent.name
    probe_run_id = args.probe_run_id or args.probe_report.resolve().parent.name

    routing_report = _load(args.routing_report)
    probe_report = _load(args.probe_report)

    print(render_receipts(routing_report, routing_run_id, probe_report, probe_run_id), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
