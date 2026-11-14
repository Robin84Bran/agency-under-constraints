"""Offline preparation/freeze and explicit GitHub activity attestation."""
import datetime as dt
import io
from pathlib import Path
import re
import subprocess
import tarfile
from ps_core import ROOT, ARMS, WORLDS, P, SCHEMAS, canonical, sha, fixture, schedule, render, maximal_payload, reservation, episode_reservation
from ps_io import Stop, read, save, save_bytes, lock

REPOSITORY='Robin84Bran/research'
ENVELOPE_FILES={'ps_transport.py','ps_collect.py','ps_io.py','ps_analysis.py','ps_freeze.py','ps.py','RUN.md','PROJECT_STATE.md','tests/test_transport.py','tests/test_usage_limit.py','tests/test_a1_failures.py'}
DEVIATION_FILES={'ps_collect.py','ps_analysis.py','ps_io.py','ps_transport.py','ps_freeze.py','ps.py','RUN.md','PROJECT_STATE.md','tests/test_v02.py'}
def active_manifest(root):
    root=Path(root)
    return next((root/n for n in ('freeze-claude-envelope.json','freeze-usage-limit.json','freeze.json') if (root/n).exists()),root/'freeze.json')


def prepare(root):
    root=Path(root);episodes=schedule()
    save(root/'config/episodes.json',episodes)
    save(root/'config/worlds.json',[fixture(s,w) for s in range(100) for w in WORLDS])
    measurements=[]
    from ps_transport import claude_command, clean_env, identity, CLAUDE_BIN
    identity(root)
    for arm in ARMS:
        for phase in ('write','act'):
            p=render(maximal_payload(arm,phase));bound=reservation(arm,phase)
            outer={'stdin':p,'argv':claude_command(Path(CLAUDE_BIN).resolve(),phase,bound['micro_usd']),
                   'environment_controls':{k:v for k,v in clean_env().items() if k.startswith(('CLAUDE_','MAX_','DISABLE_'))}}
            measurements.append({'arm':arm,'phase':phase,'maximal_prompt':p,'prompt_sha256':sha(p.encode()),
                'schema_bytes':len(canonical(SCHEMAS[phase]).encode()),'system_bytes':len(P['system'].encode()),
                'outer_request':outer,'outer_request_bytes':len(canonical(outer).encode()),**bound})
    total=sum(episode_reservation(ep) for ep in episodes if ep['actor']=='claude')
    if total+1000000>25000000 or total+1000000>=39000000: raise Stop('frontier plan cannot fit')
    save(root/'config/sizing.json',{'frontier_micro_usd':total,'protected_reserve_micro_usd':1000000,
         'including_reserve_micro_usd':total+1000000,'frontier_episodes':60,'maximum_calls':480,
         'basis':'Explicit API-equivalent planning/accounting basis USD4/million all input categories, USD20/million output. Higher nonnegative CLI total_cost_usd controls settlement. Not a cash-billing assertion.',
         'rates_status':'scenario, not verified current provider rates','actual_cash_payment_usd':None,
         'historical_hidden_allowance':826,'hidden_allowance_source':'Receipt Gap / Signal or Silence historical allowance; copied CLI source contract confirms same binary. Empirical allowance, not hard bound.',
         'output_allowance':576,'requested_output_setting':512,'measurements':measurements})
    save(root/'config/design.json',{'revision':'v0.2','bootstrap_seed':20261112,'bootstrap_replicates':10000,'order_seed':20261111,
         'generation_seed':'1000*seed+visit, visits 1..8','model_order':['qwen7b','llama8b','qwen1b','claude'],
         'local_active_seconds':86400,'frontier_active_seconds':10800,'local_timeout':180,'frontier_timeout':420,
         'frontier_envelope_micro_usd':25000000,'project_stop_micro_usd':39000000,'outer_line_micro_usd':40000000,
         'frontier_model':'claude-opus-5-5','effort':'medium','reported_effort':'UNKNOWN until returned',
         'live_identity_context_status':'UNKNOWN','live_identity_context_reason':'No runtime probes or inference in build stage',
         'frontier_first_call_rule':'first frozen scored call verifies strict structured_output, 1/2 turns, identity and complete usage; else durable stop',
         'literal_fidelity_convention':'Exactly four unique literal control=direction pairs; other encodings UNKNOWN',
         'model_calls_in_build':0})
    from ps_baselines import baseline, BASELINES
    save(root/'config/baselines.json',[baseline(s,w,k) for s in range(100) for w in WORLDS for k in BASELINES])
    return total


