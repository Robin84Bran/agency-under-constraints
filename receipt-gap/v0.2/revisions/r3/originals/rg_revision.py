"""Saved-byte-only r2 disposition and immutable STOP clearance. No dispatch."""
import argparse
from pathlib import Path
from rg_core import ROOT, sha, strict_envelope, strict_load
from rg_usage_limit import refusal


def classify(raw):
    if refusal(raw):
        return {'class':'USAGE-LIMIT NON-START', 'reason':'exact zero-usage zero-cost 429 refusal'}
    try:
        e, _ = strict_envelope(raw['stdout'], 'claude')
    except (ValueError, KeyError, TypeError):
        return {'class':'GENUINE TRANSPORT UNCERTAINTY', 'reason':'no parseable envelope or proven non-start'}
    u = e.get('usage', {})
    counters = [u.get(k) for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens','output_tokens')]
    fields = {k:e.get(k) for k in ('is_error','api_error_status','stop_reason','terminal_reason','num_turns','total_cost_usd','result')}
    fields.update(returncode=raw.get('returncode'),usage=u,modelUsage=e.get('modelUsage'))
    if any(type(n) is int and n > 0 for n in counters):
        return {'class':'MODEL-CAUSED','reason':'non-zero saved generation usage','fields':fields}
    return {'class':'UNKNOWN', 'reason':'parseable zero-generation error outside the exact 429 rule; programme ruling required', 'fields':fields}


def verify_prefixes(root):
    root=Path(root)
    evidence=strict_load((root/'revisions/r2/preservation.json').read_text())
    for name, entry in evidence['prefixes'].items():
        prefix=(root/entry['snapshot']).read_bytes()
        if len(prefix)!=entry['bytes'] or sha(prefix)!=entry['sha256'] or (root/name).read_bytes()[:len(prefix)]!=prefix:
            raise ValueError('ledger prefix changed: '+name)
    for name, digest in evidence['files'].items():
        if sha((root/name).read_bytes()) != digest:
            raise ValueError('retained evidence changed: '+name)
    for name,digest in evidence['parents'].items():
        if sha((root/name).read_bytes()) != digest:
            raise ValueError('parent freeze changed')
    return evidence


def clearance(root):
    """Record eligibility without deleting or overwriting the historical STOP."""
    from rg_collect import lock, read, save, now, Stop, decode, Ledger, provider_envelope, usage, cost_micro
    from rg_freeze import verify
    from rg_core import ModelOutputError
    root=Path(root);base=root/'collection'
    with lock(base):
        digest=verify(root,'freeze-r2.json')
        evidence=verify_prefixes(root)
        source=root/'fixtures/stopped-claude-raw.json'
        result=classify(read(source))
        stop_hash=sha((base/'STOP.json').read_bytes())
        record={'time':now(),'freeze_sha256':digest,'stop_sha256':stop_hash,'disposition':result,
                'status':'UNKNOWN','cleared':False,'ledger_prefixes':evidence['prefixes']}
        if result['class']=='MODEL-CAUSED':
            # Verify the source is the stopped call and only a content failure remains.
            saved=[root/name for name in evidence['files'] if name.endswith('.raw.json') and '/dispatches/' not in name]
            if len(saved)!=1 or saved[0].read_bytes()!=source.read_bytes():raise Stop('stopped raw binding mismatch')
            d=saved[0].parent;ep=read(d/'episode.json')['episode'];request=read(d/'0.request.json')
            try:decode(read(source),ep,request['phase'],request['reservation'])
            except ModelOutputError:pass
            else:raise Stop('saved reply is not a model-content failure')
            ledger=Ledger(base/'ledger.jsonl')
            call=read(d/'0.start.json')['id']
            if call not in ledger.calls:raise Stop('saved call lacks known settlement')
            envelope,_=provider_envelope(read(source),'claude');tin,tout=usage(envelope,'claude')
            actual=cost_micro(tin,tout,envelope)
            if actual!=ledger.calls[call] or actual>request['reservation']['micro_usd']:
                raise Stop('resource failure cannot be cleared as model output')
            if ledger.exposure+1000000>25000000:raise Stop('project exposure remains over cap')
            if ep['id'] not in ledger.finished:ledger.event(event='release',id=ep['id'])
            record.update(status='PASS',cleared=True)
        path=base/'clearance-r2.json'
        if path.exists():
            previous=read(path)
            if previous['freeze_sha256']!=digest or previous['stop_sha256']!=stop_hash:raise Stop('clearance binding mismatch')
            return previous
        save(path,record)
        return record


def stop_cleared(root, base, freeze_file):
    """Only a reviewed content failure can bypass the unchanged historical STOP."""
    if freeze_file!='freeze-r2.json' or not (base/'clearance-r2.json').exists():return False
    from rg_freeze import verify
    record=strict_load((base/'clearance-r2.json').read_text())
    verify_prefixes(root)
    return (record.get('cleared') is True and record.get('status')=='PASS'
            and record.get('freeze_sha256')==verify(root,freeze_file)
            and record.get('stop_sha256')==sha((base/'STOP.json').read_bytes())
            and record.get('disposition',{}).get('class')=='MODEL-CAUSED'
            and record['disposition']==classify(strict_load((root/'fixtures/stopped-claude-raw.json').read_text())))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['diagnose','clear'])
    p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    from rg_core import canonical
    result=clearance(a.root) if a.command=='clear' else classify(strict_load((a.root/'fixtures/stopped-claude-raw.json').read_text()))
    print(canonical(result))
    if a.command=='clear' and not result['cleared']:raise SystemExit(2)

if __name__=='__main__':main()
