"""D2 offline verification. Provider/Git calls are mocked or forbidden."""
import copy
import datetime as dt
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from bob_core import ROOT,PINS,canonical,sha,strict_load
from bob_collect import Stop,read,Ledger,LocalAdapter,collect,run_episode,ActiveTime
from bob_freeze import inventory,verify,attest,push_gate,active_freeze
from bob_d2 import (D1_SHA256,DISPOSITION,EPISODE,CALL,identity,check_local_identity,
                    freeze_d2,reconcile_d2,validate_disposition,scope)
from bob_audit import audit_episode,reconcile_ledger
from bob_analysis import score
from bob_offline import write,FakeTransport


class IdentityTests(unittest.TestCase):
    def test_all_expected_metadata_is_bound_to_exact_pins_and_layers(self):
        models=identity(ROOT)
        for model,(tag,digest) in PINS.items():
            self.assertEqual(models[model]['tag'],tag)
            self.assertEqual(models[model]['digest'],digest)
            check_local_identity(ROOT,model,models[model])
        self.assertEqual(models['qwen7b']['system'],models['qwen1b']['system'])
        self.assertEqual(models['qwen7b']['system'],'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.')
        self.assertEqual(models['llama8b']['system'],'')
        llama=dict(models['llama8b']); del llama['system']
        check_local_identity(ROOT,'llama8b',llama)

    def test_saved_ollama_qwen_metadata_matches_manifest_layers(self):
        saved=read(ROOT/'deviations/d2/evidence/receipt-gap-qwen7b-preflight.json')
        check_local_identity(ROOT,'qwen7b',saved['show'])
        self.assertEqual(saved['expected_digest'],PINS['qwen7b'][1])

    def test_all_three_preflights_accept_real_metadata_without_generation(self):
        for model in PINS:
            with self.subTest(model=model),tempfile.TemporaryDirectory() as temp:
                root=Path(temp)
                source=ROOT/'deviations/d2/evidence'
                target=root/'deviations/d2/evidence'
                shutil.copytree(source/'models',target/'models')
                shutil.copy2(source/'local-identity.json',target/'local-identity.json')
                expected=identity(root)[model]
                show=dict(template=expected['template'],system=expected['system'],model_info={'fixture.context_length':32768})
                def metadata(path,body=None,timeout=10):
                    if path=='/api/tags': return canonical(dict(models=[dict(name=PINS[model][0],digest=PINS[model][1])])).encode()
                    if path=='/api/show': return canonical(show).encode()
                    if path=='/api/version': return b'{"version":"OFFLINE-FIXTURE"}'
                    raise AssertionError('generation forbidden in preflight test: '+path)
                with patch('bob_collect.http',side_effect=metadata) as network:
                    adapter=LocalAdapter(root,model);adapter.check()
                    self.assertTrue(adapter.ready)
                    self.assertEqual([x.args[0] for x in network.call_args_list],['/api/tags','/api/show','/api/version'])
                    # Changed metadata is rejected before generate's dispatch line.
                    show['system']='wrong'
                    adapter=LocalAdapter(root,model)
                    with self.assertRaisesRegex(Stop,'template/system'):
                        adapter.generate({},'action',0)
                    self.assertNotIn('/api/generate',[x.args[0] for x in network.call_args_list])
                self.assertLessEqual(read(root/'collection/runtime'/f'{model}.json')['context_byte_allowance'],8192)

    def test_empty_qwen_or_modified_template_is_rejected(self):
        for model,item in identity(ROOT).items():
            for key,value in [('system','unexpected'),('template',item['template']+' '),('template','')]:
                show=dict(item);show[key]=value
                with self.assertRaises(Stop): check_local_identity(ROOT,model,show)
        show=dict(identity(ROOT)['qwen7b']);show['system']=''
        with self.assertRaises(Stop):check_local_identity(ROOT,'qwen7b',show)

    def test_frozen_failure_happens_before_generation(self):
        # Execute the retained D1 adapter code with a metadata-only fake. The
        # endpoint list proves the thrown error is before its sole generate.
        namespace={'__name__':'offline_d1_adapter','__file__':str(ROOT/'bob_collect.py')}
        exec((ROOT/'deviations/d2/original/bob_collect.py').read_bytes(),namespace)
        expected=identity(ROOT)['qwen7b']
        paths=[]
        def metadata(path,body=None,timeout=10):
            paths.append(path)
            if path=='/api/tags':return canonical(dict(models=[dict(name=PINS['qwen7b'][0],digest=PINS['qwen7b'][1])])).encode()
            if path=='/api/show':return canonical(dict(template=expected['template'],system=expected['system'],model_info={'qwen2.context_length':32768})).encode()
            if path=='/api/version':return b'{"version":"OFFLINE-FIXTURE"}'
            raise AssertionError('unexpected dispatch')
        namespace['http']=metadata
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(namespace['Stop'],'unexpected model system prompt'):
                namespace['LocalAdapter'](temp,'qwen7b').generate({},'action',0)
        self.assertEqual(paths,['/api/tags','/api/show','/api/version'])