def inputs(root):
    root=Path(root);names=[]
    for p in root.rglob('*'):
        rel=p.relative_to(root)
        if any(x.startswith('.') or x in ('__pycache__','collection') for x in rel.parts) or rel.as_posix() in ('freeze.json','freeze-a1.json','freeze-usage-limit.json','freeze-claude-envelope.json'): continue
        if p.is_symlink(): raise Stop('symlink freeze input')
        if p.is_file(): names.append(rel.as_posix())
    return sorted(names)


def freeze(root):
    root=Path(root)
    if (root/'freeze.json').exists(): raise Stop('freeze exists; never overwrite')
    files={n:sha((root/n).read_bytes()) for n in inputs(root)}
    value={'study':'The Portable Self','revision':'v0.2','kind':'v0.2 pre-inference offline freeze; v0.1 exposure disclosed',
           'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files,'episodes':1080,'maximum_calls':8640,
           'model_calls_made_by_builder':0,'delegating_reviewer':'Claude','review':'Builder AGREED; Claude follow-up pending',
           'frontier_reservation_micro_usd':read(root/'config/sizing.json')['frontier_micro_usd'],
           'live_contract_status':'UNKNOWN; first frozen frontier call verifies; fail closed',
           'push_status':'UNKNOWN; no push/attestation during build','runtime_status':'UNKNOWN; no runtime probe during build'}
    save(root/'freeze.json',value);return verify(root)


def verify(root):
    root=Path(root)
    manifest=active_manifest(root)
    if manifest.is_symlink(): raise Stop('symlink freeze')
    f=read(manifest)
    envelope=manifest.name=='freeze-claude-envelope.json'
    def predecessor_bytes(name):
        source=root/'revisions/claude-envelope/parent-files'/name if envelope and name in f['changed_parent_files'] else root/name
        return source.read_bytes()
    if envelope:
        for name,digest in f['parents'].items():
            if sha((root/name).read_bytes())!=digest: raise Stop('envelope deviation parent changed: '+name)
        previous=read(root/'freeze-usage-limit.json')
        changed=set(f['changed_parent_files'])
        if not changed<=ENVELOPE_FILES: raise Stop('out-of-scope envelope deviation')
        actual={n for n,h in previous['files'].items() if not (root/n).is_file() or sha((root/n).read_bytes())!=h}
        if actual!=changed: raise Stop('undeclared envelope deviation')
        for n,h in previous['files'].items():
            if sha(predecessor_bytes(n))!=h: raise Stop('preserved predecessor changed: '+n)
    legacy=read(root/'freeze-usage-limit.json') if envelope else f
    if manifest.name=='freeze-usage-limit.json' or envelope:
        for name,digest in legacy['parents'].items():
            if sha((root/name).read_bytes())!=digest: raise Stop('deviation parent changed: '+name)
        parent=read(root/'freeze.json')
        allowed=set(legacy['changed_parent_files'])
        if not allowed<=DEVIATION_FILES: raise Stop('out-of-scope frozen input deviation')
        if allowed!={n for n,h in parent['files'].items() if sha(predecessor_bytes(n))!=h}: raise Stop('undeclared parent deviation')
        for n in allowed:
            if sha((root/'revisions/usage-limit/parent-files'/n).read_bytes())!=parent['files'][n]: raise Stop('original frozen bytes missing: '+n)
    if not f.get('files') or set(inputs(root))!=set(f['files']): raise Stop('freeze inventory changed')
    for n,h in f['files'].items():
        p=root/n
        if Path(n).is_absolute() or '..' in Path(n).parts or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h: raise Stop('frozen file changed: '+n)
    total=sum(episode_reservation(ep) for ep in read(root/'config/episodes.json') if ep['actor']=='claude')
    if total!=f['frontier_reservation_micro_usd'] or total!=read(root/'config/sizing.json')['frontier_micro_usd'] or total+1000000>25000000: raise Stop('reservation freeze mismatch')
    if read(root/'config/episodes.json')!=schedule() or read(root/'config/worlds.json')!=[fixture(s,w) for s in range(100) for w in WORLDS]: raise Stop('generator/schedule drift')
    if (root/'evidence/v01-baseline.json').exists():
        for name,digest in read(root/'evidence/v01-baseline.json')['unchanged'].items():
            if name in legacy.get('changed_parent_files',[]):
                if name not in ('ps_collect.py','ps_analysis.py','ps_io.py'): raise Stop('scientific baseline deviation not allowed')
                source=root/'revisions/usage-limit/parent-files'/name
            else: source=root/name
            if sha(source.read_bytes())!=digest: raise Stop('v0.1 scientific baseline changed: '+name)
    from ps_transport import identity
    identity(root)
    return sha(manifest.read_bytes())


