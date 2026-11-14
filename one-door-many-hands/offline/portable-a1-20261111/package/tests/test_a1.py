"""A1 sibling-failure regressions. All providers and read-only Git are fake."""
import ast
import base64
import copy
import datetime as dt
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from od_core import ROOT,MODEL,PINS,canonical,render,reserve,schedule,sha,strict_load
from od_contract import request
from od_transport import Fake,raw_record
from od_collect import collect
from od_analysis import replay
from od_io import Stop,Ledger,ActiveTime,Log,read,save
from od_validation import validate,accounting,cost,stdout,ReplyFailure
from od_freeze import inputs,verify,freeze_a1,attest,A1_CHANGED
from od_provenance import receipt_gate


class Edited(Fake):
    def __init__(self,edit): super().__init__();self.edit=edit
    def generate(self,*args): return self.edit(super().generate(*args))


def payload(raw,text):
    e=strict_load(stdout(raw));e['structured_output']='A1_PAYLOAD_MARKER'
    return dict(raw,stdout_b64=raw_record(canonical(e).replace('"A1_PAYLOAD_MARKER"',text).encode())['stdout_b64'])


def change(raw,edit):
    e=strict_load(stdout(raw));edit(e)
    return dict(raw,stdout_b64=raw_record(canonical(e).encode())['stdout_b64'])


