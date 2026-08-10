"""Tests for the sequential gate (mSPRT early stopping).

The mSPRT values are checked against hand-computed literals from the
closed form, not against the implementation's own output; the stopping
behaviour is exercised end-to-end through run_gate with a fake adapter.
"""

from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import compare  # noqa: E402
import gate  # noqa: E402
import tune  # noqa: E402


class MsprtMathTest(unittest.TestCase):
    def test_empty_diffs_are_the_unit_martingale(self):
        self.assertEqual(1.0, compare.msprt_lambda([], -1.0))

    def test_known_value_matches_the_closed_form(self):
        # n=4, mean=1, mu0=-1, sigma0=tau=2:
        # sqrt(4/20) * exp(16*4*(2^2) / (2*4*20)) = 0.44721 * exp(1.6)
        expected = math.sqrt(4 / 20) * math.exp(1.6)
        self.assertAlmostEqual(
            expected, compare.msprt_lambda([1, 1, 1, 1], -1.0, sigma0=2.0), places=10
        )

    def test_lambda_at_the_null_shrinks_below_one(self):
        # mean == mu0: the exponential is 1 and the sqrt prefactor < 1, so
        # evidence never accumulates against a true null from the mean alone.
        lam = compare.msprt_lambda([-1.0] * 10, -1.0, sigma0=2.0)
        self.assertLess(lam, 1.0)

    def test_lambda_grows_with_distance_from_the_null(self):
        near = compare.msprt_lambda([0.5] * 6, 0.0, sigma0=2.0)
        far = compare.msprt_lambda([2.0] * 6, 0.0, sigma0=2.0)
        self.assertGreater(far, near)


class SequentialDecisionTest(unittest.TestCase):
    def test_strong_positive_run_stops_better(self):
        decision = compare.sequential_decision([3.0] * 6, delta=1.0, sigma0=2.0)
        self.assertEqual("better", decision["stop"])

    def test_moderate_positive_run_stops_not_worse_first(self):
        decision = compare.sequential_decision([2.0] * 8, delta=1.0, sigma0=2.0)
        self.assertEqual("not_worse", decision["stop"])

    def test_strong_negative_run_stops_worse(self):
        decision = compare.sequential_decision([-5.0] * 3, delta=1.0, sigma0=2.0)
        self.assertEqual("worse", decision["stop"])

    def test_null_ish_run_keeps_probing(self):
        decision = compare.sequential_decision(
            [0, 1, -1, 0, 1, -1, 0, 1, -1], delta=1.0, sigma0=2.0
        )
        self.assertIsNone(decision["stop"])


def _fake_adapter_returning(text: str):
    def adapter(prompt: str, model: str) -> tune.AdapterResult:
        return tune.AdapterResult(text=text, cost_usd=0.01, raw={})
    return adapter


def _write_targets(base: Path, count: int) -> list[Path]:
    paths = []
    for i in range(count):
        p = base / f"skill-{i}" / "SKILL.md"
        p.parent.mkdir(parents=True)
        p.write_text(f"---\nname: skill-{i}\ndescription: does thing {i}.\n---\n\nBody {i}.\n")
        paths.append(p)
    return paths


def _baseline_report(counts: dict[str, int]) -> dict:
    return {
        "manifest": {"model_pin": "test-model", "run_id": "baseline"},
        "probe": {
            "per_target": [
                {"target_file": k, "findings_confirmed": v, "refuted_count": 0}
                for k, v in counts.items()
            ]
        },
    }


