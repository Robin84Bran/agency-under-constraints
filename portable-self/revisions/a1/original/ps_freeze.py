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
    save(root/'config/design.json',{'revision':'v0.1-r1','bootstrap_seed':20261112,'bootstrap_replicates':10000,'order_seed':20261111,
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
        if any(x.startswith('.') or x in ('__pycache__','collection') for x in rel.parts) or rel.as_posix()=='freeze.json': continue
        if p.is_symlink(): raise Stop('symlink freeze input')
        if p.is_file(): names.append(rel.as_posix())
    return sorted(names)


def freeze(root):
    root=Path(root)
    if (root/'freeze.json').exists(): raise Stop('freeze exists; never overwrite')
    files={n:sha((root/n).read_bytes()) for n in inputs(root)}
    value={'study':'The Portable Self','revision':'v0.1-r1','kind':'pre-inference offline freeze',
           'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files,'episodes':1080,'maximum_calls':8640,
           'model_calls_made_by_builder':0,'delegating_reviewer':'Claude','review':'AGREED with notes applied',
           'frontier_reservation_micro_usd':read(root/'config/sizing.json')['frontier_micro_usd'],
           'live_contract_status':'UNKNOWN; first frozen frontier call verifies; fail closed',
           'push_status':'UNKNOWN; no push/attestation during build','runtime_status':'UNKNOWN; no runtime probe during build'}
    save(root/'freeze.json',value);return verify(root)


def verify(root):
    root=Path(root)
    if (root/'freeze.json').is_symlink(): raise Stop('symlink freeze')
    f=read(root/'freeze.json')
    if not f.get('files') or set(inputs(root))!=set(f['files']): raise Stop('freeze inventory changed')
    for n,h in f['files'].items():
        p=root/n
        if Path(n).is_absolute() or '..' in Path(n).parts or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h: raise Stop('frozen file changed: '+n)
    total=sum(episode_reservation(ep) for ep in read(root/'config/episodes.json') if ep['actor']=='claude')
    if total!=f['frontier_reservation_micro_usd'] or total!=read(root/'config/sizing.json')['frontier_micro_usd'] or total+1000000>25000000: raise Stop('reservation freeze mismatch')
    if read(root/'config/episodes.json')!=schedule() or read(root/'config/worlds.json')!=[fixture(s,w) for s in range(100) for w in WORLDS]: raise Stop('generator/schedule drift')
    from ps_transport import identity
    identity(root)
    return sha((root/'freeze.json').read_bytes())


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
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for n,h in {**read(root/'freeze.json')['files'],'freeze.json':freeze_hash}.items():
            member=tar.getmember(repo_path+'/'+n)
            if not member.isfile() or sha(tar.extractfile(member).read())!=h: raise Stop('commit has different frozen bytes: '+n)
    api='/repos/'+REPOSITORY+'/activity'
    raw=subprocess.check_output(['gh','api','--method','GET',api,'--paginate','--slurp'],cwd=clone)
    from ps_core import strict_load
    records=activity_records(strict_load(raw.decode()))
    candidates=[e for e in records if e.get('activity_type')=='push' and e.get('after')==commit]
    if not candidates: raise Stop('no matching genuine server activity push; no model dispatch')
    event=max(candidates,key=lambda e:parsed_time(e['timestamp']));ref,timestamp=push_record(event,commit)
    if parsed_time(timestamp)<parsed_time(read(root/'freeze.json')['created_at']): raise Stop('push precedes freeze')
    remote=git('ls-remote','origin',ref).decode()
    if not any(line.split()==[commit,ref] for line in remote.splitlines()): raise Stop('remote ref differs from pushed commit')
    with lock(root/'collection'):
        save_bytes(root/'collection/push-activity.json',raw)
        save(root/'collection/push-event.json',event)
        save(root/'collection/push.json',{'repo':REPOSITORY,'source_api':api,'commit':commit,'remote_ref':ref,'pushed_at':timestamp,
             'server_event_id':event['id'],'freeze_sha256':freeze_hash,'repo_path':repo_path,
             'event_sha256':sha((root/'collection/push-event.json').read_bytes()),'activity_sha256':sha(raw)})
    return freeze_hash


def push_gate(root):
    root=Path(root);h=verify(root);a=read(root/'collection/push.json');event=read(root/'collection/push-event.json')
    if a['repo']!=REPOSITORY or a['source_api']!='/repos/'+REPOSITORY+'/activity' or a['freeze_sha256']!=h: raise Stop('push attestation mismatch')
    raw=(root/'collection/push-activity.json').read_bytes()
    from ps_core import strict_load
    if sha(raw)!=a['activity_sha256'] or event not in activity_records(strict_load(raw.decode())) or sha((root/'collection/push-event.json').read_bytes())!=a['event_sha256']: raise Stop('retained server evidence changed')
    ref,timestamp=push_record(event,a['commit'])
    if ref!=a['remote_ref'] or timestamp!=a['pushed_at'] or event['id']!=a['server_event_id'] or parsed_time(timestamp)<parsed_time(read(root/'freeze.json')['created_at']): raise Stop('push metadata mismatch')
    for path in (root/'collection/episodes').glob('*/*.start.json'):
        s=read(path)
        if s['freeze_sha256']!=h or parsed_time(s['started_at'])<=parsed_time(timestamp): raise Stop('push must precede every saved start')
    return h
