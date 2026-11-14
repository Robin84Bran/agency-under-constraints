"""Real saved Claude reply, hostile mutations, and frozen no-rerun disposition."""
from copy import deepcopy
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

from trl_core import ROOT, canonical, sha
from trl_io import Stop, read
from trl_budget import maximum
from trl_transport import raw_record
from trl_validation import MODEL, positive_count, stdout, usage, validate
from trl_analysis import replay
from trl_freeze import (D3B_FREEZE_SHA256, D3C_ADDED, D3C_CHANGED,
                        freeze_d3c, verify, d3c_scope)
from trl_test import tested_inputs
from historical import frozen_bytes

FIXTURE = ROOT/'fixtures/d3c'


class RealEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.raw=read(FIXTURE/'r1-j0.raw.json')
        from trl_core import strict_load
        self.env=strict_load(stdout(self.raw))
        self.bound=read(FIXTURE/'r1-j0.request.json')['reservation']

    def validate(self,env):
        return validate(raw_record(canonical(env).encode()),'claude',3,self.bound)

    def test_original_bytes_reproduce_old_bug_and_pass_d3c(self):
        original=runpy.run_path(str(ROOT/'deviations/d3c/baseline/trl_validation.py'))
        with self.assertRaisesRegex(Stop,'unexpected real tool/subagent activity'):
            original['validate'](self.raw,'claude',3,self.bound)
        value,env,u=validate(self.raw,'claude',3,self.bound)
        self.assertEqual(value,{'cells':[0,19,38]})
        self.assertEqual((u['input'],u['cache_creation'],u['cache_read'],u['output']),(2,1460,0,195))
        self.assertEqual(u['reported_cost_micro_usd'],15588)
        self.assertEqual(env,self.env)

    def test_positive_numeric_leaves_recursively_block(self):
        for stats in ({'spawned':1},{'requested':{'background':1}},
                      {'killed':{'system':1}},{'by_type':{'new_type':{'count':1}}},
                      {'nested':[{'count':0.5}]}):
            with self.subTest(stats=stats):
                env=deepcopy(self.env);env['subagent_stats']=stats
                with self.assertRaisesRegex(Stop,'real tool/subagent'):
                    self.validate(env)
        for value in (None,{},[],{'a':0,'nested':[0,{'x':0.0}]},
                      {'metadata':'1','flag':True,'negative':-1}):
            self.assertFalse(positive_count(value))

    def test_every_real_subagent_counter_blocks_when_positive(self):
        def paths(v,prefix=()):
            for key,value in v.items():
                if type(value) is dict:yield from paths(value,prefix+(key,))
                elif type(value) in (int,float):yield prefix+(key,)
        for path in paths(self.env['subagent_stats']):
            env=deepcopy(self.env);v=env['subagent_stats']
            for key in path[:-1]:v=v[key]
            v[path[-1]]=1
            with self.subTest(path=path),self.assertRaises(Stop):self.validate(env)

    def test_server_counts_positive_unknown_and_malformed_still_block(self):
        for field in ('web_search_requests','web_fetch_requests','future_tool'):
            for count in (1,0.5,-1,True,'0',None):
                env=deepcopy(self.env);env['usage']['server_tool_use'][field]=count
                with self.subTest(field=field,count=count),self.assertRaises(Stop):self.validate(env)
        for st in (None,{},[],{'web_search_requests':0}):
            env=deepcopy(self.env);env['usage']['server_tool_use']=st
            with self.assertRaises(Stop):self.validate(env)
        env=deepcopy(self.env);env['modelUsage'][MODEL]['webSearchRequests']=1
        with self.assertRaises(Stop):self.validate(env)

    def test_all_other_envelope_guards_on_real_fixture(self):
        changes=[('type','error'),('subtype','error'),('is_error',True),
                 ('num_turns',3),('num_turns',True),('stop_reason','end_turn'),
                 ('stop_reason','max_tokens'),('modelUsage',{}),
                 ('modelUsage',{MODEL:[]}),('effort','high'),
                 ('permission_denials',None),('permission_denials',[{}]),
                 ('deferred_tool_use',[{}]),('tool_uses',[{}]),('tool_calls',[{}]),
                 ('errors',['failure']),('safety_stops',1),
                 ('total_cost_usd',1),('total_cost_usd',-1),
                 ('structured_output',None),('structured_output',{'cells':[True,19,38]}),
                 ('structured_output',{'cells':[48,19,38]}),
                 ('structured_output',{'cells':[0]}),
                 ('structured_output',{'cells':[0,19,38],'extra':0})]
        for key,value in changes:
            env=deepcopy(self.env);env[key]=value
            with self.subTest(key=key,value=value),self.assertRaises((Stop,ValueError)):
                self.validate(env)
        for key in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens','output_tokens'):
            env=deepcopy(self.env);env['usage'].pop(key)
            with self.subTest(missing=key),self.assertRaisesRegex(Stop,'usage UNKNOWN'):self.validate(env)
        for key in ('inputTokens','outputTokens','cacheReadInputTokens','cacheCreationInputTokens'):
            env=deepcopy(self.env);env['modelUsage'][MODEL][key]+=1
            with self.subTest(mismatch=key),self.assertRaisesRegex(Stop,'usage disagreement'):self.validate(env)
        for aggregate,model,value in (('input_tokens','inputTokens',3000),('output_tokens','outputTokens',1025)):
            env=deepcopy(self.env);env['usage'][aggregate]=value;env['modelUsage'][MODEL][model]=value
            with self.assertRaisesRegex(Stop,'overrun'):self.validate(env)
        for text in (stdout(self.raw)+stdout(self.raw),stdout(self.raw)[:-2]+',"num_turns":2}'):
            with self.assertRaises(ValueError):validate(raw_record(text.encode()),'claude',3,self.bound)
        for change in ({'returncode':1},{'transport_error':'timeout'},{'stdout_b64':'!!!!'}):
            raw={**self.raw,**change}
            with self.assertRaises((Stop,ValueError)):validate(raw,'claude',3,self.bound)

    def test_result_prose_never_substitutes_for_structured_output(self):
        env=deepcopy(self.env);env.pop('structured_output')
        with self.assertRaisesRegex(Stop,'structured_output'):self.validate(env)
        env=deepcopy(self.env);env['result']='irrelevant prose'
        self.assertEqual(self.validate(env)[0],{'cells':[0,19,38]})

    def test_frozen_harness_stopped_disposition_replays_without_retroactive_rewards(self):
        terminal=read(FIXTURE/'episode.json')
        row=replay(terminal['episode'],FIXTURE)
        self.assertEqual((row['Y'],row['H'],row['coverage'],row['calls']),(0,0,0,1))
        self.assertTrue(row['attempted']);self.assertFalse(row['complete'])
        self.assertEqual([e['status'] for e in terminal['events']],['technical']*3+['missing']*9)
        self.assertTrue(all(e['reward'] is None for e in terminal['events']))
        record=read(ROOT/'deviations/d3c/disposition.json')
        self.assertEqual(record['disposition'],'SCORED_NO_RERUN')
        self.assertEqual((record['Y'],record['H']),(row['Y'],row['H']))
        for name,digest in record['preserved_files'].items():
            from trl_d3 import LEDGERS, recover_prefix
            if name in LEDGERS:
                recover_prefix(ROOT,name,digest)
            else:
                self.assertEqual(sha((ROOT/name).read_bytes()),digest)