class D2Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bob-d2-')
        self.root=Path(self.temp.name)/'canonical'
        manifest=read(ROOT/'freeze-d2.json')
        for name,digest in dict(manifest['files'],**{n:sha((ROOT/n).read_bytes()) for n in ('freeze.json','freeze-d1.json')}).items():
            candidates=[ROOT/'deviations/d3/original'/name,ROOT/name]
            source=next(p for p in candidates if p.is_file() and sha(p.read_bytes())==digest)
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read_bytes())
        shutil.copytree(ROOT/'deviations/d2/evidence/prior-collection',self.root/'collection')
        self.bind_report()
        freeze_d2(self.root)
        # Synthetic freeze time permits a deterministic past server fixture;
        # real retained parents and D1 push/starts are never changed.
        f=read(self.root/'freeze-d2.json')
        f['frozen_utc']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(minutes=2)).isoformat()
        write(self.root/'freeze-d2.json',f)
        self.clone=Path(self.temp.name)/'separate-clone'; self.clone.mkdir()
        self.commit='b'*40
        event=dict(id=456,activity_type='push',ref='refs/heads/main',after=self.commit,
                   timestamp=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(minutes=1)).isoformat())
        self.event=Path(self.temp.name)/'event.json'
        self.event.write_bytes(b'  '+canonical(event).encode()+b'\n')
        self.overrides={}

    def tearDown(self):self.temp.cleanup()

    def bind_report(self):
        write(self.root/'build/test-report-d2.json',dict(status='PASS',tests=1,python_tests=1,toy_tests=0,
              source_sha256=sha(canonical(inventory(self.root)).encode())))

    def git(self,argv,**kwargs):
        self.assertEqual(argv[:3],['git','-C',str(self.clone.resolve())])
        args=tuple(argv[3:])
        if args in self.overrides:raw=self.overrides[args]
        elif args==('rev-parse','--show-toplevel'):raw=str(self.clone.resolve()).encode()
        elif args==('rev-parse','HEAD'):raw=self.commit.encode()
        elif args==('remote','get-url','origin'):raw=b'https://github.com/Robin84Bran/research.git'
        elif args==('ls-remote','origin','refs/heads/main'):raw=(self.commit+'\trefs/heads/main\n').encode()
        elif args[0]=='show':
            prefix=self.commit+':bridge-or-bus/'
            self.assertTrue(args[1].startswith(prefix));raw=(self.root/args[1][len(prefix):]).read_bytes()
        else:raise AssertionError(args)
        return subprocess.CompletedProcess(argv,0,stdout=raw)

    def attest(self):
        with patch('bob_freeze.subprocess.run',side_effect=self.git):
            return attest(self.root,self.event,self.commit,self.clone,'bridge-or-bus')


