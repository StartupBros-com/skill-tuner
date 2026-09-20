"""Tests for the `claude plugin eval` result reader (issue #52).

The runner writes aggregate-result.json with per-case with/without means
and a bare delta; this reader lifts the two series out and hands them to
compare_paired for the interval, the margin and the four-way verdict. The
fixture is a trimmed copy of a real 3-case run from 2026-09-20 (Claude Code
2.1.278); the synthetic documents cover the refusals.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import compare  # noqa: E402
import plugineval  # noqa: E402
import tune  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "plugin-eval-aggregate-result.json"


def _doc(cases, *, partial=False, schema=1, ablation="with-without", cli="2.1.278"):
    return {
        "schemaVersion": schema,
        "claudeVersion": cli,
        "partial": partial,
        "suite": {"ablation": ablation, "plugins": [{"name": "p", "version": "1.0.0"}]},
        "aggregates": {"casesTotal": len(cases)},
        "cases": [
            {"name": name, "aggregates": aggregates, "arms": {}}
            for name, aggregates in cases
        ],
    }


def _write(base: Path, name: str, doc: dict) -> Path:
    path = base / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def _run_cli(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tune.main(list(argv))
    return code, out.getvalue()


class FixtureTest(unittest.TestCase):
    def test_real_run_yields_both_arms_by_case(self):
        data = plugineval.load_result(FIXTURE)
        with_scores = plugineval.arm_scores(data, "with", source="f")
        without_scores = plugineval.arm_scores(data, "without", source="f")
        self.assertEqual(set(with_scores), set(without_scores))
        self.assertEqual(3, len(with_scores))
        self.assertTrue(all(0.0 <= v <= 1.0 for v in with_scores.values()))

    def test_fixture_never_needs_trace_paths(self):
        # tracePath points at a temp dir the runner deletes; the reader must
        # not touch it. The fixture keeps the field with a dead path on purpose.
        data = plugineval.load_result(FIXTURE)
        runs = [r for c in data["cases"] for r in c["arms"]["with"]]
        self.assertTrue(all("tracePath" in r for r in runs))
        plugineval.compare_results(f"{FIXTURE}@without", f"{FIXTURE}@with", delta=0.1)

    def test_with_vs_without_on_the_real_run_produces_a_verdict(self):
        result = plugineval.compare_results(f"{FIXTURE}@without", f"{FIXTURE}@with", delta=0.1)
        self.assertIn(result["verdict"], ("better", "not_worse", "inconclusive", "worse"))
        self.assertEqual("plugin-eval", result["source"])
        self.assertEqual("without", result["baseline"]["arm"])
        self.assertEqual("with", result["candidate"]["arm"])
        self.assertEqual("2.1.278", result["candidate"]["claude_version"])


class RefusalsTest(unittest.TestCase):
    def test_partial_document_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = _write(Path(temp), "r.json", _doc([("a", {"score": 1, "scoreWithout": 0})], partial=True))
            with self.assertRaises(plugineval.PluginEvalError) as raised:
                plugineval.load_result(path)
            self.assertIn("partial", str(raised.exception))

    def test_single_arm_run_has_no_without_series(self):
        with tempfile.TemporaryDirectory() as temp:
            doc = _doc([("a", {"score": 1}), ("b", {"score": 0.5}), ("c", {"score": 0})], ablation="none")
            path = _write(Path(temp), "r.json", doc)
            with self.assertRaises(plugineval.PluginEvalError) as raised:
                plugineval.compare_results(f"{path}@without", f"{path}@with", delta=0.1)
            self.assertIn("no baseline arm", str(raised.exception))

    def test_same_arm_of_same_run_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = _write(Path(temp), "r.json", _doc([("a", {"score": 1, "scoreWithout": 1})] * 3))
            with self.assertRaises(plugineval.PluginEvalError):
                plugineval.compare_results(f"{path}@with", f"{path}@with", delta=0.1)

    def test_case_set_mismatch_hits_compare_paired_wall(self):
        with tempfile.TemporaryDirectory() as temp:
            a = _write(Path(temp), "a.json", _doc([("x", {"score": 1}), ("y", {"score": 1}), ("z", {"score": 1})]))
            b = _write(Path(temp), "b.json", _doc([("x", {"score": 1}), ("y", {"score": 1}), ("q", {"score": 1})]))
            with self.assertRaises(compare.ComparisonError):
                plugineval.compare_results(str(a), str(b), delta=0.1)

    def test_unknown_schema_version_warns_but_pairs(self):
        with tempfile.TemporaryDirectory() as temp:
            cases = [("a", {"score": 1, "scoreWithout": 0.5}), ("b", {"score": 1, "scoreWithout": 1}), ("c", {"score": 0.5, "scoreWithout": 0.5})]
            path = _write(Path(temp), "r.json", _doc(cases, schema=2))
            result = plugineval.compare_results(f"{path}@without", f"{path}@with", delta=0.1)
            self.assertTrue(any("schemaVersion" in w for w in result.get("warnings", [])))


class RunVsRunTest(unittest.TestCase):
    def test_two_runs_pair_with_arm_scores_by_case_and_warn_on_cli_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            cases_a = [("a", {"score": 0.5}), ("b", {"score": 0.5}), ("c", {"score": 0.5})]
            cases_b = [("a", {"score": 1.0}), ("b", {"score": 1.0}), ("c", {"score": 1.0})]
            a = _write(Path(temp), "a.json", _doc(cases_a, cli="2.1.270"))
            b = _write(Path(temp), "b.json", _doc(cases_b, cli="2.1.278"))
            result = plugineval.compare_results(str(a), str(b), delta=0.1)
            self.assertEqual("with", result["baseline"]["arm"])
            self.assertEqual("with", result["candidate"]["arm"])
            self.assertTrue(any("Claude Code versions" in w for w in result.get("warnings", [])))
            self.assertEqual("better", result["verdict"])


class CliTest(unittest.TestCase):
    def test_compare_plugin_eval_requires_delta(self):
        code, out = _run_cli("compare", "--plugin-eval", "--baseline", f"{FIXTURE}@without",
                             "--candidate", f"{FIXTURE}@with", "--reports-dir", tempfile.mkdtemp())
        self.assertEqual(2, code)
        self.assertIn("--delta", out)

    def test_compare_plugin_eval_prints_the_verdict_block(self):
        code, out = _run_cli("compare", "--plugin-eval", "--baseline", f"{FIXTURE}@without",
                             "--candidate", f"{FIXTURE}@with", "--delta", "0.1",
                             "--reports-dir", tempfile.mkdtemp())
        self.assertIn(code, (0, 1))
        self.assertIn("Verdict:", out)
        self.assertIn("95% CI", out)

    def test_compare_plugin_eval_and_paired_json_are_exclusive(self):
        code, out = _run_cli("compare", "--plugin-eval", "--paired-json", "--baseline", "a", "--candidate", "b",
                             "--delta", "0.1", "--reports-dir", tempfile.mkdtemp())
        self.assertEqual(2, code)
        self.assertIn("pick one", out)


if __name__ == "__main__":
    unittest.main()