def freeze_usage_limit(root):
    """Create-once operational deviation; never replace the scientific parent freeze."""
    root=Path(root)
    if (root/'freeze-usage-limit.json').exists(): raise Stop('usage-limit freeze exists')
    parent=read(root/'freeze.json')
    changed=[n for n,h in parent['files'].items() if sha((root/n).read_bytes())!=h]
    if not set(changed)<=DEVIATION_FILES: raise Stop('out-of-scope frozen input change')
    for n in changed:
        if sha((root/'revisions/usage-limit/parent-files'/n).read_bytes())!=parent['files'][n]: raise Stop('missing preserved original: '+n)
    parents={n:sha((root/n).read_bytes()) for n in ('freeze.json','collection/push.json','collection/push-event.json','collection/push-activity.json')}
    value={**{k:v for k,v in parent.items() if k not in ('files','created_at','kind','review')},
        'kind':'post-push harness-only usage-limit deviation; no new scientific cohort',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'parents':parents,'changed_parent_files':sorted(changed),
        'review':'Delegated by Claude reviewer; programme-wide definite non-start disposition',
        'files':{n:sha((root/n).read_bytes()) for n in inputs(root)}}
    save(root/'freeze-usage-limit.json',value)
    return verify(root)


def freeze_claude_envelope(root):
    """Create-once correction binding both predecessor freezes and push generations."""
    root=Path(root);destination=root/'freeze-claude-envelope.json'
    if destination.exists(): raise Stop('envelope freeze exists')
    parent=read(root/'freeze-usage-limit.json')
    changed=sorted(n for n,h in parent['files'].items() if sha((root/n).read_bytes())!=h)
    if not set(changed)<=ENVELOPE_FILES: raise Stop('out-of-scope envelope deviation')
    for n in changed:
        if sha((root/'revisions/claude-envelope/parent-files'/n).read_bytes())!=parent['files'][n]: raise Stop('missing envelope predecessor: '+n)
    names=['freeze.json','freeze-usage-limit.json']+[f'collection/push{part}{suffix}.json' for suffix in ('','-usage-limit') for part in ('','-event','-activity')]
    value={**{k:v for k,v in parent.items() if k not in ('files','created_at','kind','review','parents','changed_parent_files')},
        'kind':'post-stop Claude envelope harness correction; no rerun or scientific change',
        'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'parents':{n:sha((root/n).read_bytes()) for n in names},
        'changed_parent_files':changed,'review':'Delegated by Claude reviewer; saved-byte re-disposition and STOP clearance',
        'files':{n:sha((root/n).read_bytes()) for n in inputs(root)}}
    save(destination,value)
    return verify(root)


def receipt_names(root):
    suffix={'freeze.json':'','freeze-usage-limit.json':'-usage-limit','freeze-claude-envelope.json':'-claude-envelope'}[active_manifest(root).name]
    return tuple('push'+part+suffix+'.json' for part in ('','-event','-activity'))


def parsed_time(text):
    try: value=dt.datetime.fromisoformat(text.replace('Z','+00:00'))
    except (TypeError,AttributeError,ValueError): raise Stop('invalid timestamp') from None
    if value.tzinfo is None: raise Stop('timestamp requires timezone')
    return value


def push_record(event,commit):
    if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit) or not isinstance(event,dict): raise Stop('invalid push record/commit')
    if event.get('activity_type')!='push' or event.get('after')!=commit or event.get('id') is None: raise Stop('activity is not matching push')
    ref=event.get('ref')
    if not isinstance(ref,str) or not ref.startswith('refs/heads/') or len(ref)<=len('refs/heads/'): raise Stop('invalid push branch ref')
    timestamp=event.get('timestamp');t=parsed_time(timestamp)
    if t>=dt.datetime.now(dt.timezone.utc): raise Stop('server push timestamp is future')
    return ref,timestamp


def activity_records(pages):
    if not isinstance(pages,list): raise Stop('activity API response must be list')
    records=[e for page in pages for e in page] if pages and all(isinstance(p,list) for p in pages) else pages
    if not all(isinstance(e,dict) for e in records): raise Stop('invalid activity API pages')
    return records


