"""Tests for reading skill-creator benchmark output (Unit 11).

skill-creator (Anthropic, first-party) already runs the experiment: eval cases,
a subagent per run, grading, and a with_skill/without_skill benchmark. What it
does not do is say whether a delta means anything -- `aggregate_benchmark.py`
reports mean and stddev, and the iteration record stores a bare
`grading_result: "won" | "lost" | "tie"` next to a pass rate, with no interval
behind it. That is the same threshold-without-a-measurement that returned
LOST, WON and WORSE for one question in this repo's own history.

So skill-tuner reads their artifacts and supplies the verdict. Integration is
at the *file* boundary, never their code: their scripts have no API contract,
use package-relative imports, and the marketplace bumps plugin SHAs nightly.
A layout is a far more stable thing to depend on than an import.

Their layout, from aggregate_benchmark.load_run_results:

    <benchmark_dir>/[runs/]eval-<n>/<config>/run-<m>/grading.json

Config directory names are discovered, not hardcoded (with_skill /
without_skill, new_skill / old_skill). eval_id comes from
eval_metadata.json when present, else from the directory name. The metric
lives at grading.summary.pass_rate.
"""

from __future__ import annotations

import json
import sys
import unittest
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import compare  # noqa: E402
import skillcreator  # noqa: E402


def _grading(pass_rate: float, *, passed: int = 1, total: int = 1) -> dict:
    return {
        "summary": {
            "pass_rate": pass_rate,
            "passed": passed,
            "failed": total - passed,
            "total": total,
        },
        "expectations": [{"text": "does the thing", "passed": passed > 0, "evidence": "x"}],
    }


def _bench(root: Path, spec: dict[int, dict[str, list[float]]], *, nested_runs=False,
           metadata=False) -> Path:
    """Materialise a skill-creator benchmark tree.

    spec: {eval_id: {config_name: [pass_rate per run, ...]}}
    """
    base = root / "runs" if nested_runs else root
    for eval_id, configs in spec.items():
        eval_dir = base / f"eval-{eval_id}"
        if metadata:
            eval_dir.mkdir(parents=True, exist_ok=True)
            (eval_dir / "eval_metadata.json").write_text(
                json.dumps({"eval_id": eval_id}), encoding="utf-8"
            )
        for config, rates in configs.items():
            for i, rate in enumerate(rates, start=1):
                run_dir = eval_dir / config / f"run-{i}"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "grading.json").write_text(
                    json.dumps(_grading(rate)), encoding="utf-8"
                )
    return root


class LoadBenchmarkTest(unittest.TestCase):
    def test_reads_their_layout_and_averages_runs_per_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {
                1: {"with_skill": [1.0, 0.8], "without_skill": [0.5, 0.5]},
                2: {"with_skill": [0.6], "without_skill": [0.4]},
            })

            loaded = skillcreator.load_benchmark(root)

            self.assertEqual({"with_skill", "without_skill"}, set(loaded))
            self.assertAlmostEqual(0.9, loaded["with_skill"]["eval-1"])  # mean of runs
            self.assertAlmostEqual(0.5, loaded["without_skill"]["eval-1"])
            self.assertAlmostEqual(0.6, loaded["with_skill"]["eval-2"])

    def test_supports_the_runs_subdirectory_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {1: {"a": [1.0], "b": [0.0]}}, nested_runs=True)
            loaded = skillcreator.load_benchmark(root)
            self.assertEqual({"a", "b"}, set(loaded))

    def test_eval_metadata_id_wins_over_directory_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eval_dir = root / "eval-0"
            (eval_dir / "with_skill" / "run-1").mkdir(parents=True)
            (eval_dir / "with_skill" / "run-1" / "grading.json").write_text(
                json.dumps(_grading(1.0)), encoding="utf-8"
            )
            eval_dir.joinpath("eval_metadata.json").write_text(
                json.dumps({"eval_id": "login-flow"}), encoding="utf-8"
            )

            loaded = skillcreator.load_benchmark(root)
            self.assertIn("login-flow", loaded["with_skill"])

    def test_config_names_are_discovered_not_assumed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {1: {"new_skill": [1.0], "old_skill": [0.5]}})
            loaded = skillcreator.load_benchmark(root)
            self.assertEqual({"new_skill", "old_skill"}, set(loaded))

    def test_a_run_without_grading_json_is_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {1: {"a": [1.0, 0.0], "b": [0.5]}})
            # Blank out one run's grading file.
            (root / "eval-1" / "a" / "run-2" / "grading.json").unlink()

            loaded = skillcreator.load_benchmark(root)
            self.assertAlmostEqual(1.0, loaded["a"]["eval-1"])  # only the surviving run

    def test_empty_or_missing_tree_raises_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(skillcreator.BenchmarkError):
                skillcreator.load_benchmark(Path(tmp))


