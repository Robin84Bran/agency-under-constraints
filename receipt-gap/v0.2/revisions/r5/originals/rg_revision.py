"""Saved-byte dispositions and immutable r2/r3 STOP clearance. No dispatch."""
import argparse
import os
from pathlib import Path
from rg_core import ROOT, sha, strict_envelope, strict_load
from rg_usage_limit import refusal, dns_nonstart, network_failure, make_pause, verified_pause


def classify_r2(raw):
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


def classify(raw):
    if dns_nonstart(raw):
        return {'class':'DEFINITE NON-START','reason':'Claude programme ruling: ENOTFOUND with zero API duration, usage and cost, empty modelUsage'}
    if network_failure(raw):
        return {'class':'GENUINE TRANSPORT UNCERTAINTY','reason':'episode transport failure; no resend; pause after three consecutive'}
    try:
        e = strict_load(raw['stdout'])
        if (e.get('is_error') is True and type(e.get('api_error_status')) is int
                and e['api_error_status'] == 400):
            from rg_collect import usage
            if usage(e,'claude') == (0,0):
                return {'class':'UNKNOWN','reason':'saved API 400 request rejection; DNS/429 non-start rulings do not cover this response; programme ruling required',
                        'api_error_status':400,'result':e.get('result')}
    except (ValueError, KeyError, TypeError, AttributeError):
        pass
    return classify_r2(raw)


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
        result=classify_r2(read(source))
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
    if freeze_file=='freeze-r3.json':
        return r3_cleared(root, base)
    if freeze_file!='freeze-r2.json' or not (base/'clearance-r2.json').exists():return False
    from rg_freeze import verify
    record=strict_load((base/'clearance-r2.json').read_text())
    verify_prefixes(root)
    return (record.get('cleared') is True and record.get('status')=='PASS'
            and record.get('freeze_sha256')==verify(root,freeze_file)
            and record.get('stop_sha256')==sha((base/'STOP.json').read_bytes())
            and record.get('disposition',{}).get('class')=='MODEL-CAUSED'
            and record['disposition']==classify_r2(strict_load((root/'fixtures/stopped-claude-raw.json').read_text())))


def clearance_r3(root):
    """Append a recognition, prepare an isolated resume, retain every stopped byte."""
    from rg_collect import lock, read, save, syncdir, now, Stop, Ledger
    from rg_freeze import verify
    from rg_core import reserve, render
    root=Path(root);base=root/'collection'
    with lock(base):
        digest=verify(root,'freeze-r3.json');verify_prefixes(root)
        target=base/'clearance-r3.json'
        if target.exists():
            if not r3_cleared(root,base):raise Stop('r3 clearance evidence mismatch')
            return read(target)
        source=root/'fixtures/stopped-claude-raw.json';raw=read(source)
        if not dns_nonstart(raw):raise Stop('r3 DNS non-start predicate failed')
        evidence=read(root/'revisions/r2/preservation.json')
        saved=[root/name for name in evidence['files'] if name.endswith('.raw.json') and '/dispatches/' not in name]
        if len(saved)!=1 or saved[0].read_bytes()!=source.read_bytes():raise Stop('stopped raw binding mismatch')
        d=saved[0].parent;terminal=read(d/'episode.json');ep=terminal['episode']
        request=read(d/'0.request.json');start=read(d/'0.start.json');call=start['id']
        if terminal['attempted_calls']!=1 or request['prompt']!=render(ep,[],10,'action') or request['reservation']!=reserve(request['prompt'],'action',ep['toolkit']):
            raise Stop('unsupported stopped episode or changed request')
        # Fixed overlay, with original dispatch 0 and exact original request.
        resume=base/'resumes/r3/episodes'/ep['id']
        for name, src in [('0.request.json',d/'0.request.json'),('dispatches/0/0/raw.json',saved[0]),('dispatches/0/0/start.json',d/'0.start.json')]:
            dest=resume/name;data=src.read_bytes();dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if dest.read_bytes()!=data:raise Stop('resume evidence conflict')
            else:
                with dest.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
                syncdir(dest.parent)
        attempt=resume/'dispatches/0/0'
        if not (attempt/'pause.json').exists():
            save(attempt/'pause.json',make_pause(raw,start,resume/'0.request.json',attempt,now()))
        verified_pause(attempt,resume/'0.request.json')
        ledger=Ledger(base/'ledger.jsonl');held=request['reservation']['micro_usd']
        if ledger.calls.get(call)!=0 or ep['id'] in ledger.finished:raise Stop('stopped call lacks zero settlement or episode is finished')
        # r1 recorded the zero settlement without its later programme disposition.
        if call not in ledger.nonstarts:
            ledger.event(event='recognize-nonstart',id=call,episode=ep['id'],reserved=held)
        record={'time':now(),'status':'PASS','cleared':True,'freeze_sha256':digest,
                'stop_sha256':sha((base/'STOP.json').read_bytes()),'disposition':classify(raw),
                'episode':ep['id'],'call':call,'reserved':held,'identical_request_sha256':sha((resume/'0.request.json').read_bytes()),
                'resume_files':{str(p.relative_to(resume)):sha(p.read_bytes()) for p in resume.rglob('*') if p.is_file()},
                'authority':'Claude delegating reviewer programme ruling; builder makes no model calls'}
        save(target,record)
        return record


