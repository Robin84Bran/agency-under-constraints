"""Offline raw replay, no providers, credentials or network imports."""
from pathlib import Path
from trl_core import PINS, Simulator, render, roles, generation_seed, canonical, sha, strict_load
from trl_io import Stop, read
from trl_budget import maximum
from trl_validation import validate, usage, stdout, LocalTransportFailure
from trl_contract import request, non_start

def disposition(raw,ep,quota):
    ns=non_start(raw)
    if ns:
        return {'value':None,'error':None,'usage':None,'classification':'DEFINITE_NON_START','non_start':ns}
    u=None
    try: u=usage(strict_load(stdout(raw)),ep['actor'])
    except (ValueError,KeyError,TypeError,UnicodeError): pass
    try:
        value,env,u=validate(raw,ep['actor'],quota,maximum(ep['regime']))
        return {'value':value,'error':None,'usage':u,'classification':'VALID','non_start':None}
    except LocalTransportFailure as exc:
        cls='TRANSPORT_FAILURE';message=str(exc)
    except (ValueError,KeyError,TypeError,UnicodeError) as exc:
        cls='MODEL_CAUSED';message=str(exc)
    except Stop as exc:
        cls='INTEGRITY_FAILURE';message=str(exc)
        try: env=strict_load(stdout(raw))
        except (ValueError,KeyError,TypeError,UnicodeError): env=None
        if (message=='running model evidence UNKNOWN' and type(env) is dict and
            env.get('model')==PINS[ep['actor']][0] and env.get('done') is not True):
            cls='TRANSPORT_FAILURE';message='local incomplete envelope/transport evidence UNKNOWN; no resend'
    return {'value':None,'error':message,'usage':u,'classification':cls,'non_start':None}


def expected(ep,r,role):
    return ep['id']+f'-r{r}-j{role}'


def inspect(ep,directory):
    """Independent raw replay, also used for safe continuation after proven non-starts."""
    directory=Path(directory);sim=Simulator(ep['seed']);calls=[];used=set();resume=False
    for r in range(1,5):
        values={};slots=[]
        for role in roles(ep['regime']):
            quota=3 if role==0 else 1
            key=f'r{r}-j{role}';folder=directory/'calls'/key
            attempts=sorted(folder.glob('[0-9][0-9][0-9][0-9]'))
            if [p.name for p in attempts]!=[f'{n:04}' for n in range(1,len(attempts)+1)]:
                raise Stop('non-contiguous attempt inventory')
            prompt=render(ep['regime'],r,role,sim.receipts)
            req=request(ep['actor'],prompt,quota,generation_seed(ep['seed'],r,role))
            last=None
            for i,p in enumerate(attempts):
                used.add(p)
                if not all((p/n).exists() for n in ('request.json','start.json','raw.json','parsed.json')):
                    raise Stop('partial/uncertain start; never resend')
                saved=read(p/'request.json');start=read(p/'start.json');parsed=read(p/'parsed.json')
                if (saved!={'id':expected(ep,r,role),'round':r,'role':role,'quota':quota,'request':req,
                    'prompt_sha256':sha(prompt.encode()),'request_sha256':sha(canonical(req).encode())} or
                    start['logical_call_id']!=expected(ep,r,role) or start['id']!=expected(ep,r,role)+f'-attempt-{i+1:04}'):
                    raise Stop('saved request/identity/history drift')
                last=disposition(read(p/'raw.json'),ep,quota)
                if any(parsed.get(k)!=v for k,v in last.items()): raise Stop('saved parse differs from raw')
                if type(parsed.get('elapsed_seconds')) not in (int,float) or parsed['elapsed_seconds']<0:
                    raise Stop('invalid elapsed time')
                if start.get('kind') not in ('FAKE','MODEL'): raise Stop('saved evidence kind missing')
                if 'kind' in parsed: raise Stop('parsed model kind is defined by durable start')
                calls.append(dict(parsed,evidence_kind=start['kind']))
                if i<len(attempts)-1 and last['classification']!='DEFINITE_NON_START':
                    raise Stop('attempt after model reply/uncertain start')
            if not attempts or last['classification']=='DEFINITE_NON_START':
                resume=bool(attempts)
                return sim,calls,(r,role,values,slots,len(attempts)+1,resume),used
            slots.extend((1,2,3) if role==0 else (role,))
            if last['error']:
                sim.terminate(last['error'],slots)
                return sim,calls,None,used
            values[role]=last['value']
        sim.execute(ep['regime'],values)
        rp=directory/f'round-{r}.json'
        if not rp.exists() or read(rp)!=sim.events[-3:]:
            raise Stop('saved completed round missing/differs from code truth')
    return sim,calls,None,used

