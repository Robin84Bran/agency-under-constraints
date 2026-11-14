"""Offline preparation/freeze and read-only GitHub activity-record attestation."""
import argparse
import datetime as dt
from pathlib import Path
import random
import re
import subprocess
from uc_core import ROOT,ACTORS,canonical,sha,strict_load,render,reserve,maximal_history,episode_reservation,P,SCHEMAS
from uc_store import Stop,read,save,save_bytes,lock,now
from uc_transport import claude_command,identities,clean_env
from uc_manifest import active,validate_a1,CHANGED,PARENT_SHA256

REPOSITORY='Robin84Bran/research'


def transport_spec():
    argv={phase:claude_command('CLAUDE_BINARY',phase,1) for phase in ('action','report')}
    for value in argv.values():value[-1]='SUBHOLD_USD'
    return dict(claude_argv=argv,environment={k:v for k,v in clean_env().items() if k.startswith(('CLAUDE_','MAX_','DISABLE_'))})


def prepare(root=ROOT):
    root=Path(root);episodes=[]
    for actor in ACTORS:
        cells=sorted((s,w,f) for s in range(10 if actor=='claude' else 50) for w in ('calm','early','late') for f in ('fallback','full'))
        random.Random(20261111).shuffle(cells)
        episodes.extend(dict(id=f'{actor}-s{s:02d}-{w}-{f}',actor=actor,seed=s,world=w,framing=f) for s,w,f in cells)
    save(root/'config/episodes.json',episodes)
    save(root/'config/transport.json',transport_spec())
    rows=[]
    for framing in ('full','fallback'):
        ep=dict(seed=0,framing=framing)
        for phase in ('action','report'):
            for depth in (range(6) if phase=='action' else [6]):
                prompt=render(ep,maximal_history(depth),6-depth,phase);hold=reserve(prompt,phase)
                outer=dict(stdin=prompt,argv=claude_command('claude',phase,hold['micro_usd']))
                rows.append(dict(framing=framing,phase=phase,depth=depth,prompt=prompt,prompt_bytes=len(prompt.encode()),
                    prompt_sha256=sha(prompt.encode()),system_bytes=len(P['system'].encode()),schema_bytes=len(canonical(SCHEMAS[phase]).encode()),
                    outer=outer,outer_bytes=len(canonical(outer).encode()),**hold))
    # Mandatory reproduction of the pre-review calculation before final sizing.
    expected={'full':[2688,2816,3008,3136,3264,3456,3328],'fallback':[2752,2880,3008,3200,3328,3456,3392]}
    for f in expected:
        if [r['input_tokens'] for r in rows if r['framing']==f]!=expected[f]:
            raise Stop('draft sizing changed; prospective review needed')
    total=sum(episode_reservation(e) for e in episodes if e['actor']=='claude')
    if total!=10083840 or total+2000000>25000000 or total+2000000>=39000000:
        raise Stop('frontier envelope does not fit frozen design')
    save(root/'config/sizing.json',dict(status='CONDITIONAL_OFFLINE_RESERVATION',frontier_micro_usd=total,
        protected_reserve_micro_usd=2000000,including_reserve_micro_usd=total+2000000,max_calls=420,
        exact_input_tokenization=None,current_cash_billing_usd=None,current_rates_status='UNKNOWN',
        basis='Historical USD4 input / USD20 output per million; empirical bytes+826, 10%/64 input; 576 output holds; aggregate actual output allowed <=512. Not provider bounds.',measurements=rows))
    save(root/'config/design.json',dict(revision='v0.1-r1',order_seed=20261111,bootstrap_seed=20261112,replicates=10000,
        planned_episodes=960,frontier_episodes=60,maximum_calls=6720,frontier_envelope_micro_usd=25000000,
        stop_micro_usd=39000000,programme_ceiling_micro_usd=40000000,runtime_status='UNKNOWN',capacity_status='UNKNOWN',
        build_model_calls=0,collection_delegated=False))
    return total


def inputs(root):
    root=Path(root);files=[]
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if rel.parts[0]=='collection' or any(x.startswith('.') or x=='__pycache__' for x in rel.parts) or rel.as_posix() in ('freeze.json','freeze-a1.json','freeze-d1.json','freeze-d2.json'):
            continue
        if p.is_symlink():
            raise Stop('symlink freeze input')
        if p.is_file():
            files.append(rel.as_posix())
    return sorted(files)