def r3_cleared(root, base):
    from rg_freeze import verify
    from rg_usage_limit import episode_directory
    from rg_collect import Ledger
    root=Path(root);base=Path(base);path=base/'clearance-r3.json'
    if not path.exists():return False
    r=strict_load(path.read_text());verify_prefixes(root)
    if (r.get('status')!='PASS' or r.get('cleared') is not True
            or r.get('freeze_sha256')!=verify(root,'freeze-r3.json')
            or r.get('stop_sha256')!=sha((base/'STOP.json').read_bytes())
            or r.get('disposition')!=classify(strict_load((root/'fixtures/stopped-claude-raw.json').read_text()))
            or r['disposition']['class']!='DEFINITE NON-START'):
        return False
    d=episode_directory(base,r['episode']);verified_pause(d/'dispatches/0/0',d/'0.request.json')
    return (r['identical_request_sha256']==sha((d/'0.request.json').read_bytes())
            and Ledger(base/'ledger.jsonl').nonstarts.get(r['call'])==(r['episode'],r['reserved']))


def verify_r4_preservation(root):
    """Retain all stopped evidence and append-only ledger prefixes."""
    root=Path(root); evidence=strict_load((root/'revisions/r4/preservation.json').read_text())
    for name,digest in evidence['parents'].items():
        if sha((root/name).read_bytes())!=digest:
            raise ValueError('r4 parent freeze changed: '+name)
    prefixes=evidence['prefixes']
    for name,digest in evidence['files'].items():
        if name in prefixes:
            e=prefixes[name];data=(root/e['snapshot']).read_bytes()
            if len(data)!=e['bytes'] or sha(data)!=e['sha256'] or (root/name).read_bytes()[:len(data)]!=data:
                raise ValueError('r4 journal prefix changed: '+name)
        elif sha((root/name).read_bytes())!=digest:
            raise ValueError('r4 stopped evidence changed: '+name)
    return evidence


def clearance_r4(root):
    """Record the actual 400 boundary without claiming a DNS clearance."""
    from rg_collect import lock, read, save, now, Stop
    from rg_freeze import verify
    root=Path(root);base=root/'collection'
    with lock(base):
        digest=verify(root,'freeze-r4.json');verify_r4_preservation(root)
        source=root/'fixtures/stopped-r3-claude-raw.json'
        d=base/'resumes/r3/episodes/claude-s00-notification-r50-check'
        if source.read_bytes()!=(d/'dispatches/0/1/raw.json').read_bytes():
            raise Stop('r4 stopped raw binding mismatch')
        result=classify(read(source))
        if result['class']!='UNKNOWN':raise Stop('r4 requires a new explicit programme ruling')
        record={'time':now(),'status':'UNKNOWN','cleared':False,'freeze_sha256':digest,
                'stop_sha256':sha((base/'STOP-r3.json').read_bytes()),'disposition':result,
                'raw_sha256':sha(source.read_bytes()),
                'identical_request_sha256':sha((d/'0.request.json').read_bytes()),
                'authority':'Claude delegating reviewer DNS/429 ruling; no ruling supplied for API 400',
                'reason':'DNS dispatch 0 was cleared and resent; STOP-r3 belongs to schema-rejected dispatch 1. No resend or ledger change.'}
        target=base/'clearance-r4.json'
        if target.exists():
            previous=read(target)
            if {k:v for k,v in previous.items() if k!='time'}!={k:v for k,v in record.items() if k!='time'}:
                raise Stop('r4 clearance binding mismatch')
            return previous
        save(target,record)
        return record


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['diagnose','diagnose-r4','clear','clear-r3','clear-r4'])
    p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    from rg_core import canonical
    result=clearance_r4(a.root) if a.command=='clear-r4' else clearance_r3(a.root) if a.command=='clear-r3' else clearance(a.root) if a.command=='clear' else classify(strict_load((a.root/('fixtures/stopped-r3-claude-raw.json' if a.command=='diagnose-r4' else 'fixtures/stopped-claude-raw.json')).read_text()))
    print(canonical(result))
    if a.command in ('clear','clear-r3','clear-r4') and not result['cleared']:raise SystemExit(2)

if __name__=='__main__':main()
