#!/usr/bin/env python3
"""skill-tuner end-task A/B: does a skill edit change what agents produce?

The probe grades documents; routing-parity grades descriptions; this grades
BEHAVIOR: the same task briefs are answered under two versions of a skill,
outputs are scored by a deterministic grader you supply, and the paired
verdict engine decides. It institutionalizes the shape of the first two
end-task experiments in this repo (experiments/ab-curl-bash-installer,
experiments/authoring-ab) with their lessons baked in:

- Every generation is a single completion through the injected adapter --
  the CLI wires ``tune.call_adapter``, whose envelope disables tools. The
  first experiment's ad-hoc runner bypassed that chokepoint and paid ~10x
  per call while the model ran an agentic session.
- Grading is a SCRIPT, not a judge: the grader is invoked per output as
  ``python3 <grader> <output_file> <case_id> <condition>`` and must print
  JSON with a ``pass_rate`` float in [0, 1] (optionally ``expectations``).
  Doctrine-neutral, rerunnable, free.
- The verdict is ``compare.compare_paired`` on per-case condition means,
  at a margin the caller states. All four outcomes are possible.

Config (JSON): ``model``, ``trials``, ``conditions`` (exactly two:
name -> file path or list of paths, concatenated in order), optional
``baseline_condition`` (default: first listed), ``cases``
(list of {id, prompt}). Python 3 standard library only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

import compare
import probe as probe_module
import provenance
import tune

AdapterFn = Callable[[str, str], tune.AdapterResult]

_FENCE_RE = re.compile(r"\A```[a-zA-Z]*\n(.*)\n```\s*\Z", re.DOTALL)


class EndtaskError(ValueError):
    """Raised before any spend on a malformed config or grader."""


def build_prompt(skill_text: str, brief: str) -> str:
    return (
        "You have this skill loaded. Follow it.\n\n"
        "=== SKILL ===\n"
        f"{skill_text}\n"
        "=== END SKILL ===\n\n"
        f"Task: {brief}\n\n"
        "Respond directly with plain text — do not use any tools. Output "
        "ONLY the complete deliverable — no commentary, no outer markdown "
        "fences."
    )


def _strip_fence(text: str) -> str:
    match = _FENCE_RE.match(text.strip())
    return match.group(1) if match else text


def load_config(config: Mapping[str, Any], *, base_dir: Path) -> dict[str, Any]:
    conditions = config.get("conditions")
    if not isinstance(conditions, Mapping) or len(conditions) != 2:
        raise EndtaskError("config needs exactly two conditions (name -> path)")
    cases = config.get("cases")
    if not cases:
        raise EndtaskError("config needs a non-empty cases list")
    if len(cases) < compare.MIN_DOCUMENTS:
        raise EndtaskError(
            f"need at least {compare.MIN_DOCUMENTS} cases for a paired verdict; "
            f"got {len(cases)}"
        )
    model = config.get("model")
    if not model:
        raise EndtaskError("config must name a model pin")
    names = list(conditions)
    baseline = config.get("baseline_condition", names[0])
    if baseline not in conditions:
        raise EndtaskError(f"baseline_condition {baseline!r} is not a condition")
    resolved: dict[str, list[Path]] = {}
    for name, raw in conditions.items():
        paths = [raw] if isinstance(raw, str) else list(raw)
        resolved[name] = [
            p if (p := Path(item)).is_absolute() else base_dir / item
            for item in paths
        ]
    return {
        "model": str(model),
        "trials": int(config.get("trials", 2)),
        "conditions": resolved,
        "baseline": baseline,
        "candidate": next(n for n in names if n != baseline),
        "cases": [{"id": str(c["id"]), "prompt": str(c["prompt"])} for c in cases],
    }


def run_grader(grader: Path, output_file: Path, case_id: str, condition: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(grader), str(output_file), case_id, condition],
        capture_output=True, text=True,
    )
    if completed.returncode != 0:
        raise EndtaskError(
            f"grader failed on {case_id}/{condition}: {completed.stderr.strip()[:200]}"
        )
    try:
        payload = json.loads(completed.stdout)
        rate = float(payload["pass_rate"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise EndtaskError(
            f"grader must print JSON with a numeric pass_rate; got "
            f"{completed.stdout[:120]!r} ({exc})"
        )
    if not 0.0 <= rate <= 1.0:
        raise EndtaskError(f"pass_rate {rate} outside [0, 1]")
    return payload


def run_endtask(
    config: Mapping[str, Any],
    adapter: AdapterFn,
    run_dir: Path,
    grader: Path,
    *,
    delta: float,
    base_dir: Path | None = None,
    budget_usd: float | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    resolved_base = base_dir if base_dir is not None else Path(".")
    spec = load_config(config, base_dir=resolved_base)
    if not grader.is_file():
        raise EndtaskError(f"grader not found: {grader}")
    started_at = provenance.utc_now()

    inputs = []
    skill_texts: dict[str, str] = {}
    for name, paths in spec["conditions"].items():
        parts = []
        for path in paths:
            item = provenance.resolve_input(path, role="target")
            inputs.append(item)
            parts.append(item.text)
        skill_texts[name] = "\n\n".join(parts)

    spend_state = {"spent": 0.0}
    guarded = probe_module.budget_guarded(adapter, budget_usd, spend_state)
    rows: list[dict[str, Any]] = []
    run_dir.mkdir(parents=True, exist_ok=True)
    trials_path = run_dir / "trials.jsonl"
    scores: dict[str, dict[str, list[float]]] = {n: {} for n in spec["conditions"]}
    halted = False

    for case in spec["cases"]:
        for condition in spec["conditions"]:
            prompt = build_prompt(skill_texts[condition], case["prompt"])
            for trial in range(1, spec["trials"] + 1):
                try:
                    result = guarded(prompt, spec["model"])
                except probe_module.BudgetExhausted:
                    halted = True
                    break
                text = _strip_fence(result.text)
                out_dir = run_dir / "outputs" / case["id"] / condition / f"run-{trial}"
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "output.md").write_text(text)
                grading = run_grader(grader, out_dir / "output.md",
                                     case["id"], condition)
                (out_dir / "grading.json").write_text(
                    json.dumps(grading, indent=2) + "\n")
                tune.append_jsonl(trials_path, {
                    "case_id": f"{case['id']}", "trial": trial,
                    "condition": condition, "response": text[:2000],
                    "cost_usd": result.cost_usd,
                    "model_resolved": result.model_resolved,
                    "pass_rate": grading["pass_rate"],
                })
                rows.append({"case_id": case["id"], "trial": trial,
                             "condition": condition,
                             "pass_rate": grading["pass_rate"],
                             "cost_usd": result.cost_usd})
                scores[condition].setdefault(case["id"], []).append(
                    grading["pass_rate"])
            if halted:
                break
        if halted:
            break

    def case_means(condition: str) -> dict[str, float]:
        return {c: sum(v) / len(v) for c, v in scores[condition].items() if v}

    base_means = case_means(spec["baseline"])
    cand_means = case_means(spec["candidate"])
    shared = sorted(set(base_means) & set(cand_means))
    verdict_result: dict[str, Any] | None = None
    if len(shared) >= compare.MIN_DOCUMENTS:
        verdict_result = compare.compare_paired(
            {c: base_means[c] for c in shared},
            {c: cand_means[c] for c in shared},
            delta=delta,
            extra={"source": "endtask", "metric": "pass_rate",
                   "baseline_config": spec["baseline"],
                   "candidate_config": spec["candidate"]},
        )

    manifest = provenance.build_manifest(
        run_id=run_id or run_dir.name,
        inputs=inputs,
        model_pin=spec["model"],
        resolved_models=sorted({r["model_resolved"] for r in rows
                                if r.get("model_resolved")}),
        started_at=started_at,
        finished_at=provenance.utc_now(),
        cli_version=provenance.cli_version(),
        tool_version=provenance.tool_version(),
        extra={"eval": "endtask"},
    )
    report = {
        "manifest": manifest,
        "endtask": {
            "delta": delta,
            "baseline": spec["baseline"],
            "candidate": spec["candidate"],
            "halted_on_budget": halted,
            "cases_scored": len(shared),
            "per_case": [
                {"case": c, "baseline": base_means.get(c),
                 "candidate": cand_means.get(c)} for c in shared
            ],
            "verdict": verdict_result,
        },
    }
    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    md_path = run_dir / "report.md"
    md_lines = ["# End-task A/B", ""]
    if verdict_result is not None:
        md_lines.append(compare.render(verdict_result))
    if halted:
        md_lines.append("\n**PARTIAL: budget cap reached.**")
    md_path.write_text("\n".join(md_lines) + "\n")

    return {
        "run_dir": str(run_dir),
        "spent_usd": round(spend_state["spent"], 6),
        "halted_on_budget": halted,
        "verdict": (verdict_result or {}).get("verdict", "insufficient-cases"),
        "cases_scored": len(shared),
        "result": verdict_result,
        "report_json": str(json_path),
        "report_md": str(md_path),
    }