def freeze(root=ROOT):
    root=Path(root)
    if list((root/'collection').glob('episodes/*/*.start.json')):
        raise Stop('freeze must precede all model starts')
    identities(root)
    files={p:sha((root/p).read_bytes()) for p in inputs(root)}
    save(root/'freeze.json',dict(study='The Useful Core',revision='v0.1-r1',created_at=now(),files=files,
        content_sha256=sha(canonical(files).encode()),planned_episodes=960,model_calls_made_by_builder=0,
        frontier_reservation_micro_usd=read(root/'config/sizing.json')['frontier_micro_usd'],
        authority='Claude reviewer delegation: folder-local build/test/freeze only; no model calls/push/collection',
        unresolved=['later push/attestation','live runtime/capacity','first frozen Claude schema contract','current cash billing/rates']))
    return verify(root)


def verify(root=ROOT):
    root=Path(root)
    if (root/'freeze.json').is_symlink():
        raise Stop('symlink freeze')
    freeze_name,f=active(root)
    if not f.get('files') or f.get('content_sha256')!=sha(canonical(f['files']).encode()):
        raise Stop('empty or inconsistent freeze')
    if set(inputs(root))!=set(f['files']):
        raise Stop('freeze inventory changed')
    for name,digest in f['files'].items():
        p=root/name
        if not p.resolve().is_relative_to(root.resolve()) or p.is_symlink() or sha(p.read_bytes())!=digest:
            raise Stop('frozen input changed: '+name)
    total=read(root/'config/sizing.json')['frontier_micro_usd']
    if total!=f.get('frontier_reservation_micro_usd') or total+2000000>25000000 or f.get('planned_episodes')!=960 or f.get('model_calls_made_by_builder')!=0:
        raise Stop('freeze plan/budget mismatch')
    return sha((root/freeze_name).read_bytes())


def freeze_a1(root=ROOT):
    root=Path(root)
    if (root/'collection/push.json').exists() or list((root/'collection').glob('episodes/*/*.start.json')):
        raise Stop('A1 is pre-push and pre-inference only')
    if sha((root/'freeze.json').read_bytes())!=PARENT_SHA256:
        raise Stop('A1 original freeze changed')
    identities(root)
    files={p:sha((root/p).read_bytes()) for p in inputs(root)}
    parent=read(root/'freeze.json')
    candidate=dict(parent,revision='v0.1-r1-a1',created_at=now(),files=files,
        parent_sha256=PARENT_SHA256,changed_inputs=sorted(CHANGED),
        content_sha256=sha(canonical(files).encode()),
        authority='Claude delegating reviewer: A1 folder-only pre-registration revision; no model calls, pushes or Git changes')
    validate_a1(root,candidate)
    save(root/'freeze-a1.json',candidate)
    return verify(root)


def freeze_d1(root=ROOT):
    """Reviewer-delegated post-push harness amendment; scientific inputs stay fixed."""
    from uc_lineage import A1_SHA256,D1_CHANGED,validate_d1,check_baseline,parent_push
    root=Path(root);base=root/'collection'
    if list(base.glob('episodes/claude*/*.start.json')) or list(base.glob('episodes/*/dispatches/*/start.json')):
        raise Stop('D1 must precede first Claude dispatch')
    check_baseline(root,base);parent_push(root,base)
    schedule=read(root/'config/episodes.json')
    if any(not (base/'episodes'/e['id']/'episode.json').exists() for e in schedule if e['actor']!='claude'):
        raise Stop('local cohort incomplete')
    files={p:sha((root/p).read_bytes()) for p in inputs(root)}
    parent=read(root/'freeze-a1.json')
    candidate=dict(parent,revision='v0.1-r1-a1-d1',created_at=now(),files=files,
        parents={'freeze.json':PARENT_SHA256,'freeze-a1.json':A1_SHA256},changed_inputs=sorted(D1_CHANGED),
        baseline_sha256=files['deviations/d1/collection-baseline.json'],content_sha256=sha(canonical(files).encode()),
        authority='Claude delegating reviewer: post-push D1, local complete, before Claude; harness only; no model calls, pushes or Git')
    validate_d1(root,candidate);save(root/'freeze-d1.json',candidate)
    return verify(root)


def parsed_time(value):
    try:
        t=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError,TypeError,AttributeError):
        raise Stop('invalid server timestamp') from None
    if t.tzinfo is None:
        raise Stop('timezone missing')
    return t


def push_record(record,commit):
    if type(record) is not dict or type(commit) is not str or re.fullmatch('[a-f0-9]{40}',commit) is None:
        raise Stop('invalid push record/commit')
    if record.get('activity_type')!='push' or record.get('after')!=commit:
        raise Stop('expected GitHub activity push for this commit')
    ref,timestamp=record.get('ref'),record.get('timestamp')
    if not isinstance(ref,str) or re.fullmatch(r'refs/heads/[^\s:]+',ref) is None or record.get('id') is None or type(record.get('id')) not in (str,int):
        raise Stop('missing/invalid server id or branch ref')
    if parsed_time(timestamp)>=dt.datetime.now(dt.timezone.utc):
        raise Stop('future server timestamp')
    return ref,timestamp


