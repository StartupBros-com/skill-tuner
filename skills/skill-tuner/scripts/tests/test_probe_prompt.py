"""Byte-for-byte prompt fixtures from the pre-refactor renderer; no model calls."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import probe
from tune import AdapterResult


FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "probe-prompts.json").read_text(encoding="utf-8")
)


class ProbePromptBytesTest(unittest.TestCase):
    def test_both_envelopes_preserve_complete_prompt_bytes(self):
        for case in FIXTURES:
            with self.subTest(system=case["system"], target=case["target"]):
                actual = probe.build_probe_prompt(
                    case["doctrine"], case["target"], doctrine_in_system=case["system"]
                )
                self.assertEqual(actual.encode("utf-8"), case["expected"].encode("utf-8"))
                if not case["system"]:
                    self.assertEqual(probe.build_probe_prompt(case["doctrine"], case["target"]), actual)
                else:
                    self.assertEqual(probe.build_probe_prompt("ignored doctrine", case["target"], doctrine_in_system=True), actual)

    def test_probe_call_delivers_the_same_bytes_to_only_the_fake_adapter(self):
        with patch("subprocess.run", side_effect=AssertionError("no subprocess")), patch(
            "socket.create_connection", side_effect=AssertionError("no network")
        ):
            for case in FIXTURES:
                calls = []

                def adapter(prompt, model):
                    calls.append((prompt, model))
                    return AdapterResult(text="[]", cost_usd=0, raw={})

                with self.subTest(system=case["system"], target=case["target"]):
                    rows = []
                    self.assertEqual(probe.run_probe_call(
                        case["doctrine"], case["target"], adapter=adapter,
                        model="synthetic", retries=0, rows=rows,
                        doctrine_in_system=case["system"],
                    ), [])
                    self.assertEqual(calls, [(case["expected"], "synthetic")])
                    self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
