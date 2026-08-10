#!/usr/bin/env python3
"""skill-tuner sequential gate: probe-until-decided against a banked baseline.

The fixed-n gate probes every target and only then compares; at ~$0.50 a
document that spends the whole leg even when the answer was visible by
document six. This mode probes targets one at a time in config order, pairs
each fresh count against the banked baseline's count for the same document,
and after every document consults two mixture SPRTs
(``compare.sequential_decision``): stop the moment non-inferiority at the
declared margin -- or a regression past it, or superiority -- is
established, else continue to the full set.

Anytime validity comes from Ville's inequality on the mSPRT martingale,
under a normal likelihood with the pre-registered sd bound
``compare.SEQUENTIAL_SIGMA0`` (overstating sigma delays stopping, never
hastens it). Two honesty rails are structural:

- The fixed-n paired verdict on whatever was collected is always computed
  and reported beside the sequential decision, and it remains the verdict
  of record for cross-run comparison.
- The report names how many targets were skipped and what that saved; a
  stopped run is never presented as a full-leg probe.

Python 3 standard library only. Every input resolves through provenance
before any spend; targets are all resolved up front, so a mid-run edit to a
skipped target cannot change what an un-stopped run would have probed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

import compare
import probe as probe_module
import provenance
import tune

AdapterFn = Callable[[str, str], tune.AdapterResult]


class GateError(ValueError):
    """Raised before any spend when the gate cannot run honestly: a config
    target missing from the baseline, or too few shared targets to ever
    reach a fixed-n verdict."""


def run_gate(
    config: Mapping[str, Any],
    adapter: AdapterFn,
    run_dir: Path,
    baseline_report: Mapping[str, Any],
    *,
    delta: float,
    alpha: float = 0.05,
    sigma0: float = compare.SEQUENTIAL_SIGMA0,
    base_dir: Path | None = None,
    retries: int = probe_module.DEFAULT_RETRIES,
    budget_usd: float | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    resolved_base_dir = base_dir if base_dir is not None else Path(".")
    probe_config = probe_module.load_config(config, base_dir=resolved_base_dir)
    started_at = provenance.utc_now()

    baseline_counts = compare.per_target_counts(baseline_report)
    missing = [str(p) for p in probe_config.target_paths if str(p) not in baseline_counts]
    if missing:
        raise GateError(
            "config targets absent from the baseline run (pairing would be "
            f"impossible): {missing[:3]}{'...' if len(missing) > 3 else ''}"
        )
    if len(probe_config.target_paths) < compare.MIN_DOCUMENTS:
        raise GateError(
            f"need at least {compare.MIN_DOCUMENTS} shared targets; got "
            f"{len(probe_config.target_paths)}"
        )

    doctrine_input = provenance.resolve_input(
        probe_config.doctrine_path, role="doctrine", pin=probe_config.pin
    )
    target_inputs = [
        provenance.resolve_input(path, role="target", pin=probe_config.pin)
        for path in probe_config.target_paths
    ]

    rows: list[dict[str, Any]] = []
    per_target: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    diffs: list[float] = []
    paired_base: dict[str, float] = {}
    paired_cand: dict[str, float] = {}
    overflow = 0
    halted_on_budget = False
    decision: dict[str, Any] = compare.sequential_decision(
        [], delta=delta, alpha=alpha, sigma0=sigma0
    )
    spend_state = {"spent": 0.0}
    guarded = probe_module.budget_guarded(adapter, budget_usd, spend_state)

    run_dir.mkdir(parents=True, exist_ok=True)
    trials_path = run_dir / "trials.jsonl"

    for index, target_input in enumerate(target_inputs, start=1):
        target_key = str(target_input.path)
        before = len(rows)
        try:
            verified, target_overflow = probe_module.probe_one_target(
                target_input.text,
                doctrine_input.text,
                adapter=guarded,
                probe_config=probe_config,
                rows=rows,
                trials_path=trials_path,
                retries=retries,
                prefix=f"t{index}-",
            )
        except probe_module.BudgetExhausted:
            halted_on_budget = True
            # The in-flight target's completed calls are durable and paid
            # for; attribute them, flagged incomplete, so the top-level
            # totals reconcile against per_target (mirrors run_probe).
            target_rows = rows[before:]
            if target_rows:
                per_target.append({
                    "target_file": target_key,
                    "findings_confirmed": None,
                    "refuted_count": None,
                    "overflow": 0,
                    "probe_calls": sum(1 for r in target_rows if r["condition"] == "probe"),
                    "verify_calls": sum(1 for r in target_rows if r["condition"] == "verify"),
                    "complete": False,
                })
            break

        confirmed = sum(1 for item in verified if item.verdict == "confirmed")
        overflow += target_overflow
        diffs.append(float(confirmed - baseline_counts[target_key]))
        paired_base[target_key] = float(baseline_counts[target_key])
        paired_cand[target_key] = float(confirmed)

        target_rows = rows[before:]
        per_target.append({
            "target_file": target_key,
            "findings_confirmed": confirmed,
            "refuted_count": sum(1 for item in verified if item.verdict == "refuted"),
            "overflow": target_overflow,
            "probe_calls": sum(1 for r in target_rows if r["condition"] == "probe"),
            "verify_calls": sum(1 for r in target_rows if r["condition"] == "verify"),
            "complete": True,
        })

        decision = compare.sequential_decision(
            diffs, delta=delta, alpha=alpha, sigma0=sigma0
        )
        trace.append({
            "n": decision["n"],
            "target_file": target_key,
            "diff": diffs[-1],
            "mean": decision["mean"],
            "lambda_margin": decision["lambda_margin"],
            "lambda_zero": decision["lambda_zero"],
            "stop": decision["stop"],
        })
        if decision["stop"] and len(diffs) >= compare.MIN_DOCUMENTS:
            break

    probed_n = len(diffs)
    total_n = len(target_inputs)
    skipped = total_n - probed_n

    fixed_n_result: dict[str, Any] | None = None
    if probed_n >= compare.MIN_DOCUMENTS:
        fixed_n_result = compare.compare_paired(paired_base, paired_cand, delta=delta)

    manifest = provenance.build_manifest(
        run_id=run_id or run_dir.name,
        inputs=[doctrine_input, *target_inputs],
        model_pin=probe_config.model,
        resolved_models=sorted(
            {row["model_resolved"] for row in rows if row.get("model_resolved")}
        ),
        started_at=started_at,
        finished_at=provenance.utc_now(),
        cli_version=provenance.cli_version(),
        tool_version=provenance.tool_version(),
        extra={"eval": "gate", "pin": probe_config.pin},
    )

    json_path, md_path = tune.write_report(run_dir, rows, ("probe", "verify"), manifest)
    summary = json.loads(json_path.read_text(encoding="utf-8"))
    gate_block: dict[str, Any] = {
        "delta": delta,
        "alpha": alpha,
        "sigma0": sigma0,
        "sequential_verdict": decision["stop"] or "undecided",
        "sigma0_exceeded": bool(decision.get("sigma0_exceeded")),
        "stopped_early": bool(decision["stop"]) and probed_n < total_n,
        "halted_on_budget": halted_on_budget,
        "targets_probed": probed_n,
        "targets_total": total_n,
        "targets_skipped": skipped,
        "doctrine_sha256": doctrine_input.sha256,
        "trace": trace,
        "per_target": per_target,
        "fixed_n": fixed_n_result,
    }
    summary["gate"] = gate_block
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "",
        "## Sequential gate verdict",
        "",
        f"**Sequential: {gate_block['sequential_verdict']}** after "
        f"{probed_n}/{total_n} targets "
        f"(delta={delta:g}, alpha={alpha:g}, sigma0={sigma0:g})",
        "",
    ]
    if gate_block["stopped_early"]:
        lines.append(
            f"- stopped early: {skipped} target(s) never probed — a stopped "
            f"run is a sequential verdict, not a full-leg probe"
        )
    if halted_on_budget:
        lines.append("- **PARTIAL: budget cap reached before a decision.**")
    if gate_block["sigma0_exceeded"]:
        lines.append(
            f"- **running sd {decision['sd']:.2f} exceeds the pre-registered "
            f"sigma0={sigma0:g}: the anytime guarantee is weakened; treat a "
            f"stop with caution and prefer the fixed-n verdict**"
        )
    if fixed_n_result is not None:
        lines.append(
            f"- fixed-n verdict of record on the {probed_n} collected pairs: "
            f"**{fixed_n_result['verdict']}** "
            f"(95% CI [{fixed_n_result['ci_low']:+.2f}, "
            f"{fixed_n_result['ci_high']:+.2f}])"
        )
    lines.append("")
    lines.append("| n | target | diff | mean | lambda_margin | lambda_zero | stop |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for step in trace:
        name = Path(step["target_file"]).parent.name
        lines.append(
            f"| {step['n']} | {name} | {step['diff']:+g} | {step['mean']:+.3f} "
            f"| {step['lambda_margin']:.2f} | {step['lambda_zero']:.2f} "
            f"| {step['stop'] or ''} |"
        )
    lines.append("")
    with md_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    return {
        "run_dir": str(run_dir),
        "spent_usd": round(spend_state["spent"], 6),
        **gate_block,
        "report_json": str(json_path),
        "report_md": str(md_path),
    }
