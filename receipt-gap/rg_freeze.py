"""Offline preparation, immutable freeze and verified server push attestation."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import random
import re
import subprocess

from rg_core import ROOT, ACTORS, P, SCHEMAS, canonical, episode_reservation, maximal_history, render, reserve, sha, strict_load
from rg_collect import Stop, read, save, syncdir


ORIGINAL_FREEZE_SHA256 = '289eaa2a465b82e889ee5e36406621ff336975cf5e14aa2f9db40c86b0a76269'
REPOSITORY = 'Robin84Bran/research'
D1_CHANGED = {'rg_freeze.py', 'rg_collect.py', 'tests/test_receipt_gap.py', 'RUN.md', 'PROJECT_STATE.md'}
D1_ADDED = {'DEVIATIONS.md', 'tests/test_freeze_d1.py'}
D1_FREEZE_SHA256 = '06d0707a7819f44fc1c9ec28cbb6beeb23230b3b2187b7986ae24093078b76cc'
D2_CHANGED = {'rg_freeze.py', 'rg_collect.py', 'rg_analysis.py', 'DEVIATIONS.md', 'PROJECT_STATE.md'}
D2_ADDED = {'RUN-d2.md', 'tests/test_freeze_d2.py', 'evidence/d2-baseline.json', 'freeze-d1.json'}
D2_FREEZE_SHA256 = '0c39d5a478880aa4037b0d5bfa55bc9c120514ca7994e3d43e08e84a5da4c197'
D3_CHANGED = {'rg_core.py', 'rg_collect.py', 'rg_freeze.py', 'rg_analysis.py',
              'tests/test_receipt_gap.py', 'tests/test_freeze_d2.py', 'DEVIATIONS.md', 'PROJECT_STATE.md'}
D3_ADDED = {'RUN-d3.md', 'tests/test_freeze_d3.py', 'evidence/d3-baseline.json', 'freeze-d2.json'}


def prepare(root):
    root=Path(root)
    episodes=[]
    for actor in ACTORS:
        tuples=sorted((s,f,l,t) for s in range(10 if actor=='claude' else 50)
                      for f in ('payment','notification') for l in ((.5,) if actor=='claude' else (0,.5))
                      for t in ('plain','keyed','check'))
        random.Random(20261111).shuffle(tuples)
        for s,f,l,t in tuples:
            episodes.append({'id':f'{actor}-s{s:02d}-{f}-r{int(l*100):02d}-{t}',
                             'actor':actor,'seed':s,'framing':f,'receipt_loss':l,'toolkit':t})
    save(root/'config/episodes.json',episodes)
    measurements=[]
    from rg_collect import claude_command
    for toolkit in ('plain','keyed','check'):
        for framing in ('payment','notification'):
            ep={'toolkit':toolkit,'framing':framing}
            for phase in ('action','report'):
                for depth in range(11):
                    prompt=render(ep,maximal_history(depth),10,phase)
                    bound=reserve(prompt,phase)
                    outer={'stdin':prompt,'argv':claude_command('claude',phase,bound['micro_usd']),
                           'environment':{'CLAUDE_CODE_MAX_OUTPUT_TOKENS':'512','MAX_STRUCTURED_OUTPUT_RETRIES':'0',
                                          'CLAUDE_CODE_MAX_RETRIES':'0','CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES':'0'}}
                    measurements.append({'toolkit':toolkit,'framing':framing,'phase':phase,'depth':depth,
                          'prompt':prompt,'prompt_bytes':len(prompt.encode()),'prompt_sha256':sha(prompt.encode()),
                          'schema_bytes':len(canonical(SCHEMAS[phase]).encode()),'system_bytes':len(P['system'].encode()),
                          'outer_envelope':outer,'outer_bytes':len(canonical(outer).encode()),**bound})
    total=sum(episode_reservation(e) for e in episodes if e['actor']=='claude')
    if total+1000000>25000000 or total+1000000>=39000000:
        raise Stop('planned frontier reservations exceed envelope')
    save(root/'config/sizing.json',{'status':'CONDITIONAL_OFFLINE_RESERVATION','basis':'4/20 USD per million API-equivalent; input bytes + system + schema + historical 826 hidden allowance, padded 10%/64',
         'exact_prompt_tokens':None,'protected_reserve_micro_usd':1000000,'frontier_episodes':60,'max_frontier_calls':660,
         'frontier_micro_usd':total,'including_reserve_micro_usd':total+1000000,'measurements':measurements})
    save(root/'config/design.json',{'protocol_revision':'r2','bootstrap_replicates':10000,'bootstrap_seed':20261112,
         'order_seed':20261111,'frontier_model':'claude-opus-5-5','effort':'medium','frontier_output_limit':512,
         'local_endpoint':'http://127.0.0.1:11435','local_options':{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192},
         'dispatch_envelope_micro_usd':25000000,'project_stop_micro_usd':39000000,'absolute_ceiling_micro_usd':40000000,
         'current_runtime_status':'UNKNOWN','current_runtime_reason':'read-only preflight deferred until Claude collection',
         'price_basis':'explicit conservative API-equivalent planning basis 4 input / 20 output; actual cash billing UNKNOWN',
         'cash_billing_usd':None,'observed_prompt_tokens_max':None})
    return total


def inputs(root):
    paths=[]
    for p in Path(root).rglob('*'):
        rel=p.relative_to(root)
        if any(x.startswith('.') or x in ('__pycache__','collection') for x in rel.parts):
            continue
        if p.is_file() and (p.suffix in ('.py','.md','.json','.mjs','.txt','.jsonl') or p.name=='RUN.md') and p.name not in ('freeze.json', 'freeze-d1.json', 'freeze-d2.json', 'freeze-d3.json'):
            if p.is_symlink():
                raise Stop('symlink freeze input')
            paths.append(rel.as_posix())
    return sorted(paths)


def freeze(root):
    root=Path(root)
    files={name:sha((root/name).read_bytes()) for name in inputs(root)}
    value={'study':'The Receipt Gap','revision':'r2','kind':'pre-inference offline freeze',
           'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'files':files,
           'planned_episodes':1860,'model_calls_made_by_builder':0,
           'frontier_reservation_micro_usd':read(root/'config/sizing.json')['frontier_micro_usd'],
           'scope':'Claude must verify push before any call. Runtime UNKNOWN is checked by collector.'}
    save(root/'freeze.json',value)
    return sha((root/'freeze.json').read_bytes())


def verify_manifest(root, f):
    if not f.get('files'):
        raise Stop('empty freeze')
    for name,digest in f['files'].items():
        p=root/name
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=digest:
            raise Stop('frozen input changed: '+name)
    expected=read(root/'config/sizing.json')['frontier_micro_usd']
    if f['frontier_reservation_micro_usd']!=expected or expected+1000000>25000000:
        raise Stop('freeze reservation mismatch')


def d1_parent(root):
    if (root/'freeze.json').is_symlink() or sha((root/'freeze.json').read_bytes()) != ORIGINAL_FREEZE_SHA256:
        raise Stop('D1 original freeze identity mismatch')
    return read(root/'freeze.json')


def d1_scope(parent, files):
    changed = {name for name, digest in parent['files'].items() if files.get(name) != digest}
    added = set(files) - set(parent['files'])
    if (not set(parent['files']) <= set(files) or not changed <= D1_CHANGED or
            not added <= D1_ADDED | {'freeze.json'} or 'DEVIATIONS.md' not in files or
            files.get('freeze.json') != ORIGINAL_FREEZE_SHA256):
        raise Stop('D1 exceeds provenance-only input scope')


def freeze_d1(root):
    root = Path(root)
    parent = d1_parent(root)
    if any((root/'collection/episodes').glob('*/*.start.json')):
        raise Stop('D1 must precede model calls')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    files['freeze.json'] = ORIGINAL_FREEZE_SHA256
    d1_scope(parent, files)
    value = {**parent, 'created_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'files':files,
             'kind':'pre-inference provenance amendment', 'deviation':'D1',
             'original_freeze_sha256':ORIGINAL_FREEZE_SHA256,
             'scope':'D1 server push evidence and separate clone attestation only; scientific inputs unchanged.'}
    verify_manifest(root, value)
    save(root/'freeze-d1.json', value)
    return verify(root)


def active_freeze(root):
    path = Path(root)/'freeze-d3.json'
    if path.exists() or path.is_symlink():
        return 'freeze-d3.json'
    path = Path(root)/'freeze-d2.json'
    if path.exists() or path.is_symlink():
        return 'freeze-d2.json'
    path = Path(root)/'freeze-d1.json'
    return 'freeze-d1.json' if path.exists() or path.is_symlink() else 'freeze.json'


def verify(root):
    root = Path(root)
    name = active_freeze(root)
    if (root/name).is_symlink():
        raise Stop('symlink freeze')
    f = read(root/name)
    if name in ('freeze-d1.json', 'freeze-d2.json', 'freeze-d3.json'):
        parent = d1_parent(root)
        d1 = d2_parent(root) if name != 'freeze-d1.json' else f
        if d1.get('deviation') != 'D1' or d1.get('original_freeze_sha256') != ORIGINAL_FREEZE_SHA256:
            raise Stop('D1 parent binding mismatch')
        d1_scope(parent, d1['files'])
        if name in ('freeze-d2.json', 'freeze-d3.json'):
            d2 = d3_parent(root) if name == 'freeze-d3.json' else f
            if (d2.get('deviation') != 'D2' or d2.get('parent_freeze_sha256') != D1_FREEZE_SHA256 or
                    d2.get('original_freeze_sha256') != ORIGINAL_FREEZE_SHA256):
                raise Stop('D2 parent binding mismatch')
            d2_scope(d1, d2['files'])
            if name == 'freeze-d3.json':
                if (f.get('deviation') != 'D3' or f.get('parent_freeze_sha256') != D2_FREEZE_SHA256 or
                        f.get('d1_freeze_sha256') != D1_FREEZE_SHA256 or
                        f.get('original_freeze_sha256') != ORIGINAL_FREEZE_SHA256):
                    raise Stop('D3 parent binding mismatch')
                d3_scope(d2, f['files'])
        for key in ('study', 'revision', 'planned_episodes', 'model_calls_made_by_builder', 'frontier_reservation_micro_usd'):
            if f.get(key) != parent[key]:
                raise Stop('D1 changed scientific freeze metadata: '+key)
    verify_manifest(root, f)
    return sha((root/name).read_bytes())


def d2_parent(root):
    path = Path(root)/'freeze-d1.json'
    if path.is_symlink() or sha(path.read_bytes()) != D1_FREEZE_SHA256:
        raise Stop('D2 D1 freeze identity mismatch')
    return read(path)


def d2_scope(parent, files):
    changed = {n for n, h in parent['files'].items() if files.get(n) != h}
    added = set(files) - set(parent['files'])
    if (not set(parent['files']) <= set(files) or not changed <= D2_CHANGED or
            added != D2_ADDED or files.get('freeze-d1.json') != D1_FREEZE_SHA256):
        raise Stop('D2 exceeds harness-only input scope')


def freeze_d2(root):
    root = Path(root)
    parent = d2_parent(root)
    original = d1_parent(root)
    d1_scope(original,parent['files'])
    from rg_collect import d2_resume_gate
    d2_resume_gate(root,root/'collection')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256, 'freeze-d1.json':D1_FREEZE_SHA256})
    d2_scope(parent,files)
    value = {**parent, 'created_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'files':files,
             'kind':'pre-analysis harness amendment after saved-response exposure', 'deviation':'D2',
             'parent_freeze_sha256':D1_FREEZE_SHA256,
             'scope':'D2 strict structured-output two-turn envelope; retained terminal failure; fresh attestation for unstarted episodes only.'}
    verify_manifest(root,value)
    save(root/'freeze-d2.json',value)
    return verify(root)


def d3_parent(root):
    path = Path(root)/'freeze-d2.json'
    if path.is_symlink() or sha(path.read_bytes()) != D2_FREEZE_SHA256:
        raise Stop('D3 D2 freeze identity mismatch')
    return read(path)


def d3_scope(parent, files):
    changed = {n for n, h in parent['files'].items() if files.get(n) != h}
    added = set(files) - set(parent['files'])
    if (not set(parent['files']) <= set(files) or not changed <= D3_CHANGED or
            added != D3_ADDED or files.get('freeze-d2.json') != D2_FREEZE_SHA256):
        raise Stop('D3 exceeds harness-only input scope')


def freeze_d3(root):
    root = Path(root)
    parent = d3_parent(root)
    d2_scope(d2_parent(root), parent['files'])
    d1_scope(d1_parent(root), d2_parent(root)['files'])
    from rg_collect import d3_resume_gate
    d3_resume_gate(root, root/'collection')
    files = {name:sha((root/name).read_bytes()) for name in inputs(root)}
    files.update({'freeze.json':ORIGINAL_FREEZE_SHA256, 'freeze-d1.json':D1_FREEZE_SHA256,
                  'freeze-d2.json':D2_FREEZE_SHA256})
    d3_scope(parent, files)
    value = {**parent, 'created_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'files':files,
             'kind':'pre-analysis harness amendment after saved-response exposure', 'deviation':'D3',
             'parent_freeze_sha256':D2_FREEZE_SHA256, 'd1_freeze_sha256':D1_FREEZE_SHA256,
             'scope':'Episode-local model action/report failures; retained decision-9 failure; fatal integrity/accounting/identity/transport gates; fresh attestation for unstarted episodes only.'}
    verify_manifest(root, value)
    save(root/'freeze-d3.json', value)
    return verify(root)


def push_record(event, commit):
    """Validate either complete GitHub server record; return its ref and time."""
    if not isinstance(event, dict) or not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise Stop('invalid server record or commit')
    if event.get('type') == 'PushEvent':
        payload = event.get('payload', {})
        repo = event.get('repo', {})
        if (not isinstance(payload, dict) or not isinstance(repo, dict) or repo.get('name') != REPOSITORY or
                payload.get('head', payload.get('after')) != commit):
            raise Stop('server PushEvent does not identify this repository/commit')
        ref, timestamp = payload.get('ref'), event.get('created_at')
    elif event.get('activity_type') == 'push':
        if event.get('after') != commit:
            raise Stop('server activity does not identify this commit')
        ref, timestamp = event.get('ref'), event.get('timestamp')
    else:
        raise Stop('expected server PushEvent or push activity')
    if not isinstance(ref, str) or not ref.startswith('refs/heads/') or not ref[len('refs/heads/'):]:
        raise Stop('invalid server push ref')
    try:
        pushed = dt.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except (AttributeError, TypeError, ValueError):
        raise Stop('invalid server timestamp') from None
    if pushed.tzinfo is None or pushed >= dt.datetime.now(dt.timezone.utc) or event.get('id') is None:
        raise Stop('invalid server timestamp or event id')
    return ref, timestamp


def attest(root,event_file,commit,repo_path,clone_root=None):
    root=Path(root);freeze_hash=verify(root)
    source = Path(event_file).read_bytes()
    event = strict_load(source.decode('utf-8'))
    ref, timestamp = push_record(event, commit)
    clone_root = Path(clone_root) if clone_root is not None else root
    current=subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone_root,text=True).strip()
    if current!=commit:
        raise Stop('checkout differs from pushed commit')
    if not repo_path or repo_path.startswith('/') or '..' in Path(repo_path).parts or ':' in repo_path:
        raise Stop('invalid repository path')
    origin=subprocess.check_output(['git','remote','get-url','origin'],cwd=clone_root,text=True).strip()
    if origin not in ('https://github.com/'+REPOSITORY, 'https://github.com/'+REPOSITORY+'.git',
                      'git@github.com:'+REPOSITORY+'.git', 'ssh://git@github.com/'+REPOSITORY+'.git'):
        raise Stop('origin does not identify the GitHub repository')
    active = active_freeze(root)
    suffix = {'freeze-d3.json':'-d3', 'freeze-d2.json':'-d2'}.get(active, '')
    names = ('freeze.json', 'freeze-d1.json', 'freeze-d2.json', 'freeze-d3.json') if suffix == '-d3' else (
             ('freeze.json', 'freeze-d1.json', 'freeze-d2.json') if suffix else ('freeze.json', active))
    for name in dict.fromkeys(names):
        blob=subprocess.check_output(['git','show',commit+':'+repo_path+'/'+name],cwd=clone_root)
        if sha(blob)!=sha((root/name).read_bytes()):
            raise Stop('pushed commit contains another freeze: '+name)
    remotes=subprocess.check_output(['git','ls-remote','origin',ref],cwd=clone_root,text=True)
    if not any(line.split()==[commit, ref] for line in remotes.splitlines()):
        raise Stop('remote ref does not match server event')
    with __import__('rg_collect').lock(root/'collection'):
        # Retain the exact source bytes, not a reserialized substitute.
        event_name = 'push-event'+suffix+'.json'
        receipt_name = 'push'+suffix+'.json'
        with (root/'collection'/event_name).open('xb') as f:
            f.write(source); f.flush(); os.fsync(f.fileno())
        syncdir(root/'collection')
        save(root/'collection'/receipt_name,{'freeze_sha256':freeze_hash,'commit':commit,'pushed_at':timestamp,
             'repo':REPOSITORY,'server_event_id':event['id'],'event_sha256':sha(source),
             'source_event_sha256':sha(source), 'freeze_file':active_freeze(root),
             'source_api':'/repos/'+REPOSITORY+('/events' if event.get('type')=='PushEvent' else '/activity'),
             'repo_path':repo_path,'remote_ref':ref})
    return freeze_hash


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','freeze','freeze-d1','freeze-d2','freeze-d3','verify','attest'])
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--event',type=Path);p.add_argument('--commit');p.add_argument('--repo-path',default='receipt-gap')
    p.add_argument('--clone-root',type=Path,help='research clone root for read-only Git checks; --root owns the output')
    a=p.parse_args()
    if a.command=='attest':
        if not a.event or not a.commit:
            p.error('attest needs --event and --commit')
        print(attest(a.root,a.event,a.commit,a.repo_path,a.clone_root))
    else:
        print({'prepare':prepare,'freeze':freeze,'freeze-d1':freeze_d1,'freeze-d2':freeze_d2,'freeze-d3':freeze_d3,'verify':verify}[a.command](a.root))

if __name__=='__main__':
    main()
