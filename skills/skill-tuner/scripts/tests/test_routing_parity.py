"""Tests for the routing-parity blind-battery eval (Unit 4 / R10, KTD6).

Every test drives ``routing_parity``'s importable functions directly with a
FAKE adapter matching tune's ``(prompt, model) -> AdapterResult`` signature,
so ZERO live ``claude`` calls are ever made. Scenarios map 1:1 to the unit
spec:

1. AE1 -- equal-or-better across 2 trials -> land verdict, both scores.
2. AE2 -- pruned worse -> refuse verdict naming failing prompt ids.
3. Blinding -- description text reaching the battery builder raises
   BlindingViolation (frontmatter-strip path + substring guard).
4. Pairing mismatch (missing trial row in one condition) raises.
5. Prompt-order rotation differs between trial 1 and trial 2 (offset =
   trial index).
6. Distractor descriptions are read from their files and present in
   router prompts.
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import routing_parity  # noqa: E402
import tune  # noqa: E402


# --------------------------------------------------------------------------
# Shared fixture builders
# --------------------------------------------------------------------------


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


def _write_distractors(base: Path, n: int = 5) -> list[Path]:
    paths = []
    for index in range(n):
        slug = f"distractor-{index}"
        paths.append(
            _write_skill(
                base,
                slug,
                f"Distractor {index} handles distractor-{index} tasks end to end.",
                f"This skill processes distractor-{index} work end to end.",
            )
        )
    return paths


def _battery_file(base: Path, target_id: str) -> Path:
    """A pre-built battery: 2 obvious + 1 paraphrase for the target, plus a
    shared near-miss + none-of-the-above pool. Prompts intentionally avoid
    any of the target's description text (blinding by construction)."""
    cases = [
        {
            "case_id": f"{target_id}__obvious__1",
            "kind": "obvious",
            "target_id": target_id,
            "prompt": "Please generate the quarterly alpha report from these raw numbers.",
        },
        {
            "case_id": f"{target_id}__obvious__2",
            "kind": "obvious",
            "target_id": target_id,
            "prompt": "I need an alpha summary built from this data dump.",
        },
        {
            "case_id": f"{target_id}__paraphrase__1",
            "kind": "paraphrase",
            "target_id": target_id,
            "prompt": "Can you condense these alpha figures into a short write-up?",
        },
        {
            "case_id": "shared__near_miss__1",
            "kind": "near_miss",
            "target_id": None,
            "prompt": "Just read through this file and tell me what it does, no changes needed.",
        },
        {
            "case_id": "shared__none_of_the_above__1",
            "kind": "none_of_the_above",
            "target_id": None,
            "prompt": "What's a good recipe for banana bread?",
        },
    ]
    path = base / "battery.json"
    path.write_text(json.dumps(cases), encoding="utf-8")
    return path


def _base_config(base: Path, target_path: Path, distractor_paths: list[Path], **overrides) -> dict:
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
        "distractors": [str(p) for p in distractor_paths],
        "battery_file": str(_battery_file(base, "alpha")),
    }
    config.update(overrides)
    return config


def _correct_router_adapter(prompt: str, model: str) -> tune.AdapterResult:
    """A perfect router: fires 'alpha' on alpha-shaped requests, else 'none'."""
    alpha_markers = (
        "quarterly alpha report",
        "alpha summary built",
        "condense these alpha figures",
    )
    if any(marker in prompt for marker in alpha_markers):
        return tune.AdapterResult(text="alpha", cost_usd=0.0, raw={})
    return tune.AdapterResult(text="none", cost_usd=0.0, raw={})


def _regressing_router_adapter(prompt: str, model: str) -> tune.AdapterResult:
    """Behaves like the perfect router, except the pruned condition
    misroutes exactly one obvious alpha prompt to 'none'."""
    is_pruned = "Handles alpha things." in prompt
    if is_pruned and "quarterly alpha report" in prompt:
        return tune.AdapterResult(text="none", cost_usd=0.0, raw={})
    return _correct_router_adapter(prompt, model)


