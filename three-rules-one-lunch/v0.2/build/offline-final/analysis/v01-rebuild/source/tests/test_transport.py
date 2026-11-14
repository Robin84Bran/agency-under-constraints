from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from trl_core import *
from trl_budget import maximum
from trl_io import Stop, read
from trl_transport import *


class TransportTests(unittest.TestCase):
    def raw(self):
        req=request('claude',render('shared',1,1,[]),1,11,maximum('shared'))
        return Fake().generate('claude',req,Path('.'))

    def edit(self,fn):
        e=strict_load(stdout(self.raw()));fn(e)
        return raw_record(canonical(e).encode())

    def test_required_schema_and_output_flags(self):
        cmd=claude_command('binary',1,32512)
        self.assertEqual(cmd[cmd.index('--output-format')+1],'json')
        self.assertEqual(strict_load(cmd[cmd.index('--json-schema')+1]),schema(1))
        for flag in ('--safe-mode','--restricted','--strict-mcp-config','--disable-slash-commands','--max-turns'):
            self.assertIn(flag,cmd)
        self.assertEqual(cmd[cmd.index('--tools')+1],'')
        self.assertNotIn('--bare',cmd) # --bare excludes subscription auth.

    def test_environment_isolated(self):
        with patch.dict('os.environ',{'ANTHROPIC_BASE_URL':'evil','MAX_THINKING_TOKENS':'9000','ANTHROPIC_API_KEY':'do-not-copy'}):
            e=clean_env()
        for k in ('ANTHROPIC_BASE_URL','MAX_THINKING_TOKENS','ANTHROPIC_API_KEY'):self.assertNotIn(k,e)
        self.assertEqual(e['CLAUDE_CODE_MAX_OUTPUT_TOKENS'],'1024')
        self.assertEqual(e['MAX_STRUCTURED_OUTPUT_RETRIES'],'0')

    def test_fake_envelope_validates(self):
        v,e,u=validate(self.raw(),'claude',1,maximum('shared'))
        self.assertEqual(v,{'cells':[18]});self.assertEqual(cost(u),1600)

    def test_result_prose_never_fallback(self):
        raw=self.edit(lambda e:(e.pop('structured_output'),e.update(result='{"cells":[1]}')))
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_structured_output_string_rejected(self):
        raw=self.edit(lambda e:e.update(structured_output='{"cells":[1]}'))
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_exit_failure_even_valid_payload(self):
        raw=self.raw();raw['returncode']=1
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_unsupported_turn_count_or_two_turn_end_turn_rejected(self):
        for turns,reason in ((3,'tool_use'),(2,'end_turn')):
            raw=self.edit(lambda e:e.update(num_turns=turns,stop_reason=reason))
            with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_identity_and_effort_rejected(self):
        for fn in (lambda e:e.update(modelUsage={}),lambda e:e.update(effort='high')):
            with self.assertRaises(Stop):validate(self.edit(fn),'claude',1,maximum('shared'))

    def test_real_tools_rejected(self):
        raw=self.edit(lambda e:e['usage']['server_tool_use'].update(web_search_requests=1))
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_missing_usage_is_unknown(self):
        raw=self.edit(lambda e:e['usage'].pop('cache_creation_input_tokens'))
        self.assertIsNone(usage(strict_load(stdout(raw)),'claude'))
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_usage_totals_reconcile(self):
        raw=self.edit(lambda e:e['modelUsage'][MODEL].update(inputTokens=999))
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_local_truncation_rejected(self):
        req=request('qwen7b',render('shared',1,1,[]),1,11,maximum('shared'))
        raw=Fake().generate('qwen7b',req,Path('.'))
        e=strict_load(stdout(raw));e['done_reason']='length'
        bad=raw_record(canonical(e).encode(),running=raw['running'])
        with self.assertRaises(ValueError):validate(bad,'qwen7b',1,maximum('shared'))

    def test_local_effective_context_rejected(self):
        req=request('qwen7b',render('shared',1,1,[]),1,11,maximum('shared'))
        raw=Fake().generate('qwen7b',req,Path('.'));raw['running']['models'][0]['context_length']=2048
        with self.assertRaises(Stop):validate(raw,'qwen7b',1,maximum('shared'))

    def test_live_frontier_fails_before_process(self):
        with patch('trl_transport.subprocess.run',side_effect=AssertionError('must never dispatch')):
            with self.assertRaises(Stop):Claude().generate('claude',{},Path('.'))

    def test_full_raw_bytes_preserved(self):
        b=b'\xff\x00raw\n'
        raw=raw_record(b,b)
        self.assertEqual(__import__('base64').b64decode(raw['stdout_b64']),b)
        with self.assertRaises(UnicodeError):stdout(raw)

    def test_unknown_server_tool_counts_rejected(self):
        raw=self.edit(lambda e:e['usage'].update(server_tool_use={}))
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_analysis_imports_no_provider(self):
        import subprocess
        subprocess.check_call([__import__('sys').executable,'-B','-c',
            "import sys; import trl_analysis; assert 'trl_transport' not in sys.modules; assert 'urllib.request' not in sys.modules"],cwd=ROOT)

    def test_malformed_model_usage_shape_rejected(self):
        for value in ([MODEL],{MODEL:[]},None):
            raw=self.edit(lambda e:e.update(modelUsage=value))
            with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))

    def test_boolean_returncode_rejected(self):
        raw=self.raw();raw['returncode']=False
        with self.assertRaises(Stop):validate(raw,'claude',1,maximum('shared'))
