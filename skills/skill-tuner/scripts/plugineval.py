#!/usr/bin/env python3
"""Read `claude plugin eval` results and supply the verdict they stop short of.
Python 3 standard library only.

`claude plugin eval` (Claude Code v2.1.269+) runs a plugin's cases in isolated
sessions, with the plugin and without it, and writes `aggregate-result.json`:
a versioned document (``schemaVersion: 1``, "new fields are added without
renaming existing ones") with a per-case ``aggregates`` block and per-run
scores under ``cases[].arms.with[]`` and ``cases[].arms.without[]``. What it
reports is a three-run mean per case, a ``meanDelta``, and a pass/fail
against ``--threshold``. No interval, no margin, no way to compare two
versions of the same plugin. Same gap as skill-creator's benchmark, cleaner
input: a schema, not a directory layout.

So this module extracts and ``compare.compare_paired`` decides. Two pairings:

- **with vs without**, from ONE result file: the case's with-arm score
  against its without-arm score (``aggregates.score`` vs
  ``aggregates.scoreWithout``). Answers "did the plugin help, with an
  interval and a margin" instead of a bare ``Δ``.
- **run vs run**, from TWO result files of the same suite: with-arm scores
  paired by case name. Answers "is this version of the plugin better than
  that one", which the runner cannot ask at all.

Integration is at the file boundary, deliberately, as with skillcreator.py:
the document is read as data, unknown fields are ignored, and nothing here
depends on the CLI's internals. Two deliberate refusals: a ``partial: true``
document (cost ceiling, interruption or auth failure cut the suite short) is
not a series, and ``tracePath`` is never read (it points at a temp directory
the runner deletes unless ``--keep-temp`` was passed).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import compare

SCHEMA_VERSION = 1
ARMS = ("with", "without")


class PluginEvalError(RuntimeError):
    """Raised when a result document cannot be read as `claude plugin eval`
    writes them, or when the requested arm is not in it."""


def load_result(path: Path) -> dict[str, Any]:
    """Read one aggregate-result.json. Refuses documents the runner marked
    partial, and anything that is not a case list."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PluginEvalError(f"{path}: cannot read plugin eval result: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise PluginEvalError(f"{path}: expected an aggregate-result.json with a cases list")
    if data.get("partial"):
        reason = data.get("partialReason") or "unknown reason"
        raise PluginEvalError(
            f"{path}: the runner marked this document partial ({reason}); "
            "a suite that did not finish is not a paired series"
        )
    return data


def schema_warnings(path: Path, data: Mapping[str, Any]) -> list[str]:
    version = data.get("schemaVersion")
    if version != SCHEMA_VERSION:
        return [
            f"{path}: schemaVersion is {version!r}, this reader was written against "
            f"{SCHEMA_VERSION}; fields are added without renaming, so the pairing "
            "below is probably still right, but check the docs before trusting it"
        ]
    return []


def arm_scores(data: Mapping[str, Any], arm: str, *, source: str = "") -> dict[str, float]:
    """The per-case series for one arm: ``aggregates.score`` for the with-arm,
    ``aggregates.scoreWithout`` for the without-arm. The with-arm mean is the
    runner's own case score; the without-arm field exists only when the run
    had a baseline arm (``--ablation with-without``, the default when a plugin
    resolves), so a single-arm run refuses here rather than pairing against
    nothing."""
    if arm not in ARMS:
        raise PluginEvalError(f"{source}: unknown arm {arm!r}; expected one of {', '.join(ARMS)}")
    key = "score" if arm == "with" else "scoreWithout"
    scores: dict[str, float] = {}
    for case in data.get("cases", []):
        name = case.get("name")
        aggregates = case.get("aggregates") or {}
        value = aggregates.get(key)
        if not isinstance(name, str) or not name:
            raise PluginEvalError(f"{source}: a case has no name")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            if arm == "without":
                raise PluginEvalError(
                    f"{source}: case {name!r} has no without-arm score; the run had no "
                    "baseline arm (ablation none), so there is nothing to pair the "
                    "with-arm against"
                )
            raise PluginEvalError(f"{source}: case {name!r} has no numeric score")
        scores[name] = float(value)
    if not scores:
        raise PluginEvalError(f"{source}: no cases in the document")
    return scores


def parse_ref(ref: str) -> tuple[Path, str]:
    """``PATH`` or ``PATH@with`` / ``PATH@without``. The default arm is the
    with-arm, so ``--baseline a.json --candidate b.json`` pairs two runs of
    the suite and ``--baseline r.json@without --candidate r.json@with`` pairs
    the arms of one run."""
    path_part, sep, arm = ref.rpartition("@")
    if sep and arm in ARMS and path_part:
        return Path(path_part), arm
    return Path(ref), "with"


def _describe(path: Path, arm: str, data: Mapping[str, Any]) -> dict[str, Any]:
    suite = data.get("suite") or {}
    plugins = [p.get("name") for p in (suite.get("plugins") or []) if isinstance(p, dict)]
    return {
        "path": str(path),
        "arm": arm,
        "claude_version": data.get("claudeVersion"),
        "ablation": suite.get("ablation"),
        "plugins": plugins,
        "cases_total": (data.get("aggregates") or {}).get("casesTotal"),
    }


def compare_results(
    baseline_ref: str,
    candidate_ref: str,
    *,
    delta: float,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Pair two arm series (from one or two result files) and decide."""
    base_path, base_arm = parse_ref(baseline_ref)
    cand_path, cand_arm = parse_ref(candidate_ref)
    base_doc = load_result(base_path)
    cand_doc = load_result(cand_path) if cand_path != base_path else base_doc
    warnings = schema_warnings(base_path, base_doc)
    if cand_path != base_path:
        warnings += schema_warnings(cand_path, cand_doc)
        base_cli, cand_cli = base_doc.get("claudeVersion"), cand_doc.get("claudeVersion")
        if base_cli and cand_cli and base_cli != cand_cli:
            warnings.append(
                f"runs used different Claude Code versions ({base_cli} vs {cand_cli}); "
                "the agent under test may have moved with it"
            )
    elif base_arm == cand_arm:
        raise PluginEvalError(
            f"{base_path}: both sides name the {base_arm}-arm of the same run; "
            "pair @without against @with, or two different result files"
        )
    baseline = arm_scores(base_doc, base_arm, source=f"{base_path}@{base_arm}")
    candidate = arm_scores(cand_doc, cand_arm, source=f"{cand_path}@{cand_arm}")
    return compare.compare_paired(
        baseline,
        candidate,
        delta=delta,
        exclude=exclude,
        warnings=warnings,
        extra={
            "source": "plugin-eval",
            "baseline": _describe(base_path, base_arm, base_doc),
            "candidate": _describe(cand_path, cand_arm, cand_doc),
        },
    )
