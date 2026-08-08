"""Tests for the generic --paired-json compare source (issue #15).

compare_paired() was always source-agnostic ("Loaders extract; this
decides"), but the CLI only exposed the probe-report and skill-creator
loaders. These tests cover the third loader: two flat {case: number} JSON
files from any external tool (first consumer: memory-dream's recall eval).

The loader validates shape only; key pairing and the MIN_DOCUMENTS floor
stay compare_paired's job, so an external series refuses on exactly the
same walls a probe report does.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import compare  # noqa: E402
import tune  # noqa: E402


def _scores_file(base: Path, name: str, scores: dict) -> Path:
    path = base / name
    path.write_text(json.dumps(scores), encoding="utf-8")
    return path


def _run_cli(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tune.main(list(argv))
    return code, out.getvalue()


class LoadPairedScoresTest(unittest.TestCase):
    def test_flat_object_of_numbers_loads_as_floats(self):
        with tempfile.TemporaryDirectory() as temp:
            path = _scores_file(Path(temp), "a.json", {"q1": 90, "q2": 72.5})
            scores = compare.load_paired_scores(path)
            self.assertEqual(scores, {"q1": 90.0, "q2": 72.5})
            self.assertTrue(all(isinstance(v, float) for v in scores.values()))

    def test_non_object_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.json"
            path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            with self.assertRaises(compare.ComparisonError):
                compare.load_paired_scores(path)

    def test_empty_object_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = _scores_file(Path(temp), "a.json", {})
            with self.assertRaises(compare.ComparisonError):
                compare.load_paired_scores(path)

    def test_non_numeric_score_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = _scores_file(Path(temp), "a.json", {"q1": "high"})
            with self.assertRaises(compare.ComparisonError):
                compare.load_paired_scores(path)

    def test_boolean_score_refuses(self):
        # bool is an int subclass; a True score is a bug upstream, not a 1.0.
        with tempfile.TemporaryDirectory() as temp:
            path = _scores_file(Path(temp), "a.json", {"q1": True})
            with self.assertRaises(compare.ComparisonError):
                compare.load_paired_scores(path)

    def test_missing_file_refuses_with_comparison_error(self):
        with self.assertRaises(compare.ComparisonError):
            compare.load_paired_scores(Path("/nonexistent/paired.json"))


class PairedJsonCliTest(unittest.TestCase):
    BASE = {"q1": 60.0, "q2": 70.0, "q3": 80.0, "q4": 55.0}

    def _files(self, temp: Path, cand: dict) -> tuple[Path, Path]:
        return (
            _scores_file(temp, "baseline.json", self.BASE),
            _scores_file(temp, "candidate.json", cand),
        )

    def test_strictly_better_series_exits_zero_with_verdict(self):
        with tempfile.TemporaryDirectory() as temp:
            base, cand = self._files(
                Path(temp), {k: v + 10 for k, v in self.BASE.items()}
            )
            code, out = _run_cli(
                "compare", "--paired-json",
                "--baseline", str(base), "--candidate", str(cand),
                "--delta", "2.0", "--json",
            )
            self.assertEqual(code, 0, out)
            result = json.loads(out)
            self.assertEqual(result["verdict"], "better")
            self.assertEqual(result["source"], "paired-json")

    def test_worse_series_exits_one(self):
        with tempfile.TemporaryDirectory() as temp:
            base, cand = self._files(
                Path(temp), {k: v - 10 for k, v in self.BASE.items()}
            )
            code, out = _run_cli(
                "compare", "--paired-json",
                "--baseline", str(base), "--candidate", str(cand),
                "--delta", "2.0", "--json",
            )
            self.assertEqual(code, 1, out)
            self.assertEqual(json.loads(out)["verdict"], "worse")

    def test_delta_is_required(self):
        with tempfile.TemporaryDirectory() as temp:
            base, cand = self._files(Path(temp), dict(self.BASE))
            code, out = _run_cli(
                "compare", "--paired-json",
                "--baseline", str(base), "--candidate", str(cand),
            )
            self.assertEqual(code, 2)
            self.assertIn("--delta is required", out)

    def test_metric_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base, cand = self._files(Path(temp), dict(self.BASE))
            code, out = _run_cli(
                "compare", "--paired-json",
                "--baseline", str(base), "--candidate", str(cand),
                "--delta", "2.0", "--metric", "pass_rate",
            )
            self.assertEqual(code, 2)
            self.assertIn("--metric", out)

    def test_skill_creator_and_paired_json_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as temp:
            base, cand = self._files(Path(temp), dict(self.BASE))
            code, out = _run_cli(
                "compare", "--paired-json", "--skill-creator", temp,
                "--baseline", str(base), "--candidate", str(cand),
                "--delta", "2.0",
            )
            self.assertEqual(code, 2)
            self.assertIn("pick one", out)

    def test_mismatched_case_sets_refuse(self):
        with tempfile.TemporaryDirectory() as temp:
            base, _ = self._files(Path(temp), dict(self.BASE))
            cand = _scores_file(Path(temp), "candidate.json", {"q1": 1.0, "zz": 2.0})
            code, out = _run_cli(
                "compare", "--paired-json",
                "--baseline", str(base), "--candidate", str(cand),
                "--delta", "2.0",
            )
            self.assertEqual(code, 2)
            self.assertIn("cannot compare", out)

    def test_skill_creator_metric_default_still_pass_rate(self):
        # --metric's default moved from "pass_rate" to None so paired-json can
        # reject an explicit flag; the skill-creator branch must still see
        # pass_rate when the flag is omitted.
        with tempfile.TemporaryDirectory() as temp:
            import skillcreator as tune_skillcreator

            captured: dict = {}

            def fake_compare_benchmark(path, **kwargs):
                captured.update(kwargs)
                raise tune_skillcreator.BenchmarkError("stop here")

            with mock.patch.object(
                tune_skillcreator, "compare_benchmark", fake_compare_benchmark
            ):
                code, out = _run_cli(
                    "compare", "--skill-creator", temp,
                    "--baseline", "without_skill", "--candidate", "with_skill",
                    "--delta", "0.05",
                )
            self.assertEqual(code, 2)
            self.assertEqual(captured.get("metric"), "pass_rate")


if __name__ == "__main__":
    unittest.main()
