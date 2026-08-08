#!/usr/bin/env python3
"""Read skill-creator benchmark output and supply the missing verdict.
Python 3 standard library only.

skill-creator (Anthropic, first-party) already runs the experiment properly:
eval cases, an isolated subagent per run, graded expectations, and a
with_skill/without_skill benchmark. What it stops short of is saying whether a
delta means anything. `aggregate_benchmark.py` reports mean and stddev, and the
improvement record stores a bare ``grading_result: "won" | "lost" | "tie"``
beside a pass rate. A threshold with no interval behind it cannot express *we
could not tell*, so it answers every time -- and on a noisy measurement most of
those answers are luck. This repo has the receipts: one question, three runs,
LOST at n=1, WON at n=6, WORSE at n=16.

So this module extracts and ``compare.compare_paired`` decides. Nothing here
duplicates their harness; running the experiment is their job and they do it
better than a second implementation would.

**Integration is at the file boundary, deliberately.** Their scripts have no
API contract, import package-relative, and the official marketplace bumps
plugin SHAs nightly -- importing them would break on someone else's schedule.
A directory layout is a far more stable thing to depend on, and this reader
mirrors ``aggregate_benchmark.load_run_results`` rather than calling it:

    <benchmark_dir>/[runs/]eval-<n>/<config>/run-<m>/grading.json

Config directory names are discovered, never assumed -- they are
with_skill/without_skill in one flow and new_skill/old_skill in another.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

import compare

DEFAULT_METRIC = "pass_rate"


class BenchmarkError(RuntimeError):
    """Raised when a benchmark tree cannot be read as skill-creator writes
    them, or when a named config is not in it."""


def _eval_key(eval_dir: Path) -> str:
    """Their eval identity: eval_metadata.json wins, directory name is the
    fallback. Mirrors aggregate_benchmark's precedence so a tree read by both
    tools lines up case for case."""
    metadata = eval_dir / "eval_metadata.json"
    if metadata.is_file():
        try:
            recorded = json.loads(metadata.read_text(encoding="utf-8")).get("eval_id")
        except (json.JSONDecodeError, OSError):
            recorded = None
        if recorded is not None:
            return str(recorded)
    return eval_dir.name


def _metric_from_grading(grading: Mapping[str, Any], metric: str) -> float | None:
    summary = grading.get("summary")
    if isinstance(summary, Mapping) and metric in summary:
        return float(summary[metric])
    if metric in grading:
        return float(grading[metric])
    return None


def load_benchmark(
    benchmark_dir: Path | str, *, metric: str = DEFAULT_METRIC
) -> dict[str, dict[str, float]]:
    """Load a benchmark tree into ``{config: {eval_key: mean metric}}``.

    Runs within one (config, eval) are averaged: skill-creator runs each case
    several times precisely because a single run is noisy, and the mean is the
    per-case number worth pairing on. A run whose grading.json is missing or
    unreadable is skipped rather than fatal -- one lost run should not discard
    the case that survived beside it.
    """
    root = Path(benchmark_dir)
    if not root.is_dir():
        raise BenchmarkError(f"not a directory: {root}")

    search_dir = root / "runs" if (root / "runs").is_dir() else root
    eval_dirs = sorted(search_dir.glob("eval-*"))
    if not eval_dirs:
        raise BenchmarkError(
            f"no eval-* directories under {search_dir}. Expected skill-creator's "
            "layout: <benchmark_dir>/[runs/]eval-<n>/<config>/run-<m>/grading.json"
        )

    collected: dict[str, dict[str, list[float]]] = {}

    for eval_dir in eval_dirs:
        key = _eval_key(eval_dir)
        for config_dir in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            run_dirs = sorted(config_dir.glob("run-*"))
            if not run_dirs:
                continue  # inputs/, outputs/ and friends are not configs
            for run_dir in run_dirs:
                grading_file = run_dir / "grading.json"
                if not grading_file.is_file():
                    continue
                try:
                    grading = json.loads(grading_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                value = _metric_from_grading(grading, metric)
                if value is None:
                    continue
                collected.setdefault(config_dir.name, {}).setdefault(key, []).append(value)

    if not collected:
        raise BenchmarkError(
            f"found eval directories under {search_dir} but no readable "
            f"grading.json with a '{metric}' metric"
        )

    return {
        config: {key: statistics.mean(values) for key, values in cases.items()}
        for config, cases in collected.items()
    }


def compare_benchmark(
    benchmark_dir: Path | str,
    *,
    baseline: str,
    candidate: str,
    delta: float,
    metric: str = DEFAULT_METRIC,
    exclude: Sequence[str] = (),
) -> dict[str, Any]:
    """Pair two of a benchmark's configs by eval case and judge the difference.

    ``delta`` has no default here on purpose. For confirmed-finding counts 1.0
    is a sensible margin; for a pass rate on 0..1 it would wave through every
    regression there is. The margin is a judgment about what change would
    matter, and the caller has to make it.
    """
    loaded = load_benchmark(benchmark_dir, metric=metric)

    missing = [name for name in (baseline, candidate) if name not in loaded]
    if missing:
        raise BenchmarkError(
            f"config(s) {missing} not in this benchmark. Available: "
            f"{sorted(loaded)}"
        )

    return compare.compare_paired(
        loaded[baseline],
        loaded[candidate],
        delta=delta,
        exclude=exclude,
        extra={
            "source": "skill-creator benchmark",
            "metric": metric,
            "benchmark_dir": str(benchmark_dir),
            "baseline_config": baseline,
            "candidate_config": candidate,
        },
    )
