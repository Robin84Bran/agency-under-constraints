"""Exclusive, portable freeze; verification performs no network or provider I/O."""
import datetime as dt
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def inventory(root):
    root=Path(root)
    paths=set(root.glob('*.py'))
    paths.add(root/'PROTOCOL.md'); paths.add(root/'RUN.md'); paths.add(root/'survey_inventory.json')
    for folder in ('tests','config','evidence','imported','agreement-r2'):
        paths.update(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.update((root/'build').glob('*.py'))
    paths.update(p for p in (root/'build').glob('*.json') if p.is_file() and not p.name.startswith('postfreeze_'))
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(paths)}


def verify_freeze(root):
    root=Path(root); path=root/'freeze.json'
    record=json.loads(path.read_text())
    files=record['files']
    if hashlib.sha256(canonical(files)).hexdigest()!=record['content_sha256']:
        raise ValueError('freeze content digest is invalid')
    if (root/'freeze-d1.json').exists():
        from sos_d1 import verify
        amendment=verify(root,record,inventory(root))
        return dict(record,_d1=amendment)
    for name,expected in files.items():
        p=root/name
        if p.is_symlink() or not p.is_file() or digest(p)!=expected:
            raise ValueError('frozen file changed: '+name)
    if inventory(root)!=files:
        raise ValueError('freeze inventory changed; unexpected or missing frozen inputs')
    return record


def freeze(root):
    root=Path(root); path=root/'freeze.json'
    if path.exists(): raise FileExistsError('freeze.json already exists; never overwrite')
    report=json.loads((root/'imported/reconciliation.json').read_text())
    if report['status']!='PASS': raise ValueError('truth reconciliation did not pass')
    reports=[json.loads(p.read_text()) for p in (root/'build').glob('test_report*.json')]
    tests=max(reports,key=lambda r:r['tested_utc']) if reports else {}
    if tests['status']!='PASS' or tests['tests_run']<1: raise ValueError('offline tests did not pass')
    design=json.loads((root/'config/design.json').read_text())
    if len(design['primary_ids'])!=240: raise ValueError('primary design incomplete')
    for name in ('config/reuse.json','config/requests.json','config/collector.json','RUN.md'):
        if not (root/name).is_file(): raise ValueError('missing freeze prerequisite: '+name)
    files=inventory(root)
    record={'format':1,'status':'FROZEN_OFFLINE_NO_INFERENCE','frozen_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'files':files,'content_sha256':hashlib.sha256(canonical(files)).hexdigest(),
            'new_calls':0,'new_usd':0,'primary_episodes':240,'receipt_episodes':len(design['receipt_ids']),
            'push_status':'UNKNOWN','runtime_identity_status':'UNKNOWN',
            'authority':'Offline build authorized 11 November 2026; no inference performed. Claude must push before calls.'}
    with path.open('x',encoding='utf-8') as handle:
        json.dump(record,handle,ensure_ascii=False,sort_keys=True,indent=2);handle.write('\n')
        handle.flush()
        import os
        os.fsync(handle.fileno())
    verify_freeze(root)
    return {'freeze_sha256':digest(path),'content_sha256':record['content_sha256'],'files':len(files)}


def record_push(root, github_time, commit, remote, source, deviation=None):
    """Save an operator's real server receipt; does not run git or contact GitHub."""
    root=Path(root);record=verify_freeze(root)
    pushed=dt.datetime.fromisoformat(github_time.replace('Z','+00:00'))
    target='freeze.json'
    if deviation is not None:
        if deviation!='D1' or '_d1' not in record: raise ValueError('verified D1 freeze required')
        target='freeze-d1.json'
        record=record['_d1']
    frozen=dt.datetime.fromisoformat(record['frozen_utc'])
    if pushed.tzinfo is None or not frozen<=pushed<=dt.datetime.now(dt.timezone.utc):
        raise ValueError('push timestamp must follow freeze and precede current time')
    if len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('expected pushed 40-character commit SHA')
    if not remote.strip() or not source.strip(): raise ValueError('remote and real server evidence source required')
    value={'freeze_sha256':digest(root/target),'github_time':github_time,'commit':commit,
           'remote':remote,'server_timestamp_source':source,'attested_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    from sos_collect import save_new
    if deviation: value['original_freeze_sha256']=record['original_freeze_sha256']
    save_new(root/'collection'/('push-d1.json' if deviation else 'push.json'),value)
    return value