def attest(root,clone_root,repo_path,commit):
    """Only this explicit command contacts GitHub; never pushes or edits clone."""
    root=Path(root).resolve();clone=Path(clone_root).resolve();freeze_hash=verify(root)
    if clone==root or clone==Path('<WORKSPACE>') or clone.is_relative_to(Path('<WORKSPACE>')): raise Stop('attestation requires separate research clone')
    if not repo_path or Path(repo_path).is_absolute() or '..' in Path(repo_path).parts or ':' in repo_path: raise Stop('invalid repo path')
    def git(*args): return subprocess.check_output(['git',*args],cwd=clone)
    origin=git('remote','get-url','origin').decode().strip()
    allowed=('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git','git@github.com:'+REPOSITORY+'.git','ssh://git@github.com/'+REPOSITORY+'.git')
    if origin not in allowed or git('rev-parse','HEAD').decode().strip()!=commit: raise Stop('clone origin/HEAD mismatch')
    # Compare every committed frozen byte, not just a claimed freeze manifest.
    archive=git('archive',commit,'--',repo_path)
    ancestors=read(active_manifest(root))['parents'] if active_manifest(root).name=='freeze-claude-envelope.json' else {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for n,h in {**read(active_manifest(root))['files'],**ancestors,active_manifest(root).name:freeze_hash,
                    'freeze.json':sha((root/'freeze.json').read_bytes())}.items():
            member=tar.getmember(repo_path+'/'+n)
            if not member.isfile() or sha(tar.extractfile(member).read())!=h: raise Stop('commit has different frozen bytes: '+n)
    api='/repos/'+REPOSITORY+'/activity'
    raw=subprocess.check_output(['gh','api','--method','GET',api,'--paginate','--slurp'],cwd=clone)
    from ps_core import strict_load
    records=activity_records(strict_load(raw.decode()))
    candidates=[e for e in records if e.get('activity_type')=='push' and e.get('after')==commit]
    if not candidates: raise Stop('no matching genuine server activity push; no model dispatch')
    event=max(candidates,key=lambda e:parsed_time(e['timestamp']));ref,timestamp=push_record(event,commit)
    if parsed_time(timestamp)<parsed_time(read(active_manifest(root))['created_at']): raise Stop('push precedes freeze')
    remote=git('ls-remote','origin',ref).decode()
    if not any(line.split()==[commit,ref] for line in remote.splitlines()): raise Stop('remote ref differs from pushed commit')
    receipt,event_name,activity_name=receipt_names(root)
    with lock(root/'collection'):
        save_bytes(root/'collection'/activity_name,raw)
        save(root/'collection'/event_name,event)
        save(root/'collection'/receipt,{'repo':REPOSITORY,'source_api':api,'commit':commit,'remote_ref':ref,'pushed_at':timestamp,
             'server_event_id':event['id'],'freeze_sha256':freeze_hash,'repo_path':repo_path,
             'event_sha256':sha((root/'collection'/event_name).read_bytes()),'activity_sha256':sha(raw)})
    return freeze_hash


def checked_receipt(root,names,freeze_hash,created_at):
    receipt,event_name,activity_name=names
    a=read(root/'collection'/receipt);event=read(root/'collection'/event_name)
    if a['repo']!=REPOSITORY or a['source_api']!='/repos/'+REPOSITORY+'/activity' or a['freeze_sha256']!=freeze_hash: raise Stop('push attestation mismatch')
    raw=(root/'collection'/activity_name).read_bytes()
    from ps_core import strict_load
    if sha(raw)!=a['activity_sha256'] or event not in activity_records(strict_load(raw.decode())) or sha((root/'collection'/event_name).read_bytes())!=a['event_sha256']: raise Stop('retained server evidence changed')
    ref,timestamp=push_record(event,a['commit'])
    if ref!=a['remote_ref'] or timestamp!=a['pushed_at'] or event['id']!=a['server_event_id'] or parsed_time(timestamp)<parsed_time(created_at): raise Stop('push metadata mismatch')
    return timestamp


def push_gate(root):
    root=Path(root);h=verify(root)
    timestamp=checked_receipt(root,receipt_names(root),h,read(active_manifest(root))['created_at'])
    lineage={h:timestamp}
    manifests={h:active_manifest(root).name}
    if active_manifest(root).name in ('freeze-usage-limit.json','freeze-claude-envelope.json'):
        for name,suffix in [('freeze.json',''),('freeze-usage-limit.json','-usage-limit')]:
            if name==active_manifest(root).name: continue
            old=sha((root/name).read_bytes())
            lineage[old]=checked_receipt(root,tuple('push'+part+suffix+'.json' for part in ('','-event','-activity')),old,read(root/name)['created_at'])
            manifests[old]=name
    for path in (root/'collection/episodes').glob('*/*.start.json'):
        s=read(path);frozen=s['freeze_sha256']
        if frozen not in lineage or parsed_time(s['started_at'])<=parsed_time(lineage[frozen]): raise Stop('push must precede every saved start')
        generation=('freeze.json','freeze-usage-limit.json','freeze-claude-envelope.json').index(manifests[frozen])
        successors=[read(root/n)['created_at'] for n in manifests.values()
                    if ('freeze.json','freeze-usage-limit.json','freeze-claude-envelope.json').index(n)>generation]
        if successors and parsed_time(s['started_at'])>=min(map(parsed_time,successors)): raise Stop('new start bound to obsolete freeze')
    return h