class RunGateTest(unittest.TestCase):
    def test_null_diffs_probe_everything_and_stay_undecided(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            targets = _write_targets(base, 4)
            doctrine = base / "DOCTRINE.md"
            doctrine.write_text("Rules.\n")
            config = {
                "model": "test-model",
                "doctrine_file": str(doctrine),
                "target_files": [str(p) for p in targets],
                "max_findings": 5,
            }
            baseline = _baseline_report({str(p): 0 for p in targets})

            result = gate.run_gate(
                config, _fake_adapter_returning("[]"), base / "run", baseline,
                delta=1.0, base_dir=base,
            )

            self.assertEqual("undecided", result["sequential_verdict"])
            self.assertEqual(4, result["targets_probed"])
            self.assertFalse(result["stopped_early"])
            # Zero-width fixed-n interval at zero: the record says not_worse.
            self.assertEqual("not_worse", result["fixed_n"]["verdict"])

    def test_big_regression_stops_early_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            targets = _write_targets(base, 5)
            doctrine = base / "DOCTRINE.md"
            doctrine.write_text("Rules.\n")
            config = {
                "model": "test-model",
                "doctrine_file": str(doctrine),
                "target_files": [str(p) for p in targets],
                "max_findings": 5,
            }
            # Baseline found 5 everywhere; the candidate probe returns [] so
            # every diff is -5 — decidedly worse than any sane margin.
            baseline = _baseline_report({str(p): 5 for p in targets})

            result = gate.run_gate(
                config, _fake_adapter_returning("[]"), base / "run", baseline,
                delta=1.0, base_dir=base,
            )

            self.assertEqual("worse", result["sequential_verdict"])
            self.assertTrue(result["stopped_early"])
            self.assertEqual(3, result["targets_probed"])
            self.assertEqual(2, result["targets_skipped"])
            self.assertEqual("worse", result["fixed_n"]["verdict"])
            # The report carries the gate block and the trace.
            report = json.loads(Path(result["report_json"]).read_text())
            self.assertEqual("worse", report["gate"]["sequential_verdict"])
            self.assertEqual(3, len(report["gate"]["trace"]))

    def test_target_missing_from_baseline_refuses_before_spend(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            targets = _write_targets(base, 3)
            doctrine = base / "DOCTRINE.md"
            doctrine.write_text("Rules.\n")
            config = {
                "model": "test-model",
                "doctrine_file": str(doctrine),
                "target_files": [str(p) for p in targets],
            }
            baseline = _baseline_report({str(targets[0]): 1})  # others missing

            calls = []

            def counting_adapter(prompt, model):
                calls.append(prompt)
                return tune.AdapterResult(text="[]", cost_usd=0.01, raw={})

            with self.assertRaises(gate.GateError):
                gate.run_gate(
                    config, counting_adapter, base / "run", baseline,
                    delta=1.0, base_dir=base,
                )
            self.assertEqual(0, len(calls))


class ReviewFixesTest(unittest.TestCase):
    """Pins for the 2026-08-10 adversarial-review findings."""

    def test_stop_is_not_honored_before_min_documents(self):
        # A huge first diff crosses the mSPRT at n=1; the gate must keep
        # probing to MIN_DOCUMENTS so a fixed-n verdict always exists.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            targets = _write_targets(base, 5)
            doctrine = base / "DOCTRINE.md"
            doctrine.write_text("Rules.\n")
            config = {
                "model": "test-model",
                "doctrine_file": str(doctrine),
                "target_files": [str(p) for p in targets],
                "max_findings": 8,
            }
            baseline = _baseline_report({str(p): 0 for p in targets})

            findings = json.dumps([
                {"rule": "r", "target_quote": "Body", "issue": "x",
                 "proposed_fix": "y"}
            ] * 8)

            def adapter(prompt: str, model: str) -> tune.AdapterResult:
                if "skeptical verifier" in prompt:
                    return tune.AdapterResult(text="CONFIRMED yes", cost_usd=0.01, raw={})
                return tune.AdapterResult(text=findings, cost_usd=0.01, raw={})

            result = gate.run_gate(
                config, adapter, base / "run", baseline, delta=1.0, base_dir=base,
            )

            self.assertEqual("better", result["sequential_verdict"])
            self.assertEqual(3, result["targets_probed"])
            self.assertIsNotNone(result["fixed_n"])
            self.assertEqual(0, tune._gate_exit_code(result))

    def test_exit_policy_defers_to_fixed_n_when_undecided(self):
        undecided_pass = {
            "sequential_verdict": "undecided",
            "fixed_n": {"verdict": "not_worse"},
        }
        undecided_fail = {
            "sequential_verdict": "undecided",
            "fixed_n": {"verdict": "inconclusive"},
        }
        stopped_worse = {
            "sequential_verdict": "worse",
            "fixed_n": {"verdict": "worse"},
        }
        halted = {
            "sequential_verdict": "undecided",
            "fixed_n": {"verdict": "not_worse"},
            "halted_on_budget": True,
        }
        self.assertEqual(0, tune._gate_exit_code(undecided_pass))
        self.assertEqual(1, tune._gate_exit_code(undecided_fail))
        self.assertEqual(1, tune._gate_exit_code(stopped_worse))
        self.assertEqual(1, tune._gate_exit_code(halted))

    def test_running_sd_above_sigma0_is_flagged(self):
        decision = compare.sequential_decision([8.0, -8.0, 8.0], delta=1.0, sigma0=2.0)
        self.assertTrue(decision["sigma0_exceeded"])
        calm = compare.sequential_decision([1.0, 0.0, 1.0], delta=1.0, sigma0=2.0)
        self.assertFalse(calm["sigma0_exceeded"])


if __name__ == "__main__":
    unittest.main()
