"""D2: exact pinned local metadata and one append-only pre-generation disposition.

No network, model process or Git operations occur in this module.
"""
import ast
from pathlib import Path

from bob_core import PINS,canonical,sha,strict_load
from bob_collect import Stop,read,save,now,lock

D1_SHA256='699a9e609fa26a526791f5673320ee49db9836a57e49c1fe192798b5a7e95142'
DISPOSITION='deviations/d2/disposition.json'
IDENTITY='deviations/d2/evidence/local-identity.json'
CHANGED={'bob.py','bob_freeze.py','bob_collect.py','bob_audit.py','DEVIATIONS.md',
         'tests/test_collect.py','tests/test_d1.py'}
ADDED={'bob_d2.py','tests/test_d2.py','RUN-d2.md','PROJECT_STATE-d2.md',DISPOSITION,
       IDENTITY,'deviations/d2/evidence/receipt-gap-qwen7b-preflight.json'}
EPISODE='qwen7b-38-required-registry'
CALL=EPISODE+'-action-0'


def parent(root):
    from bob_freeze import d1_parent
    d1_parent(root)
    p=Path(root)/'freeze-d1.json'
    if p.is_symlink() or sha(p.read_bytes())!=D1_SHA256:
        raise Stop('D2 pinned D1 parent mismatch')
    return read(p)


def identity(root):
    """Verify the archived manifest -> layer chain; no dependency on model store."""
    root=Path(root)
    models=read(root/IDENTITY)['models']
    if set(models)!=set(PINS):
        raise Stop('D2 local identity inventory mismatch')
    for model,(tag,digest) in PINS.items():
        item=models[model]
        raw=(root/item['manifest_file']).read_bytes()
        if item['tag']!=tag or item['digest']!=digest or sha(raw)!=digest:
            raise Stop('D2 local manifest digest mismatch')
        layers={x['mediaType'].split('.')[-1]:x['digest'] for x in strict_load(raw)['layers']}
        for kind in ('template','system','params'):
            descriptor=item['layers'].get(kind)
            if (descriptor is None)!=(kind not in layers):
                raise Stop('D2 missing/extra identity layer')
            if descriptor is not None:
                data=(root/descriptor['file']).read_bytes()
                if 'sha256:'+sha(data)!=layers[kind] or sha(data)!=descriptor['sha256']:
                    raise Stop('D2 identity layer hash mismatch')
                if kind in ('template','system') and item[kind]!=data.decode():
                    raise Stop('D2 expected identity differs from pinned layer')
        if 'system' not in layers and item['system']!='':
            raise Stop('D2 invented system text')
    return models


def check_local_identity(root,model,show):
    expected=identity(root)[model]
    system=show.get('system')
    if system is None:
        system=''
    if show.get('template')!=expected['template'] or system!=expected['system']:
        raise Stop('local pinned template/system mismatch')


def validate_disposition(root,pre_resume=False):
    """Check original bytes/prefix, never infer dispatch from elapsed time alone."""
    root=Path(root)
    d=read(root/DISPOSITION)
    if (d['episode_id']!=EPISODE or d['call_id']!=CALL or
        d['disposition']!='retain-technical-failure-no-rerun' or d['generation_request_sent'] is not False):
        raise Stop('D2 disposition identity/policy mismatch')
    for name,digest in d['evidence_files'].items():
        path=root/name
        if path.is_symlink():
            raise Stop('D2 evidence symlink')
        raw=path.read_bytes()
        archived=root/'deviations/d2/evidence/prior-collection'/Path(name).relative_to('collection')
        if sha(archived.read_bytes())!=digest:
            raise Stop('D2 prior evidence archive changed: '+name)
        if name.endswith('.jsonl'):
            raw=raw[:len(archived.read_bytes())]
        if sha(raw)!=digest:
            raise Stop('D2 original evidence changed: '+name)
    cost=(root/'collection/cost.jsonl').read_bytes()
    size=d['cost_ledger_prefix_bytes']
    if sha(cost[:size])!=d['cost_ledger_prefix_sha256'] or pre_resume and len(cost)!=size:
        raise Stop('D2 cost prefix mismatch or collection already resumed')
    receipt=read(root/'collection/calls'/f'{CALL}.json')
    if (receipt['error']!='Stop: unexpected model system prompt' or
        any(receipt[k] is not None for k in ('response_sha256','stderr_sha256','returncode','envelope','parsed','usage')) or
        any((root/'collection/raw'/f'{CALL}.{suffix}').exists() for suffix in ('stdout','stderr'))):
        raise Stop('D2 pre-generation proof missing/ambiguous')
    episode=read(root/'collection/episodes'/f'{EPISODE}.json')
    if episode['events'] or episode['decisions']!=0 or episode['committed'] or episode['calls']!=[CALL]:
        raise Stop('D2 unexpected episode effects')
    from bob_analysis import score
    scored=score(episode['episode'],episode,True)
    if any(scored[k]!=v for k,v in d['scoring'].items()):
        raise Stop('D2 disposition differs from frozen scoring')
    return d


