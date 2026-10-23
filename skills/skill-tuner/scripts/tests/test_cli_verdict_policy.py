"""Offline contracts for the shared CLI passing-verdict policy."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import compare
import endtask
import tune


# Literal expectations, independent of the production tuple. Lists and dicts
# deliberately pin the existing non-hash-based membership behavior.
VERDICTS = [
    ("better", True), ("not_worse", True), ("worse", False),
    ("inconclusive", False), ("insufficient-cases", False),
    ("undecided", False), ("unknown", False), ("", False),
    (None, False), (0, False), (False, False), ([], False), ({}, False),
]


class CliVerdictPolicyTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for target in ("subprocess.Popen", "socket.socket", "tune.call_adapter"):
            self.stack.enter_context(mock.patch(
                target, side_effect=AssertionError("unexpected external call")
            ))

    def compare_args(self, *, as_json=True):
        argv = ["compare", "--paired-json", "--baseline", "baseline.json",
                "--candidate", "candidate.json", "--delta", "0.1"]
        if as_json:
            argv.append("--json")
        return tune.build_parser().parse_args(argv)

    def test_compare_preserves_exit_codes_json_and_logging(self):
        args = self.compare_args()
        for verdict, passes in VERDICTS:
            with self.subTest(verdict=verdict):
                result = {"verdict": verdict}
                output = io.StringIO()
                with (
                    mock.patch.object(compare, "load_paired_scores", return_value={}),
                    mock.patch.object(compare, "compare_paired", return_value=result),
                    mock.patch.object(tune, "_log_compare_invocation") as log,
                    redirect_stdout(output),
                ):
                    self.assertEqual(0 if passes else 1, args.handler(args))
                self.assertEqual(json.dumps(result, indent=2) + "\n", output.getvalue())
                log.assert_called_once_with(args, result)

    def test_compare_preserves_render_then_log_order(self):
        args = self.compare_args(as_json=False)
        result = {"verdict": "not_worse"}
        output = io.StringIO()

        def log_after_output(*_):
            self.assertEqual("rendered verdict\n", output.getvalue())

        with (
            mock.patch.object(compare, "load_paired_scores", return_value={}),
            mock.patch.object(compare, "compare_paired", return_value=result),
            mock.patch.object(compare, "render", return_value="rendered verdict") as render,
            mock.patch.object(tune, "_log_compare_invocation", side_effect=log_after_output),
            redirect_stdout(output),
        ):
            self.assertEqual(0, args.handler(args))
        render.assert_called_once_with(result)

    def test_endtask_preserves_exit_codes_and_summary(self):
        args = tune.build_parser().parse_args([
            "endtask", "--config", "offline.json", "--grader", "grader.py",
            "--delta", "0.1", "--yes",
        ])
        spec = {"cases": [{}, {}, {}], "trials": 1, "model": "offline"}
        with (
            mock.patch.object(tune, "_load_json_config", return_value={}),
            mock.patch.object(tune, "resolve_run_dir", return_value=(Path("unused"), "offline")),
            mock.patch.object(tune, "enforce_budget_preflight"),
            mock.patch.object(tune, "confirm_or_abort"),
            mock.patch.object(endtask, "load_config", return_value=spec),
            mock.patch.object(endtask, "run_endtask") as run,
        ):
            for verdict, passes in VERDICTS:
                with self.subTest(verdict=verdict):
                    run.return_value = {"verdict": verdict, "cases_scored": 3, "spent_usd": 0.0}
                    output = io.StringIO()
                    with redirect_stdout(output):
                        self.assertEqual(0 if passes else 1, args.handler(args))
                    self.assertEqual(
                        f"Run offline: verdict={verdict} cases=3 spent=$0.0000\n",
                        output.getvalue(),
                    )

    def test_gate_preserves_decision_matrix_and_budget_override(self):
        for fixed, fixed_passes in VERDICTS:
            for sequential, sequential_passes in VERDICTS:
                for halted in (False, True):
                    with self.subTest(fixed=fixed, sequential=sequential, halted=halted):
                        result = {
                            "fixed_n": {"verdict": fixed},
                            "sequential_verdict": sequential,
                            "halted_on_budget": halted,
                        }
                        passes = not halted and fixed_passes and (
                            sequential == "undecided" or sequential_passes
                        )
                        self.assertEqual(0 if passes else 1, tune._gate_exit_code(result))

    def test_gate_preserves_missing_field_behavior(self):
        for fixed in (None, {}, {"other": "better"}):
            with self.subTest(fixed=fixed):
                self.assertEqual(1, tune._gate_exit_code({
                    "fixed_n": fixed, "sequential_verdict": "better",
                }))
        self.assertEqual(1, tune._gate_exit_code({"sequential_verdict": "undecided"}))
        self.assertEqual(1, tune._gate_exit_code({"halted_on_budget": True}))
        with self.assertRaises(KeyError):
            tune._gate_exit_code({})

    def test_compare_missing_verdict_still_logs_then_raises(self):
        args = self.compare_args()
        result = {"other": "better"}
        output = io.StringIO()
        with (
            mock.patch.object(compare, "load_paired_scores", return_value={}),
            mock.patch.object(compare, "compare_paired", return_value=result),
            mock.patch.object(tune, "_log_compare_invocation") as log,
            redirect_stdout(output),
        ):
            with self.assertRaises(KeyError):
                args.handler(args)
        self.assertEqual(json.dumps(result, indent=2) + "\n", output.getvalue())
        log.assert_called_once_with(args, result)


if __name__ == "__main__":
    unittest.main()
