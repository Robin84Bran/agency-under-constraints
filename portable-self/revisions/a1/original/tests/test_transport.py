import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ps_core import *
from ps_io import Stop, EpisodeFailure
from ps_transport import *
from ps_offline import Fake

class TransportTests(unittest.TestCase):
    def raw(self,actor='claude',turns=2):
        ep={'actor':actor,'seed':0,'world':'different-stable','arm':'keyed','id':'test'}
        p=World(ep).payload();f=Fake(turns);req=f.request(ep,render(p),'write',reservation('keyed','write'),0)
        return ep,p,f.generate(req,Path('.'))
    def check(self,raw,ep,p): return decode(raw,ep,p,reservation('keyed','write'),True)
    def altered(self,field,value,actor='claude'):
        ep,p,raw=self.raw(actor);e=strict_load(raw['stdout']);e[field]=value;raw['stdout']=canonical(e);return ep,p,raw

    def test_frontier_one_two_turns(self):
        for n in (1,2):
            ep,p,raw=self.raw(turns=n);value,metrics=self.check(raw,ep,p)
            self.assertEqual(value['slot'],p['writable_slot']);self.assertEqual(metrics['input_tokens'],105);self.assertEqual(metrics['reported_effort'],'UNKNOWN')

    def test_bad_turns(self):
        for value in [0,3,True,2.,None,'2']:
            ep,p,raw=self.altered('num_turns',value)
            with self.subTest(value=value),self.assertRaises(Stop): self.check(raw,ep,p)
        ep,p,raw=self.altered('stop_reason','end_turn')
        with self.assertRaises(Stop): self.check(raw,ep,p)

    def test_no_prose_fallback(self):
        for value in [None,'{"slot":1,"note":""}',[],1]:
            ep,p,raw=self.altered('structured_output',value)
            with self.subTest(value=value),self.assertRaises(Stop): self.check(raw,ep,p)

    def test_strict_structured_payload(self):
        ep,p,raw=self.altered('structured_output',{'slot':1,'note':'x','extra':1})
        with self.assertRaises(EpisodeFailure): self.check(raw,ep,p)

    def test_envelope_identity_effort_tools(self):
        for field,value in [('modelUsage',{'wrong':{}}),('effort','high'),('type','message'),('subtype','error_max_turns'),('is_error',True),('permission_denials',[{}]),('tool_calls',[{}]),('deferred_tool_use',[{}]),('modelUsage',{MODEL:{'webSearchRequests':1}})]:
            ep,p,raw=self.altered(field,value)
            with self.subTest(field=field),self.assertRaises(Stop): self.check(raw,ep,p)

    def test_complete_cache_usage(self):
        ep,p,raw=self.raw();e=strict_load(raw['stdout']);e['usage'].pop('cache_read_input_tokens');raw['stdout']=canonical(e)
        with self.assertRaises(Stop): self.check(raw,ep,p)
        e['usage']['cache_read_input_tokens']=True;raw['stdout']=canonical(e)
        with self.assertRaises(Stop): self.check(raw,ep,p)

    def test_cost_round_up_and_categories(self):
        self.assertEqual(cost_micro(100,50,{}),1400)
        self.assertEqual(cost_micro(100,50,{'total_cost_usd':.0020001}),2001)
        self.assertEqual(cost_micro(100,50,{'total_cost_usd':.0001}),1400)
        for v in [-1,True,'NaN','Infinity']:
            with self.assertRaises(Stop): cost_micro(0,0,{'total_cost_usd':v})

    def test_local_request_preserves_defaults(self):
        ep,p,_=self.raw('qwen7b');body=local_request(ep,render(p),7)
        self.assertIs(body['stream'],False);self.assertNotIn('system',body);self.assertNotIn('template',body)
        self.assertEqual(body['options']['seed'],8);self.assertEqual(body['options']['num_ctx'],8192)
        ep['seed']=19;self.assertEqual(local_request(ep,'x',0)['options']['seed'],19001)

    def test_incomplete_done_eval_is_transport_episode(self):
        for field,value in [('done',False),('done',None),('done',1),('eval_count',None),('eval_count',True)]:
            ep,p,raw=self.altered(field,value,'qwen7b')
            with self.subTest(field=field,value=value),self.assertRaises(EpisodeFailure): self.check(raw,ep,p)

    def test_output_length_episode_input_truncation_fatal(self):
        ep,p,raw=self.altered('done_reason','length','qwen7b')
        with self.assertRaises(EpisodeFailure): self.check(raw,ep,p)
        for field,value in [('input_truncated',True),('prompt_eval_count',8100),('prompt_eval_count',None),('model','wrong')]:
            ep,p,raw=self.altered(field,value,'qwen7b')
            with self.subTest(field=field),self.assertRaises(Stop): self.check(raw,ep,p)

    def test_live_running_context_and_digest(self):
        ep,p,raw=self.raw('qwen7b')
        with self.assertRaises(Stop): decode(raw,ep,p,reservation('keyed','write'),False)
        raw['running']={'models':[{'name':PINS['qwen7b'][0],'digest':PINS['qwen7b'][1],'context_length':8192}]}
        decode(raw,ep,p,reservation('keyed','write'),False)

    def test_inner_json_and_outer_json(self):
        ep,p,raw=self.altered('response','{"slot":1,"note":"","note":"x"}','qwen7b')
        with self.assertRaises(EpisodeFailure): self.check(raw,ep,p)
        ep,p,raw=self.raw('qwen7b');raw['stdout']='{}{}'
        with self.assertRaises(Stop): self.check(raw,ep,p)

    def test_identity_layers_offline(self):
        data=identity(ROOT)
        self.assertTrue(data['qwen7b']['system'].startswith('You are Qwen'))
        self.assertEqual(data['llama8b']['system'],'')
        self.assertEqual(sha(data['qwen7b']['template'].encode()),'eb4402837c7829a690fa845de4d7f3fd842c2adee476d5341da8a46ea9255175')

    def test_live_show_matches_real_system(self):
        expected=identity(ROOT)['qwen7b']
        def metadata(path,body=None,timeout=10):
            return canonical({'models':[{'name':PINS['qwen7b'][0],'digest':PINS['qwen7b'][1]}]}) if path=='/api/tags' else canonical({'template':expected['template'],'system':expected['system']}) if path=='/api/show' else '{}'
        with patch('ps_transport.http',side_effect=metadata): Local(ROOT).preflight('qwen7b')
        def wrong(path,body=None,timeout=10):
            data=strict_load(metadata(path,body))
            if path=='/api/show': data['system']=''
            return canonical(data)
        with patch('ps_transport.http',side_effect=wrong),self.assertRaises(Stop): Local(ROOT).preflight('qwen7b')

    def test_cli_flags_no_credentials_copied(self):
        cmd=claude_command(CLAUDE_BIN,'write',21504)
        self.assertEqual(cmd[cmd.index('--max-turns')+1],'2')
        for flag in ['--safe-mode','--restricted','--strict-mcp-config','--no-session-persistence','--json-schema','--output-format','--disable-slash-commands']: self.assertIn(flag,cmd)
        env=clean_env();self.assertEqual(env['MAX_STRUCTURED_OUTPUT_RETRIES'],'0');self.assertNotIn('ANTHROPIC_API_KEY',env)

    def test_byte_integrity(self):
        import base64
        ep,p,raw=self.raw();raw['stdout_b64']=base64.b64encode(b'other').decode()
        with self.assertRaises(Stop): self.check(raw,ep,p)
