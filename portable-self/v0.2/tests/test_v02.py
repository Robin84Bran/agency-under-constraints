"""v0.2 transport delta, real-envelope contract and inherited science checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ps_core import ROOT, ARMS, ACTORS, SCHEMAS, World, canonical, sha, render, reservation, schedule
from ps_io import Stop, EpisodeFailure, TransportFailure, read
from ps_transport import decode, usage, local_request, claude_command, Local
from ps_offline import Fake
from ps_collect import collect
from ps_analysis import score


def episode(actor='claude',seed=0,arm='keyed'):
    return {'id':f'{actor}-{seed:02d}-different-stable-{arm}', 'actor':actor,
            'seed':seed,'world':'different-stable','arm':arm}


class V02Tests(unittest.TestCase):
    def test_every_actor_phase_gets_exact_schema(self):
        for actor in ACTORS:
            for arm in ARMS:
                ep=episode(actor,arm=arm)
                for index in range(8):
                    phase='write' if index<4 else 'act'
                    with self.subTest(actor=actor,arm=arm,index=index):
                        if actor=='claude':
                            cmd=claude_command('/fixture/claude',phase,25000)
                            self.assertEqual(cmd[cmd.index('--json-schema')+1],canonical(SCHEMAS[phase]))
                        else:
                            req=local_request(ep,'frozen prompt',index)
                            self.assertIsInstance(req['format'],dict)
                            self.assertEqual(req['format'],SCHEMAS[phase])
                            self.assertNotIn('system',req);self.assertNotIn('template',req)
                            self.assertEqual(req['options'],{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192,'seed':index+1})
        items=SCHEMAS['act']['properties']['controls']['items']['anyOf']
        self.assertEqual(items,[{'type':'integer','enum':[1,2,3,4]},{'type':'null'}])
        self.assertEqual(SCHEMAS['act']['properties']['controls']['minItems'],4)
        self.assertEqual(SCHEMAS['act']['properties']['controls']['maxItems'],4)

    def test_scientific_inputs_and_validator_unchanged(self):
        baseline=read(ROOT/'evidence/v01-baseline.json')
        for name,digest in baseline['unchanged'].items():
            source=ROOT/name
            if name in ('ps_collect.py','ps_analysis.py','ps_io.py'):
                source=ROOT/'revisions/usage-limit/parent-files'/name
            with self.subTest(name=name): self.assertEqual(sha(source.read_bytes()),digest)
        inherited=(ROOT/'evidence/PROTOCOL-v01.md').read_bytes()
        self.assertEqual(sha(inherited),baseline['protocol_sha256'])
        self.assertTrue((ROOT/'PROTOCOL.md').read_bytes().endswith(inherited))
        self.assertEqual(read(ROOT/'config/episodes.json'),schedule())

    def test_offline_support_evidence_binds_binary_strings(self):
        support=read(ROOT/'evidence/ollama-schema-support.json')
        self.assertEqual(support['status'],'VERIFIED_OFFLINE')
        self.assertEqual(support['model_calls'],0)
        # Retained exact snippets can be checked without requiring local binaries in a clone.
        for source in support['sources']:
            self.assertEqual(len(source['sha256']),64)
            for snippet in source['snippets']:
                self.assertEqual(bytes.fromhex(snippet['hex']).decode(),snippet['needle'])

    def real(self):
        ep=episode();p=World(ep).payload()
        e=read(ROOT/'fixtures/real-claude-envelope.json')
        return ep,p,e

    def test_real_claude_envelope_unmodified_is_episode_content_failure(self):
        ep,p,e=self.real()
        self.assertEqual(usage(e,'claude'),(1602,199))
        self.assertEqual(e['num_turns'],2);self.assertEqual(e['stop_reason'],'tool_use')
        self.assertIsInstance(e['subagent_stats'],dict)
        # The actual sibling fixture contains op/job/key, not a Portable Self write.
        # It must pass integrity checks and fail only this project's inner contract.
        with self.assertRaises(EpisodeFailure) as caught:
            decode({'stdout':canonical(e),'stderr':'','returncode':0},ep,p,reservation('keyed','write'),True)
        self.assertNotIsInstance(caught.exception,Stop)
        self.assertIn('invalid write',str(caught.exception))

    def test_real_envelope_portable_payload_derivative_accepts_one_two_turns(self):
        ep,p,e=self.real()
        for turns in (1,2):
            derived=copy.deepcopy(e)
            derived.update(structured_output={'slot':p['writable_slot'],'note':''},result='prose is never used',num_turns=turns,stop_reason='tool_use' if turns==2 else 'end_turn')
            value,metrics=decode({'stdout':canonical(derived),'stderr':'','returncode':0},ep,p,reservation('keyed','write'),True)
            self.assertEqual(value,derived['structured_output']);self.assertEqual(metrics['input_tokens'],1602)

    def test_nested_activity_positive_count_only(self):
        ep,p,e=self.real();e['structured_output']={'slot':p['writable_slot'],'note':''}
        for stats in ({},{'spawned':0,'requested':{'foreground':0}},None,e['subagent_stats']):
            derived={**e,'subagent_stats':stats}
            decode({'stdout':canonical(derived),'stderr':'','returncode':0},ep,p,reservation('keyed','write'),True)
        for stats in ({'spawned':1},{'requested':{'foreground':1}},{'killed':{'system':1}},{'by_type':{'unknown':1}}):
            with self.subTest(stats=stats),self.assertRaises(Stop):
                decode({'stdout':canonical({**e,'subagent_stats':stats}),'stderr':'','returncode':0},ep,p,reservation('keyed','write'),True)
        derived=copy.deepcopy(e);derived['usage']['server_tool_use']['web_fetch_requests']=1
        with self.assertRaises(Stop): decode({'stdout':canonical(derived),'stderr':'','returncode':0},ep,p,reservation('keyed','write'),True)

    def test_real_fixture_first_bad_payload_continues_next_episode(self):
        original=read(ROOT/'fixtures/real-claude-envelope.json')
        def mutate(raw,ep,i):
            return {'stdout':canonical(original),'stderr':'','returncode':0} if ep['seed']==0 and i==0 else raw
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'fake';eps=[episode(seed=s) for s in (0,1)];fake=Fake(mutate=mutate)
            collect(ROOT,'claude',fake_transport=fake,output=base,episodes=eps)
            self.assertEqual(fake.calls,9)
            self.assertFalse(score(eps[0],base,True)['technical_complete'])
            self.assertTrue(score(eps[1],base,True)['technical_complete'])
            self.assertFalse((base/'STOP.json').exists())

    def test_ollama_version_pin_fails_closed(self):
        from ps_transport import identity
        expected=identity(ROOT)['qwen7b']
        def metadata(path,body=None,timeout=10):
            if path=='/api/version': return canonical({'version':'other'})
            if path=='/api/tags': return canonical({'models':[{'name':'qwen2.5:7b','digest':expected['digest']}]})
            return canonical({'template':expected['template'],'system':expected['system']})
        with patch('ps_transport.http',side_effect=metadata),self.assertRaises(Stop): Local(ROOT).preflight('qwen7b')

    def test_v01_partial_retained_fixed_denominator(self):
        inventory=read(ROOT/'evidence/v01-inventory.json')
        self.assertEqual(inventory['observed_terminal_records'],288)
        partial=[e for e in inventory['episodes'] if e['state']=='partial']
        self.assertEqual(len(partial),1);row=partial[0]
        self.assertEqual((row['calls_started'],row['valid_calls']),(5,4))
        self.assertEqual((row['Y'],row['F'],row['technical_missing']),(0,0,16))
        self.assertTrue(all(x['correct'] is None for x in row['facts']))
