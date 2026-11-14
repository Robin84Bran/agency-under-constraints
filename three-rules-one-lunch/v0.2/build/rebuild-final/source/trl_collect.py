"""Serial local-only collector. Durable first responses, no generated retries."""
import argparse
from pathlib import Path
import time
import uuid
from trl_core import ROOT, Simulator, render, roles, generation_seed, canonical, sha, strict_load
from trl_io import Stop, lock, now, read, save
from trl_budget import ActiveTime, maximum
from trl_validation import validate, usage, stdout, LocalTransportFailure
from trl_transport import request, Local, Fake, raw_record, non_start
from trl_journal import Journal, prefix


class OperationalPause(Stop):
    pass


def planned(root=ROOT):
    return read(Path(root)/'config/episodes.json')


from trl_replay import disposition, expected, inspect


def episode(ep,transport,base,journal,timer,freeze_hash,run_id):
    if ep['actor']=='claude': raise Stop('Claude v0.1 is reused, never rerun')
    d=Path(base)/'episodes'/ep['id']
    if d.exists():
        if (d/'episode.json').exists(): raise Stop('terminal episode never rerun')
        sim,calls,next_,used=inspect(ep,d)
        if next_ is None or not next_[-1]: raise Stop('partial episode has no proven non-start; never resend')
    else:
        d.mkdir(parents=True);sim=Simulator(ep['seed']);calls=[];next_=(1,roles(ep['regime'])[0],{},[],1,False)
    started_at=read(d/'begin.json')['time'] if (d/'begin.json').exists() else now()
    if not (d/'begin.json').exists(): save(d/'begin.json',{'episode':ep,'time':started_at,'run_id':run_id})
    r0,j0,buffered,prior_slots,attempt0,_=next_
    error=None;classification=None
    for r in range(r0,5):
        values=dict(buffered) if r==r0 else {};slots=list(prior_slots) if r==r0 else []
        for role in roles(ep['regime']):
            if r==r0 and role<j0: continue
            quota=3 if role==0 else 1;key=f'r{r}-j{role}'
            attempt=attempt0 if (r,role)==(r0,j0) else 1
            ident=expected(ep,r,role)+f'-attempt-{attempt:04}'
            p=d/'calls'/key/f'{attempt:04}'
            prompt=render(ep['regime'],r,role,sim.receipts)
            req=request(ep['actor'],prompt,quota,generation_seed(ep['seed'],r,role))
            timer.admit(180)
            save(p/'request.json',{'id':expected(ep,r,role),'round':r,'role':role,'quota':quota,'request':req,
                'prompt_sha256':sha(prompt.encode()),'request_sha256':sha(canonical(req).encode())})
            save(p/'start.json',{'id':ident,'logical_call_id':expected(ep,r,role),'started_at':now(),
                'freeze_sha256':freeze_hash,'run_id':run_id,'kind':'FAKE' if isinstance(transport,Fake) else 'MODEL'})
            journal.event(event='start',id=ident,episode=ep['id'],request_sha256=sha((p/'request.json').read_bytes()),
                path=p.relative_to(base).as_posix(),freeze_sha256=freeze_hash,kind='FAKE' if isinstance(transport,Fake) else 'MODEL',start_sha256=sha((p/'start.json').read_bytes()))
            began=time.monotonic()
            try: raw=transport.generate(ep['actor'],req,p)
            except Exception as exc: raw=raw_record(stderr=str(exc).encode(),returncode=None,transport_error=type(exc).__name__)
            save(p/'raw.json',raw)
            parsed=disposition(raw,ep,quota)
            parsed.update(id=ident,round=r,role=role,elapsed_seconds=time.monotonic()-began,finished_at=now())
            save(p/'parsed.json',parsed);calls.append(parsed)
            journal.event(event='finish',id=ident,classification=parsed['classification'],
                raw_sha256=sha((p/'raw.json').read_bytes()),parsed_sha256=sha((p/'parsed.json').read_bytes()))
            if parsed['classification']=='DEFINITE_NON_START':
                save(p/'pause.json',{'classification':'DEFINITE_NON_START','reason':parsed['non_start'],
                    'model_outcome':'UNKNOWN','request_sha256':sha((p/'request.json').read_bytes()),'time':now()})
                raise OperationalPause(parsed['non_start']+' non-start; exact request preserved, no model penalty')
            slots.extend((1,2,3) if role==0 else (role,))
            error=parsed['error'];classification=parsed['classification']
            if error: break
            values[role]=parsed['value']
        if error:
            sim.terminate(error,slots);break
        sim.execute(ep['regime'],values);save(d/f'round-{r}.json',sim.events[-3:])
    result={'episode':ep,'kind':'FAKE' if isinstance(transport,Fake) else 'MODEL','started_at':started_at,
        'finished_at':now(),'complete':error is None,'error':error,'classification':classification,
        'fatal':classification=='INTEGRITY_FAILURE','events':sim.events,'receipts':sim.receipts,
        'attempted_calls':sum(c['classification']!='DEFINITE_NON_START' for c in calls),
        'non_start_attempts':sum(c['classification']=='DEFINITE_NON_START' for c in calls),'run_id':run_id}
    save(d/'episode.json',result)
    if result['fatal']:
        save(Path(base)/'STOP.json',{'reason':error,'time':now(),'episode':ep['id']});raise Stop(error)
    return result


from trl_audit import evidence_gate


def collect(root):
    from trl_freeze import push_gate
    root=Path(root);digest=push_gate(root)
    base=root/'collection'
    with lock(base/'collector.lock'):
        if push_gate(root)!=digest: raise Stop('freeze changed before admission')
        journal=evidence_gate(root);timer=ActiveTime(base/'time-local.jsonl',43200)
        run=str(uuid.uuid4());timer.begin(run)
        journal.event(event='checkpoint',id=run+'-begin',ledger='collection/time-local.jsonl',prefix=prefix(base/'time-local.jsonl'))
        transport=Local();actor=None;streak=0
        try:
            for ep in planned(root):
                if (base/'episodes'/ep['id']/'episode.json').exists(): continue
                if ep['actor']!=actor:
                    actor=ep['actor'];save(base/'runtime'/(actor+'-'+run+'.json'),transport.preflight(actor))
                result=episode(ep,transport,base,journal,timer,digest,run)
                streak=streak+1 if result['classification']=='TRANSPORT_FAILURE' else 0
                if streak==3:
                    save(base/('STOP-transport-'+run+'.json'),{'reason':'three consecutive transport failures',
                        'run_id':run,'time':now()});raise Stop('durable transport pause; no automatic continuation')
        finally:
            timer.end()
            journal.event(event='checkpoint',id=run+'-end',ledger='collection/time-local.jsonl',prefix=prefix(base/'time-local.jsonl'))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--cohort',choices=['local'],required=True);a=p.parse_args()
    collect(a.root)

if __name__=='__main__': main()
