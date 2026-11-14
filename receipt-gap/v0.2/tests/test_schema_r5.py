"""r5 provider projection and saved-400 resume, entirely offline."""
import copy
import itertools
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import rg_collect as c
import rg_analysis as a
import rg_freeze as f
import rg_r5 as r5
import rg_revision as r
from rg_claude_schema import claude_schema, revised_request
from rg_core import ROOT, ACTION_SCHEMAS, action, ModelOutputError, canonical, sha, reserve, render, P, maximal_history
from rg_usage_limit import schema_nonstart, nonstart, verified_pause, episode_directory, operational_events
from rg_offline import Fake
from test_v02 import accepts


class ProjectionTests(unittest.TestCase):
    def test_finite_space_is_superset_and_validator_recovers_exact_legal_set(self):
        keys=(None,'x','X_-9','x'*16,'x'*17,'','a b','é','a\n',5,True)
        for toolkit in ACTION_SCHEMAS:
            provider=claude_schema('action',toolkit)
            self.assertFalse(set(provider)&{'oneOf','anyOf','allOf'})
            self.assertEqual(provider['required'],['op','job','key'])
            self.assertIs(provider['additionalProperties'],False)
            extras=[]
            for op,job,key in itertools.product(('send','status','finish','other',None),(None,0,1,2,3,4,5,True,1.5,'1'),keys):
                v={'op':op,'job':job,'key':key}
                local=accepts(ACTION_SCHEMAS[toolkit],v);remote=accepts(provider,v)
                try:action(v,toolkit);valid=True
                except ModelOutputError:valid=False
                self.assertEqual(local,valid,(toolkit,v))
                self.assertEqual(remote and valid,local,(toolkit,v))
                if local:self.assertTrue(remote,(toolkit,v))
                if remote and not local:
                    extras.append(v)
                    self.assertTrue(op=='finish' and (job is not None or key is not None) or op!='finish' and job is None,(toolkit,v))
            self.assertTrue(extras)
            for v in ({},[],None,{'op':'finish','job':None},{'op':'finish','job':None,'key':None,'extra':None}):
                self.assertFalse(accepts(provider,v))

    def test_branch_projection_proves_inclusion_beyond_sample_keys(self):
        # All local branches have exactly these fields. Their property domains
        # are identical to, or a single type/const within, the provider domains.
        for toolkit,local in ACTION_SCHEMAS.items():
            p=claude_schema('action',toolkit)['properties']
            for branch in local['oneOf']:
                self.assertEqual(set(branch['properties']),set(p))
                self.assertEqual(branch['required'],['op','job','key'])
                self.assertIs(branch['additionalProperties'],False)
                props=branch['properties'];self.assertIn(props['op']['const'],p['op']['enum'])
                job=props['job'];self.assertIn(job['type'],p['job']['type'])
                if job['type']=='integer':self.assertEqual(job,{**p['job'],'type':'integer'})
                key=props['key']
                for domain in key.get('anyOf',[key]):
                    if domain['type']=='string':self.assertEqual(domain,{**p['key'],'type':'string'})
                    else:self.assertEqual(domain,{'type':'null'})

    def test_local_scientific_inputs_and_validator_are_byte_identical(self):
        parent=c.read(ROOT/'freeze-r4.json')['files']
        for n in ('rg_core.py','config/action-plain-schema.json','config/action-keyed-schema.json','config/action-check-schema.json','config/prompts.json','config/episodes.json','config/report-schema.json','config/sizing.json'):
            self.assertEqual(sha((ROOT/n).read_bytes()),parent[n],n)

    def test_provider_projection_fits_unchanged_conservative_reservations(self):
        for toolkit,framing,phase,depth in itertools.product(ACTION_SCHEMAS,('notification','payment'),('action','report'),range(11)):
            ep={'toolkit':toolkit,'framing':framing};prompt=render(ep,maximal_history(depth),10,phase)
            size=len(prompt.encode())+len(P['system'].encode())+len(canonical(claude_schema(phase,toolkit)).encode())+826
            self.assertGreaterEqual(reserve(prompt,phase,toolkit)['input_tokens'],size*1.10)

    def test_exact_400_and_near_misses(self):
        raw=c.read(ROOT/'fixtures/stopped-r3-claude-raw.json')
        self.assertTrue(schema_nonstart(raw));self.assertTrue(nonstart(raw))
        self.assertEqual(r.classify(raw)['class'],'HARNESS NON-START')
        mutations=[('api_error_status',401),('result','API Error: 400 other'),('duration_api_ms',1),('total_cost_usd',.01),('modelUsage',{'claude-opus-5-5':{}}),('structured_output',{}),('subagent_stats',{'calls':1})]
        for k,v in mutations:
            changed=copy.deepcopy(raw);e=c.strict_load(raw['stdout']);e[k]=v;changed['stdout']=canonical(e)
            self.assertFalse(schema_nonstart(changed),(k,v))
        for field in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
            changed=copy.deepcopy(raw);e=c.strict_load(raw['stdout']);e['usage'][field]=1;changed['stdout']=canonical(e)
            self.assertFalse(schema_nonstart(changed),field)
        changed=copy.deepcopy(raw);changed['transport_error']='uncertain';self.assertFalse(schema_nonstart(changed))
        e=c.strict_load(raw['stdout']);e['usage']['server_tool_use']={'web_search_requests':1}
        changed=copy.deepcopy(raw);changed['stdout']=canonical(e);self.assertFalse(schema_nonstart(changed))