class VerdictTest(unittest.TestCase):
    def test_supplies_an_interval_where_their_report_supplies_a_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            # with_skill wins every eval by a hair -- the kind of delta a
            # bare pass-rate comparison happily calls "won".
            root = _bench(Path(tmp), {
                i: {"with_skill": [0.55], "without_skill": [0.50]} for i in range(1, 7)
            })

            result = skillcreator.compare_benchmark(
                root, baseline="without_skill", candidate="with_skill", delta=0.1
            )

            self.assertAlmostEqual(0.05, result["mean_diff"], places=3)
            self.assertEqual(6, result["n"])
            # Zero variance: every eval moved by exactly the same amount.
            self.assertEqual("better", result["verdict"])
            self.assertTrue(result["passes_legacy_count_rule"])

    def test_a_noisy_wash_is_inconclusive_not_won(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Same total either way, wildly split per eval. Their pass-rate
            # sum would call this a tie; a threshold on a lucky sample would
            # call it won. It is neither.
            root = _bench(Path(tmp), {
                1: {"w": [1.0], "b": [0.0]},
                2: {"w": [0.0], "b": [1.0]},
                3: {"w": [1.0], "b": [0.0]},
                4: {"w": [0.0], "b": [1.0]},
                5: {"w": [0.5], "b": [0.5]},
            })

            result = skillcreator.compare_benchmark(
                root, baseline="b", candidate="w", delta=0.1
            )

            self.assertEqual("inconclusive", result["verdict"])
            self.assertLess(result["ci_low"], -0.1)

    def test_unpaired_eval_refuses_rather_than_dropping_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {
                1: {"w": [1.0], "b": [0.5]},
                2: {"w": [1.0], "b": [0.5]},
                3: {"w": [1.0], "b": [0.5]},
                4: {"w": [1.0]},  # baseline never ran this one
            })

            with self.assertRaises(compare.ComparisonError):
                skillcreator.compare_benchmark(root, baseline="b", candidate="w", delta=0.1)

    def test_naming_a_config_that_is_not_there_lists_what_is(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {1: {"with_skill": [1.0], "without_skill": [0.5]}})

            with self.assertRaises(skillcreator.BenchmarkError) as ctx:
                skillcreator.compare_benchmark(
                    root, baseline="nope", candidate="with_skill", delta=0.1
                )

            self.assertIn("without_skill", str(ctx.exception))

    def test_result_records_where_the_numbers_came_from(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {i: {"w": [0.6], "b": [0.5]} for i in range(1, 5)})

            result = skillcreator.compare_benchmark(
                root, baseline="b", candidate="w", delta=0.1
            )

            self.assertEqual("skill-creator benchmark", result["source"])
            self.assertEqual("pass_rate", result["metric"])
            self.assertEqual(str(root), result["benchmark_dir"])


class CliTest(unittest.TestCase):
    """End-to-end through tune.py, since the wiring is where a reader like
    this usually breaks."""

    def _run(self, argv: list[str]) -> tuple[int, str]:
        import contextlib
        import io

        import tune

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = tune.main(argv)
        return code, buf.getvalue()

    def test_compare_reads_a_benchmark_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {
                i: {"with_skill": [0.9], "without_skill": [0.4]} for i in range(1, 6)
            })

            code, out = self._run([
                "compare", "--skill-creator", str(root),
                "--baseline", "without_skill", "--candidate", "with_skill",
                "--delta", "0.05",
            ])

            self.assertEqual(0, code)  # better / not_worse exit 0
            self.assertIn("skill-creator benchmark", out)
            self.assertIn("pass_rate", out)
            self.assertIn("better", out)

    def test_delta_is_required_for_a_benchmark_source(self):
        # 1.0 is a margin in findings per document. Applied to a 0..1 pass
        # rate it would call any regression tolerable, so the default must
        # not silently carry over.
        with tempfile.TemporaryDirectory() as tmp:
            root = _bench(Path(tmp), {i: {"a": [0.1], "b": [0.9]} for i in range(1, 5)})

            code, out = self._run([
                "compare", "--skill-creator", str(root),
                "--baseline", "b", "--candidate", "a",
            ])

            self.assertEqual(2, code)
            self.assertIn("--delta is required", out)

    def test_probe_reports_still_default_their_delta(self):
        # The report path keeps its 1.0 default; only the benchmark path
        # demands an explicit margin.
        import tune

        parser = tune.build_parser()
        args = parser.parse_args([
            "compare", "--baseline", "a", "--candidate", "b",
        ])
        self.assertIsNone(args.delta)
        self.assertIsNone(args.skill_creator)


if __name__ == "__main__":
    unittest.main()
