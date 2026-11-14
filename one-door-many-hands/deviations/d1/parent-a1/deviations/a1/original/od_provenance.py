"""Network-free GitHub activity receipt validation."""
import datetime as dt
import re
from pathlib import Path
from od_core import sha
from od_io import read,Stop
REPOSITORY='Robin84Bran/research'


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


def receipt_gate(root):
    root=Path(root);a=read(root/'collection/push.json');source=(root/'collection/push-event.json').read_bytes();event=read(root/'collection/push-event.json')
    ref,s=push_record(event,a['commit'])
    f=read(root/'freeze.json')
    if a['freeze_sha256']!=sha((root/'freeze.json').read_bytes()) or a['repo']!=REPOSITORY or a['source_api']!='/repos/'+REPOSITORY+'/activity' or a['event_sha256']!=sha(source) or a['pushed_at']!=s or a['remote_ref']!=ref or a['server_event_id']!=event['id']: raise Stop('push receipt binding mismatch')
    if timestamp(s)<=timestamp(f['created_at']): raise Stop('push must follow freeze')
    return timestamp(s)
