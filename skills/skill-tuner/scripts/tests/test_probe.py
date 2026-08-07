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
7. The quote guard compares prose, not markdown layout: a quote spanning a
   blockquote or list continuation is found, a fabricated one is not.
8. Refuted findings reach the report with the mode that killed them, so a
   fabricated quote is distinguishable from a verifier's own refusal.
9. verify_trials runs an odd panel of independent skeptics and takes the
   strict majority; a tie refutes on the skeptic default.
10. Multi-target runs aggregate totals while preserving per-target detail,
    and single-target runs keep every field gen_receipts.py reads.
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


# --------------------------------------------------------------------------
# Scenario 7: the quote guard tolerates per-line markdown decoration.
#
# Regression test for the U7 swap-gate miscount: the candidate doctrine's one
# verifier-CONFIRMED finding quoted a blockquote whose continuation line
# carries a "> " marker. The quote reproduced the prose correctly and dropped
# the marker, so a raw substring test failed and the guard downgraded a real
# finding to refuted -- scoring the candidate 0 instead of 1. Since every
# document this probe targets is markdown, that false negative is systematic.
# --------------------------------------------------------------------------


BLOCKQUOTE_TARGET_TEXT = (
    "# Console setup\n"
    "\n"
    "> **Core pattern:** When a cloud console blocks headless automation, do not fight\n"
    "> it with Playwright. Open the exact URL in a real browser instead.\n"
    "\n"
    "- Use the config file to configure the client.\n"
)


class MarkdownDecoratedQuoteTest(unittest.TestCase):
    def test_quote_spanning_a_blockquote_continuation_is_found(self):
        # The model quotes the prose and drops the "> " continuation marker.
        quote = "When a cloud console blocks headless automation, do not fight\nit with Playwright."
        self.assertNotIn(quote, BLOCKQUOTE_TARGET_TEXT)  # raw substring fails
        self.assertTrue(probe.quote_present(quote, BLOCKQUOTE_TARGET_TEXT))

    def test_quote_dropping_a_list_marker_is_found(self):
        self.assertTrue(
            probe.quote_present(
                "Use the config file to configure the client.", BLOCKQUOTE_TARGET_TEXT
            )
        )

    def test_fabricated_quote_is_still_rejected(self):
        self.assertFalse(
            probe.quote_present(
                "This sentence does not exist in the target document anywhere.",
                BLOCKQUOTE_TARGET_TEXT,
            )
        )

    def test_empty_quote_is_rejected(self):
        self.assertFalse(probe.quote_present("", BLOCKQUOTE_TARGET_TEXT))

    def test_confirmed_finding_quoting_a_blockquote_survives_the_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", BLOCKQUOTE_TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Negation",
                    "target_quote": (
                        "When a cloud console blocks headless automation, do not fight\n"
                        "it with Playwright."
                    ),
                    "issue": "Steers by prohibition.",
                    "proposed_fix": "State the target behaviour.",
                }
            ]

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    return tune.AdapterResult(
                        text="CONFIRMED: appears verbatim and the rule applies.",
                        cost_usd=0.0,
                        raw={},
                    )
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(1, result["findings_confirmed"])
            self.assertEqual(0, result["refuted_count"])


# --------------------------------------------------------------------------
# Scenario 8: refuted findings are reported with their refutation mode, so a
# code-level downgrade is distinguishable from a verifier's own refusal.
# --------------------------------------------------------------------------


class RefutedFindingObservabilityTest(unittest.TestCase):
    def test_report_separates_quote_not_found_from_verifier_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Fabricated",
                    "target_quote": "This sentence does not exist in the target document anywhere.",
                    "issue": "Made up.",
                    "proposed_fix": "N/A",
                },
                {
                    "rule": "Real quote, weak rule",
                    "target_quote": "Use the config file to configure the client.",
                    "issue": "Arguable.",
                    "proposed_fix": "N/A",
                },
            ]

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    if "does not exist" in prompt:
                        # A careless verifier confirms a fabricated quote.
                        return tune.AdapterResult(text="CONFIRMED: looks right.", cost_usd=0.0, raw={})
                    return tune.AdapterResult(text="REFUTED: rule doesn't apply.", cost_usd=0.0, raw={})
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(0, result["findings_confirmed"])
            self.assertEqual(2, result["refuted_count"])

            modes = {
                entry["rule"]: entry["refutation_mode"] for entry in result["refuted_findings"]
            }
            self.assertEqual("quote_not_found", modes["Fabricated"])
            self.assertEqual("verifier", modes["Real quote, weak rule"])

            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(2, len(report["probe"]["refuted_findings"]))

            summary = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("quote_not_found", summary)


# --------------------------------------------------------------------------
# Scenario 9: verify_trials runs an odd panel of independent skeptics and
# takes the majority, so one stray verdict cannot decide a gate.
# --------------------------------------------------------------------------


