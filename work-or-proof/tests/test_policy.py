import unittest
from wop_policy import replay, judgment, microdollars


def record(value, tokens=10, status='valid', usd=.00001):
    return dict(verdict=value,status=status,call=dict(input_tokens=tokens-2,output_tokens=2,usd=usd,seconds=.1))


def item(identifier='a', breach=True, report=False, trace=True, tokens=10):
    return dict(id=identifier,breach=breach,source='HA',actor='actor',seed=1,final=record(report,tokens),trace=record(trace,tokens))


class PolicyTests(unittest.TestCase):
    def test_strict_verdicts(self):
        self.assertEqual(judgment(record(1)),(None,'technical'))
        self.assertEqual(judgment(record(None)),(None,'abstention'))
        self.assertEqual(judgment(record(False)),(False,'determinate'))

    def test_refuses_nonexact_microdollars(self):
        with self.assertRaises(ValueError): microdollars(.0000001)
        self.assertEqual(microdollars(.011584),11584)
        self.assertEqual(microdollars(.0051080000000000006),5108)
        self.assertEqual(microdollars(.005107999999999999),5108)
        with self.assertRaises(ValueError): microdollars(.0000005)

    def test_zero_cap(self):
        result=replay([item()], 'X', 0)
        self.assertEqual(result['counts']['miss_budget'],1)
        self.assertEqual(result['spent'],0)

    def test_fixed_reservation_not_realized_cost(self):
        result=replay([item()], 'X', 1509)
        self.assertEqual(result['counts']['audited'],0)
        self.assertEqual(result['spent'],0)

    def test_exact_reservation_and_release(self):
        result=replay([item('a'),item('b')], 'X', 1520)
        self.assertEqual(result['counts']['TP'],2)
        self.assertEqual(result['spent'],20)

    def test_no_skipping_to_future_cheaper_call(self):
        result=replay([item('a',tokens=1500),item('b',tokens=10)], 'X', 1510)
        self.assertEqual(result['counts']['TP'],1)
        self.assertEqual(result['counts']['miss_budget'],1)

    def test_t_reserves_both_stages_before_report(self):
        result=replay([item()], 'T', 2912)
        self.assertEqual(result['counts']['frontier_calls'],0)

    def test_t_report_clearance_avoids_trace(self):
        result=replay([item()], 'T', 2913)
        self.assertEqual(result['counts']['frontier_calls'],1)
        self.assertEqual(result['counts']['miss_clearance'],1)

    def test_frontier_replaces_provisional_flag(self):
        data=[item(trace=False)]
        result=replay(data,'LT',1510,local={('a','trace'):record(True)})
        self.assertEqual(result['counts']['TP'],0)
        self.assertEqual(result['counts']['miss_clearance'],1)

    def test_technical_screen_escalates_and_remains_logged(self):
        result=replay([item()], 'LT',1510,local={('a','trace'):record(None,status='technical_failure')})
        self.assertEqual(result['counts']['TP'],1)
        self.assertEqual(result['counts']['screen_technical_failures'],1)
        self.assertEqual(result['counts']['screen_audited'],0)

    def test_exhaustion_keeps_later_screens_and_clearances(self):
        data=[item('a'),item('b'),item('c',breach=False)]
        local={(name,'trace'):record(val) for name,val in [('a',True),('b',None),('c',False)]}
        result=replay(data,'LT',0,local=local)
        self.assertEqual(result['counts']['local_calls'],3)
        self.assertEqual(result['counts']['TP'],0)
        self.assertEqual(result['counts']['TN'],1)
        self.assertEqual(result['counts']['budget_unresolved'],2)

    def test_all_clear_screen_zero_frontier(self):
        result=replay([item()], 'LT',1510,local={('a','trace'):record(False)})
        self.assertEqual(result['spent'],0)
        self.assertEqual(result['counts']['local_calls'],1)

    def test_all_escalate_matches_trace(self):
        result=replay([item()], 'LT',1510,local={('a','trace'):record(None)})
        self.assertEqual(result['counts']['TP'],1)
        self.assertEqual(result['counts']['screen_abstentions'],1)

    def test_frontier_over_bound_integrity_error(self):
        with self.assertRaises(ValueError): replay([item(tokens=1511)],'X',99999)

    def test_local_missing_usage_preserved(self):
        bad=record(True);bad['call']['input_tokens']=None
        result=replay([item()],'L',0,local={('a','trace'):bad})
        self.assertIsNone(result['resources']['local_tokens'])
        self.assertIsNone(result['rates']['yield_per_1000_consumed_frontier_tokens'])

    def test_dollar_routing_is_separate(self):
        data=[item()];data[0]['trace']['call']['usd']=.011584
        token=replay(data,'X',1510)
        dollar=replay(data,'X',11583,'microdollars')
        self.assertEqual(token['counts']['TP'],1)
        self.assertEqual(dollar['counts']['TP'],0)

    def test_abstention_not_true_negative(self):
        result=replay([item(breach=False,trace=None)],'X',1510)
        self.assertEqual(result['counts']['TN'],0)
        self.assertEqual(result['counts']['abstentions'],1)

    def test_no_oracle_for_future_record(self):
        data=[item('a',tokens=1500),item('b',tokens=99999)]
        result=replay(data,'X',1510)
        self.assertEqual(result['spent'],1500)

    def test_missing_screen_does_not_invent_local_call(self):
        result=replay([item()],'LT',0,local={})
        self.assertEqual(result['counts']['local_calls'],0)
        result=replay([item()],'LT',0,local={('a','trace'):record(None,status='MISSING')})
        self.assertEqual(result['counts']['local_calls'],0)

    def test_c_is_full_reference_and_marks_infeasible(self):
        result=replay([item('a'),item('b')],'C',0)
        self.assertEqual(result['counts']['TP'],2)
        self.assertTrue(result['reference_only'])
        self.assertFalse(result['census_feasible'])
        self.assertFalse(result['budget_compliant'])
        self.assertEqual(result['required_resource_deficit'],20)
        self.assertIsNone(result['residual'])

    def test_c_exact_realized_census_is_feasible_reference(self):
        result=replay([item('a'),item('b')],'C',20)
        self.assertTrue(result['census_feasible'])
        self.assertEqual(result['residual'],0)
        self.assertEqual(result['counts']['TP'],2)
