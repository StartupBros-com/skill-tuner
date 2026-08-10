"""Tests for the doctrine-in-system-prompt envelope (v0.6.0).

The invariants that matter: the doctrine leaves the probe user prompt and
arrives via the system adapter; verify skeptics never see it; the manifest
records the new adapter_shape so compare can refuse cross-shape pairs.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import probe  # noqa: E402
import provenance  # noqa: E402
import tune  # noqa: E402


class AdapterCommandTest(unittest.TestCase):
    def test_system_prompt_rides_append_system_prompt(self):
        command = tune.build_adapter_command("ask", "m", "DOCTRINE TEXT")
        self.assertIn("--append-system-prompt", command)
        self.assertEqual("DOCTRINE TEXT", command[command.index("--append-system-prompt") + 1])

    def test_no_system_prompt_keeps_the_banked_shape(self):
        command = tune.build_adapter_command("ask", "m")
        self.assertNotIn("--append-system-prompt", command)


class DoctrineInSystemTest(unittest.TestCase):
    def test_probe_prompt_omits_doctrine_and_manifest_records_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "skill-a" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("---\nname: skill-a\ndescription: does a.\n---\n\nBody A.\n")
            doctrine = base / "DOCTRINE.md"
            doctrine.write_text("THE-DOCTRINE-SENTINEL rules live here.\n")
            config = {
                "model": "test-model",
                "doctrine_file": str(doctrine),
                "target_file": str(target),
                "max_findings": 3,
            }

            plain_calls: list[str] = []
            system_calls: list[tuple[str, str]] = []

            def plain(prompt: str, model: str) -> tune.AdapterResult:
                plain_calls.append(prompt)
                return tune.AdapterResult(text="CONFIRMED fine", cost_usd=0.0, raw={})

            def system_adapter(prompt: str, model: str, system: str) -> tune.AdapterResult:
                system_calls.append((prompt, system))
                return tune.AdapterResult(
                    text=json.dumps([{"rule": "r", "target_quote": "Body A.",
                                      "issue": "i", "proposed_fix": "f"}]),
                    cost_usd=0.0, raw={},
                )

            result = probe.run_probe(
                config, plain, base / "run", base_dir=base,
                doctrine_in_system=True, system_adapter=system_adapter,
            )

            # Exactly one probe call, through the system adapter, doctrine in
            # the system channel and NOT in the user prompt.
            self.assertEqual(1, len(system_calls))
            probe_prompt, system_text = system_calls[0]
            self.assertIn("THE-DOCTRINE-SENTINEL", system_text)
            self.assertNotIn("THE-DOCTRINE-SENTINEL", probe_prompt)
            self.assertIn("Body A.", probe_prompt)
            # Verify skeptics stay blind: plain adapter only, no doctrine.
            self.assertTrue(plain_calls)
            for prompt in plain_calls:
                self.assertIn("skeptical verifier", prompt)
                self.assertNotIn("THE-DOCTRINE-SENTINEL", prompt)
            # The manifest records the new shape.
            report = json.loads(Path(result["report_json"]).read_text())
            self.assertEqual(provenance.ADAPTER_SHAPE_DOCTRINE_SYSTEM,
                             report["manifest"]["adapter_shape"])

    def test_doctrine_in_system_without_adapter_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "s" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("---\nname: s\ndescription: d.\n---\nBody.\n")
            config = {"model": "m", "target_file": str(target),
                      "doctrine_file": str(target)}
            with self.assertRaises(ValueError):
                probe.run_probe(
                    config, lambda p, m: tune.AdapterResult("x", 0.0, {}),
                    base / "run", base_dir=base, doctrine_in_system=True,
                )


if __name__ == "__main__":
    unittest.main()
