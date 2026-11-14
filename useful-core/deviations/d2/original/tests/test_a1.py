"""A1 regressions: fake replies and mocked read-only Git only."""
import datetime as dt
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uc_core import ROOT,PINS,canonical,sha,strict_load,transport_load,episode_reservation
from uc_store import Stop,EpisodeFailure,Ledger,ActiveTime,Journal,save,read
from uc_transport import usage,cost_micro
from uc_offline import Fake
from uc_collect import run_episode,collect,check_frontier_contract
from uc_analysis import audit_episode,audit_ledger,audit_contract,score,audit_provenance
from uc_freeze import prepare,freeze,freeze_a1,verify,attest,push_gate


class Mutant(Fake):
    def __init__(self,actor,change=lambda e,p:None,raw_change=lambda raw:None,kind='normal'):
        super().__init__(actor,kind);self.change=change;self.raw_change=raw_change

    def generate(self,request,work):
        raw=super().generate(request,work)
        if raw['stdout']:
            env=strict_load(raw['stdout'].decode());self.change(env,self.current[2])
            raw['stdout']=canonical(env).encode()
        self.raw_change(raw)
        return raw


class FailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)

    def run_one(self,f,ident='case'):
        ep=dict(id=ident,actor=f.actor,seed=0,world='early',framing='fallback')
        ledger=Ledger(self.base/'ledger.jsonl');timer=ActiveTime(self.base/'time.jsonl',100000)
        terminal=run_episode(ep,f,self.base,ledger,timer,'OFFLINE-FAKE',True)
        calls=audit_episode(self.base,ep,terminal,True)
        all_episodes=[];all_calls=[]
        for path in (self.base/'episodes').glob('*/episode.json'):
            saved=read(path);all_episodes.append(saved['episode'])
            all_calls.extend(audit_episode(self.base,saved['episode'],saved,True))
        audit_ledger(self.base,all_episodes,all_calls)
        return ep,terminal,ledger,calls

    def test_each_action_validator_ends_only_episode_in_both_cohorts(self):
        bad=[{},dict(op=[],ref=None,tier=None),dict(op='read',ref=True,tier=None),
             dict(op='read',ref=None,tier=False),dict(op='read',ref='a'*12,tier=None),
             dict(op='check',ref=None,tier=None),dict(op='deliver',ref='b'*12,tier='none'),
             dict(op='wait',ref=None,tier=None,key='illegal')]
        for actor in ('qwen7b','claude'):
            for i,value in enumerate(bad):
                def change(e,p,value=value):
                    if p=='action':e['structured_output' if actor=='claude' else 'response']=value if actor=='claude' else canonical(value)
                with self.subTest(actor=actor,value=value):
                    ep,r,l,c=self.run_one(Mutant(actor,change),actor+str(i))
                    self.assertFalse(r['fatal']);self.assertEqual(r['failure_kind'],'content')
                    self.assertEqual(r['events'],[]);self.assertIsNone(r['report']);self.assertEqual(len(c),1)
                    self.assertEqual(score(ep,r)['U'],0)
        self.assertFalse((self.base/'STOP.json').exists())
        self.assertTrue(all(v==0 for v in l.holds.values()))

    def test_bad_reports_preserve_committed_utility(self):
        for actor in ('qwen7b','claude'):
            for i,value in enumerate(({},dict(delivered=True),dict(delivered='FULL'),dict(delivered='core',key=1))):
                def change(e,p,value=value):
                    if p=='report':e['structured_output' if actor=='claude' else 'response']=value if actor=='claude' else canonical(value)
                ep,r,l,c=self.run_one(Mutant(actor,change),actor+str(i))
                self.assertEqual(r['failure_kind'],'content');self.assertEqual(score(ep,r)['U'],2)
                self.assertIsNone(r['report']);self.assertEqual(r['delivered'],'core')

    def test_first_frontier_content_failure_revalidates_and_continues(self):
        for kind in ('invalid_action','missing_payload','string_payload','length'):
            with tempfile.TemporaryDirectory() as d:
                self.base=Path(d)
                ep,r,l,c=self.run_one(Fake('claude',kind))
                self.assertFalse(r['fatal']);self.assertEqual(l.holds[ep['id']],0)
                self.assertEqual(read(self.base/'claude-contract.json')['status'],'MODEL_FAILURE')
                check_frontier_contract(self.base,'OFFLINE-FAKE',[ep])
                next_ep,nr,nl,nc=self.run_one(Fake('claude'),'next')
                self.assertTrue(nr['technically_complete']);audit_contract(self.base,c+nc)

    def test_local_malformed_payloads_preserve_usage(self):
        for i,text in enumerate(('{','{} {}','```json\n{}\n```','{"op":NaN}',
                                 '{"op":"read","op":"wait","ref":null,"tier":null}')):
            ep,r,l,c=self.run_one(Mutant('qwen7b',lambda e,p:e.update(response=text)),str(i))
            self.assertFalse(r['fatal']);self.assertEqual(r['failure_kind'],'content')
            self.assertEqual(c[0]['output_tokens'],20)

    def test_payload_duplicates_nonfinite_and_metadata_strictness(self):
        for i,payload in enumerate(('{"op":"read","op":"wait","ref":null,"tier":null}',
                                     '{"op":NaN,"ref":null,"tier":null}','{"delivered":1e999}')):
            def raw_change(raw):
                e=strict_load(raw['stdout'].decode());e.pop('structured_output')
                raw['stdout']=(canonical(e)[:-1]+',"structured_output":'+payload+'}').encode()
            ep,r,l,c=self.run_one(Mutant('claude',raw_change=raw_change),str(i))
            self.assertFalse(r['fatal']);self.assertEqual(r['failure_kind'],'content');self.assertGreater(l.spent,0)
            self.assertEqual(c[0]['input_tokens'],215);self.assertEqual(l.holds[ep['id']],0)
        for text in ('{"usage":{"input_tokens":1,"input_tokens":2}}',
                     '{"structured_output":{},"structured_output":{}}','{"usage":NaN}',
                     '{"usage":{"x":1e999}}','{} {}'):
            with self.assertRaises(ValueError):transport_load(text)

    def test_length_keeps_first_identity_usage_and_turn_gates(self):
        for actor in ('qwen7b','claude'):
            mutations=([dict(model='wrong'),dict(eval_count=193),dict(input_truncated=True)] if actor!='claude'
                       else [dict(modelUsage={'wrong':{}}),dict(effort='high'),dict(num_turns=3),dict(context_truncated=True)])
            for i,change in enumerate(mutations):
                with tempfile.TemporaryDirectory() as d:
                    self.base=Path(d)
                    ep,r,l,c=self.run_one(Mutant(actor,lambda e,p:e.update(change),kind='length'))
                    self.assertTrue(r['fatal']);self.assertEqual(r['failure_kind'],'fatal')

    def test_incomplete_local_does_not_hide_integrity_failure(self):
        for i,change in enumerate((dict(model='wrong'),dict(input_truncated=True),dict(eval_count=193),dict(prompt_eval_count=8100))):
            with tempfile.TemporaryDirectory() as d:
                self.base=Path(d)
                ep,r,l,c=self.run_one(Mutant('qwen7b',lambda e,p:e.update(change),kind='not_done'))
                self.assertTrue(r['fatal'])

    def test_exhausted_schema_generation_is_content_with_known_accounting(self):
        def exhausted(e,p):e.update(subtype='error_max_structured_output_retries',is_error=True)
        ep,r,l,c=self.run_one(Mutant('claude',exhausted,lambda raw:raw.update(returncode=1)))
        self.assertEqual(r['failure_kind'],'content');self.assertFalse(r['fatal']);self.assertEqual(l.holds[ep['id']],0)
        with tempfile.TemporaryDirectory() as d:
            self.base=Path(d)
            ep,r,l,c=self.run_one(Mutant('claude',lambda e,p:(exhausted(e,p),e.pop('usage')),lambda raw:raw.update(returncode=1)))
            self.assertTrue(r['fatal']);self.assertEqual(l.holds[ep['id']],episode_reservation(ep))

    def test_paid_transport_uncertainty_is_immediately_fatal(self):
        for changes in (dict(returncode=1),dict(returncode=None,transport_error='timeout')):
            with tempfile.TemporaryDirectory() as d:
                self.base=Path(d)
                ep,r,l,c=self.run_one(Mutant('claude',raw_change=lambda raw:raw.update(changes)))
                self.assertTrue(r['fatal']);self.assertGreater(l.spent,0);self.assertGreater(l.holds[ep['id']],0)

    def test_paid_bad_metadata_keeps_unsettled_hold(self):
        for metadata in ('"usage":{"input_tokens":1,"input_tokens":2}',
                         '"usage":NaN','"usage":{"input_tokens":1e999}'):
            with tempfile.TemporaryDirectory() as d:
                self.base=Path(d)
                def raw_change(raw):raw['stdout']=('{'+metadata+',"structured_output":{}}').encode()
                ep,r,l,c=self.run_one(Mutant('claude',raw_change=raw_change))
                self.assertTrue(r['fatal']);self.assertEqual(l.spent,0);self.assertEqual(l.holds[ep['id']],episode_reservation(ep))

    def test_report_transport_failure_retains_delivery(self):
        def raw_change(raw):
            e=strict_load(raw['stdout'].decode())
            if 'delivered' in strict_load(e['response']):
                e['done']=False;raw['stdout']=canonical(e).encode()
        ep,r,l,c=self.run_one(Mutant('qwen7b',raw_change=raw_change))
        self.assertEqual(r['failure_kind'],'transport');self.assertEqual(score(ep,r)['U'],2)
        self.assertEqual(len(c),4);self.assertIsNone(r['report'])

    def test_unexpected_adapter_and_decoder_errors_are_harness_fatal(self):
        class Broken(Fake):
            def generate(self,request,work):raise ValueError('harness bug')
        ep,r,l,c=self.run_one(Broken('qwen7b'))
        self.assertTrue(r['fatal']);self.assertIn('adapter',r['error'])
        with tempfile.TemporaryDirectory() as d:
            self.base=Path(d)
            ep=dict(id='decoder',actor='qwen7b',seed=0,world='early',framing='fallback')
            with patch('uc_collect.decode',side_effect=KeyError('implementation bug')):
                r=run_episode(ep,Fake('qwen7b'),self.base,Ledger(self.base/'ledger.jsonl'),ActiveTime(self.base/'time.jsonl',1000),'OFFLINE-FAKE',True)
            self.assertTrue(r['fatal']);self.assertEqual(r['failure_kind'],'fatal')

    def test_cache_classes_count_once_and_missing_stays_unknown(self):
        e=dict(usage=dict(input_tokens=2,cache_creation_input_tokens=1600,cache_read_input_tokens=7,output_tokens=199),total_cost_usd=0)
        self.assertEqual(usage(e,'claude'),(1609,199));self.assertEqual(cost_micro(*usage(e,'claude'),e),10416)
        for key in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens'):
            copied=dict(e,usage=dict(e['usage']));del copied['usage'][key]
            self.assertIsNone(usage(copied,'claude')[0])
            with self.assertRaises(Stop):cost_micro(*usage(copied,'claude'),copied)


class CohortTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def collection(self,kinds,actors=None):
        actors=actors or ['qwen7b']*len(kinds)
        episodes=[dict(id='episode-'+str(i),actor=a,seed=i,world='early',framing='fallback') for i,a in enumerate(actors)]
        save(self.root/'config/episodes.json',episodes)
        class Scripted(Fake):
            def request(f,ep,*args):
                f.actor=ep['actor'];f.kind=kinds[int(ep['id'].split('-')[1])]
                return super(Scripted,f).request(ep,*args)
        f=Scripted('qwen7b');f.preflight=lambda actor:dict(offline=True,actor=actor)
        actual=run_episode
        def run(*args,**kwargs):return actual(*args,**kwargs,fake=True)
        self.addCleanup(patch.stopall)
        patch('uc_freeze.push_gate',return_value='OFFLINE-FAKE').start()
        patch('uc_collect.Local',return_value=f).start()
        patch('uc_collect.run_episode',side_effect=run).start()
        return f,episodes

    def test_content_streaks_do_not_pause_and_break_transport_streak(self):
        f,eps=self.collection(['not_done','missing_eval','invalid_action','invalid_action','length','invalid_action','not_done','missing_eval','normal','not_done','missing_eval'])
        collect(self.root,'local')
        self.assertEqual(len(list((self.root/'collection/episodes').glob('*/episode.json'))),len(eps))
        self.assertFalse(list((self.root/'collection').glob('STOP*.json')))

    def test_pause_is_cohort_wide_durable_and_reconstructed_after_crash(self):
        f,eps=self.collection(['not_done','missing_eval','not_done','normal'],['qwen7b','qwen7b','llama8b','llama8b'])
        actual_save=save
        # A real process death cannot write the generic STOP either.
        class Crash(BaseException):pass
        def death(path,value):
            if Path(path).name=='STOP-local.json':raise Crash()
            return actual_save(path,value)
        with patch('uc_collect.save',side_effect=death),self.assertRaises(Crash):collect(self.root,'local')
        self.assertEqual(f.calls,3)
        with self.assertRaises(EpisodeFailure):collect(self.root,'local')
        self.assertEqual(f.calls,3)
        stop=read(self.root/'collection/STOP-local.json')
        self.assertEqual(stop['episodes'],[e['id'] for e in eps[:3]])
        self.assertEqual(stop['kind'],'transport-pause')
        for name,pin in stop['journal_prefixes'].items():
            raw=(self.root/'collection'/name).read_bytes()
            self.assertGreaterEqual(len(raw),pin['bytes']);self.assertEqual(sha(raw[:pin['bytes']]),pin['sha256'])
            Journal(self.root/'collection'/name)
        with self.assertRaises(Stop):collect(self.root,'local')
        self.assertEqual(f.calls,3)

    def test_many_frontier_content_failures_continue_in_frozen_order(self):
        f,eps=self.collection(['invalid_action']*4+['normal'],['claude']*5)
        patch('uc_collect.Claude',return_value=f).start()
        collect(self.root,'claude','FAKE-CLAUDE')
        self.assertTrue(read(self.root/'collection/episodes/episode-4/episode.json')['technically_complete'])
        self.assertFalse(list((self.root/'collection').glob('STOP*.json')))
        calls=[]
        for ep in eps:calls.extend(audit_episode(self.root/'collection',ep,read(self.root/'collection/episodes'/ep['id']/'episode.json'),True))
        audit_contract(self.root/'collection',calls);audit_ledger(self.root/'collection',eps,calls)
        before=f.calls;collect(self.root,'claude','FAKE-CLAUDE');self.assertEqual(f.calls,before)

    def test_prefix_evidence_allows_append_but_rejects_edits_and_truncation(self):
        path=self.root/'ledger.jsonl';l=Ledger(path);l.event(event='reserve',id='one',amount=1000)
        prefix=path.read_bytes();pin=dict(bytes=len(prefix),sha256=sha(prefix))
        l.event(event='release',id='one');self.assertEqual(sha(path.read_bytes()[:pin['bytes']]),pin['sha256'])
        Ledger(path)
        full=path.read_bytes();path.write_bytes(full.replace(b'1000',b'1001'))
        with self.assertRaises(Stop):Ledger(path)
        path.write_bytes(prefix)
        with self.assertRaises(Stop):Ledger(path)


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.root=self.base/'project';self.root.mkdir();self.clone=self.base/'clone';self.clone.mkdir()
        (self.root/'uc_core.py').write_text('# old harness\n');prepare(self.root)
        with patch('uc_freeze.identities',return_value={}):freeze(self.root)
        self.original=(self.root/'freeze.json').read_bytes();self.parent=sha(self.original)
        for name in ('uc_manifest.PARENT_SHA256','uc_freeze.PARENT_SHA256'):
            p=patch(name,self.parent);p.start();self.addCleanup(p.stop)
        save(self.root/'revision-note.json',dict(pre_registration=True))
        target=self.root/'deviations/a1/original/uc_core.py';target.parent.mkdir(parents=True);target.write_bytes((self.root/'uc_core.py').read_bytes())
        (self.root/'uc_core.py').write_text('# A1 harness\n')

    def seal(self):
        with patch('uc_freeze.identities',return_value={}):return freeze_a1(self.root)

    def test_parent_and_scientific_inputs_and_archives_are_immutable(self):
        digest=self.seal();self.assertEqual(verify(self.root),digest);self.assertEqual((self.root/'freeze.json').read_bytes(),self.original)
        with self.assertRaises(FileExistsError):self.seal()
        (self.root/'freeze.json').write_bytes(self.original+b' ')
        with self.assertRaises(Stop):verify(self.root)
        (self.root/'freeze.json').write_bytes(self.original)
        (self.root/'config/prompts.json').write_text('{}')
        with self.assertRaises(Stop):verify(self.root)

    def test_scope_rejection_before_seal_and_starts_block_revision(self):
        protected=self.root/'config/design.json';before=protected.read_bytes();protected.write_text('{}')
        with self.assertRaises(Stop):self.seal()
        self.assertFalse((self.root/'freeze-a1.json').exists());protected.write_bytes(before)
        save(self.root/'collection/episodes/started/1.start.json',dict(start=True))
        with self.assertRaises(Stop):self.seal()

    def test_a1_activity_attestation_binds_both_freezes_and_all_blobs(self):
        digest=self.seal();commit='a'*40
        import time;time.sleep(.002)
        event=dict(activity_type='push',id=1,after=commit,ref='refs/heads/main',timestamp=dt.datetime.now(dt.timezone.utc).isoformat())
        source=self.base/'event.json';source.write_text(canonical(event)+'\n');shown=[]
        def git(cmd,**kwargs):
            self.assertEqual(Path(kwargs['cwd']),self.clone)
            if cmd[1]=='rev-parse':return commit+'\n'
            if cmd[1]=='remote':return 'git@github.com:Robin84Bran/research.git\n'
            if cmd[1]=='ls-remote':return commit+'\trefs/heads/main\n'
            self.assertEqual(cmd[1],'show');name=cmd[2].split(':useful-core/',1)[1];shown.append(name)
            return (self.root/name).read_bytes()
        with patch('uc_freeze.subprocess.check_output',side_effect=git):attest(self.root,source,commit,'useful-core',self.clone)
        self.assertIn('freeze.json',shown);self.assertIn('freeze-a1.json',shown)
        self.assertEqual(push_gate(self.root),digest);self.assertEqual(audit_provenance(self.root,self.root/'collection'),digest)
        self.assertEqual(read(self.root/'collection/push.json')['freeze_file'],'freeze-a1.json')
        self.assertEqual((self.root/'collection/push-event.json').read_bytes(),source.read_bytes());self.assertEqual(list(self.clone.iterdir()),[])
        receipt=self.root/'collection/push.json';value=read(receipt);value['freeze_file']='freeze.json';receipt.write_text(canonical(value))
        with self.assertRaises(Stop):push_gate(self.root)
        with self.assertRaises(ValueError):audit_provenance(self.root,self.root/'collection')

    def test_current_original_freeze_and_every_archived_source_hash(self):
        from uc_manifest import PARENT_SHA256,CHANGED
        # The fixture patches only the expected test parent; inspect the real constant independently.
        self.assertEqual(sha((ROOT/'freeze.json').read_bytes()),'fc497643b1e72f1e928ab8a36dc74d72bc2b82d6a70239c1e18868924a854d51')
        parent=read(ROOT/'freeze.json')
        for name in CHANGED:self.assertEqual(sha((ROOT/'deviations/a1/original'/name).read_bytes()),parent['files'][name])