class SavedResumeTests(unittest.TestCase):
    def prepare(self,root):
        ep=next(e for e in c.read(ROOT/'config/episodes.json') if e['actor']=='claude')
        base=root/'collection';old=Path('resumes/r3/episodes')/ep['id']
        shutil.copytree(ROOT/'collection'/old,base/old)
        for n in ('STOP.json','STOP-r3.json','ledger.jsonl'):shutil.copyfile(ROOT/'collection'/n,base/n)
        for n in ('config/prior-spend.json','evidence/v01-ledger.jsonl','fixtures/stopped-r3-claude-raw.json'):
            p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
        c.save(root/'config/episodes.json',[ep]);return ep,base

    def test_clearance_resume_accounting_prompt_identity_and_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ep,base=self.prepare(root)
            before={str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file()}
            ledger_before=c.Ledger(base/'ledger.jsonl');exposure=ledger_before.exposure
            with patch('rg_freeze.verify',return_value='r5-test'),patch('rg_r5.verify_preservation'):
                record=r5.clearance_r5(root);self.assertTrue(r5.r5_cleared(root,base))
                self.assertEqual(r5.clearance_r5(root),record)
                for n,data in before.items():
                    if n=='ledger.jsonl':self.assertTrue((base/n).read_bytes().startswith(data))
                    else:self.assertEqual((base/n).read_bytes(),data,n)
                self.assertEqual(c.Ledger(base/'ledger.jsonl').exposure,exposure)
                d=episode_directory(base,ep['id']);original=c.read(d/'0.rejected-request.json')
                self.assertEqual(c.read(d/'0.request.json'),revised_request(original,ep['toolkit']))
                for i in ('0','1'):verified_pause(d/'dispatches/0'/i,d/'0.request.json')
                c.save(base/'OFFLINE-FAKE.json',{'real_model_calls':0})
                class Provider(Fake):
                    def generate(inner,*args):
                        if inner.calls==0:self.assertEqual(args[1],original['prompt'])
                        return super().generate(*args)
                c.run_episode(ep,Provider(),base,c.Ledger(base/'ledger.jsonl'),c.ActiveTime(base/'test-time.jsonl',7200),'OFFLINE-FAKE',True,'STOP-r5.json')
                ledger=c.Ledger(base/'ledger.jsonl')
                self.assertIn(record['call'],ledger.restored)
                self.assertEqual(ledger.holds[ep['id']],0)
                self.assertEqual(a.reconcile(root,base)['status'],'RECONCILED')
                rows,_=a.load_rows(root,base);self.assertEqual(len(rows),1)
                self.assertEqual([e['kind'] for e in operational_events(base)],['dns non-start','harness non-start'])
                self.assertTrue(r5.r5_cleared(root,base))
                request=c.read(d/'0.request.json');request['prompt']+='tamper'
                (d/'0.request.json').write_text(canonical(request))
                with self.assertRaises(ValueError):episode_directory(base,ep['id'])

    def test_full_collector_admits_r5_and_resends_with_mocked_provider_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ep,base=self.prepare(root)
            with patch('rg_freeze.verify',return_value='r5-test'),patch('rg_r5.verify_preservation'):
                record=r5.clearance_r5(root)
                provider=Fake();provider.preflight=lambda actor:{'fixture':True}
                with patch('rg_collect.push_gate',return_value='r5-test'),patch('rg_collect.prior_spend_gate',return_value={}),patch('rg_collect.Claude',return_value=provider):
                    c.collect(root,'claude',binary='mocked-only',freeze_file='freeze-r5.json')
                self.assertEqual(provider.calls,6)
                self.assertTrue(c.read(episode_directory(base,ep['id'])/'episode.json')['trajectory_valid'])
                self.assertTrue(r5.r5_cleared(root,base))
                self.assertTrue((base/'STOP.json').exists());self.assertTrue((base/'STOP-r3.json').exists())
                c.save(base/'STOP-r2.json',{'reason':'unrelated stop'})
                with self.assertRaisesRegex(c.Stop,'unrelated stop'):c.collect(root,'claude',binary='mocked-only',freeze_file='freeze-r5.json')

    def test_r5_seals_all_five_parents_and_is_create_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f.prepare(root);f.freeze(root);f.revise(root)
            c.save(root/'revisions/r2/preservation.json',{'files':{},'parents':{},'prefixes':{}})
            f.revise_r2(root);f.revise_r3(root)
            c.save(root/'revisions/r4/preservation.json',{'files':{},'parents':{},'prefixes':{}});f.revise_r4(root)
            names=('freeze.json','freeze-r1.json','freeze-r2.json','freeze-r3.json','freeze-r4.json')
            parents={n:sha((root/n).read_bytes()) for n in names}
            c.save(root/'revisions/r5/preservation.json',{'files':{},'parents':parents,'prefixes':{}})
            digest=f.revise_r5(root)
            self.assertEqual(c.read(root/'freeze-r5.json')['parents'],parents)
            self.assertEqual(f.verify(root,'freeze-r5.json'),digest)
            with self.assertRaises(FileExistsError):f.revise_r5(root)
            c.save(root/'event.json',{'activity_type':'push','after':'a'*40,'ref':'refs/heads/test',
                   'timestamp':c.read(root/'freeze-r5.json')['created_at'],'id':'r5-test'})
            checked=[]
            def fake_git(cmd,**kwargs):
                if cmd[1:]==['rev-parse','HEAD']:return 'a'*40+'\n'
                if cmd[1:]==['remote','get-url','origin']:return 'https://github.com/Robin84Bran/research.git\n'
                if cmd[1]=='show':
                    name=cmd[2].split(':receipt-gap/v0.2/')[1];checked.append(name)
                    return (root/name).read_bytes()
                if cmd[1]=='ls-remote':return 'a'*40+'\trefs/heads/test\n'
                raise AssertionError(cmd)
            with patch('rg_freeze.subprocess.check_output',side_effect=fake_git):
                self.assertEqual(f.attest(root,root/'event.json','a'*40,'receipt-gap/v0.2',root,'freeze-r5.json'),digest)
            self.assertTrue(set(parents)<=set(checked))
            self.assertEqual(c.read(root/'collection/push-r5.json')['freeze_sha256'],digest)
            with patch('rg_collect.checked_receipt',return_value=c.dt.datetime.now(c.dt.timezone.utc)):
                self.assertEqual(c.push_gate(root,'freeze-r5.json'),digest)


    def test_no_clearance_and_new_stop_block_before_provider_construction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'collection';c.save(base/'STOP-r3.json',{'reason':'400'})
            with patch('rg_collect.Claude',side_effect=AssertionError('provider constructed')):
                with self.assertRaisesRegex(c.Stop,'clearance required'):c.collect(root,'claude','fake',freeze_file='freeze-r5.json')
            with patch('rg_r5.r5_cleared',return_value=True):
                c.save(base/'STOP-r5.json',{'reason':'new stop'})
                with self.assertRaisesRegex(c.Stop,'new stop'):c.collect(root,'claude','fake',freeze_file='freeze-r5.json')
