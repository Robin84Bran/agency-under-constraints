"""Network-free GitHub activity receipt validation."""
import datetime as dt
import re
from pathlib import Path
from od_core import sha,canonical
from od_io import read,Stop
REPOSITORY='Robin84Bran/research'

def active_path(root):
    root=Path(root)
    if (root/'freeze-d3.json').exists(): return root/'freeze-d3.json'
    if (root/'freeze-d2.json').exists(): return root/'freeze-d2.json'
    if (root/'freeze-d1-final.json').exists(): return root/'freeze-d1-final.json'
    if (root/'freeze-d1.json').exists(): return root/'freeze-d1.json'
    return root/('freeze-a1.json' if (root/'freeze-a1.json').exists() else 'freeze.json')

def timestamp(s):
    try: t=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
    except (TypeError,ValueError,AttributeError): raise Stop('invalid server timestamp') from None
    if t.tzinfo is None: raise Stop('timezone required')
    return t


def push_record(e,commit):
    if type(e) is not dict or type(commit) is not str or re.fullmatch('[0-9a-f]{40}',commit) is None: raise Stop('invalid activity/commit')
    if e.get('activity_type')!='push' or e.get('after')!=commit: raise Stop('GitHub activity push record required')
    ref=e.get('ref');s=e.get('timestamp');t=timestamp(s)
    if type(ref) is not str or not ref.startswith('refs/heads/') or len(ref)<=11 or e.get('id') is None or t>=dt.datetime.now(dt.timezone.utc): raise Stop('invalid push ref/id/time')
    return ref,s


def parent_receipt_gate(root):
    root=Path(root);a=read(root/'collection/push.json');source=(root/'collection/push-event.json').read_bytes();event=read(root/'collection/push-event.json')
    ref,s=push_record(event,a['commit'])
    path=root/('freeze-a1.json' if (root/'freeze-d1.json').exists() else active_path(root).name)
    f=read(path)
    if a['freeze_sha256']!=sha(path.read_bytes()) or a['repo']!=REPOSITORY or a['source_api']!='/repos/'+REPOSITORY+'/activity' or a['event_sha256']!=sha(source) or a['pushed_at']!=s or a['remote_ref']!=ref or a['server_event_id']!=event['id']: raise Stop('push receipt binding mismatch')
    if timestamp(s)<=timestamp(f['created_at']): raise Stop('push must follow freeze')
    return timestamp(s)


def receipt_gate(root):
    return parent_receipt_gate(root)


def allowed_hashes(root):
    root=Path(root)
    if (root/'freeze-d3.json').exists():
        return {sha((root/'freeze-d3.json').read_bytes()),*read(root/'freeze-d3.json')['parents'].values()}
    if (root/'freeze-d2.json').exists():
        return {sha((root/'freeze-d2.json').read_bytes()),*read(root/'freeze-d2.json')['parents'].values()}
    if (root/'freeze-d1.json').exists():
        return {sha(active_path(root).read_bytes()),read(active_path(root))['parents']['freeze-a1.json']}
    return {sha(active_path(root).read_bytes())}


def start_gate(root,start,directory=None,attested=None):
    root=Path(root);h=start['freeze_sha256'];t=timestamp(start['started_at'])
    pushed=receipt_gate(root)
    if h not in allowed_hashes(root) or t<=pushed: raise Stop('start freeze/push mismatch')
    if (root/'freeze-d3.json').exists():
        f=read(root/'freeze-d3.json')
        if h==sha((root/'freeze-d3.json').read_bytes()):
            from od_d3 import d3_gate
            if start.get('accounting_revision')!='D3' or t<=(attested if attested is not None else d3_gate(root)): raise Stop('start predates D3 attestation/policy')
        else:
            from od_d3 import baseline
            n='episodes/'+start['id']+'/start.json'
            if directory is not None: n=Path(directory).relative_to(root/'collection').as_posix()+'/start.json'
            # Resume attempts have the same episode id; bind the actual bytes
            # against any exact saved start in that episode's baseline.
            saved=baseline(root)['files'];digest=sha((canonical(start)+'\n').encode())
            if directory is not None: matches=[saved.get(n)]
            else:
                from od_usage import directories
                matches=[saved.get(p.relative_to(root/'collection').as_posix()+'/start.json') for p in directories(root/'collection',start['id'])]
            if t>=timestamp(f['created_at']) or digest not in matches: raise Stop('start outside D3 parent boundary')
        return
    if (root/'freeze-d2.json').exists():
        if h==sha((root/'freeze-d2.json').read_bytes()):
            from od_d2 import d2_gate
            if t<=d2_gate(root): raise Stop('start predates D2 attestation')
        else:
            from od_d2 import baseline
            f=read(root/'freeze-d2.json');n='episodes/'+start['id']+'/start.json'
            if t>=timestamp(f['created_at']) or baseline(root)['files'].get(n)!=sha((canonical(start)+'\n').encode()): raise Stop('start outside D2 parent boundary')
        return
    if (root/'freeze-d1.json').exists():
        f=read(active_path(root))
        if h==f['parents']['freeze-a1.json']:
            from od_d1 import baseline
            n='episodes/'+start['id']+'/start.json'
            if t>=timestamp(f['created_at']) or baseline(root)['files'].get(n)!=sha((canonical(start)+'\n').encode()): raise Stop('start outside D1 parent boundary')
        else:
            from od_d1 import d1_gate
            if t<=d1_gate(root): raise Stop('start predates D1 attestation')
