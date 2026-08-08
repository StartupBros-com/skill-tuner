"""CLI wiring tests (Unit 6).

U4/U5 built routing_parity.run_routing_parity_eval and probe.run_probe as
importable orchestrators, but tune.py's routing-parity/probe subcommands
never called them -- that integration seam is what this unit closes. These
two tests prove the wiring by driving tune.main() (the actual CLI entry
point) end to end with --config, and faking the adapter at the exact seam
the CLI itself uses: tune.call_adapter, the single chokepoint every real
eval call goes through. Patching that one function is enough to prove each
subcommand reaches its real orchestrator without ever shelling out to the
live `claude` CLI.
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import tune  # noqa: E402


def _write_skill(base: Path, slug: str, description: str, body: str) -> Path:
    skill_dir = base / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        textwrap.dedent(
            f"""\
            ---
            name: {slug}
            description: {description}
            ---

            {body}
            """
        ),
        encoding="utf-8",
    )
    return skill_md


def _write_distractors(base: Path, n: int = 5) -> list[str]:
    paths = []
    for index in range(n):
        slug = f"distractor-{index}"
        path = _write_skill(
            base,
            slug,
            f"Distractor {index} handles distractor-{index} tasks end to end.",
            f"This skill processes distractor-{index} work end to end.",
        )
        paths.append(str(path))
    return paths


class RoutingParityCliWiringTest(unittest.TestCase):
    """tune.py routing-parity --config <json> must reach
    routing_parity.run_routing_parity_eval, not the generic --cases path."""

    def test_routing_parity_subcommand_with_config_reaches_the_real_orchestrator(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(
                base,
                "alpha",
                "Alpha handles alpha reporting and alpha summaries end to end.",
                "This skill turns raw alpha numbers into alpha reports and alpha summaries.",
            )
            distractors = _write_distractors(base)
            battery = [
                {
                    "case_id": "alpha__obvious__1",
                    "kind": "obvious",
                    "target_id": "alpha",
                    "prompt": "Please generate the quarterly alpha report from these numbers.",
                },
                {
                    "case_id": "shared__near_miss__1",
                    "kind": "near_miss",
                    "target_id": None,
                    "prompt": "Just read through this file and tell me what it does, no changes needed.",
                },
            ]
            battery_path = base / "battery.json"
            battery_path.write_text(json.dumps(battery), encoding="utf-8")

            config = {
                "model": "test-model",
                "trials": 2,
                "targets": [
                    {
                        "id": "alpha",
                        "path": str(target_path),
                        "pruned_description": "Handles alpha things.",
                    }
                ],
                "distractors": distractors,
                "battery_file": str(battery_path),
            }
            config_path = base / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            reports_dir = base / "reports"

            def fake_call_adapter(prompt, model, **kwargs):
                if "quarterly alpha report" in prompt:
                    return tune.AdapterResult(text="alpha", cost_usd=0.0, raw={})
                return tune.AdapterResult(text="none", cost_usd=0.0, raw={})

            with mock.patch("tune.call_adapter", side_effect=fake_call_adapter) as patched:
                exit_code = tune.main(
                    [
                        "routing-parity",
                        "--config",
                        str(config_path),
                        "--reports-dir",
                        str(reports_dir),
                        "--yes",
                        "--allow-unmetered",
                    ]
                )

            self.assertEqual(0, exit_code)
            self.assertTrue(patched.called, "the CLI never reached call_adapter")

            run_dirs = list(reports_dir.iterdir())
            self.assertEqual(1, len(run_dirs))
            report = json.loads((run_dirs[0] / "report.json").read_text(encoding="utf-8"))
            # "routing_parity" (with its verdict/scores) only exists on the
            # report written by routing_parity.run_routing_parity_eval --
            # the generic _run_eval path never writes that key.
            self.assertIn("routing_parity", report)
            self.assertIn(report["routing_parity"]["verdict"], {"land", "refuse"})
            self.assertIn("original", report["routing_parity"]["scores"])
            self.assertIn("pruned", report["routing_parity"]["scores"])


class ProbeCliWiringTest(unittest.TestCase):
    """tune.py probe --config <json> must reach probe.run_probe, not the
    generic --cases path."""

    def test_probe_subcommand_with_config_reaches_the_real_orchestrator(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = base / "doctrine.md"
            doctrine_path.write_text(
                "- Negation [research] -- state the target behaviour, not the ban.\n",
                encoding="utf-8",
            )
            target_path = base / "target.md"
            target_path.write_text("Setup steps.\nDon't ever skip validation here.\n", encoding="utf-8")

            config = {
                "doctrine_file": str(doctrine_path),
                "target_file": str(target_path),
                "model": "test-model",
            }
            config_path = base / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            reports_dir = base / "reports"

            def fake_call_adapter(prompt, model, **kwargs):
                return tune.AdapterResult(text="[]", cost_usd=0.0, raw={})

            with mock.patch("tune.call_adapter", side_effect=fake_call_adapter) as patched:
                exit_code = tune.main(
                    [
                        "probe",
                        "--config",
                        str(config_path),
                        "--reports-dir",
                        str(reports_dir),
                        "--yes",
                        "--allow-unmetered",
                    ]
                )

            self.assertEqual(0, exit_code)
            self.assertTrue(patched.called, "the CLI never reached call_adapter")

            run_dirs = list(reports_dir.iterdir())
            self.assertEqual(1, len(run_dirs))
            report = json.loads((run_dirs[0] / "report.json").read_text(encoding="utf-8"))
            # "probe" (with findings_confirmed/refuted_count) only exists on
            # the report written by probe.run_probe.
            self.assertIn("probe", report)
            self.assertEqual(0, report["probe"]["findings_confirmed"])
            self.assertEqual(0, report["probe"]["refuted_count"])


if __name__ == "__main__":
    unittest.main()


class ProbeTargetFlagTest(unittest.TestCase):
    """`probe --target` builds the config in memory.

    A committed config file is the right interface for a reproducible
    battery. It is the wrong one for an agent mid-way through fixing a
    document, which would otherwise have to author JSON to a temp path just
    to ask what is wrong with a file. Same runner, same guards, one less step.
    """

    def _args(self, argv):
        return tune.build_parser().parse_args(argv)

    def test_target_builds_a_config_without_a_file(self):
        args = self._args([
            "probe", "--target", "a.md", "--target", "b.md",
            "--model", "m", "--max-findings", "3", "--verify-trials", "5",
        ])
        config = tune._config_from_targets(args)

        self.assertEqual("m", config["model"])
        self.assertEqual(3, config["max_findings"])
        self.assertEqual(5, config["verify_trials"])
        self.assertEqual(2, len(config["target_files"]))
        # Paths are resolved, so the run does not depend on the caller's cwd.
        self.assertTrue(all(p.startswith("/") for p in config["target_files"]))
        self.assertNotIn("doctrine_file", config)  # bundled default

    def test_doctrine_and_pin_pass_through(self):
        args = self._args([
            "probe", "--target", "a.md", "--doctrine", "d.md",
            "--pin", "origin/main", "--model", "m",
        ])
        config = tune._config_from_targets(args)

        self.assertTrue(config["doctrine_file"].endswith("d.md"))
        self.assertEqual("origin/main", config["pin"])

    def test_config_still_works_and_target_takes_precedence(self):
        plain = self._args(["probe", "--config", "c.json"])
        self.assertIsNone(plain.target)

        both = self._args(["probe", "--config", "c.json", "--target", "a.md"])
        self.assertEqual(["a.md"], both.target)