def _unaffected(raw,allowed):
    tree=ast.parse(raw)
    def prune(body,prefix=''):
        out=[]
        for node in body:
            name=prefix+getattr(node,'name','')
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and name in allowed:
                continue
            if isinstance(node,ast.ClassDef):
                node.body=prune(node.body,name+'.')
            out.append(node)
        return out
    tree.body=prune(tree.body)
    return ast.dump(tree,include_attributes=False)


def scope(root,files):
    root=Path(root)
    p=parent(root)
    extras=set(ADDED)|{'deviations/d2/original/'+n for n in CHANGED}
    # Evidence inventory is determined by pinned parent/layer/archive contents,
    # then bound in freeze-d2. No new scientific inputs are permitted.
    extras|={n for n in files if n.startswith('deviations/d2/evidence/models/') or
             n.startswith('deviations/d2/evidence/prior-collection/')}
    if set(files)!=set(p['files'])|extras:
        raise Stop('D2 inventory outside declared amendment')
    for name,digest in p['files'].items():
        if name not in CHANGED and files.get(name)!=digest:
            raise Stop('D2 changed scientific/frozen input: '+name)
        if name in CHANGED and files.get('deviations/d2/original/'+name)!=digest:
            raise Stop('D2 D1 original archive mismatch: '+name)
    for name,allowed in {
        'bob_collect.py':{'Ledger.apply','LocalAdapter.check','frontier_gate','run_episode'},
        'bob_audit.py':{'reconcile_ledger'},
    }.items():
        if _unaffected((root/'deviations/d2/original'/name).read_bytes(),allowed)!=_unaffected((root/name).read_bytes(),allowed):
            raise Stop('D2 changed unrelated mechanism: '+name)
    identity(root)
    validate_disposition(root)
    return p


def verify_d2(root,record):
    from bob_freeze import ORIGINAL_FREEZE_SHA256,TRANSPORT_POLICY
    p=scope(root,record['files'])
    if (record.get('deviation')!='D2' or record.get('parent_freeze_sha256')!=D1_SHA256 or
        record.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256 or
        record.get('transport_policy')!=TRANSPORT_POLICY or
        record.get('disposition_sha256')!=sha((Path(root)/DISPOSITION).read_bytes())):
        raise Stop('D2 freeze binding/policy mismatch')
    for key in ('format','local_episodes','frontier_episodes','maximum_generations','new_model_calls','new_usd',
                'frontier_reservation_micro_usd','protected_reserve_micro_usd'):
        if record.get(key)!=p[key]:
            raise Stop('D2 changed scientific/budget metadata: '+key)


def freeze_d2(root):
    from bob_freeze import inventory,verify
    root=Path(root)
    if (root/'freeze-d2.json').exists() or (root/'freeze-d2.json').is_symlink():
        raise Stop('D2 freeze exists; never overwrite')
    files=inventory(root)
    p=scope(root,files)
    d=validate_disposition(root,pre_resume=True)
    expected={n for n in d['evidence_files'] if '/starts/' in n or '/episode-starts/' in n}
    actual={q.relative_to(root).as_posix() for folder in ('starts','episode-starts') for q in (root/'collection'/folder).glob('*.json')}
    if actual!=expected:
        raise Stop('D2 requires only the retained pre-generation start')
    report=read(root/'build/test-report-d2.json')
    if report.get('status')!='PASS' or report.get('tests',0)<1 or report.get('source_sha256')!=sha(canonical(files).encode()):
        raise Stop('passing tests must bind exact D2 source')
    record=dict(p,files=files,content_sha256=sha(canonical(files).encode()),deviation='D2',
                parent_freeze_sha256=D1_SHA256,disposition_sha256=sha((root/DISPOSITION).read_bytes()),
                frozen_utc=now(),tests=report['tests'],test_counts=dict(python=report['python_tests'],toy=report['toy_tests']),
                unresolved=['new D2 push attestation before future calls','live local metadata/capacity must be rechecked',
                            'first started episode retained as technical failure; no rerun',
                            'D1 empirical frontier conditions remain in force'])
    save(root/'freeze-d2.json',record)
    verify(root)
    return dict(freeze_file='freeze-d2.json',freeze_sha256=sha((root/'freeze-d2.json').read_bytes()),
                parent_freeze_sha256=D1_SHA256,tests=report['tests'])


