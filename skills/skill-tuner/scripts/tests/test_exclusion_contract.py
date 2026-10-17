"""Offline contracts for the shared ingestion/pairing exclusion policy."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import compare
import plugineval


class ExclusionContractTest(unittest.TestCase):
    def document(self, name='prefix/MiXeD café/suffix', *, error=True):
        cases = [
            {'name': key, 'aggregates': {'score': 0.5, 'scoreWithout': 0.5}}
            for key in ('keep-a', 'keep-b', 'keep-c')
        ]
        cases.append({
            'name': name,
            'aggregates': {'score': 0.1, 'scoreWithout': 0.9},
            'arms': {'with': [{'error': 'timed out'}] if error else [], 'without': []},
        })
        return {'cases': cases}

    def paired(self, doc, patterns):
        base = plugineval.arm_scores(doc, 'without', source='base', exclude=patterns)
        cand = plugineval.arm_scores(doc, 'with', source='candidate', exclude=patterns)
        return base, cand, compare.compare_paired(base, cand, delta=0.1, exclude=patterns)

    def test_matching_contract_at_both_boundaries(self):
        name = 'prefix/MiXeD café/suffix'
        for patterns in [(name,), ('prefix',), ('MiXeD',), ('suffix',), ('café',), (' ',), ('', 'café'), ('missing', 'café', 'café')]:
            with self.subTest(patterns=patterns):
                doc = self.document(name)
                original = copy.deepcopy(doc)
                base, cand, result = self.paired(doc, patterns)
                self.assertIn(name, base)
                self.assertIn(name, cand)
                self.assertEqual(doc, original)
                self.assertEqual(result['excluded'], [name])
                self.assertEqual(result['documents'], ['keep-a', 'keep-b', 'keep-c'])
                self.assertEqual(result['n'], 3)
                self.assertEqual(result['baseline_total'], 1.5)
                self.assertEqual(result['candidate_total'], 1.5)
                self.assertEqual(result['verdict'], 'not_worse')
                self.assertEqual(result['warnings'], ['excluded from both sides: ' + name])

    def test_nonmatches_preserve_errored_run_refusal(self):
        name = 'prefix/MiXeD café/suffix'
        expected = "candidate: case 'prefix/MiXeD café/suffix' has 1 errored run(s) in the with-arm (timed out); its mean is a degraded aggregate, not a score. Re-run the suite, or pass --exclude prefix/MiXeD café/suffix to drop the case from both sides"
        for patterns in [(), ('',), ('', ''), ('mixed',), ('cafe',), (' café ',), ('*',), ('^prefix',), ('missing', '')]:
            with self.subTest(patterns=patterns):
                with self.assertRaises(plugineval.PluginEvalError) as caught:
                    self.paired(self.document(name), patterns)
                self.assertEqual(str(caught.exception), expected)
                _, _, result = self.paired(self.document(name, error=False), patterns)
                self.assertEqual(result['excluded'], [])
                self.assertEqual(result['n'], 4)

    def test_wildcards_and_whitespace_are_literal(self):
        for name, patterns in [('literal*case', ('*',)), (' padded ', (' padded ',)), ('bracket[case]', ('[',))]:
            with self.subTest(name=name):
                _, _, result = self.paired(self.document(name), patterns)
                self.assertEqual(result['excluded'], [name])

    def test_exclusion_does_not_bypass_score_validation(self):
        for value in [None, True, '0.5', {}, []]:
            for arm, key in [('with', 'score'), ('without', 'scoreWithout')]:
                with self.subTest(value=value, arm=arm):
                    doc = self.document('bad')
                    doc['cases'][-1]['aggregates'][key] = value
                    with self.assertRaises(plugineval.PluginEvalError) as caught:
                        plugineval.arm_scores(doc, arm, source='test', exclude=('bad',))
                    self.assertIn('no numeric score' if arm == 'with' else 'no without-arm score', str(caught.exception))

    def test_exclusion_remains_symmetric_for_unpaired_names(self):
        base = {'a': 1, 'b': 2, 'c': 3, 'drop/base': 50}
        cand = {'a': 1, 'b': 2, 'c': 3, 'drop/candidate': -50}
        result = compare.compare_paired(base, cand, delta=1, exclude=('drop/',))
        self.assertEqual(result['excluded'], ['drop/base', 'drop/candidate'])
        self.assertEqual(result['baseline_total'], 6)
        self.assertEqual(result['candidate_total'], 6)
        with self.assertRaises(compare.ComparisonError):
            compare.compare_paired(base, cand, delta=1, exclude=('drop/base',))

    def test_minimum_remaining_cases_still_enforced(self):
        with self.assertRaises(compare.ComparisonError) as caught:
            self.paired(self.document('bad'), ('bad', 'keep-c'))
        self.assertEqual(str(caught.exception), 'need at least 3 cases to say anything; got 2')

    def test_matching_only_applies_to_requested_errored_arm(self):
        scores = plugineval.arm_scores(self.document('bad'), 'without', exclude=('',))
        self.assertEqual(scores['bad'], 0.9)


if __name__ == '__main__':
    unittest.main()