# --------------------------------------------------------------------------
# Scenario 1 (AE1): equal-or-better -> land verdict, both scores recorded.
# --------------------------------------------------------------------------


class ParityGateEqualOrBetterTest(unittest.TestCase):
    def test_equal_or_better_yields_land_verdict_with_both_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(
                base,
                "alpha",
                "Alpha handles alpha reporting and alpha summaries end to end.",
                "This skill turns raw alpha numbers into alpha reports and alpha summaries.",
            )
            distractors = _write_distractors(base)
            config = _base_config(base, target_path, distractors)
            run_dir = base / "run"

            result = routing_parity.run_routing_parity_eval(
                config, adapter=_correct_router_adapter, run_dir=run_dir, base_dir=base
            )

            self.assertEqual("land", result["verdict"])
            self.assertEqual([], result["failing_case_ids"])
            self.assertIn("original", result["scores"])
            self.assertIn("pruned", result["scores"])
            self.assertEqual(1.0, result["scores"]["original"]["accuracy"])
            self.assertEqual(1.0, result["scores"]["pruned"]["accuracy"])

            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual("land", report["routing_parity"]["verdict"])
            self.assertIn("original", report["routing_parity"]["scores"])
            self.assertIn("pruned", report["routing_parity"]["scores"])


class DiscordantAnnotationTest(unittest.TestCase):
    """The verdict carries a noise annotation: discordant (case, trial)
    counts and the exact two-sided binomial p on them. The verdict itself
    stays the conservative point rule; the annotation tells the reader
    whether a refuse is distinguishable from routing noise."""

    @staticmethod
    def _score(condition, trial_correct):
        correct = sum(1 for v in trial_correct.values() if v)
        total = len(trial_correct)
        return routing_parity.ScoreResult(
            condition=condition, total=total, correct=correct,
            accuracy=correct / total, near_miss_total=0, near_miss_correct=0,
            near_miss_accuracy=1.0,
            failing_case_ids=sorted(k.split("|")[0] for k, v in trial_correct.items() if not v),
            trial_correct=trial_correct,
        )

    def test_one_lost_one_gained_annotates_as_pure_noise(self):
        original = self._score("original", {"a|1": True, "b|1": False, "c|1": True})
        pruned = self._score("pruned", {"a|1": False, "b|1": True, "c|1": True})

        verdict = routing_parity.determine_verdict(original, pruned)

        self.assertEqual(1, verdict["discordant_lost"])
        self.assertEqual(1, verdict["discordant_gained"])
        self.assertEqual(1.0, verdict["discordant_p"])

    def test_consistent_losses_annotate_as_signal(self):
        original = self._score("original", {k: True for k in ("a|1", "b|1", "c|1", "d|1")})
        pruned = self._score("pruned", {"a|1": False, "b|1": False, "c|1": False, "d|1": True})

        verdict = routing_parity.determine_verdict(original, pruned)

        self.assertEqual("refuse", verdict["verdict"])
        self.assertEqual(3, verdict["discordant_lost"])
        self.assertEqual(0, verdict["discordant_gained"])
        # exact two-sided binomial on 0 of 3: 2 * 0.5**3
        self.assertAlmostEqual(0.25, verdict["discordant_p"])

    def test_all_concordant_yields_none_p(self):
        same = {"a|1": True, "b|1": True}
        verdict = routing_parity.determine_verdict(
            self._score("original", dict(same)), self._score("pruned", dict(same))
        )
        self.assertEqual("land", verdict["verdict"])
        self.assertIsNone(verdict["discordant_p"])


# --------------------------------------------------------------------------
# Scenario 2 (AE2): pruned worse -> refuse verdict naming failing prompt ids.
# --------------------------------------------------------------------------


