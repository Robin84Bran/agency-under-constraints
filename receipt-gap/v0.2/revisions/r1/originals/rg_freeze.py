"""v0.2 immutable offline freeze; server push attestation is a later explicit action."""
import argparse
import datetime as dt
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

from rg_core import (ROOT, ACTORS, P, canonical, episode_reservation, maximal_history,
                     render, reserve, schema_for, sha, strict_load)
from rg_collect import Stop, read, save, syncdir

REPOSITORY = 'Robin84Bran/research'


def verify_prior(root):
    root = Path(root)
    data = (root/'evidence/v01-ledger.jsonl').read_bytes()
    prior = read(root/'config/prior-spend.json')
    holds, spent, calls, finished = {}, 0, set(), set()
    for line in data.decode().splitlines():
        e = strict_load(line); op, ident = e['event'], e['id']
        if op == 'reserve':
            if ident in holds or type(e['amount']) is not int or e['amount'] < 0:
                raise Stop('invalid prior reservation')
            holds[ident] = e['amount']
        elif op == 'settle':
            episode = e['episode']
            if (episode not in holds or episode in finished or ident in calls or
                any(type(e[k]) is not int or e[k] < 0 for k in ('actual','reserved')) or e['reserved'] > holds[episode]):
                raise Stop('invalid prior settlement')
            spent += e['actual']; holds[episode] -= e['reserved']; calls.add(ident)
        elif op == 'release':
            if ident not in holds or ident in finished:
                raise Stop('invalid prior release')
            holds[ident] = 0; finished.add(ident)
        else:
            raise Stop('unknown prior event')
    expected = {'event':'carry','id':'v0.1','settled_micro_usd':spent,
                'holds':{'v0.1/'+k:n for k,n in holds.items() if n}, 'source_sha256':sha(data)}
    if expected != prior:
        raise Stop('prior spend differs from retained ledger')
    return prior


def prepare(root):
    root = Path(root)
    # The inherited explicit order is authoritative, never reshuffled.
    for name in ('episodes.json', 'prompts.json', 'report-schema.json', 'prior-spend.json',
                 'action-plain-schema.json', 'action-keyed-schema.json', 'action-check-schema.json'):
        path = root/'config'/name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as f:
                f.write((ROOT/'config'/name).read_bytes())
    snapshot = root/'evidence/v01-ledger.jsonl'
    if not snapshot.exists():
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        with snapshot.open('xb') as f:
            f.write((ROOT/'evidence/v01-ledger.jsonl').read_bytes())
    prior = read(root/'config/prior-spend.json')
    schedule = read(root/'config/episodes.json')
    if len(schedule) != 1860 or sum(e['actor']=='claude' for e in schedule) != 60:
        raise Stop('sample changed')
    measurements = []
    from rg_collect import claude_command, clean_env
    for toolkit in ('plain','keyed','check'):
        for framing in ('payment','notification'):
            ep = {'toolkit':toolkit,'framing':framing}
            for phase in ('action','report'):
                for depth in range(11):
                    prompt = render(ep,maximal_history(depth),10,phase)
                    bound = reserve(prompt,phase,toolkit)
                    schema = schema_for(phase,toolkit)
                    outer = {'stdin':prompt, 'argv':claude_command('claude',phase,bound['micro_usd'],toolkit),
                             'environment':{k:v for k,v in clean_env().items() if k.startswith(('CLAUDE_','MAX_','DISABLE_'))}}
                    measurements.append({'toolkit':toolkit,'framing':framing,'phase':phase,'depth':depth,
                        'prompt':prompt,'prompt_bytes':len(prompt.encode()),'prompt_sha256':sha(prompt.encode()),
                        'schema':schema,'schema_bytes':len(canonical(schema).encode()),'system_bytes':len(P['system'].encode()),
                        'outer_envelope':outer,'outer_bytes':len(canonical(outer).encode()),**bound})
    total = sum(episode_reservation(e) for e in schedule if e['actor']=='claude')
    cumulative = total + prior['settled_micro_usd'] + sum(prior['holds'].values()) + 1000000
    if cumulative > 25000000 or cumulative >= 39000000:
        raise Stop('planned cumulative project reservations exceed envelope')
    save(root/'config/sizing.json', {'status':'CONDITIONAL_OFFLINE_RESERVATION',
        'basis':'unchanged 4/20 USD per million; exact prompt+system+toolkit schema+826 hidden allowance, padded 10%/64',
        'exact_prompt_tokens':None,'protected_reserve_micro_usd':1000000,'frontier_episodes':60,'max_frontier_calls':660,
        'frontier_micro_usd':total,'including_reserve_micro_usd':total+1000000,
        'cumulative_including_prior_and_reserve_micro_usd':cumulative,'measurements':measurements})
    design = read(ROOT/'evidence/v01-design.json')
    design.update(protocol_revision='v0.2', local_runtime_version='0.33.3',
                  scientific_change='per-toolkit exact constrained action schema for every actor',
                  prior_settled_micro_usd=prior['settled_micro_usd'], prior_holds_micro_usd=sum(prior['holds'].values()),
                  current_runtime_status='UNKNOWN',current_runtime_reason='offline builder; no runtime calls')
    save(root/'config/design.json',design)
    return total


def inputs(root):
    root = Path(root)
    paths = [*root.glob('*.py'), *root.glob('*.md')]
    for directory in ('config','evidence','fixtures'):
        paths += list((root/directory).rglob('*'))
    paths += list((root/'tests').glob('test_*.py'))
    paths += list((root/'offline').rglob('*'))
    out = []
    for path in paths:
        if path.is_symlink():
            raise Stop('symlink freeze input')
        if path.is_file() and path.suffix in ('.py','.md','.json','.jsonl','.mjs'):
            out.append(path.relative_to(root).as_posix())
    return sorted(set(out))


