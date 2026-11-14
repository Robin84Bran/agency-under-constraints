import copy
import unittest
from od_core import *
from od_contract import *
from od_transport import Fake,raw_record
from od_validation import *
from od_io import Stop

class Validation(unittest.TestCase):
    def setup_raw(self,actor='claude'):
        e=next(e for e in schedule() if e['actor']==actor);bound=reserve(render(e));raw=Fake().generate(e,request(e,render(e),bound),None)
        return e,bound,raw,strict_load(stdout(raw))
    def changed(self,raw,e):return dict(raw,stdout_b64=raw_record(canonical(e).encode())['stdout_b64'])
    def test_two_turn_strict(self):
        ep,b,r,e=self.setup_raw()
        self.assertTrue(validate(r,'claude',b)['schema_valid'])
        for turns in (1,2):
            e['num_turns']=turns;self.assertTrue(validate(self.changed(r,e),'claude',b)['schema_valid'])
        for turns in (0,3,True,2.0):
            e['num_turns']=turns
            with self.assertRaises(Stop):validate(self.changed(r,e),'claude',b)
    def test_no_result_fallback(self):
        for value in (None,'{"fleet":6}',[6]):
            ep,b,r,e=self.setup_raw();e['structured_output']=value;e['result']='{"fleet":6}'
            with self.assertRaises(ReplyFailure):validate(self.changed(r,e),'claude',b)
    def test_cached_input_and_reported_cost(self):
        ep,b,r,e=self.setup_raw();u=usage(e,'claude')
        self.assertEqual(sum(u[k] for k in ('input','cache_read','cache_creation')),250);self.assertEqual(cost(u),2000)
        del e['total_cost_usd'];self.assertIsNone(usage(e,'claude'))
    def test_usage_model_effort_and_tools(self):
        for edit in [lambda e:e.update(effort='high'),lambda e:e.update(modelUsage={}),lambda e:e.update(permission_denials=[{}]),
                     lambda e:e['usage'].update(output_tokens=True),lambda e:e['modelUsage'][MODEL].update(inputTokens=0),
                     lambda e:e['usage']['server_tool_use'].update(web_search_requests=1),lambda e:e.update(total_cost_usd=-1),lambda e:e.update(num_turns=2,stop_reason='end_turn')]:
            ep,b,r,e=self.setup_raw();edit(e)
            with self.assertRaises(Stop):validate(self.changed(r,e),'claude',b)
    def test_invalid_payload_is_reply_failure(self):
        ep,b,r,e=self.setup_raw();e['structured_output']={'fleet':True}
        with self.assertRaises(ReplyFailure):validate(self.changed(r,e),'claude',b)
    def test_duplicate_envelope_keys(self):
        ep,b,r,e=self.setup_raw();r=raw_record(b'{"structured_output":{"fleet":1,"fleet":6}}')
        with self.assertRaises(Stop):validate(r,'claude',b)
    def test_claude_length(self):
        ep,b,r,e=self.setup_raw();e.update(num_turns=1,stop_reason='max_tokens')
        with self.assertRaises(ReplyFailure):validate(self.changed(r,e),'claude',b)
    def test_local_done_count_transport(self):
        for edit in [lambda e:e.update(done=False),lambda e:e.pop('eval_count'),lambda e:e.update(eval_count=True)]:
            ep,b,r,e=self.setup_raw('qwen7b');edit(e)
            with self.assertRaises(TransportFailure):validate(self.changed(r,e),'qwen7b',b)
    def test_local_length_episode(self):
        for edit in [lambda e:e.update(done_reason='length'),lambda e:e.update(eval_count=192)]:
            ep,b,r,e=self.setup_raw('qwen7b');edit(e)
            with self.assertRaises(ReplyFailure):validate(self.changed(r,e),'qwen7b',b)
    def test_local_identity_context_fatal(self):
        for edit in [lambda e:e.update(model='wrong'),lambda e:e.update(done_reason='unknown'),lambda e:e.update(prompt_eval_count=8100),lambda e:e.update(input_truncated=True)]:
            ep,b,r,e=self.setup_raw('qwen7b');edit(e)
            with self.assertRaises(Stop):validate(self.changed(r,e),'qwen7b',b)
        ep,b,r,e=self.setup_raw('qwen7b')
        with self.assertRaises(Stop):validate(dict(r,running={}),ep['actor'],b)
        with self.assertRaises(Stop):validate(r,ep['actor'],b,expected_input_tokens=301)
    def test_local_duplicate_payload(self):
        ep,b,r,e=self.setup_raw('qwen7b');e['response']='{"fleet":6,"fleet":1}'
        with self.assertRaises(ReplyFailure):validate(self.changed(r,e),'qwen7b',b)
    def test_request_flags(self):
        ep,b,r,e=self.setup_raw();req=request(ep,render(ep),b)
        self.assertIn('--json-schema',req['argv']);self.assertEqual(req['argv'][req['argv'].index('--output-format')+1],'json')
        ep,b,r,e=self.setup_raw('qwen7b');self.assertIs(request(ep,render(ep),b)['stream'],False)
