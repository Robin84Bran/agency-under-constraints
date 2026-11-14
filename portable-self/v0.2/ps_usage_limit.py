"""Immutable non-start attempts, reset gating and operational-only replay."""
import datetime as dt
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from ps_core import sha
from ps_io import Stop, read, save, now
from ps_transport import usage_limit_refusal, provider_envelope


def reset_time(raw,started_at):
    message=provider_envelope(raw['stdout'],'claude')[0]['result']
    match=re.search(r'resets (\d{1,2}(?::\d{2})?[ap]m) \(([^)]+)\)$',message)
    if not match: return None
    try:
        zone=ZoneInfo(match[2]);began=dt.datetime.fromisoformat(started_at).astimezone(zone)
        clock=dt.datetime.strptime(match[1],'%I:%M%p' if ':' in match[1] else '%I%p')
        reset=began.replace(hour=clock.hour,minute=clock.minute,second=0,microsecond=0)
        if reset<=began: reset+=dt.timedelta(days=1)
        return reset.astimezone(dt.timezone.utc).isoformat()
    except (ValueError,ZoneInfoNotFoundError): return None


def prefix_for(index,attempt=0):
    return str(index) if attempt==0 else f'{index}-attempt-{attempt}'


def check_pause(directory,prefix):
    path=directory/f'{prefix}.pause.json';pause=read(path)
    for kind in ('request','start','raw'):
        if sha((directory/f'{prefix}.{kind}.json').read_bytes())!=pause[kind+'_sha256']:
            raise Stop('usage-limit attempt evidence changed')
    raw=read(directory/f'{prefix}.raw.json');start=read(directory/f'{prefix}.start.json')
    if start['request_sha256']!=pause['request_sha256']: raise Stop('non-start request binding changed')
    if (directory/f'{prefix}.event.json').exists(): raise Stop('non-start cannot have an applied event')
    if not usage_limit_refusal(raw) or start['id']!=pause['id'] or pause['reset_at']!=reset_time(raw,start['started_at']):
        raise Stop('invalid usage-limit pause')
    if pause['disposition']!='DEFINITE_NON_START' or pause['actual_micro_usd']!=0: raise Stop('invalid non-start disposition')
    return pause


def call_location(directory,index):
    """Return current attempt; every earlier attempt must be a proven non-start."""
    directory=Path(directory);attempt=0;pauses=[];original=directory/f'{index}.request.json'
    while True:
        prefix=prefix_for(index,attempt)
        request=directory/f'{prefix}.request.json'
        if attempt and request.exists() and request.read_bytes()!=original.read_bytes():
            raise Stop('usage-limit retry changed request bytes')
        if not (directory/f'{prefix}.pause.json').exists(): return prefix,pauses
        pauses.append(check_pause(directory,prefix));attempt+=1


def record_pause(directory,prefix,ledger,timer,began=None):
    raw=read(directory/f'{prefix}.raw.json');start=read(directory/f'{prefix}.start.json');ident=start['id']
    if not usage_limit_refusal(raw): raise Stop('cannot pause ambiguous call')
    if ident not in ledger.started or ledger.started[ident]['episode']!=directory.name: raise Stop('non-start lacks matching allocation')
    if start['request_sha256']!=sha((directory/f'{prefix}.request.json').read_bytes()): raise Stop('non-start request binding changed')
    if sha(ledger.journal.raw[:start['ledger_prefix_bytes']])!=start['ledger_prefix_sha256']: raise Stop('non-start prefix changed')
    if (directory/f'{prefix}.event.json').exists(): raise Stop('non-start has applied output')
    if ident not in timer.holds: raise Stop('non-start active-time allocation missing')
    if ident not in ledger.settled: ledger.event(event='settle',id=ident,actual=0)
    if ledger.settled[ident]!=0: raise Stop('nonzero refusal settlement')
    if began is not None: timer.end(ident,began)
    elif ident not in timer.settled:
        # Saved zero-generation bytes prove non-start. Keep the entire crash-time
        # reservation charged; never replenish the frozen active-time allowance.
        timer.journal.append({'event':'settle','id':ident,'seconds':timer.holds[ident],
                              'reason':'usage-limit non-start recovery; conservative time hold retained'})
        timer.settled[ident]=timer.holds[ident]
    path=directory/f'{prefix}.pause.json'
    if not path.exists():
        save(path,{'id':ident,'disposition':'DEFINITE_NON_START','event':'usage-limit pause','actual_micro_usd':0,
             'reset_at':reset_time(raw,start['started_at']),'recorded_at':now(),
             **{kind+'_sha256':sha((directory/f'{prefix}.{kind}.json').read_bytes()) for kind in ('request','start','raw')}})
    check_pause(directory,prefix)
    if ident not in ledger.usage_pauses:
        ledger.event(event='usage-limit-pause',id=ident,pause_file=str(path.relative_to(directory.parent.parent)),pause_sha256=sha(path.read_bytes()))
    return read(path)


def recover_pauses(base,ledger,timer):
    """Finish a crash-interrupted pause solely from saved definite refusal bytes."""
    for path in sorted((Path(base)/'episodes').glob('*/*.raw.json')):
        prefix=path.name.removesuffix('.raw.json');directory=path.parent
        # Terminals belong to the original frozen handling and require explicit
        # evidence-based re-disposition. This project has no historical Claude calls.
        if (directory/'episode.json').exists(): continue
        startpath=directory/f'{prefix}.start.json'
        if not startpath.exists(): continue
        ident=read(startpath)['id']
        if ident in ledger.usage_pauses: continue
        if usage_limit_refusal(read(path)): record_pause(directory,prefix,ledger,timer)


def pause_ready(pause):
    # Unknown reset syntax remains a clean pause; never guess that a reset passed.
    return pause['reset_at'] is not None and dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat(pause['reset_at'])


def audit_pauses(base,ledger):
    base=Path(base);events=[]
    for ident,event in ledger.usage_pauses.items():
        rel=Path(event['pause_file'])
        if rel.is_absolute() or '..' in rel.parts: raise Stop('invalid pause evidence path')
        path=base/rel
        if sha(path.read_bytes())!=event['pause_sha256']: raise Stop('pause ledger binding changed')
        prefix=path.name.removesuffix('.pause.json');pause=check_pause(path.parent,prefix)
        if pause['id']!=ident or ledger.settled.get(ident)!=0: raise Stop('pause accounting mismatch')
        start=read(path.parent/f'{prefix}.start.json')
        if ledger.started[ident]['episode']!=path.parent.name or start['id']!=ident: raise Stop('non-start episode allocation changed')
        if sha(ledger.journal.raw[:start['ledger_prefix_bytes']])!=start['ledger_prefix_sha256']: raise Stop('non-start prefix changed')
        events.append({'id':ident,'event':'usage-limit pause','disposition':'DEFINITE_NON_START','actual_micro_usd':0,'reset_at':pause['reset_at']})
    if {p for p in (base/'episodes').glob('*/*.pause.json')}!={base/e['pause_file'] for e in ledger.usage_pauses.values()}:
        raise Stop('unregistered usage-limit pause')
    return events
