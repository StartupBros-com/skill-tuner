"""Tests for the end-task A/B subcommand (fake adapter, fake grader)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import endtask  # noqa: E402
import tune  # noqa: E402

GRADER = '''\
import json, sys
text = open(sys.argv[1]).read()
print(json.dumps({"pass_rate": 1.0 if "GOOD" in text else 0.5}))
'''


def _setup(base: Path, cases: int = 4) -> tuple[dict, Path]:
    old = base / "old-SKILL.md"
    old.write_text("Skill vOLD: answer plainly.\n")
    new = base / "new-SKILL.md"
    new.write_text("Skill vNEW-SENTINEL: answer plainly and say GOOD.\n")
    grader = base / "grader.py"
    grader.write_text(GRADER)
    config = {
        "model": "test-model",
        "trials": 2,
        "conditions": {"old": str(old), "new": str(new)},
        "cases": [{"id": f"case-{i}", "prompt": f"do thing {i}"}
                  for i in range(cases)],
    }
    return config, grader


def _adapter(prompt: str, model: str) -> tune.AdapterResult:
    text = "output GOOD" if "vNEW-SENTINEL" in prompt else "output ok"
    return tune.AdapterResult(text=text, cost_usd=0.01, raw={})


class EndtaskTest(unittest.TestCase):
    def test_full_run_produces_a_paired_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config, grader = _setup(base)

            result = endtask.run_endtask(
                config, _adapter, base / "run", grader,
                delta=0.05, base_dir=base,
            )

            # new scores 1.0 everywhere, old 0.5: zero-variance diffs +0.5.
            self.assertEqual("better", result["verdict"])
            self.assertEqual(4, result["cases_scored"])
            report = json.loads(Path(result["report_json"]).read_text())
            self.assertEqual("old", report["endtask"]["baseline"])
            self.assertEqual(0.5, report["endtask"]["per_case"][0]["baseline"])
            self.assertEqual(1.0, report["endtask"]["per_case"][0]["candidate"])
            self.assertEqual(tune.DEFAULT_MODEL and "test-model",
                             report["manifest"]["model_pin"])

    def test_grader_contract_violations_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config, grader = _setup(base)
            grader.write_text("print('not json')\n")
            with self.assertRaises(endtask.EndtaskError):
                endtask.run_endtask(config, _adapter, base / "run", grader,
                                    delta=0.05, base_dir=base)

    def test_too_few_cases_refuse_before_spend(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config, grader = _setup(base, cases=2)
            calls = []

            def counting(prompt, model):
                calls.append(prompt)
                return _adapter(prompt, model)

            with self.assertRaises(endtask.EndtaskError):
                endtask.run_endtask(config, counting, base / "run", grader,
                                    delta=0.05, base_dir=base)
            self.assertEqual(0, len(calls))

    def test_budget_halt_reports_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config, grader = _setup(base, cases=4)
            result = endtask.run_endtask(
                config, _adapter, base / "run", grader,
                delta=0.05, base_dir=base, budget_usd=0.045,
            )
            self.assertTrue(result["halted_on_budget"])

    def test_manifest_records_distinct_resolved_models(self):
        self._assert_resolved_models(
            ["model-z", "model-a", "model-z", None] * 4,
            ["model-a", "model-z"],
        )

    def test_manifest_keeps_unknown_models_empty(self):
        self._assert_resolved_models([None] * 16, [])

    def test_budget_halt_keeps_completed_model_provenance(self):
        self._assert_resolved_models(
            ["model-z", None, "model-a", "model-z", "model-a"],
            ["model-a", "model-z"],
            budget_usd=0.045,
        )

    def _assert_resolved_models(self, models, expected, *, budget_usd=None):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config, grader = _setup(base)
            returned = iter(models)
            calls = []

            def adapter(prompt, model):
                resolved = next(returned)
                calls.append(resolved)
                return tune.AdapterResult(
                    text="output GOOD", cost_usd=0.01, raw={},
                    model_resolved=resolved,
                )

            # No provider, grader process or git/CLI subprocess is needed.
            with patch("endtask.run_grader", return_value={"pass_rate": 1.0}), \
                 patch("endtask.provenance._git", return_value=(127, "", "")), \
                 patch("endtask.provenance.cli_version", return_value="test-cli"):
                result = endtask.run_endtask(
                    config, adapter, base / "run", grader,
                    delta=0.05, base_dir=base, budget_usd=budget_usd,
                )

            report = json.loads(Path(result["report_json"]).read_text())
            trials = tune.read_jsonl(base / "run" / "trials.jsonl")
            self.assertEqual(models, calls)
            self.assertEqual(models, [row["model_resolved"] for row in trials])
            self.assertEqual(expected, report["manifest"]["resolved_models"])
            self.assertEqual("test-model", report["manifest"]["model_pin"])
            self.assertEqual(round(len(models) * 0.01, 6), result["spent_usd"])
            self.assertEqual(budget_usd is not None, result["halted_on_budget"])


if __name__ == "__main__":
    unittest.main()
