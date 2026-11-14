"""r5 saved-byte clearance and immutable resume; no provider dispatch."""
import os
from pathlib import Path
from rg_core import ROOT, sha, strict_load, render, reserve
from rg_claude_schema import revised_request
from rg_usage_limit import schema_nonstart, make_pause, verified_pause, episode_directory


def verify_preservation(root):
    root=Path(root);e=strict_load((root/'revisions/r5/preservation.json').read_text())
    for name,digest in e['parents'].items():
        if sha((root/name).read_bytes())!=digest:raise ValueError('r5 parent changed: '+name)
    for name,digest in e['files'].items():
        p=root/name
        if name in e['prefixes']:
            prefix=e['prefixes'][name];data=(root/prefix['snapshot']).read_bytes()
            if len(data)!=prefix['bytes'] or sha(data)!=prefix['sha256'] or not p.read_bytes().startswith(data):
                raise ValueError('r5 journal prefix changed: '+name)
        elif p.is_symlink() or sha(p.read_bytes())!=digest:
            raise ValueError('r5 saved evidence changed: '+name)
    return e


def clearance_r5(root):
    from rg_collect import lock, read, save, now, Stop, Ledger, syncdir
    from rg_freeze import verify
    from rg_revision import classify
    root=Path(root);base=root/'collection'
    with lock(base):
        digest=verify(root,'freeze-r5.json');verify_preservation(root)
        target=base/'clearance-r5.json'
        if target.exists():
            if not r5_cleared(root,base):raise Stop('r5 clearance evidence mismatch')
            return read(target)
        ident='claude-s00-notification-r50-check'
        old=base/'resumes/r3/episodes'/ident
        ep=read(old/'episode.json')['episode'];original=read(old/'0.request.json')
        raw=read(old/'dispatches/0/1/raw.json');start=read(old/'dispatches/0/1/start.json')
        if (not schema_nonstart(raw) or (old/'dispatches/0/1/raw.json').read_bytes()!=(root/'fixtures/stopped-r3-claude-raw.json').read_bytes()
                or original['prompt']!=render(ep,[],10,'action')
                or original['reservation']!=reserve(original['prompt'],'action',ep['toolkit'])):
            raise Stop('r5 stopped request binding mismatch')
        resume=base/'resumes/r5/episodes'/ident
        sources=[('0.rejected-request.json',old/'0.request.json')]
        sources += [(str(p.relative_to(old)),p) for p in (old/'dispatches').rglob('*') if p.is_file()]
        for name,p in sources:
            dest=resume/name;data=p.read_bytes();dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if dest.read_bytes()!=data:raise Stop('r5 resume evidence conflict')
            else:
                with dest.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
                syncdir(dest.parent)
        request=revised_request(original,ep['toolkit'])
        if (resume/'0.request.json').exists():
            if read(resume/'0.request.json')!=request:raise Stop('r5 corrected request changed')
        else:save(resume/'0.request.json',request)
        attempt=resume/'dispatches/0/1'
        if not (attempt/'pause.json').exists():
            save(attempt/'pause.json',make_pause(raw,start,resume/'0.rejected-request.json',attempt,now()))
        for i in ('0','1'):verified_pause(resume/'dispatches/0'/i,resume/'0.request.json')
        ledger=Ledger(base/'ledger.jsonl');call=start['id'];held=original['reservation']['micro_usd']
        if ledger.calls.get(call)!=0 or ident in ledger.finished:raise Stop('r5 lacks zero settlement or is terminal in ledger')
        if call not in ledger.nonstarts:ledger.event(event='recognize-nonstart',id=call,episode=ident,reserved=held)
        record={'time':now(),'status':'PASS','cleared':True,'freeze_sha256':digest,
                'stop_sha256':sha((base/'STOP-r3.json').read_bytes()),
                'original_stop_sha256':sha((base/'STOP.json').read_bytes()),
                'raw_sha256':sha((old/'dispatches/0/1/raw.json').read_bytes()),
                'disposition':classify(raw),'episode':ident,'call':call,'reserved':held,
                'identical_prompt_sha256':sha(original['prompt'].encode()),
                'rejected_request_sha256':sha((resume/'0.rejected-request.json').read_bytes()),
                'corrected_request_sha256':sha((resume/'0.request.json').read_bytes()),
                'resume_files':{str(p.relative_to(resume)):sha(p.read_bytes()) for p in resume.rglob('*') if p.is_file()},
                'authority':'Claude delegating reviewer r5 ruling; builder makes no model calls',
                'resume':'resend identical prompt with corrected provider schema; restore reservation only at dispatch'}
        save(target,record);return record


def r5_cleared(root,base):
    from rg_collect import Ledger
    from rg_freeze import verify
    from rg_revision import classify
    root=Path(root);base=Path(base);p=base/'clearance-r5.json'
    if not p.exists():return False
    r=strict_load(p.read_text())
    if (r.get('status')!='PASS' or r.get('cleared') is not True
            or r.get('freeze_sha256')!=verify(root,'freeze-r5.json')
            or r.get('stop_sha256')!=sha((base/'STOP-r3.json').read_bytes())
            or r.get('original_stop_sha256')!=sha((base/'STOP.json').read_bytes())):return False
    d=episode_directory(base,r['episode']);original=strict_load((d/'0.rejected-request.json').read_text())
    old=base/'resumes/r3/episodes'/r['episode']
    if (d/'0.rejected-request.json').read_bytes()!=(old/'0.request.json').read_bytes():return False
    for source in (old/'dispatches').rglob('*'):
        if source.is_file() and (d/source.relative_to(old)).read_bytes()!=source.read_bytes():return False
    current=strict_load((d/'0.request.json').read_text());raw=strict_load((d/'dispatches/0/1/raw.json').read_text())
    for i in ('0','1'):verified_pause(d/'dispatches/0'/i,d/'0.request.json')
    return (r['call']==strict_load((d/'dispatches/0/1/start.json').read_text())['id']
            and r['raw_sha256']==sha((root/'fixtures/stopped-r3-claude-raw.json').read_bytes())
            and current==revised_request(original,'check')
            and r['identical_prompt_sha256']==sha(current['prompt'].encode())
            and r['rejected_request_sha256']==sha((d/'0.rejected-request.json').read_bytes())
            and r['corrected_request_sha256']==sha((d/'0.request.json').read_bytes())
            and r['raw_sha256']==sha((d/'dispatches/0/1/raw.json').read_bytes())
            and r['disposition']==classify(raw) and r['disposition']['class']=='HARNESS NON-START'
            and Ledger(base/'ledger.jsonl').nonstarts.get(r['call'])==(r['episode'],r['reserved']))


if __name__=='__main__':
    import argparse
    from rg_core import canonical
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args()
    print(canonical(clearance_r5(a.root)))
