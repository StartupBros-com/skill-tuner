"""Tests for the marginal-value probe eval (Unit 5 / R11).

Every test drives ``probe``'s importable functions directly with a FAKE
adapter matching tune's ``(prompt, model) -> AdapterResult`` signature, so
ZERO live ``claude`` calls are ever made. In-prompt presentation (KTD2): the
probe call carries the doctrine + target document inline; each verify call
carries exactly one finding + the target document inline, in a fresh call --
no shared conversational state, every verify is its own self-contained
adapter invocation. Scenarios map 1:1 to the unit spec:

1. Each finding verifies in its own fresh adapter call (call count = 1 probe
   + N verify); no verifier prompt leaks another finding's issue/fix text.
2. Refuted findings excluded from the report; refuted count still recorded.
3. Zero findings is a valid, well-formed result.
4. A quote absent from the target downgrades a CONFIRMED verdict to refuted
   via a local existence check, even when the (fake, careless) verifier
   says CONFIRMED -- the verifier cannot confirm a quote that isn't there.
5. max_findings cap respected; overflow beyond the cap is recorded, not
   verified.
6. Malformed probe JSON retries through the adapter path, succeeding on the
   second attempt; persistent malformed JSON raises after retries exhaust.
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
import tune  # noqa: E402


TARGET_TEXT = (
    "Setup steps.\n"
    "Don't ever skip validation here.\n"
    "Use the config file to configure the client.\n"
)

DOCTRINE_TEXT = (
    "- Negation [research] -- state the target behaviour, not the ban.\n"
    "- Single source of truth [craft] -- keep each meaning in one place.\n"
)

# Markers probe.py's own prompt builders are expected to emit -- used here to
# tell probe prompts apart from verify prompts without depending on wording.
PROBE_MARKER = "=== DOCTRINE ==="
VERIFY_MARKER = "=== CANDIDATE FINDING ==="


def _write(base: Path, name: str, text: str) -> Path:
    path = base / name
    path.write_text(text, encoding="utf-8")
    return path


def _config(doctrine_path: Path, target_path: Path, **overrides) -> dict:
    config = {
        "doctrine_file": str(doctrine_path),
        "target_file": str(target_path),
        "model": "test-model",
    }
    config.update(overrides)
    return config


# --------------------------------------------------------------------------
# Scenario 1: per-finding fresh, self-contained verify calls.
# --------------------------------------------------------------------------


class PerFindingFreshCallTest(unittest.TestCase):
    def test_each_finding_verifies_in_its_own_self_contained_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Negation",
                    "target_quote": "Don't ever skip validation here.",
                    "issue": "Prohibits without stating the positive target.",
                    "proposed_fix": "State: always validate before continuing.",
                },
                {
                    "rule": "Single source of truth",
                    "target_quote": "Use the config file to configure the client.",
                    "issue": "Restates a lookup the config file already owns.",
                    "proposed_fix": "Point at the config file instead of restating it.",
                },
            ]

            calls: list[str] = []

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                calls.append(prompt)
                if VERIFY_MARKER in prompt:
                    return tune.AdapterResult(
                        text="CONFIRMED: quote and rule both check out.", cost_usd=0.0, raw={}
                    )
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(3, len(calls))  # 1 probe + 2 verify

            probe_calls = [c for c in calls if PROBE_MARKER in c and VERIFY_MARKER not in c]
            verify_calls = [c for c in calls if VERIFY_MARKER in c]
            self.assertEqual(1, len(probe_calls))
            self.assertEqual(2, len(verify_calls))

            finding_a, finding_b = findings_payload
            prompt_for_a = next(p for p in verify_calls if finding_a["issue"] in p)
            prompt_for_b = next(p for p in verify_calls if finding_b["issue"] in p)
            self.assertNotEqual(prompt_for_a, prompt_for_b)

            # Self-contained: the other finding's metadata never leaks in.
            self.assertNotIn(finding_b["issue"], prompt_for_a)
            self.assertNotIn(finding_b["proposed_fix"], prompt_for_a)
            self.assertNotIn(finding_a["issue"], prompt_for_b)
            self.assertNotIn(finding_a["proposed_fix"], prompt_for_b)

            # But each verify prompt still carries the full target doc inline.
            self.assertIn(TARGET_TEXT, prompt_for_a)
            self.assertIn(TARGET_TEXT, prompt_for_b)

            self.assertEqual(2, result["findings_confirmed"])


class InPromptPresentationTest(unittest.TestCase):
    def test_probe_prompt_carries_doctrine_and_target_inline_with_empty_list_permitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            captured = {}

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                captured["prompt"] = prompt
                captured["model"] = model
                return tune.AdapterResult(text="[]", cost_usd=0.0, raw={})

            probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertIn(DOCTRINE_TEXT, captured["prompt"])
            self.assertIn(TARGET_TEXT, captured["prompt"])
            self.assertEqual("test-model", captured["model"])
            # Explicit instruction that an empty list is legitimate, not a failure.
            self.assertIn("empty", captured["prompt"].lower())


# --------------------------------------------------------------------------
# Scenario 2: refuted findings excluded from report, count still recorded.
# --------------------------------------------------------------------------


class RefutedExclusionTest(unittest.TestCase):
    def test_refuted_findings_excluded_but_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Negation",
                    "target_quote": "Don't ever skip validation here.",
                    "issue": "Prohibition-only phrasing.",
                    "proposed_fix": "Always validate before continuing.",
                },
                {
                    "rule": "Single source of truth",
                    "target_quote": "Use the config file to configure the client.",
                    "issue": "Not actually a duplicated meaning.",
                    "proposed_fix": "No change needed.",
                },
            ]

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    if "Negation" in prompt:
                        return tune.AdapterResult(
                            text="CONFIRMED: prohibition-only, rule applies.", cost_usd=0.0, raw={}
                        )
                    return tune.AdapterResult(
                        text="REFUTED: this is not a duplicated meaning.", cost_usd=0.0, raw={}
                    )
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(1, result["findings_confirmed"])
            self.assertEqual(1, result["refuted_count"])
            confirmed_rules = {f["rule"] for f in result["confirmed_findings"]}
            self.assertEqual({"Negation"}, confirmed_rules)

            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(1, report["probe"]["findings_confirmed"])
            self.assertEqual(1, report["probe"]["refuted_count"])
            self.assertEqual(
                {"Negation"}, {f["rule"] for f in report["probe"]["confirmed_findings"]}
            )


# --------------------------------------------------------------------------
# Scenario 3: zero findings is a valid, well-formed result.
# --------------------------------------------------------------------------


class ZeroFindingsTest(unittest.TestCase):
    def test_empty_findings_list_is_a_valid_well_formed_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            calls: list[str] = []

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                calls.append(prompt)
                return tune.AdapterResult(text="[]", cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(0, result["findings_confirmed"])
            self.assertEqual(0, result["refuted_count"])
            self.assertEqual(0, result["overflow"])
            self.assertEqual([], result["confirmed_findings"])
            self.assertEqual(1, len(calls))  # only the probe call, no verify calls

            self.assertTrue((run_dir / "report.json").exists())
            self.assertTrue((run_dir / "report.md").exists())
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(0, report["probe"]["findings_confirmed"])
            self.assertEqual([], report["probe"]["confirmed_findings"])


# --------------------------------------------------------------------------
# Scenario 4: absent quote downgrades CONFIRMED to refuted (code-level guard).
# --------------------------------------------------------------------------


class NonexistentQuoteDowngradeTest(unittest.TestCase):
    def test_confirmed_verdict_for_absent_quote_is_downgraded_to_refuted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Negation",
                    "target_quote": "This sentence does not exist in the target document anywhere.",
                    "issue": "Fabricated quote.",
                    "proposed_fix": "N/A",
                }
            ]

            verify_prompts: list[str] = []

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    verify_prompts.append(prompt)
                    # A careless verifier that wrongly confirms anyway --
                    # the code-level existence guard must catch this.
                    return tune.AdapterResult(text="CONFIRMED: looks right to me.", cost_usd=0.0, raw={})
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(1, len(verify_prompts))
            self.assertIn(findings_payload[0]["target_quote"], verify_prompts[0])
            self.assertIn(TARGET_TEXT, verify_prompts[0])  # still self-contained

            self.assertEqual(0, result["findings_confirmed"])
            self.assertEqual(1, result["refuted_count"])
            self.assertEqual([], result["confirmed_findings"])


# --------------------------------------------------------------------------
# Scenario 5: max_findings cap respected; overflow recorded, not verified.
# --------------------------------------------------------------------------


class MaxFindingsCapTest(unittest.TestCase):
    def test_overflow_beyond_cap_is_recorded_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path, max_findings=1)
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Negation",
                    "target_quote": "Don't ever skip validation here.",
                    "issue": "Prohibition-only phrasing.",
                    "proposed_fix": "Always validate before continuing.",
                },
                {
                    "rule": "Single source of truth",
                    "target_quote": "Use the config file to configure the client.",
                    "issue": "Duplicated lookup.",
                    "proposed_fix": "Point at config instead.",
                },
            ]

            verify_calls: list[str] = []

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    verify_calls.append(prompt)
                    return tune.AdapterResult(text="CONFIRMED: checks out.", cost_usd=0.0, raw={})
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(1, len(verify_calls))
            self.assertEqual(1, result["findings_confirmed"])
            self.assertEqual(1, result["overflow"])

            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(1, report["probe"]["overflow"])


# --------------------------------------------------------------------------
# Scenario 6: malformed probe JSON retries, then succeeds / exhausts.
# --------------------------------------------------------------------------


class MalformedProbeRetryTest(unittest.TestCase):
    def test_malformed_probe_json_retries_then_succeeds_on_second_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            probe_calls: list[str] = []

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    return tune.AdapterResult(text="CONFIRMED: fine.", cost_usd=0.0, raw={})
                probe_calls.append(prompt)
                if len(probe_calls) == 1:
                    return tune.AdapterResult(text="not-json at all", cost_usd=0.0, raw={})
                return tune.AdapterResult(text="[]", cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(2, len(probe_calls))
            self.assertEqual(0, result["findings_confirmed"])

    def test_probe_call_raises_after_exhausting_retries_on_persistent_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            def always_malformed(prompt: str, model: str) -> tune.AdapterResult:
                return tune.AdapterResult(text="still not json", cost_usd=0.0, raw={})

            with self.assertRaises(probe.ProbeParseError):
                probe.run_probe(config, always_malformed, run_dir, base_dir=base)


# --------------------------------------------------------------------------
# Bundled default doctrine_file.
# --------------------------------------------------------------------------


class DefaultDoctrineFileTest(unittest.TestCase):
    def test_default_doctrine_file_is_the_bundled_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = {"target_file": str(target_path), "model": "test-model"}
            run_dir = base / "run"

            captured = {}

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                captured["prompt"] = prompt
                return tune.AdapterResult(text="[]", cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            bundled_skill_md = SCRIPTS_DIR.parent / "SKILL.md"
            self.assertTrue(bundled_skill_md.exists())
            self.assertIn("Negation", captured["prompt"])  # from the real bundled doctrine
            self.assertEqual(str(bundled_skill_md), result["doctrine_file"])


if __name__ == "__main__":
    unittest.main()