def freeze(root):
    root = Path(root)
    prior = verify_prior(root)
    if any((root/'collection/episodes').glob('*/*.start.json')):
        raise Stop('freeze must precede every v0.2 call')
    sizing = read(root/'config/sizing.json')
    value = {'study':'The Receipt Gap','revision':'v0.2','kind':'pre-v0.2-inference freeze after disclosed v0.1 results',
             'created_at':dt.datetime.now(dt.timezone.utc).isoformat(),
             'files':{name:sha((root/name).read_bytes()) for name in inputs(root)},
             'planned_episodes':1860,'model_calls_made_by_builder':0,
             'frontier_reservation_micro_usd':sizing['frontier_micro_usd'],
             'prior_settled_micro_usd':prior['settled_micro_usd'],'prior_holds_micro_usd':sum(prior['holds'].values()),
             'single_scientific_change':'per-toolkit exact action schema passed to every actor',
             'scope':'offline build only; separate fresh push and attestation before any model call; stop after v0.2'}
    save(root/'freeze.json',value)
    return verify(root)


def verify(root):
    root = Path(root)
    path = root/'freeze.json'
    if path.is_symlink():
        raise Stop('symlink freeze')
    f = read(path)
    if f.get('revision') != 'v0.2' or not f.get('files') or set(f['files']) != set(inputs(root)):
        raise Stop('freeze input inventory mismatch')
    for name, digest in f['files'].items():
        rel = PurePosixPath(name)
        p = root/name
        if (rel.is_absolute() or '..' in rel.parts or
            any((root/Path(*rel.parts[:i])).is_symlink() for i in range(1,len(rel.parts)+1)) or
            not p.is_file() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes()) != digest):
            raise Stop('frozen input changed: '+name)
    prior = verify_prior(root)
    expected = sum(episode_reservation(e) for e in read(root/'config/episodes.json') if e['actor']=='claude')
    cumulative = expected+prior['settled_micro_usd']+sum(prior['holds'].values())+1000000
    if (f['frontier_reservation_micro_usd'] != expected or
        read(root/'config/sizing.json')['frontier_micro_usd'] != expected or
        cumulative > 25000000 or cumulative >= 39000000):
        raise Stop('freeze cumulative reservation mismatch')
    return sha(path.read_bytes())


# D1: retain both documented GitHub server shapes, not a local Git timestamp.
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


def attest(root, event_file, commit, repo_path, clone_root=None):
    root = Path(root); digest = verify(root)
    source = Path(event_file).read_bytes(); event = strict_load(source.decode())
    ref, timestamp = push_record(event,commit)
    if dt.datetime.fromisoformat(timestamp.replace('Z','+00:00')) < dt.datetime.fromisoformat(read(root/'freeze.json')['created_at']):
        raise Stop('server push preceded this v0.2 freeze')
    clone = Path(clone_root) if clone_root is not None else root
    if not repo_path or repo_path.startswith('/') or '..' in Path(repo_path).parts or ':' in repo_path:
        raise Stop('invalid repository path')
    current = subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()
    if current != commit:
        raise Stop('checkout differs from pushed commit')
    origin = subprocess.check_output(['git','remote','get-url','origin'],cwd=clone,text=True).strip()
    if origin not in ('https://github.com/'+REPOSITORY,'https://github.com/'+REPOSITORY+'.git',
                      'git@github.com:'+REPOSITORY+'.git','ssh://git@github.com/'+REPOSITORY+'.git'):
        raise Stop('origin does not identify the GitHub repository')
    for name, expected in {'freeze.json':digest, **read(root/'freeze.json')['files']}.items():
        blob = subprocess.check_output(['git','show',commit+':'+repo_path+'/'+name],cwd=clone)
        if sha(blob) != expected:
            raise Stop('pushed input differs: '+name)
    remote = subprocess.check_output(['git','ls-remote','origin',ref],cwd=clone,text=True)
    if not any(line.split() == [commit,ref] for line in remote.splitlines()):
        raise Stop('remote ref differs from server record')
    from rg_collect import lock
    with lock(root/'collection'):
        with (root/'collection/push-event.json').open('xb') as f:
            f.write(source);f.flush();os.fsync(f.fileno())
        syncdir(root/'collection')
        save(root/'collection/push.json',{'freeze_sha256':digest,'freeze_file':'freeze.json','commit':commit,
            'repo':REPOSITORY,'pushed_at':timestamp,'remote_ref':ref,'server_event_id':event['id'],
            'event_sha256':sha(source),'source_event_sha256':sha(source),'repo_path':repo_path,
            'source_api':'/repos/'+REPOSITORY+('/events' if event.get('type')=='PushEvent' else '/activity')})
    return digest


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command',choices=['prepare','freeze','verify','attest'])
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--event',type=Path);p.add_argument('--commit')
    p.add_argument('--repo-path',default='receipt-gap/v0.2');p.add_argument('--clone-root',type=Path)
    a = p.parse_args()
    if a.command == 'attest':
        if not a.event or not a.commit:
            p.error('attest needs --event and --commit')
        print(attest(a.root,a.event,a.commit,a.repo_path,a.clone_root))
    else:
        print({'prepare':prepare,'freeze':freeze,'verify':verify}[a.command](a.root))

if __name__ == '__main__':
    main()