class D3cFreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        parent=read(ROOT/'freeze-d3b.json')
        for name,digest in parent['files'].items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(frozen_bytes(name,digest))
        (self.root/'freeze-d3b.json').write_bytes((ROOT/'freeze-d3b.json').read_bytes())
        for name in D3C_ADDED|D3C_CHANGED:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
            sealed=read(ROOT/'freeze-d3c.json')
            p.write_bytes(frozen_bytes(name,sealed['files'][name]))
        self.report()

    def report(self):
        (self.root/'evidence/test-report-d3c.json').write_text(canonical({
            'status':'PASS','failures':0,'errors':0,'tests':1,
            'tested_files':tested_inputs(self.root),'fixture':True})+'\n')

    def test_seal_parent_chain_create_once_and_no_dispatch_clearance(self):
        digest=freeze_d3c(self.root)
        self.assertEqual(verify(self.root),digest)
        f=read(self.root/'freeze-d3c.json')
        self.assertEqual(f['parent_freeze_sha256'],D3B_FREEZE_SHA256)
        with self.assertRaises(FileExistsError):freeze_d3c(self.root)
        from trl_collect import readiness,collect
        with self.assertRaises(Stop):readiness(self.root)
        with patch('trl_collect.Claude',side_effect=AssertionError('no model construction')):
            with self.assertRaises((Stop,FileNotFoundError)):collect(self.root,'claude')
        self.assertFalse((self.root/'collection').exists())

    def test_changed_science_baselines_or_files_cannot_be_sealed(self):
        freeze_d3c(self.root);f=read(self.root/'freeze-d3c.json')
        for name in ('config/prompts.json','deviations/d3c/baseline/trl_validation.py'):
            changed=deepcopy(f);changed['files'][name]='0'*64
            with self.assertRaises(Stop):d3c_scope(self.root,changed)
        p=self.root/'trl_validation.py';p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(Stop):verify(self.root)

    def test_missing_or_stale_test_report_blocks_sealing(self):
        (self.root/'trl_validation.py').write_text('changed after tests')
        with self.assertRaisesRegex(Stop,'passing D3c tests'):freeze_d3c(self.root)