class FreezeD2Tests(D2Fixture):
    def test_both_parent_freezes_and_science_stay_exact(self):
        f=verify(self.root)
        self.assertEqual(active_freeze(self.root),'freeze-d2.json')
        self.assertEqual(f['parent_freeze_sha256'],D1_SHA256)
        self.assertEqual(f['disposition_sha256'],sha((self.root/DISPOSITION).read_bytes()))
        self.assertEqual(f['files']['bob_analysis.py'],read(self.root/'freeze.json')['files']['bob_analysis.py'])
        with self.assertRaises(Stop):freeze_d2(self.root)

    def test_parent_or_saved_evidence_tampering_stops(self):
        for name in ['freeze.json','freeze-d1.json','collection/calls/'+CALL+'.json','collection/push.json',
                     'collection/local-time.jsonl','collection/cost.jsonl']:
            with self.subTest(name=name):
                p=self.root/name;raw=p.read_bytes();p.write_bytes(b' '+raw)
                with self.assertRaises(Stop):verify(self.root)
                p.write_bytes(raw)

    def test_scientific_and_unrelated_collector_changes_cannot_refreeze(self):
        (self.root/'freeze-d2.json').unlink()
        for name,transform in [('config/prompts.json',lambda x:x+b' '),
                               ('bob_collect.py',lambda x:x.replace(b'cost<0:',b'cost<=0:'))]:
            p=self.root/name;raw=p.read_bytes();p.write_bytes(transform(raw));self.bind_report()
            with self.assertRaises(Stop):freeze_d2(self.root)
            p.write_bytes(raw)

    def test_d2_requires_exact_passing_tests_and_only_original_start(self):
        (self.root/'freeze-d2.json').unlink()
        write(self.root/'build/test-report-d2.json',dict(status='PASS',tests=1,source_sha256='wrong'))
        with self.assertRaisesRegex(Stop,'passing tests'):freeze_d2(self.root)
        self.bind_report();write(self.root/'collection/starts/new.json',dict(started='2026-11-11T00:00:00Z'))
        with self.assertRaisesRegex(Stop,'retained pre-generation'):freeze_d2(self.root)


class ReconciliationTests(D2Fixture):
    def test_append_only_resume_keeps_score_timer_and_original_evidence(self):
        d=read(self.root/DISPOSITION)
        before={n:(self.root/n).read_bytes() for n in d['evidence_files']}
        self.assertTrue(Ledger(self.root/'collection/cost.jsonl').blocked)
        with patch('bob_collect.http') as network,patch('bob_collect.subprocess.run') as process:
            result=reconcile_d2(self.root)
            self.assertEqual(result['status'],'PASS');network.assert_not_called();process.assert_not_called()
        ledger=Ledger(self.root/'collection/cost.jsonl')
        self.assertFalse(ledger.blocked);self.assertIn(EPISODE,ledger.finished)
        for name,raw in before.items():
            current=(self.root/name).read_bytes()
            self.assertTrue(current.startswith(raw) if name=='collection/cost.jsonl' else current==raw,name)
        saved=read(self.root/'collection/episodes'/f'{EPISODE}.json')
        audit_episode(self.root,saved['episode'],saved,read(self.root/'freeze-d2.json')['original_freeze_sha256'])
        self.assertEqual({k:score(saved['episode'],saved,True)[k] for k in d['scoring']},d['scoring'])
        self.assertEqual(reconcile_ledger(self.root,{EPISODE:saved})['status'],'PASS')
        raw=(self.root/'collection/cost.jsonl').read_bytes()
        reconcile_d2(self.root)
        self.assertEqual((self.root/'collection/cost.jsonl').read_bytes(),raw)
        with self.assertRaises(Stop):ledger.reserve(saved['episode'])

    def test_unknown_stop_paid_hold_or_forged_resume_never_clear(self):
        p=self.root/'collection/cost.jsonl';raw=p.read_bytes()
        for extra in [dict(event='stop',id='unrelated',reason='unknown'),
                      dict(event='d2-resume',id=EPISODE,deviation='D2',freeze_sha256='wrong',disposition_sha256='wrong',time='2026-11-11T00:00:00Z')]:
            p.write_bytes(raw+(canonical(extra)+'\n').encode())
            with self.assertRaises(Stop):reconcile_d2(self.root)
        p.write_bytes(raw)
        value=read(self.root/'collection/calls'/f'{CALL}.json');value['usage']={'micro_usd':1}
        write(self.root/'collection/calls'/f'{CALL}.json',value)
        with self.assertRaises(Stop):reconcile_d2(self.root)

    def test_interrupted_reconciliation_completes_release(self):
        from bob_collect import Ledger as RealLedger
        original=RealLedger.event
        def interrupted(ledger,**event):
            if event['event']=='release':raise RuntimeError('simulated crash before release')
            return original(ledger,**event)
        with patch.object(RealLedger,'event',interrupted):
            with self.assertRaisesRegex(RuntimeError,'simulated crash'):reconcile_d2(self.root)
        self.assertEqual(reconcile_d2(self.root)['status'],'PASS')

    def test_new_stop_after_resume_is_not_cleared(self):
        reconcile_d2(self.root)
        ledger=Ledger(self.root/'collection/cost.jsonl')
        with self.assertRaises(Stop):ledger.event(event='stop',id='later',reason='unknown usage')
        with self.assertRaises(Stop):reconcile_d2(self.root)


