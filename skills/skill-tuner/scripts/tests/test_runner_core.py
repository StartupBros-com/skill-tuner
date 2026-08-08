"""Tests for the skill-tuner runner core: CLI skeleton, guarded adapter,
and report/resume machinery shared by every eval.

Every test in this file drives ``tune``'s importable functions directly with
a FAKE adapter (or a fake ``subprocess.run``) so that ZERO live ``claude``
calls are ever made. Where a scenario needs to prove "no subprocess ran", the
fake adapter shells out to a real, harmless command (``touch <marker>``) so
the assertion is a real process check, not just a Python mock call count --
mirroring the marker-file shape used by the reference eval harness.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(SCRIPTS_DIR))

import tune  # noqa: E402


class AdapterChokepointTest(unittest.TestCase):
    """The single adapter chokepoint (KTD2/R8): build + run + parse + retry."""

    def test_build_adapter_command_shape(self):
        command = tune.build_adapter_command("do the thing", "test-model")

        self.assertEqual("claude", command[0])
        self.assertIn("-p", command)
        self.assertIn("do the thing", command)
        self.assertIn("--output-format", command)
        self.assertIn("json", command)
        self.assertIn("--setting-sources", command)
        self.assertIn("--no-session-persistence", command)
        self.assertIn("--disable-slash-commands", command)
        self.assertIn("--tools", command)
        self.assertIn("--model", command)
        self.assertIn("test-model", command)

    def test_call_adapter_retries_after_malformed_json_then_succeeds(self):
        responses = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="not-json", stderr=""),
            subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps({"result": "ok", "total_cost_usd": 0.02}),
                stderr="",
            ),
        ]
        calls = {"run": 0, "backoff": []}

        def fake_run(command, **kwargs):
            response = responses[calls["run"]]
            calls["run"] += 1
            return response

        def fake_backoff(delay):
            calls["backoff"].append(delay)

        result = tune.call_adapter(
            "prompt", "test-model", retries=1, run=fake_run, backoff=fake_backoff
        )

        self.assertEqual("ok", result.text)
        self.assertAlmostEqual(0.02, result.cost_usd)
        self.assertEqual(2, calls["run"])
        self.assertEqual(1, len(calls["backoff"]))

    def test_call_adapter_raises_after_exhausting_retries(self):
        def always_malformed(command, **kwargs):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="nope", stderr="")

        with self.assertRaises(RuntimeError):
            tune.call_adapter(
                "prompt", "test-model", retries=1, run=always_malformed, backoff=lambda d: None
            )


class AuthModeTest(unittest.TestCase):
    def test_detect_auth_mode_from_env_without_any_subprocess_call(self):
        self.assertEqual("api-key", tune.detect_auth_mode({"ANTHROPIC_API_KEY": "sk-test"}))
        self.assertEqual("subscription", tune.detect_auth_mode({}))


class BudgetGateTest(unittest.TestCase):
    def test_enforce_budget_preflight_rejects_unmetered_api_key_run_and_names_override(self):
        with self.assertRaisesRegex(RuntimeError, "allow-unmetered"):
            tune.enforce_budget_preflight("api-key", None, False)
        # Both escape hatches are accepted.
        tune.enforce_budget_preflight("api-key", None, True)
        tune.enforce_budget_preflight("api-key", 5.0, False)

    def test_subscription_runs_are_exempt_from_the_dollar_gate(self):
        tune.enforce_budget_preflight("subscription", None, False)


class ExecuteBatteryBudgetRejectionTest(unittest.TestCase):
    """Scenario 1: unmetered API-key run rejected before ANY subprocess call."""

    def test_unmetered_api_key_run_rejected_before_any_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            marker = tmp_path / "adapter_ran"
            run_dir = tmp_path / "run"

            def marker_adapter(prompt, model):
                subprocess.run(["touch", str(marker)], check=True)
                return tune.AdapterResult(text="stub", cost_usd=1.0, raw={})

            trials = [tune.TrialSpec(case_id="c1", trial=1, condition="baseline", prompt="p")]

            with self.assertRaisesRegex(RuntimeError, "budget"):
                tune.execute_battery(
                    trials,
                    run_dir=run_dir,
                    adapter=marker_adapter,
                    model="test-model",
                    budget_usd=None,
                    allow_unmetered=False,
                    auth_mode="api-key",
                    yes=True,
                )

            self.assertFalse(marker.exists(), "adapter ran before the budget gate rejected the run")
            self.assertFalse((run_dir / "trials.jsonl").exists())

            result = tune.execute_battery(
                trials,
                run_dir=run_dir,
                adapter=marker_adapter,
                model="test-model",
                budget_usd=None,
                allow_unmetered=True,
                auth_mode="api-key",
                yes=True,
            )

            self.assertTrue(marker.exists())
            self.assertEqual(1, result["completed_trials"])


class ExecuteBatteryBudgetCapTest(unittest.TestCase):
    """Scenario 2: budget cap reached mid-battery halts cleanly, persists partial trials."""

    def test_budget_cap_reached_mid_battery_halts_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            calls = []

            def fake_adapter(prompt, model):
                calls.append(prompt)
                return tune.AdapterResult(text=f"resp-{prompt}", cost_usd=1.0, raw={})

            trials = [
                tune.TrialSpec(case_id="c1", trial=1, condition="baseline", prompt="p1"),
                tune.TrialSpec(case_id="c1", trial=1, condition="candidate", prompt="p2"),
                tune.TrialSpec(case_id="c2", trial=1, condition="baseline", prompt="p3"),
                tune.TrialSpec(case_id="c2", trial=1, condition="candidate", prompt="p4"),
            ]

            result = tune.execute_battery(
                trials,
                run_dir=run_dir,
                adapter=fake_adapter,
                model="test-model",
                budget_usd=2.0,
                allow_unmetered=False,
                auth_mode="api-key",
                yes=True,
            )

            self.assertTrue(result["halted"])
            self.assertEqual(2, len(calls))
            rows = tune.read_jsonl(run_dir / "trials.jsonl")
            self.assertEqual(2, len(rows))
            self.assertEqual(2, result["completed_trials"])


class ExecuteBatteryResumeTest(unittest.TestCase):
    """Scenario 3: --resume after a simulated crash skips completed keys."""

    def test_resume_after_simulated_crash_skips_completed_and_finishes_remainder(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            trials = [
                tune.TrialSpec(case_id="c1", trial=1, condition="baseline", prompt="p1"),
                tune.TrialSpec(case_id="c1", trial=1, condition="candidate", prompt="p2"),
                tune.TrialSpec(case_id="c2", trial=1, condition="baseline", prompt="p3"),
                tune.TrialSpec(case_id="c2", trial=1, condition="candidate", prompt="p4"),
            ]

            calls = []

            def crashing_adapter(prompt, model):
                calls.append(prompt)
                if len(calls) > 2:
                    raise RuntimeError("simulated crash")
                return tune.AdapterResult(text=f"resp-{prompt}", cost_usd=0.0, raw={})

            with self.assertRaisesRegex(RuntimeError, "simulated crash"):
                tune.execute_battery(
                    trials,
                    run_dir=run_dir,
                    adapter=crashing_adapter,
                    model="m",
                    budget_usd=None,
                    allow_unmetered=True,
                    auth_mode="api-key",
                    yes=True,
                )

            rows_after_crash = tune.read_jsonl(run_dir / "trials.jsonl")
            self.assertEqual(2, len(rows_after_crash), "completed trials before the crash must persist")

            calls_resume = []

            def healthy_adapter(prompt, model):
                calls_resume.append(prompt)
                return tune.AdapterResult(text=f"resp-{prompt}", cost_usd=0.0, raw={})

            result = tune.execute_battery(
                trials,
                run_dir=run_dir,
                adapter=healthy_adapter,
                model="m",
                budget_usd=None,
                allow_unmetered=True,
                auth_mode="api-key",
                yes=True,
            )

            self.assertEqual(2, len(calls_resume), "resume must only run the remaining two trials")
            rows_final = tune.read_jsonl(run_dir / "trials.jsonl")
            self.assertEqual(4, len(rows_final))
            self.assertEqual(
                {(t.case_id, t.trial, t.condition) for t in trials},
                tune.completed_keys(rows_final),
            )


class ReportWriterTest(unittest.TestCase):
    """Scenario 4: report writer emits report.json (parses) + report.md (names both conditions)."""

    def test_report_writer_emits_report_json_and_report_md_naming_both_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            trials = [
                {"case_id": "c1", "trial": 1, "condition": "baseline", "response": "a", "cost_usd": 0.1},
                {"case_id": "c1", "trial": 1, "condition": "candidate", "response": "b", "cost_usd": 0.2},
            ]

            json_path, md_path = tune.write_report(run_dir, trials, ("baseline", "candidate"))

            self.assertTrue(json_path.exists())
            parsed = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("baseline", parsed["conditions"])
            self.assertIn("candidate", parsed["conditions"])

            self.assertTrue(md_path.exists())
            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("baseline", md_text)
            self.assertIn("candidate", md_text)


class PreflightEstimateOrderingTest(unittest.TestCase):
    """Scenario 5: pre-flight estimate is printed before the first adapter call."""

    def test_preflight_estimate_printed_before_first_adapter_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            events = []

            def fake_print(message):
                events.append(("print", message))

            def fake_adapter(prompt, model):
                events.append(("call", prompt))
                return tune.AdapterResult(text="ok", cost_usd=0.0, raw={})

            trials = [tune.TrialSpec(case_id="c1", trial=1, condition="baseline", prompt="p1")]

            tune.execute_battery(
                trials,
                run_dir=run_dir,
                adapter=fake_adapter,
                model="m",
                budget_usd=None,
                allow_unmetered=True,
                auth_mode="subscription",
                yes=True,
                print_fn=fake_print,
            )

            self.assertGreaterEqual(len(events), 2)
            self.assertEqual("print", events[0][0])
            self.assertIn("Planned trials", events[0][1])
            self.assertEqual("call", events[1][0])


class PreflightConfirmationTest(unittest.TestCase):
    def test_non_interactive_run_without_yes_aborts_before_any_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            calls = []

            def fake_adapter(prompt, model):
                calls.append(prompt)
                return tune.AdapterResult(text="ok", cost_usd=0.0, raw={})

            trials = [tune.TrialSpec(case_id="c1", trial=1, condition="baseline", prompt="p1")]

            with self.assertRaises(RuntimeError):
                tune.execute_battery(
                    trials,
                    run_dir=run_dir,
                    adapter=fake_adapter,
                    model="m",
                    budget_usd=None,
                    allow_unmetered=True,
                    auth_mode="subscription",
                    yes=False,
                    isatty=False,
                )

            self.assertEqual(0, len(calls))


class ResumeKeyTest(unittest.TestCase):
    def test_completed_keys_ignores_malformed_rows(self):
        rows = [
            {"case_id": "c1", "trial": 1, "condition": "baseline"},
            {"case_id": "c2", "trial": "not-an-int", "condition": "baseline"},
            {"case_id": None, "trial": 1, "condition": "baseline"},
        ]
        self.assertEqual({("c1", 1, "baseline")}, tune.completed_keys(rows))


class RunIdResolutionTest(unittest.TestCase):
    def test_resolve_run_dir_derives_content_slug_with_numeric_suffix_on_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports_dir = Path(tmp)
            _, run_id_1 = tune.resolve_run_dir(
                reports_dir, "routing-parity", ["a", "b"], run_id=None, resume_id=None
            )
            _, run_id_2 = tune.resolve_run_dir(
                reports_dir, "routing-parity", ["a", "b"], run_id=None, resume_id=None
            )

            # Same content, nothing written between them: the slug is stable
            # and no suffix is burned. Suffixes exist to avoid merging into a
            # run that produced output, not to count attempts.
            self.assertEqual(run_id_1, run_id_2)

            # Once a run has actually written something, the next fresh run
            # steps aside rather than merging into it.
            (reports_dir / run_id_1).mkdir(parents=True)
            _, run_id_3 = tune.resolve_run_dir(
                reports_dir, "routing-parity", ["a", "b"], run_id=None, resume_id=None
            )
            self.assertNotEqual(run_id_1, run_id_3)
            self.assertTrue(run_id_3.startswith(run_id_1))

    def test_resolve_run_dir_resume_reuses_exact_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports_dir = Path(tmp)
            run_dir, run_id = tune.resolve_run_dir(
                reports_dir, "probe", ["x"], run_id=None, resume_id="probe-fixed"
            )
            run_dir_again, run_id_again = tune.resolve_run_dir(
                reports_dir, "probe", ["x"], run_id=None, resume_id="probe-fixed"
            )

            self.assertEqual(run_dir, run_dir_again)
            self.assertEqual("probe-fixed", run_id)
            self.assertEqual("probe-fixed", run_id_again)

    def test_resolve_run_dir_honors_explicit_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports_dir = Path(tmp)
            run_dir, run_id = tune.resolve_run_dir(
                reports_dir, "probe", ["x"], run_id="my-explicit-id", resume_id=None
            )
            self.assertEqual("my-explicit-id", run_id)
            # Resolving a run dir must not create it. A pre-flight that then
            # refuses to spend -- unmetered, or non-interactive without --yes
            # -- has to leave nothing behind, and these directories are
            # invisible to git (it does not track empty ones), so strays
            # accumulate unseen.
            self.assertFalse(run_dir.exists())


class CaseLoadingTest(unittest.TestCase):
    def test_load_cases_and_build_trial_specs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases_path = Path(tmp) / "cases.jsonl"
            rows = [
                {"id": "c1", "prompts": {"baseline": "b1", "candidate": "c1p"}},
                {"id": "c2", "prompts": {"baseline": "b2", "candidate": "c2p"}},
            ]
            cases_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            cases = tune.load_cases(cases_path)
            conditions = tune.conditions_from_cases(cases)
            specs = tune.build_trial_specs(cases, trials_n=2)

            self.assertEqual(("baseline", "candidate"), conditions)
            self.assertEqual(8, len(specs))
            self.assertEqual(
                {
                    ("c1", 1, "baseline"), ("c1", 1, "candidate"),
                    ("c1", 2, "baseline"), ("c1", 2, "candidate"),
                    ("c2", 1, "baseline"), ("c2", 1, "candidate"),
                    ("c2", 2, "baseline"), ("c2", 2, "candidate"),
                },
                {(s.case_id, s.trial, s.condition) for s in specs},
            )

    def test_conditions_from_cases_rejects_mismatched_condition_pairs(self):
        cases = [
            {"id": "c1", "prompts": {"baseline": "b1", "candidate": "c1p"}},
            {"id": "c2", "prompts": {"baseline": "b2", "other": "c2p"}},
        ]
        with self.assertRaises(ValueError):
            tune.conditions_from_cases(cases)


class CliParserTest(unittest.TestCase):
    """Subcommand CLI: routing-parity, probe, report. No doctor subcommand."""

    def test_parser_parses_known_subcommands(self):
        parser = tune.build_parser()

        args = parser.parse_args(["routing-parity", "--cases", "x.jsonl", "--yes"])
        self.assertEqual("x.jsonl", str(args.cases))
        self.assertTrue(hasattr(args, "handler"))

        args = parser.parse_args(["probe", "--cases", "y.jsonl", "--resume", "run-123"])
        self.assertEqual("run-123", args.resume)

        args = parser.parse_args(["report", "run-abc"])
        self.assertEqual("run-abc", args.run_id)

    def test_parser_rejects_unknown_subcommand(self):
        parser = tune.build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["bogus-subcommand"])

    def test_parser_has_no_doctor_subcommand(self):
        parser = tune.build_parser()
        subparsers_action = next(
            action for action in parser._actions if action.dest == "command"
        )
        self.assertNotIn("doctor", subparsers_action.choices)


class ManifestGuardTest(unittest.TestCase):
    """R9/AE4: no invocable-entry registration for tune.py in the plugin manifest
    or the skill's frontmatter -- skill-tuner is model-invoked doctrine only."""

    def test_plugin_manifest_has_no_invocable_entry_for_tune(self):
        manifest_path = REPO_ROOT / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertNotIn("commands", manifest)
        self.assertNotIn("tools", manifest)
        self.assertNotIn("tune.py", json.dumps(manifest))

    def test_skill_frontmatter_has_no_invocable_entry_for_tune(self):
        skill_path = REPO_ROOT / "skills" / "skill-tuner" / "SKILL.md"
        text = skill_path.read_text(encoding="utf-8")

        parts = text.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "SKILL.md must have YAML frontmatter")
        frontmatter = parts[1]

        self.assertNotIn("commands", frontmatter)
        self.assertNotIn("tools", frontmatter)
        self.assertNotIn("tune.py", frontmatter)


if __name__ == "__main__":
    unittest.main()
