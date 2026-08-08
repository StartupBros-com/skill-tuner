#!/usr/bin/env python3
"""Differential test: does our reader see a benchmark the way skill-creator does?

`skillcreator.load_benchmark` was written from reading Anthropic's
`aggregate_benchmark.load_run_results`, and its unit tests use fixtures built
from that same reading. If the reading is wrong, the fixtures agree with the
reader and both are wrong together. That is not a test, it is an echo.

This feeds identical trees to both implementations and compares what they
extract. It needs skill-creator installed, so it is a maintenance script rather
than a unit test -- a suite that fails on a machine without a particular plugin
cache is the coupling this repo already removed once from test_doctor.

Run it after any change to the reader, and after skill-creator updates:

    python3 scripts/validate_skillcreator_reader.py

Exits non-zero on any disagreement.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import statistics
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "skill-tuner" / "scripts"))

import skillcreator  # noqa: E402

SEARCH_ROOTS = [
    Path.home() / ".claude/plugins/cache/claude-plugins-official/skill-creator",
    Path.home() / ".claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator",
]


def find_their_aggregator() -> Path | None:
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for candidate in sorted(root.rglob("aggregate_benchmark.py")):
            return candidate
    return None


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("their_aggregate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Tree builders -- each returns (name, root, expected_config_names)
# --------------------------------------------------------------------------


def _write_run(run_dir: Path, pass_rate: float) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "grading.json").write_text(
        json.dumps({"summary": {"pass_rate": pass_rate, "passed": 1, "failed": 0, "total": 1}}),
        encoding="utf-8",
    )


def build_trees(base: Path) -> list[tuple[str, Path]]:
    trees: list[tuple[str, Path]] = []

    # 1. The ordinary shape: one run per eval per config.
    root = base / "simple"
    for i in (1, 2, 3):
        _write_run(root / f"eval-{i}" / "with_skill" / "run-1", 0.5 + i / 10)
        _write_run(root / f"eval-{i}" / "without_skill" / "run-1", 0.2 + i / 10)
    trees.append(("simple", root))

    # 2. Unequal run counts -- where a mean-of-means and a mean-of-runs part ways.
    root = base / "uneven"
    _write_run(root / "eval-1" / "with_skill" / "run-1", 1.0)
    _write_run(root / "eval-1" / "with_skill" / "run-2", 0.0)
    _write_run(root / "eval-2" / "with_skill" / "run-1", 0.5)
    _write_run(root / "eval-1" / "without_skill" / "run-1", 0.4)
    _write_run(root / "eval-2" / "without_skill" / "run-1", 0.6)
    trees.append(("uneven-run-counts", root))

    # 3. The runs/ subdirectory layout their loader also accepts.
    root = base / "nested"
    for i in (1, 2):
        _write_run(root / "runs" / f"eval-{i}" / "a" / "run-1", 0.7)
        _write_run(root / "runs" / f"eval-{i}" / "b" / "run-1", 0.3)
    trees.append(("nested-runs-dir", root))

    # 4. eval_metadata.json overriding the directory name.
    root = base / "metadata"
    for i, label in enumerate(["login-flow", "checkout"], start=1):
        eval_dir = root / f"eval-{i}"
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "eval_metadata.json").write_text(
            json.dumps({"eval_id": label}), encoding="utf-8"
        )
        _write_run(eval_dir / "with_skill" / "run-1", 0.8)
        _write_run(eval_dir / "without_skill" / "run-1", 0.2)
    trees.append(("eval-metadata-id", root))

    # 5. A missing grading.json mid-tree.
    root = base / "missing"
    for i in (1, 2):
        _write_run(root / f"eval-{i}" / "with_skill" / "run-1", 0.9)
        _write_run(root / f"eval-{i}" / "with_skill" / "run-2", 0.1)
        _write_run(root / f"eval-{i}" / "without_skill" / "run-1", 0.5)
    (root / "eval-1" / "with_skill" / "run-2" / "grading.json").unlink()
    trees.append(("missing-grading-json", root))

    # 6. Non-config directories sitting beside the configs.
    root = base / "noise"
    for i in (1, 2):
        _write_run(root / f"eval-{i}" / "with_skill" / "run-1", 0.6)
        _write_run(root / f"eval-{i}" / "without_skill" / "run-1", 0.4)
        (root / f"eval-{i}" / "inputs").mkdir(parents=True, exist_ok=True)
        (root / f"eval-{i}" / "outputs").mkdir(parents=True, exist_ok=True)
        (root / f"eval-{i}" / "outputs" / "result.txt").write_text("x", encoding="utf-8")
    trees.append(("non-config-dirs", root))

    # 7. The other config naming their loader supports.
    root = base / "versions"
    for i in (1, 2, 3):
        _write_run(root / f"eval-{i}" / "new_skill" / "run-1", 0.55)
        _write_run(root / f"eval-{i}" / "old_skill" / "run-1", 0.45)
    trees.append(("new-vs-old-skill", root))

    return trees


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------


def theirs_per_eval(their_module, root: Path) -> dict[str, dict[str, float]]:
    """Reduce their per-run rows to per-(config, eval) means, keyed by the
    eval identity they report."""
    raw = their_module.load_run_results(root)
    out: dict[str, dict[str, list[float]]] = {}
    for config, rows in raw.items():
        for row in rows:
            key = str(row["eval_id"])
            out.setdefault(config, {}).setdefault(key, []).append(row["pass_rate"])
    return {
        config: {k: statistics.mean(v) for k, v in cases.items()}
        for config, cases in out.items()
    }


def normalise(mapping: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """Their eval_id is an int parsed out of `eval-<n>`; ours is the directory
    name. Same identity, different spelling -- align on the numeric part where
    one exists so the comparison is about *values*, not naming."""
    aligned: dict[str, dict[str, float]] = {}
    for config, cases in mapping.items():
        aligned[config] = {}
        for key, value in cases.items():
            stripped = key[len("eval-"):] if key.startswith("eval-") else key
            aligned[config][stripped] = round(value, 9)
    return aligned


def main() -> int:
    aggregator_path = find_their_aggregator()
    if aggregator_path is None:
        print("skill-creator not installed; nothing to differentially test.")
        print("Install with: /plugin install skill-creator@claude-plugins-official")
        return 0

    print(f"their aggregator: {aggregator_path}")
    their_module = load_module(aggregator_path)

    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for name, root in build_trees(base):
            mine = normalise(skillcreator.load_benchmark(root))
            theirs = normalise(theirs_per_eval(their_module, root))

            if mine == theirs:
                configs = ", ".join(sorted(mine))
                print(f"  ok    {name:<22} configs=[{configs}]")
            else:
                failures += 1
                print(f"  FAIL  {name}")
                print(f"        ours:   {json.dumps(mine, sort_keys=True)}")
                print(f"        theirs: {json.dumps(theirs, sort_keys=True)}")

    print()
    if failures:
        print(f"{failures} tree(s) read differently. Our reader does not match theirs.")
        return 1
    print("Both readers extract the same values from every tree shape.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