class PreservationTests(unittest.TestCase):
    def test_exhaustive_audit_matches_every_explicit_current_and_original_site(self):
        from deviations.a1.build_audit import build,tables
        # Rebuild the historical A1 audit from exact retained A1 sources.
        import shutil
        from deviations.a1.audit import MODULES
        with tempfile.TemporaryDirectory() as temp:
            audit_root=Path(temp)
            shutil.copytree(ROOT/'deviations/a1/original',audit_root/'deviations/a1/original')
            for name in MODULES:
                archived=ROOT/'deviations/d1/original'/name
                shutil.copyfile(archived if archived.exists() else ROOT/name,audit_root/name)
            result=build(audit_root)
        stored=read(ROOT/'deviations/a1/audit.json')
        self.assertEqual(result,stored)
        document=(ROOT/'DEVIATIONS.md').read_text()
        self.assertTrue(document.endswith(tables(result)))
        self.assertEqual(result['counts']['fixed']+result['counts']['already_right'],result['counts']['original_sites'])

    def test_scientific_functions_and_frozen_inputs_unchanged(self):
        import ast
        from uc_manifest import CHANGED
        parent=read(ROOT/'freeze.json')
        for name,digest in parent['files'].items():
            if name not in CHANGED:
                from uc_lineage import D1_CHANGED
                source=ROOT/('deviations/d1/original/'+name if name in D1_CHANGED else name)
                self.assertEqual(sha(source.read_bytes()),digest,name)
        allowed={'uc_core.py':{'action','report'},'uc_analysis.py':{'classify_reply','audit_episode','audit_provenance','audit_contract','audit_ledger','analyze'}}
        for name,changed in allowed.items():
            old=ast.parse((ROOT/'deviations/a1/original'/name).read_text());new=ast.parse((ROOT/name).read_text())
            functions={node.name:node for node in new.body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
            for node in old.body:
                if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name not in changed:
                    self.assertEqual(ast.dump(node),ast.dump(functions[node.name]),name+':'+node.name)
