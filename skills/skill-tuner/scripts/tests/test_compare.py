"""Tests for the paired probe comparison (Unit 9.6).

The gate this replaces was `confirmed(candidate) >= confirmed(incumbent)` on
raw totals. That rule passes or fails on noise in either direction, and did
both: it failed at n=1 on a margin of 2 and passed at n=6 on a margin of 2,
from the same pair of doctrines. A verdict that cannot express "we could not
tell" will always answer, and half those answers are luck.

Scenarios:
1. Strictly better on every document -> `better` (CI excludes zero).
2. Strictly worse on every document -> `worse`.
3. Identical scores -> `not_worse` with a zero-width interval.
4. The real swap-gate shape (3 up, 3 down) -> `inconclusive` at delta=1.
5. Mismatched target sets refuse to compare rather than pairing by position.
6. Different model pins refuse; different CLI versions warn.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import compare  # noqa: E402


def _report(counts: dict[str, int], *, model="claude-sonnet-5", cli="2.1.224") -> dict:
    return {
        "manifest": {"model_pin": model, "cli_version": cli, "run_id": "r"},
        "probe": {
            "findings_confirmed": sum(counts.values()),
            "per_target": [
                {"target_file": name, "findings_confirmed": n, "refuted_count": 0}
                for name, n in counts.items()
            ],
        },
    }


class VerdictTest(unittest.TestCase):
    def test_strictly_better_is_better(self):
        base = _report({"a": 1, "b": 1, "c": 1, "d": 1, "e": 1, "f": 1})
        cand = _report({"a": 3, "b": 3, "c": 3, "d": 3, "e": 3, "f": 3})

        result = compare.compare_probe_reports(base, cand, delta=1.0)

        self.assertEqual("better", result["verdict"])
        self.assertGreater(result["ci_low"], 0)
        self.assertEqual(2.0, result["mean_diff"])

    def test_strictly_worse_is_worse(self):
        base = _report({"a": 3, "b": 3, "c": 3, "d": 3, "e": 3, "f": 3})
        cand = _report({"a": 1, "b": 1, "c": 1, "d": 1, "e": 1, "f": 1})

        result = compare.compare_probe_reports(base, cand, delta=1.0)

        self.assertEqual("worse", result["verdict"])
        self.assertLess(result["ci_high"], 0)

    def test_identical_scores_are_not_worse(self):
        counts = {"a": 2, "b": 1, "c": 3}
        result = compare.compare_probe_reports(
            _report(counts), _report(counts), delta=1.0
        )

        self.assertEqual("not_worse", result["verdict"])
        self.assertEqual(0.0, result["mean_diff"])
        self.assertEqual(0.0, result["ci_low"])
        self.assertEqual(0.0, result["ci_high"])

    def test_the_real_swap_gate_shape_is_inconclusive(self):
        # swapgate2, exactly: incumbent 9, candidate 11, split 3-3.
        base = _report(
            {
                "browser-console-setup": 1,
                "agent-swarm": 3,
                "design-drift": 1,
                "cli-doctor-mode": 1,
                "branch-harmonization": 1,
                "curl-bash-installer": 2,
            }
        )
        cand = _report(
            {
                "browser-console-setup": 0,
                "agent-swarm": 1,
                "design-drift": 0,
                "cli-doctor-mode": 3,
                "branch-harmonization": 3,
                "curl-bash-installer": 4,
            }
        )

        result = compare.compare_probe_reports(base, cand, delta=1.0)

        self.assertEqual("inconclusive", result["verdict"])
        self.assertEqual(11, result["candidate_total"])
        self.assertEqual(9, result["baseline_total"])
        self.assertAlmostEqual(0.333, result["mean_diff"], places=2)
        self.assertAlmostEqual(-1.62, result["ci_low"], places=1)
        self.assertAlmostEqual(2.29, result["ci_high"], places=1)
        self.assertEqual(3, result["documents_won"])
        self.assertEqual(3, result["documents_lost"])
        # The raw-count rule the old gate used would have said yes.
        self.assertTrue(result["passes_legacy_count_rule"])

    def test_n_to_resolve_accounts_for_the_observed_mean_not_just_spread(self):
        # The non-inferiority bound is `mean - half > -delta`, so the sample
        # size that would settle a run depends on how far the point estimate
        # already sits from the margin. An estimate derived from the spread
        # alone can return a number *below* the n you already have, which
        # reads as "collect fewer documents" -- observed on the real ablation
        # run (n=16, inconclusive, and the old formula said 12).
        n = compare.n_to_resolve(mean=-0.250, sd=1.693, delta=1.0)
        self.assertEqual(23, n)
        self.assertGreater(n, 16)

    def test_n_to_resolve_is_none_when_the_estimate_itself_breaches_the_margin(self):
        # mean at or past -delta: no sample size rescues it, and reporting a
        # number would promise that one does.
        self.assertIsNone(compare.n_to_resolve(mean=-1.4, sd=1.0, delta=1.0))

    def test_n_to_resolve_never_undercuts_an_already_sufficient_run(self):
        n = compare.n_to_resolve(mean=-0.05, sd=0.4, delta=1.0)
        self.assertIsNotNone(n)
        self.assertGreaterEqual(n, 3)

    def test_underpowered_run_reports_the_n_it_would_need(self):
        base = _report({"a": 1, "b": 3, "c": 1, "d": 1, "e": 1, "f": 2})
        cand = _report({"a": 0, "b": 1, "c": 0, "d": 3, "e": 3, "f": 4})

        result = compare.compare_probe_reports(base, cand, delta=1.0)

        self.assertEqual("inconclusive", result["verdict"])
        self.assertGreater(result["n_for_delta"], 6)


class PairingTest(unittest.TestCase):
    def test_mismatched_target_sets_refuse(self):
        base = _report({"a": 1, "b": 1})
        cand = _report({"a": 1, "c": 1})

        with self.assertRaises(compare.ComparisonError):
            compare.compare_probe_reports(base, cand, delta=1.0)

    def test_too_few_documents_refuse(self):
        with self.assertRaises(compare.ComparisonError):
            compare.compare_probe_reports(
                _report({"a": 1}), _report({"a": 2}), delta=1.0
            )


class ExcludeTest(unittest.TestCase):
    """Dropping a document from both sides.

    The case this exists for: an input drifts after a baseline is banked.
    Re-measuring the whole baseline to regain a valid comparison costs a full
    leg; excluding the one document that moved costs nothing and keeps every
    other pair honest. Excluding must apply to *both* sides or it becomes a
    way to delete losing documents.
    """

    def test_excluded_document_is_dropped_from_both_sides(self):
        base = _report({"a": 1, "b": 2, "c": 3, "drifted": 9})
        cand = _report({"a": 1, "b": 2, "c": 3, "drifted": 0})

        result = compare.compare_probe_reports(base, cand, delta=1.0, exclude=["drifted"])

        self.assertEqual(3, result["n"])
        self.assertNotIn("drifted", result["documents"])
        self.assertEqual(6, result["baseline_total"])
        self.assertEqual(6, result["candidate_total"])
        self.assertEqual(["drifted"], result["excluded"])

    def test_exclusion_is_recorded_as_a_warning(self):
        base = _report({"a": 1, "b": 2, "c": 3, "drifted": 9})
        cand = _report({"a": 1, "b": 2, "c": 3, "drifted": 0})

        result = compare.compare_probe_reports(base, cand, delta=1.0, exclude=["drifted"])

        self.assertTrue(any("drifted" in w for w in result["warnings"]))

    def test_exclude_matches_on_path_suffix(self):
        docs = {"/x/design-drift/SKILL.md": 1, "/x/b/SKILL.md": 2,
                "/x/c/SKILL.md": 3, "/x/d/SKILL.md": 1}
        base = _report(docs)
        cand = _report({**docs, "/x/design-drift/SKILL.md": 4})

        result = compare.compare_probe_reports(base, cand, delta=1.0, exclude=["design-drift"])

        # Matched on suffix, so a full path need not be spelled out.
        self.assertEqual(3, result["n"])
        self.assertEqual(["/x/design-drift/SKILL.md"], result["excluded"])

    def test_excluding_everything_refuses(self):
        base = _report({"a": 1, "b": 2, "c": 3})
        cand = _report({"a": 1, "b": 2, "c": 3})

        with self.assertRaises(compare.ComparisonError):
            compare.compare_probe_reports(base, cand, delta=1.0, exclude=["a", "b", "c"])


class ConfoundTest(unittest.TestCase):
    def test_different_model_pins_refuse(self):
        base = _report({"a": 1, "b": 1, "c": 1}, model="claude-opus-5")
        cand = _report({"a": 1, "b": 1, "c": 1}, model="claude-sonnet-5")

        with self.assertRaises(compare.ComparisonError):
            compare.compare_probe_reports(base, cand, delta=1.0)

    def test_different_cli_versions_warn_but_compare(self):
        base = _report({"a": 1, "b": 1, "c": 1}, cli="2.1.221")
        cand = _report({"a": 1, "b": 1, "c": 1}, cli="2.1.224")

        result = compare.compare_probe_reports(base, cand, delta=1.0)

        self.assertTrue(result["warnings"])
        self.assertIn("2.1.221", " ".join(result["warnings"]))


if __name__ == "__main__":
    unittest.main()