class PushD2Tests(D2Fixture):
    def test_new_receipt_preserves_d1_and_requires_all_three_committed_freezes(self):
        prior=(self.root/'collection/push.json').read_bytes()
        push=self.attest()
        self.assertEqual(push['freeze_file'],'freeze-d2.json')
        self.assertEqual(push['parent_freeze_sha256'],D1_SHA256)
        self.assertEqual((self.root/'collection/push.json').read_bytes(),prior)
        self.assertEqual((self.root/'collection/push-d2-event.json').read_bytes(),self.event.read_bytes())
        self.assertEqual(push_gate(self.root,verify(self.root)),push)
        with self.assertRaises(Stop):self.attest()

    def test_wrong_parent_blob_and_new_push_before_freeze_rejected(self):
        for name in ('freeze.json','freeze-d1.json','freeze-d2.json'):
            self.overrides={('show',self.commit+':bridge-or-bus/'+name):b'wrong'}
            with self.assertRaises(Stop):self.attest()
            self.assertFalse((self.root/'collection/push-d2.json').exists())
        self.overrides={}
        e=read(self.event);e['timestamp']='2020-01-01T00:00:00Z';write(self.event,e)
        with self.assertRaisesRegex(Stop,'predates'):self.attest()

    def test_old_push_never_clears_d2_dispatch(self):
        reconcile_d2(self.root)
        with patch('bob_collect.http') as network:
            with self.assertRaises(FileNotFoundError):collect(self.root,('qwen7b',))
            network.assert_not_called()

    def test_skip_retained_failure_and_resume_next_frozen_episode(self):
        self.attest();reconcile_d2(self.root)
        next_ep=read(self.root/'config/order.json')[1]
        with patch('bob_collect.LocalAdapter'),patch('bob_collect.run_episode',side_effect=RuntimeError('offline next episode')) as dispatch,patch('bob_collect.http') as network:
            with self.assertRaisesRegex(RuntimeError,'offline next episode'):collect(self.root,('qwen7b',))
            self.assertEqual(dispatch.call_args.args[1],next_ep)
            self.assertNotEqual(next_ep['id'],EPISODE);network.assert_not_called()

    def test_future_starts_bind_d2_and_old_starts_keep_d1(self):
        push=self.attest();reconcile_d2(self.root)
        ep=read(self.root/'config/order.json')[1]
        run_episode(self.root,ep,FakeTransport(ep),Ledger(self.root/'collection/cost.jsonl'),
                    ActiveTime(self.root/'collection/local-time.jsonl',43200),read(self.root/'freeze-d2.json')['original_freeze_sha256'])
        for p in (self.root/'collection/starts').glob('*.json'):
            v=read(p)
            if v['id']==CALL:self.assertEqual(v['amendment_freeze_sha256'],D1_SHA256)
            else:
                self.assertEqual(v['deviation'],'D2');self.assertEqual(v['amendment_freeze_sha256'],push['freeze_sha256'])
        push_gate(self.root,verify(self.root))
        p=next(p for p in (self.root/'collection/starts').glob('*.json') if p.stem!=CALL)
        v=read(p);v['amendment_freeze_sha256']=D1_SHA256;write(p,v)
        with self.assertRaises(Stop):push_gate(self.root,verify(self.root))