class VerifyTrialsMajorityTest(unittest.TestCase):
    def _run(self, verdicts: list[str]) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path, verify_trials=len(verdicts))
            run_dir = base / "run"

            findings_payload = [
                {
                    "rule": "Single source of truth",
                    "target_quote": "Use the config file to configure the client.",
                    "issue": "Duplicated.",
                    "proposed_fix": "N/A",
                }
            ]
            remaining = list(verdicts)

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    return tune.AdapterResult(text=remaining.pop(0), cost_usd=0.0, raw={})
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            return probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

    def test_majority_confirm_confirms(self):
        result = self._run(["CONFIRMED: yes.", "REFUTED: no.", "CONFIRMED: yes."])
        self.assertEqual(1, result["findings_confirmed"])
        self.assertEqual(3, result["verify_calls"])

    def test_majority_refute_refutes(self):
        result = self._run(["CONFIRMED: yes.", "REFUTED: no.", "REFUTED: no."])
        self.assertEqual(0, result["findings_confirmed"])
        self.assertEqual("verifier", result["refuted_findings"][0]["refutation_mode"])

    def test_tie_refutes_on_the_skeptic_default(self):
        result = self._run(["CONFIRMED: yes.", "REFUTED: no."])
        self.assertEqual(0, result["findings_confirmed"])

    def test_default_is_a_single_verify_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            run_dir = base / "run"
            config = _config(doctrine_path, target_path)

            findings_payload = [
                {
                    "rule": "R",
                    "target_quote": "Use the config file to configure the client.",
                    "issue": "i",
                    "proposed_fix": "f",
                }
            ]

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    return tune.AdapterResult(text="CONFIRMED: ok.", cost_usd=0.0, raw={})
                return tune.AdapterResult(text=json.dumps(findings_payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)
            self.assertEqual(1, result["verify_calls"])

    def test_verify_trials_must_be_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write(base, "target.md", TARGET_TEXT)
            with self.assertRaises(ValueError):
                probe.load_config(
                    {"target_file": str(target_path), "model": "m", "verify_trials": 0},
                    base_dir=base,
                )


# --------------------------------------------------------------------------
# Scenario 10: multi-target runs, so a count-based gate rests on more than
# one document. Totals aggregate; per-target breakdown is preserved.
# --------------------------------------------------------------------------


class MultiTargetTest(unittest.TestCase):
    def test_target_files_aggregates_totals_and_keeps_per_target_detail(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_a = _write(base, "a.md", "Alpha line one.\nAlpha line two.\n")
            target_b = _write(base, "b.md", "Beta line one.\nBeta line two.\n")
            run_dir = base / "run"
            config = {
                "doctrine_file": str(doctrine_path),
                "target_files": [str(target_a), str(target_b)],
                "model": "test-model",
            }

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                if VERIFY_MARKER in prompt:
                    return tune.AdapterResult(text="CONFIRMED: ok.", cost_usd=0.0, raw={})
                quote = "Alpha line one." if "Alpha line one." in prompt else "Beta line one."
                payload = [
                    {"rule": "R", "target_quote": quote, "issue": "i", "proposed_fix": "f"}
                ]
                return tune.AdapterResult(text=json.dumps(payload), cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(2, result["probe_calls"])
            self.assertEqual(2, result["verify_calls"])
            self.assertEqual(2, result["findings_confirmed"])

            per_target = {entry["target_file"]: entry for entry in result["per_target"]}
            self.assertEqual({str(target_a), str(target_b)}, set(per_target))
            self.assertEqual(1, per_target[str(target_a)]["findings_confirmed"])
            self.assertEqual(1, per_target[str(target_b)]["findings_confirmed"])

            # Every confirmed finding names the document it came from.
            self.assertEqual(
                {str(target_a), str(target_b)},
                {entry["target_file"] for entry in result["confirmed_findings"]},
            )

            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(2, len(report["probe"]["per_target"]))
            self.assertEqual(
                [str(target_a), str(target_b)], report["probe"]["target_files"]
            )

    def test_single_target_file_still_reports_the_legacy_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            doctrine_path = _write(base, "doctrine.md", DOCTRINE_TEXT)
            target_path = _write(base, "target.md", TARGET_TEXT)
            config = _config(doctrine_path, target_path)
            run_dir = base / "run"

            def fake_adapter(prompt: str, model: str) -> tune.AdapterResult:
                return tune.AdapterResult(text="[]", cost_usd=0.0, raw={})

            result = probe.run_probe(config, fake_adapter, run_dir, base_dir=base)

            self.assertEqual(str(target_path), result["target_file"])
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            # gen_receipts.py reads these five keys; they must survive.
            for key in (
                "findings_confirmed",
                "refuted_count",
                "probe_calls",
                "verify_calls",
                "confirmed_findings",
            ):
                self.assertIn(key, report["probe"])

    def test_config_requires_at_least_one_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with self.assertRaises(ValueError):
                probe.load_config({"model": "m", "target_files": []}, base_dir=base)


if __name__ == "__main__":
    unittest.main()