def validate_resume(root,event):
    """Shared by operational ledger and independent audit; exact one-stop release."""
    from bob_freeze import verify
    root=Path(root)
    f=verify(root)
    d=validate_disposition(root)
    required=dict(event='d2-resume',id=EPISODE,deviation='D2',
                  freeze_sha256=sha((root/'freeze-d2.json').read_bytes()),
                  disposition_sha256=sha((root/DISPOSITION).read_bytes()))
    if f.get('deviation')!='D2' or {k:v for k,v in event.items() if k!='time'}!=required:
        raise Stop('invalid D2 resume event')
    from bob_freeze import parsed_time
    if parsed_time(event['time'])<parsed_time(f['frozen_utc']):
        raise Stop('D2 resume predates freeze')
    raw=(root/'collection/cost.jsonl').read_bytes()
    tail=raw[d['cost_ledger_prefix_bytes']:].splitlines()
    if tail and strict_load(tail[0])!=event:
        raise Stop('D2 resume must immediately follow original stop')
    if any(strict_load(line).get('event')=='d2-resume' for line in tail[1:]):
        raise Stop('duplicate D2 resume')
    return d


def reconcile_d2(root):
    """Offline, append-only and idempotent; never releases a paid/ambiguous hold."""
    from bob_freeze import verify
    from bob_collect import Ledger
    from bob_audit import reconcile_ledger
    root=Path(root)
    with lock(root/'collection/collector.lock'):
        if verify(root).get('deviation')!='D2':
            raise Stop('reconciliation requires frozen D2')
        validate_disposition(root)
        ledger=Ledger(root/'collection/cost.jsonl')
        if ledger.blocked:
            validate_disposition(root,pre_resume=True)
            ledger.event(event='d2-resume',id=EPISODE,deviation='D2',
                         freeze_sha256=sha((root/'freeze-d2.json').read_bytes()),
                         disposition_sha256=sha((root/DISPOSITION).read_bytes()))
        if EPISODE not in ledger.finished:
            ledger.event(event='release',id=EPISODE)
        records={p.stem:read(p) for p in (root/'collection/episodes').glob('*.json')}
        result=reconcile_ledger(root,records)
        if result['status']!='PASS':
            raise Stop('D2 reconciliation did not clear the exact stop')
        return dict(status='PASS',disposition='retain-technical-failure-no-rerun',**{'ledger':result})


def check_d2_push(root,freeze,push):
    from bob_freeze import check_d1_push,push_record,parsed_time,ORIGINAL_FREEZE_SHA256,REPOSITORY
    root=Path(root)
    d=validate_disposition(root)
    check_d1_push(root,parent(root),read(root/'collection/push.json'),starts_deviation='D1')
    if (push.get('freeze_file')!='freeze-d2.json' or push.get('freeze_sha256')!=sha((root/'freeze-d2.json').read_bytes()) or
        push.get('parent_freeze_sha256')!=D1_SHA256 or push.get('original_freeze_sha256')!=ORIGINAL_FREEZE_SHA256 or
        push.get('repo')!=REPOSITORY or push.get('evidence_file')!='collection/push-d2-event.json'):
        raise Stop('push does not bind D2 and both parents')
    p=root/'collection/push-d2-event.json'
    if p.is_symlink() or sha(p.read_bytes())!=push.get('evidence_sha256'):
        raise Stop('D2 raw push evidence missing/changed')
    supplied=push_record(strict_load(p.read_bytes()),push.get('commit'))
    if any(push.get(k)!=v for k,v in supplied.items()):
        raise Stop('D2 receipt differs from raw server evidence')
    pushed=parsed_time(push['github_time'])
    if pushed<parsed_time(freeze['frozen_utc']):
        raise Stop('push must follow D2 freeze')
    for folder in ('starts','episode-starts'):
        for p in (root/'collection'/folder).glob('*.json'):
            rel=p.relative_to(root).as_posix()
            v=read(p)
            if rel in d['evidence_files']:
                continue  # Exact retained D1 bytes were already verified above.
            if v.get('deviation')!='D2' or v.get('amendment_freeze_sha256')!=push['freeze_sha256'] or parsed_time(v['started'])<pushed:
                raise Stop('D2 push must precede and bind every new start')
    return push