class A1(unittest.TestCase):
    def jobs(self,actor='claude',n=4): return [e for e in schedule() if e['actor']==actor][:n]
    def raw(self,actor='claude'):
        ep=self.jobs(actor,1)[0];b=reserve(render(ep))
        return b,Fake().generate(ep,request(ep,render(ep),b),None)
    def test_every_content_failure_including_first_continues_and_scores(self):
        texts=['null','[]','"{bad json"','{"fleet":true}','{"fleet":2}',
               '{"fleet":6,"key":"illegal"}','{}','{"fleet":6,"done_reason":"stop"}',
               '{"fleet":6,"fleet":1}','{"fleet":NaN}','{"fleet":1e999}']
        edits=[lambda r,v=v:payload(r,v) for v in texts]
        edits += [lambda r:change(r,lambda e:e.pop('structured_output')),
                  lambda r:change(r,lambda e:e.update(num_turns=1,stop_reason='max_tokens')),
                  lambda r:change(r,lambda e:e.update(num_turns=2,stop_reason='length'))]
        for edit in edits:
            with self.subTest(edit=edit),tempfile.TemporaryDirectory() as d:
                base=Path(d)/'fake';fake=Edited(edit);jobs=self.jobs(n=2)
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),2);self.assertFalse((base/'STOP.json').exists())
                rows,ledger=replay(ROOT,base,True,jobs)
                self.assertEqual(ledger['spent_micro_usd'],4000);self.assertEqual(ledger['open_holds_micro_usd'],0)
                for row in rows:
                    self.assertFalse(row['schema_valid']);self.assertEqual(row['choice_status'],'REPLY_FAILURE')
                    self.assertEqual(row['operational_value'],0);self.assertEqual(row['optimal'],0)
                    self.assertIsNone(row['chosen_value']);self.assertIsNone(row['fleet'])
                collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),2)
    def test_local_malformed_json_extra_keys_and_length_continue(self):
        for response in ('not JSON','{"fleet":6,"key":"illegal"}','{"fleet":true}','{"fleet":NaN}'):
            with self.subTest(response=response),tempfile.TemporaryDirectory() as d:
                fake=Edited(lambda r:change(r,lambda e:e.update(response=response)))
                jobs=self.jobs('qwen7b',4);base=Path(d)/'fake'
                collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                rows,_=replay(ROOT,base,True,jobs)
                self.assertEqual(len(fake.calls),4);self.assertTrue(all(r['choice_status']=='REPLY_FAILURE' for r in rows))
    def test_payload_metadata_split_and_fatal_precedence(self):
        b,r=self.raw()
        for text in ('{"fleet":6,"fleet":1}','{"fleet":NaN}','{"fleet":1e999}'):
            bad=payload(r,text);self.assertEqual(cost(accounting(bad,'claude')),2000)
            with self.assertRaises(ReplyFailure):validate(bad,'claude',b)
            for field,value in (('effort','high'),('modelUsage',{}),('total_cost_usd',26)):
                raw=payload(change(r,lambda e:e.update({field:value})),text)
                with self.assertRaises(Stop):validate(raw,'claude',b)
        for text in ('{"fleet":',):
            with self.assertRaises(Stop):validate(payload(r,text),'claude',b)
        duplicated=canonical(strict_load(stdout(r)))[:-1]+',"num_turns":1}'
        raw=raw_record(duplicated.encode());self.assertIsNone(accounting(raw,'claude'))
        with self.assertRaises(Stop):validate(raw,'claude',b)
        text=canonical(strict_load(stdout(r))).replace('"input_tokens":100','"input_tokens":100,"input_tokens":100')
        self.assertIsNone(accounting(raw_record(text.encode()),'claude'))
    def test_schema_provider_rejection_settles_and_continues(self):
        def edit(r):
            r=change(r,lambda e:e.update(subtype='error_max_structured_output_retries',is_error=True,errors=['invalid model output']))
            return dict(r,returncode=1)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'fake';jobs=self.jobs(n=2);fake=Edited(edit)
            collect(ROOT,'claude',fake_transport=fake,output=base,jobs_override=jobs)
            rows,ledger=replay(ROOT,base,True,jobs)
            self.assertEqual(len(fake.calls),2);self.assertEqual(ledger['spent_micro_usd'],4000)
            self.assertTrue(all(r['reason']=='provider rejected model structured output' for r in rows))
        b,r=self.raw();bad=edit(r)
        for edit2 in (lambda e:e.update(effort='high'),lambda e:e.update(num_turns=3),lambda e:e.pop('total_cost_usd')):
            with self.assertRaises(Stop):validate(change(bad,edit2),'claude',b)
        with self.assertRaises(Stop):validate(dict(r,returncode=1),'claude',b)
    def test_cache_categories_exactly_once_and_missing_unknown(self):
        b,r=self.raw()
        def edit(e):
            e['usage'].update(input_tokens=2,cache_creation_input_tokens=1600,cache_read_input_tokens=7,output_tokens=199)
            e['modelUsage'][MODEL].update(inputTokens=2,cacheCreationInputTokens=1600,cacheReadInputTokens=7,outputTokens=199)
            e['total_cost_usd']=0.016788
        r=change(r,edit);u=validate(r,'claude',b)['usage']
        self.assertEqual(sum(u[k] for k in ('input','cache_creation','cache_read')),1609)
        self.assertEqual(u['output'],199);self.assertEqual(cost(u),16788)
        self.assertEqual(cost(dict(u,reported_cost_micro_usd=0)),10416)
        for field in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens','output_tokens'):
            bad=change(r,lambda e:e['usage'].pop(field));self.assertIsNone(accounting(bad,'claude'))
            with self.assertRaises(Stop):validate(bad,'claude',b)
    def test_three_transport_failures_pause_durably(self):
        for fault in ('done','usage','timeout'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as d:
                base=Path(d)/'fake';jobs=self.jobs('qwen7b');fake=Fake(fault)
                with self.assertRaisesRegex(Stop,'three consecutive'):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),3);stop=(base/'STOP.json').read_bytes()
                rows,_=replay(ROOT,base,True,jobs)
                self.assertEqual([r['attempted'] for r in rows],[True,True,True,False])
                with self.assertRaises(Stop):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(stop,(base/'STOP.json').read_bytes());self.assertEqual(len(fake.calls),3)
    def test_transport_streak_survives_restart_and_crash_before_stop(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'fake';jobs=self.jobs('qwen7b');fake=Fake('done')
            collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs[:2])
            with patch('od_collect.durable_stop'),self.assertRaisesRegex(Stop,'three consecutive'):
                collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
            self.assertFalse((base/'STOP.json').exists());self.assertEqual(len(fake.calls),3)
            with self.assertRaisesRegex(Stop,'three consecutive'):
                collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
            self.assertTrue((base/'STOP.json').exists());self.assertEqual(len(fake.calls),3)
    def test_success_and_content_failure_break_transport_streak(self):
        for middle in (None,'invalid'):
            class Sequence(Fake):
                def generate(self,*args):
                    self.fault=middle if len(self.calls)==2 else 'done'
                    return super().generate(*args)
            with tempfile.TemporaryDirectory() as d:
                jobs=self.jobs('qwen7b',5);base=Path(d)/'fake';fake=Sequence()
                collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),5);self.assertFalse((base/'STOP.json').exists());replay(ROOT,base,True,jobs)
    def test_harness_exception_never_downgraded_to_local_transport(self):
        for error in (Stop('identity drift'),RuntimeError('harness bug'),ValueError('bad configuration')):
            class Broken(Fake):
                def generate(self,*args): self.calls.append(args[0]['id']);raise error
            with tempfile.TemporaryDirectory() as d:
                fake=Broken();base=Path(d)/'fake';jobs=self.jobs('qwen7b')
                with self.assertRaises(Stop):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
                self.assertEqual(len(fake.calls),1);replay(ROOT,base,True,jobs)
    def test_prefixes_allow_append_reject_rewrite_and_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'fake';jobs=self.jobs('qwen7b');fake=Fake('done')
            collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs[:1])
            p=base/'local-time.jsonl';prefix=p.read_bytes()
            collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs[:2])
            self.assertTrue(p.read_bytes().startswith(prefix));Log(p)
            current=p.read_bytes();p.write_bytes(prefix)
            with self.assertRaises(Stop):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
            self.assertEqual(len(fake.calls),2)
            p.write_bytes(current.replace(b'preflight',b'prEflight',1))
            with self.assertRaises(Stop):Log(p)
    def test_temporary_cwd_failure_is_fatal_and_never_resent(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'fake';jobs=self.jobs('qwen7b');fake=Fake()
            with patch('od_collect.tempfile.TemporaryDirectory',side_effect=OSError('cwd unavailable')):
                with self.assertRaises(OSError):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
            self.assertTrue((base/'STOP.json').exists());self.assertEqual(fake.calls,[])
            with self.assertRaises(Stop):collect(ROOT,'local',fake_transport=fake,output=base,jobs_override=jobs)
            self.assertEqual(fake.calls,[])
    def test_real_pinned_identity_all_three_models(self):
        from od_identity import identity,verify_preflight
        models=identity(ROOT)
        self.assertEqual(models['qwen7b']['template'],models['qwen1b']['template'])
        self.assertIn('Alibaba',models['qwen7b']['system']);self.assertEqual(models['llama8b']['system'],'')
        for actor,m in models.items():
            meta={'tags':{'models':[{'name':m['tag'],'digest':m['digest']}]},'show':{'template':m['template'],'system':m['system']}}
            verify_preflight(ROOT,actor,meta)
            for field in ('template','system'):
                bad=copy.deepcopy(meta);bad['show'][field]+='changed'
                with self.assertRaises(Stop):verify_preflight(ROOT,actor,bad)
            bad=copy.deepcopy(meta);bad['tags']['models'][0]['digest']='0'*64
            with self.assertRaises(Stop):verify_preflight(ROOT,actor,bad)
    def package(self,root):
        for name in inputs(ROOT)+['freeze.json']:
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    def test_a1_freeze_parent_scope_create_once_and_drift(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.package(root);parent=(root/'freeze.json').read_bytes()
            h=freeze_a1(root);self.assertEqual(verify(root),h);self.assertEqual(parent,(root/'freeze.json').read_bytes())
            with self.assertRaises(FileExistsError):freeze_a1(root)
            f=read(root/'freeze-a1.json');p=root/'config/prompts.json';p.write_bytes(p.read_bytes()+b' ')
            f['files']['config/prompts.json']=sha(p.read_bytes());(root/'freeze-a1.json').write_text(canonical(f))
            with self.assertRaisesRegex(Stop,'frozen science'):verify(root)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.package(root);freeze_a1(root)
            (root/'freeze.json').write_bytes(parent+b' ')
            with self.assertRaisesRegex(Stop,'parent freeze'):verify(root)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.package(root);(root/'collection').mkdir()
            with self.assertRaises(Stop):freeze_a1(root)
    def test_a1_attestation_binds_both_freezes_and_activity_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'project';clone=Path(d)/'clone';clone.mkdir();self.package(root);h=freeze_a1(root)
            created=dt.datetime.fromisoformat(read(root/'freeze-a1.json')['created_at'])
            # Test-only past fixture: preserve ordering without a wall-clock sleep.
            earlier=(created-dt.timedelta(seconds=10)).isoformat();f=read(root/'freeze-a1.json');f['created_at']=earlier
            (root/'freeze-a1.json').write_text(canonical(f)+'\n');h=verify(root)
            event=Path(d)/'activity.json';commit='a'*40
            save(event,{'activity_type':'push','id':123,'ref':'refs/heads/main','after':commit,'timestamp':(created-dt.timedelta(seconds=1)).isoformat()})
            seen=[]
            def git(args,cwd,timeout):
                self.assertEqual(cwd,clone);seen.append(args)
                if args[1:]==['rev-parse','HEAD']:return (commit+'\n').encode()
                if args[1:]==['remote','get-url','origin']:return b'git@github.com:Robin84Bran/research.git\n'
                if args[1]=='show':return (root/args[2].split('one-door-many-hands/')[1]).read_bytes()
                if args[1]=='ls-remote':return (commit+'\trefs/heads/main\n').encode()
                raise AssertionError(args)
            with patch('od_freeze.subprocess.check_output',side_effect=git):attest(root,event,commit,clone,'one-door-many-hands')
            self.assertEqual((root/'collection/push-event.json').read_bytes(),event.read_bytes());receipt_gate(root)
            for name in ('freeze.json','freeze-a1.json'):
                self.assertIn(['git','show',commit+':one-door-many-hands/'+name],seen)
            receipt=read(root/'collection/push.json');self.assertEqual(receipt['freeze_sha256'],h)
            receipt['freeze_sha256']=sha((root/'freeze.json').read_bytes());(root/'collection/push.json').write_text(canonical(receipt))
            with self.assertRaises(Stop):receipt_gate(root)
            self.assertEqual(list(clone.iterdir()),[])
    def test_scientific_analysis_functions_and_contract_unchanged(self):
        old=ast.parse((ROOT/'deviations/a1/original/od_analysis.py').read_text());new=ast.parse((ROOT/'od_analysis.py').read_text())
        functions=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='replay'}
        self.assertEqual(functions(old),functions(new))
        parent=read(ROOT/'freeze.json')
        for name,h in parent['files'].items():
            if name not in A1_CHANGED:self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
    def test_exhaustive_raise_and_fatal_inventory(self):
        from od_audit import audit_sites
        text=(ROOT/'DEVIATIONS.md').read_text()
        markers=[line.split('|')[1].strip().strip('`') for line in text.splitlines() if line.startswith('| `')]
        self.assertEqual(markers,[row['site'] for row in audit_sites(ROOT)])
