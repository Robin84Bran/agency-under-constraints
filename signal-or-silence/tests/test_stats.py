import unittest
from sos_stats import (bootstrap_endpoints, evaluate_sample, inverse_group_weights,
                       percentile, ratio, weighted_rate, wilson)


class StatisticsTests(unittest.TestCase):
    def test_wilson_empty_is_unknown(self):
        self.assertIsNone(wilson(0, 0))
        self.assertIsNone(ratio(1, 0))

    def test_wilson_nominal_interval(self):
        low, high = wilson(50, 100)
        self.assertAlmostEqual(low, 1 - high)
        self.assertLess(low, .5)
        self.assertGreater(high, .5)
        self.assertEqual(wilson(0, 10)[0], 0)

    def test_duplicate_weight_denominator(self):
        weights = inverse_group_weights(['a', 'a', 'a', 'b'])
        self.assertAlmostEqual(sum(weights), 2)
        self.assertAlmostEqual(weighted_rate([1, 1, 1, 0], weights), .5)
        self.assertEqual(weighted_rate([1, 1, 1, 0]), .75)

    def test_multiplicity_is_not_deduplicated(self):
        terms = [(1, 1), (0, 1)]
        self.assertAlmostEqual(evaluate_sample(terms, ['a', 'b'], ['a', 'a', 'b']), 2 / 3)
        self.assertIsNone(evaluate_sample([(0, 0), (0, 1)], ['a', 'b'], ['a']))

    def test_bootstrap_omits_less_than_ten_supporting_blocks(self):
        result = bootstrap_endpoints({'rate': [[(1, 1)] * 9]}, list(range(9)), replicates=10)
        self.assertIsNone(result['rate']['interval'])
        self.assertEqual(result['rate']['support_blocks'], 9)
        self.assertIn('fewer than ten', result['rate']['reason'])

    def test_paired_bootstrap_preserves_identical_arm_difference(self):
        terms = [(i % 2, 1) for i in range(20)]
        result = bootstrap_endpoints({'change': [terms, terms]}, list(range(20)), replicates=80)
        self.assertEqual(result['change']['interval'], [0, 0])
        self.assertEqual(result['change']['null_replicates'], 0)

    def test_bootstrap_seed_reproducible_and_null_subsets_counted(self):
        # Ten supported units, one common shared block for the other 90 rows.
        units = list(range(10)) + [10] * 90
        terms = [(1, 1)] * 10 + [(0, 0)] * 90
        a = bootstrap_endpoints({'rate': [terms]}, units, replicates=60)
        b = bootstrap_endpoints({'rate': [terms]}, units, replicates=60)
        self.assertEqual(a, b)
        self.assertEqual(a['rate']['interval'], [1, 1])

    def test_percentile_interpolates(self):
        self.assertEqual(percentile([0, 10], .25), 2.5)
        self.assertIsNone(percentile([], .5))

    def test_truthless_resamples_are_null_and_counted(self):
        terms = [(1, 1)] + [(0, 0)] * 19
        result = bootstrap_endpoints({'rate': [terms]}, list(range(20)), replicates=100, minimum_blocks=1)
        self.assertGreater(result['rate']['null_replicates'], 0)
        self.assertEqual(result['rate']['interval'], [1, 1])