def attest(root,event_file,commit,repo_path,clone_root):
    root=Path(root);freeze_hash=verify(root);clone=Path(clone_root)
    if not repo_path or repo_path.startswith('/') or '..' in Path(repo_path).parts or ':' in repo_path:
        raise Stop('unsafe repo path')
    if root.resolve().is_relative_to(clone.resolve()) or clone.resolve().is_relative_to(root.resolve()):
        raise Stop('use a separate research clone')
    source=Path(event_file).read_bytes();event=strict_load(source.decode());ref,timestamp=push_record(event,commit)
    freeze_name,f=active(root)
    if parsed_time(timestamp)<=parsed_time(f['created_at']):
        raise Stop('push must follow freeze')
    def git(*args,text=False):
        return subprocess.check_output(['git',*args],cwd=clone,text=text,timeout=30)
    if git('rev-parse','HEAD',text=True).strip()!=commit:
        raise Stop('clone HEAD differs')
    origin=git('remote','get-url','origin',text=True).strip()
    if origin not in ('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git','git@github.com:'+REPOSITORY+'.git','ssh://git@github.com/'+REPOSITORY+'.git'):
        raise Stop('noncanonical origin')
    # Bind every committed input, not just a manifest describing unrelated blobs.
    manifests={freeze_name:freeze_hash}
    if freeze_name!='freeze.json':manifests['freeze.json']=PARENT_SHA256
    for name,digest in {**f['files'],**manifests}.items():
        if sha(git('show',commit+':'+repo_path+'/'+name))!=digest:
            raise Stop('committed bytes differ: '+name)
    if not any(line.split()==[commit,ref] for line in git('ls-remote','origin',ref,text=True).splitlines()):
        raise Stop('remote ref differs from activity')
    with lock(root/'collection'):
        if list((root/'collection').glob('episodes/*/*.start.json')):
            raise Stop('attestation must precede starts')
        save_bytes(root/'collection/push-event.json',source)
        save(root/'collection/push.json',dict(repo=REPOSITORY,commit=commit,remote_ref=ref,pushed_at=timestamp,
            server_event_id=event['id'],event_sha256=sha(source),source_api='/repos/'+REPOSITORY+'/activity',
            freeze_sha256=freeze_hash,manifest_sha256=f['content_sha256'],repo_path=repo_path,freeze_file=freeze_name))
    return freeze_hash


def push_gate(root=ROOT):
    root=Path(root);digest=verify(root)
    if (root/'freeze-d2.json').exists():
        from uc_d2 import provenance
        return provenance(root,root/'collection')
    if (root/'freeze-d1.json').exists():
        from uc_lineage import d1_provenance
        return d1_provenance(root,root/'collection')
    a=read(root/'collection/push.json')
    source=(root/'collection/push-event.json').read_bytes();e=strict_load(source.decode());ref,timestamp=push_record(e,a['commit'])
    freeze_name,f=active(root)
    if (a.get('repo')!=REPOSITORY or a.get('source_api')!='/repos/'+REPOSITORY+'/activity' or a.get('freeze_file')!=freeze_name or
        a.get('freeze_sha256')!=digest or a.get('event_sha256')!=sha(source) or a.get('pushed_at')!=timestamp or
        a.get('remote_ref')!=ref or a.get('server_event_id')!=e['id'] or a.get('manifest_sha256')!=f['content_sha256']):
        raise Stop('push attestation binding mismatch')
    pushed=parsed_time(timestamp)
    if pushed<=parsed_time(f['created_at']):
        raise Stop('push predates freeze')
    for p in (root/'collection').glob('episodes/*/*.start.json'):
        s=read(p)
        if s.get('freeze_sha256')!=digest or parsed_time(s['started_at'])<=pushed:
            raise Stop('push must bind and precede every start')
    return digest


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','freeze','freeze-a1','freeze-d1','verify','attest','attest-d1'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--event',type=Path);p.add_argument('--commit');p.add_argument('--repo-path',default='useful-core');p.add_argument('--clone-root',type=Path)
    a=p.parse_args()
    if a.command=='attest-d1':
        from uc_lineage import attest_d1
        print(attest_d1(a.root))
    elif a.command=='attest':
        if not a.event or not a.commit or not a.clone_root:
            p.error('attest requires --event --commit --clone-root')
        print(attest(a.root,a.event,a.commit,a.repo_path,a.clone_root))
    else:
        print({'prepare':prepare,'freeze':freeze,'freeze-a1':freeze_a1,'freeze-d1':freeze_d1,'verify':verify}[a.command](a.root))

if __name__=='__main__':
    main()