class ParityGateWorseTest(unittest.TestCase):
    def test_pruned_regression_yields_refuse_verdict_naming_failing_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(
                base,
                "alpha",
                "Alpha handles alpha reporting and alpha summaries end to end.",
                "This skill turns raw alpha numbers into alpha reports and alpha summaries.",
            )
            distractors = _write_distractors(base)
            config = _base_config(base, target_path, distractors)
            run_dir = base / "run"

            result = routing_parity.run_routing_parity_eval(
                config, adapter=_regressing_router_adapter, run_dir=run_dir, base_dir=base
            )

            self.assertEqual("refuse", result["verdict"])
            self.assertIn("alpha__obvious__1", result["failing_case_ids"])
            self.assertEqual(1.0, result["scores"]["original"]["accuracy"])
            self.assertLess(result["scores"]["pruned"]["accuracy"], 1.0)
            # The noise annotation rides the verdict end to end.
            self.assertGreaterEqual(result["discordant_lost"], 1)
            self.assertIsNotNone(result["discordant_p"])

            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual("refuse", report["routing_parity"]["verdict"])
            self.assertIn("alpha__obvious__1", report["routing_parity"]["failing_case_ids"])


# --------------------------------------------------------------------------
# Scenario 3: blinding -- frontmatter-strip path + substring guard.
# --------------------------------------------------------------------------


class DescriptionExtractionTest(unittest.TestCase):
    """Unit 6 regression: real skills fold a long description with YAML's
    ``>-`` block-scalar style across multiple indented lines; reading only
    the first line after ``description:`` used to silently return the bare
    ``>-`` indicator instead of the folded text."""

    def test_extract_description_folds_block_scalar_across_continuation_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skill_dir = base / "alpha"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                textwrap.dedent(
                    """\
                    ---
                    name: alpha
                    description: >-
                      Handles alpha reporting end to end. Use when a project needs
                      an alpha summary, "alpha analysis", or alpha reconciliation.
                    ---

                    Alpha body.
                    """
                ),
                encoding="utf-8",
            )

            description = routing_parity.extract_description(skill_md.read_text(encoding='utf-8'))

            self.assertEqual(
                'Handles alpha reporting end to end. Use when a project needs '
                'an alpha summary, "alpha analysis", or alpha reconciliation.',
                description,
            )
            self.assertNotIn(">-", description)

    def test_extract_description_plain_single_line_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = _write_skill(base, "alpha", "Handles alpha things.", "Alpha body.")
            self.assertEqual(
                "Handles alpha things.",
                routing_parity.extract_description(path.read_text(encoding="utf-8")),
            )


class BlindingGuardTest(unittest.TestCase):
    def test_extract_body_strips_frontmatter_so_description_never_reaches_builder(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            description = "Alpha handles distinctive-alpha-description-text end to end."
            path = _write_skill(base, "alpha", description, "This body talks about alpha work only.")

            body = routing_parity.extract_body(path.read_text(encoding='utf-8'))

            self.assertNotIn(description, body)
            self.assertNotIn("distinctive-alpha-description-text", body)
            self.assertIn("This body talks about alpha work only.", body)

    def test_build_battery_raises_blinding_violation_when_generated_prompt_leaks_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            description = "Alpha handles distinctive-alpha-description-text end to end."
            pruned_description = "Handles distinctive-alpha-description-text."
            target_path = _write_skill(base, "alpha", description, "This body talks about alpha work only.")
            distractors = _write_distractors(base)

            config = {
                "model": "test-model",
                "trials": 2,
                "targets": [
                    {"id": "alpha", "path": str(target_path), "pruned_description": pruned_description}
                ],
                "distractors": [str(p) for p in distractors],
            }

            def leaking_adapter(prompt: str, model: str) -> tune.AdapterResult:
                # A buggy authoring call that echoes the out-of-band description
                # text into a generated battery prompt -- exactly what the
                # substring guard exists to catch.
                leaked = json.dumps(
                    [
                        {"kind": "obvious", "prompt": f"Please help with: {description}"},
                        {"kind": "obvious", "prompt": "Please generate an alpha report."},
                        {"kind": "paraphrase", "prompt": "Condense these alpha figures."},
                    ]
                )
                return tune.AdapterResult(text=leaked, cost_usd=0.0, raw={})

            targets, _distractors, _trials_n, model = routing_parity.load_config(config, base_dir=base)

            with self.assertRaises(routing_parity.BlindingViolation):
                routing_parity.build_battery(
                    targets, config, adapter=leaking_adapter, model=model, base_dir=base
                )

    def test_authoring_response_in_a_code_fence_still_builds_the_battery(self):
        # 2026-08-08, live: the authoring model wrapped its array in a fence
        # and the strict parse died at char 0. Extraction now goes through
        # the probe's tolerant helper, so a fenced answer is still an answer.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(
                base, "alpha", "Alpha routes alpha work.", "This body talks about alpha work only."
            )
            distractors = _write_distractors(base)
            config = {
                "model": "test-model",
                "trials": 2,
                "targets": [
                    {"id": "alpha", "path": str(target_path), "pruned_description": "Alpha."}
                ],
                "distractors": [str(p) for p in distractors],
            }

            fenced = (
                "```json\n"
                + json.dumps(
                    [
                        {"kind": "obvious", "prompt": "Please do the alpha task."},
                        {"kind": "obvious", "prompt": "Run an alpha pass on this."},
                        {"kind": "paraphrase", "prompt": "Give this the once-over you do."},
                    ]
                )
                + "\n```"
            )

            def fencing_adapter(prompt: str, model: str) -> tune.AdapterResult:
                return tune.AdapterResult(text=fenced, cost_usd=0.0, raw={})

            targets, _d, _t, model = routing_parity.load_config(config, base_dir=base)
            battery = routing_parity.build_battery(
                targets, config, adapter=fencing_adapter, model=model, base_dir=base
            )

            authored = [case for case in battery if case.target_id == "alpha"]
            self.assertEqual(3, len(authored))

    def test_authoring_retries_are_bounded_then_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(
                base, "alpha", "Alpha routes alpha work.", "This body talks about alpha work only."
            )
            distractors = _write_distractors(base)
            config = {
                "model": "test-model",
                "trials": 2,
                "targets": [
                    {"id": "alpha", "path": str(target_path), "pruned_description": "Alpha."}
                ],
                "distractors": [str(p) for p in distractors],
            }

            calls = []

            def broken_adapter(prompt: str, model: str) -> tune.AdapterResult:
                calls.append(prompt)
                return tune.AdapterResult(text="I cannot answer in JSON.", cost_usd=0.0, raw={})

            targets, _d, _t, model = routing_parity.load_config(config, base_dir=base)
            with self.assertRaises(ValueError):
                routing_parity.build_battery(
                    targets, config, adapter=broken_adapter, model=model, base_dir=base
                )
            import probe as probe_module
            self.assertEqual(probe_module.DEFAULT_RETRIES + 1, len(calls))

    def test_build_battery_from_battery_file_also_passes_through_the_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            description = "Alpha handles distinctive-alpha-description-text end to end."
            target_path = _write_skill(base, "alpha", description, "This body talks about alpha work only.")
            distractors = _write_distractors(base)

            leaking_battery_path = base / "battery.json"
            leaking_battery_path.write_text(
                json.dumps(
                    [
                        {
                            "case_id": "alpha__obvious__1",
                            "kind": "obvious",
                            "target_id": "alpha",
                            "prompt": f"Please help with: {description}",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            config = {
                "model": "test-model",
                "trials": 2,
                "targets": [
                    {"id": "alpha", "path": str(target_path), "pruned_description": "Handles alpha things."}
                ],
                "distractors": [str(p) for p in distractors],
                "battery_file": str(leaking_battery_path),
            }

            targets, _distractors, _trials_n, model = routing_parity.load_config(config, base_dir=base)

            with self.assertRaises(routing_parity.BlindingViolation):
                routing_parity.build_battery(
                    targets,
                    config,
                    adapter=lambda p, m: tune.AdapterResult(text="[]", cost_usd=0.0, raw={}),
                    model=model,
                    base_dir=base,
                )


# --------------------------------------------------------------------------
# Scenario 4: pairing mismatch raises.
# --------------------------------------------------------------------------


class PairingCheckTest(unittest.TestCase):
    def test_missing_trial_row_in_one_condition_raises_pairing_mismatch(self):
        rows = [
            {"case_id": "c1", "trial": 1, "condition": "original"},
            {"case_id": "c1", "trial": 2, "condition": "original"},
            {"case_id": "c1", "trial": 1, "condition": "pruned"},
            # (c1, 2, "pruned") is missing.
        ]
        with self.assertRaises(routing_parity.PairingMismatch):
            routing_parity.check_pairing(rows, ("original", "pruned"))

    def test_identical_coverage_does_not_raise(self):
        rows = [
            {"case_id": "c1", "trial": 1, "condition": "original"},
            {"case_id": "c1", "trial": 1, "condition": "pruned"},
        ]
        routing_parity.check_pairing(rows, ("original", "pruned"))  # must not raise


# --------------------------------------------------------------------------
# Scenario 5: prompt-order rotation differs between trial 1 and trial 2.
# --------------------------------------------------------------------------


class PromptRotationTest(unittest.TestCase):
    def test_description_listing_order_rotates_by_trial(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(base, "alpha", "Alpha description.", "Alpha body.")
            distractors = _write_distractors(base)
            config = _base_config(base, target_path, distractors)

            targets, distractor_skills, trials_n, _model = routing_parity.load_config(config, base_dir=base)
            battery = routing_parity.build_battery(
                targets,
                config,
                adapter=lambda p, m: tune.AdapterResult(text="[]", cost_usd=0.0, raw={}),
                model="test-model",
                base_dir=base,
            )

            specs = routing_parity.build_router_trial_specs(battery, targets, distractor_skills, trials_n=2)

            case_id = battery[0].case_id
            trial1_prompt = next(
                s.prompt for s in specs if s.case_id == case_id and s.trial == 1 and s.condition == "original"
            )
            trial2_prompt = next(
                s.prompt for s in specs if s.case_id == case_id and s.trial == 2 and s.condition == "original"
            )

            self.assertNotEqual(trial1_prompt, trial2_prompt)

            entries_trial1 = routing_parity.rotate(
                routing_parity.build_description_entries("original", targets, distractor_skills), 0
            )
            entries_trial2 = routing_parity.rotate(
                routing_parity.build_description_entries("original", targets, distractor_skills), 1
            )
            self.assertNotEqual(entries_trial1, entries_trial2)
            self.assertEqual(entries_trial1[0], entries_trial2[-1])


# --------------------------------------------------------------------------
# Scenario 6: distractor descriptions read from their files, present in
# router prompts.
# --------------------------------------------------------------------------


class DistractorDescriptionTest(unittest.TestCase):
    def test_distractor_descriptions_read_from_file_appear_in_router_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target_path = _write_skill(base, "alpha", "Alpha description.", "Alpha body.")
            distractor_paths = _write_distractors(base)
            config = _base_config(base, target_path, distractor_paths)

            targets, distractors, trials_n, _model = routing_parity.load_config(config, base_dir=base)
            battery = routing_parity.build_battery(
                targets,
                config,
                adapter=lambda p, m: tune.AdapterResult(text="[]", cost_usd=0.0, raw={}),
                model="test-model",
                base_dir=base,
            )
            specs = routing_parity.build_router_trial_specs(battery, targets, distractors, trials_n=2)

            self.assertEqual(5, len(distractors))
            sample_prompt = specs[0].prompt
            for distractor in distractors:
                self.assertEqual(
                    routing_parity.extract_description(
                        distractor.path.read_text(encoding='utf-8')
                    ),
                    distractor.description,
                )
                self.assertIn(distractor.description, sample_prompt)
                self.assertIn(distractor.id, sample_prompt)


if __name__ == "__main__":
    unittest.main()
