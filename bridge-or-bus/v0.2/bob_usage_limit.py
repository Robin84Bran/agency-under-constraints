"""Saved-byte proof of a Claude subscription non-start; no provider operations."""
import datetime as dt
from bob_paths import collection_dir
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from bob_core import canonical,sha,strict_load
from bob_collect import Stop,read,save,save_bytes,now,usage

COUNTERS=('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens')
REFUSAL=re.compile(r"You've hit your [^\n]+ limit · resets ([^\n]+)")


def definite_nonstart(env):
    if type(env) is not dict or env.get('api_error_status')!=429 or type(env.get('api_error_status')) is not int or env.get('is_error') is not True:
        return False
    u=env.get('usage')
    if type(u) is not dict or any(type(u.get(k)) is not int or u[k]!=0 for k in COUNTERS):return False
    if type(env.get('total_cost_usd')) not in (int,float) or env['total_cost_usd']!=0:return False
    if type(env.get('result')) is not str or REFUSAL.fullmatch(env['result']) is None:return False
    if 'structured_output' in env or env.get('permission_denials'):return False
    # Contradictory extra token/tool/activity evidence must keep frozen handling.
    def zero_activity(value):
        if type(value) is dict:return all(zero_activity(v) for k,v in value.items() if type(v) in (dict,list) or 'token' in k.lower() or type(v) in (int,float,bool) or k in ('server_tool_use','webSearchRequests','requested','completed','background','foreground'))
        if type(value) is list:return all(zero_activity(x) for x in value)
        return type(value) in (int,float) and value==0
    return all(zero_activity(env.get(k,{})) for k in ('usage','modelUsage','subagent_stats')) and all(env.get(k,0)==0 for k in ('queued_turn_count','safety_stops'))


def reset_time(env, recorded):
    """Resolve the CLI's local clock against refusal date; never guess an unknown format."""
    match=re.fullmatch(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm) \(([^)]+)\)',REFUSAL.fullmatch(env['result'])[1],re.I)
    if not match:return None
    try:
        hour,minute=int(match[1]),int(match[2] or 0)
        if not 1<=hour<=12 or not 0<=minute<60:return None
        local=dt.datetime.fromisoformat(recorded).astimezone(ZoneInfo(match[4]))
        reset=local.replace(hour=hour%12+(12 if match[3].lower()=='pm' else 0),minute=minute,second=0,microsecond=0)
        if reset<=local:reset+=dt.timedelta(days=1)
        return reset.astimezone(dt.timezone.utc).isoformat()
    except (ValueError,KeyError):return None


def prefix(path):
    p=Path(path);raw=p.read_bytes() if p.exists() else b''
    return dict(bytes=len(raw),sha256=sha(raw))


def verify_prefix(path,record):
    raw=Path(path).read_bytes() if Path(path).exists() else b''
    if len(raw)<record['bytes'] or sha(raw[:record['bytes']])!=record['sha256']:
        raise Stop('usage-limit ledger prefix changed')


def records(root):
    root=Path(root);out=[]
    for path in sorted((collection_dir(root)/'usage-limits').glob('*.json')):
        r=read(path);ident=path.stem
        if r['id']!=ident or r['event']!='usage-limit pause' or r['disposition']!='DEFINITE_NONSTART':raise Stop('invalid usage-limit record')
        raw=(path.parent/f'{ident}.stdout').read_bytes();stderr=(path.parent/f'{ident}.stderr').read_bytes()
        env=strict_load(raw)
        if not definite_nonstart(env) or env!=r['envelope'] or sha(raw)!=r['response_sha256'] or sha(stderr)!=r['stderr_sha256']:
            raise Stop('usage-limit refusal evidence changed')
        if r['usage']!=usage(env,'claude') or r['episode']['model']!='claude' or r['episode_id']!=r['episode']['id']:
            raise Stop('usage-limit accounting/actor mismatch')
        cid=r['call_id'];directory=collection_dir(root)
        if sha((directory/'requests'/f'{cid}.json').read_bytes())!=r['request_sha256'] or sha((directory/'starts'/f'{cid}.json').read_bytes())!=r['start_sha256']:
            raise Stop('usage-limit request/start changed')
        for name,rec in r['ledger_prefixes'].items():verify_prefix(directory/name,rec)
        if r['resume_after_utc']!=reset_time(env,r['time']):raise Stop('usage-limit reset changed')
        cost=[strict_load(x) for x in (directory/'cost.jsonl').read_bytes().splitlines()]
        if not any(e['event']=='settle' and e['id']==ident and e['episode']==r['episode']['id'] and e['slot']==r['slot'] and e['actual']==0 for e in cost):raise Stop('usage-limit zero settlement missing')
        out.append(r)
    return out


def pending(root,freeze_hash):
    """Only a complete, proven pause can explain an otherwise incomplete episode."""
    root=Path(root);directory=collection_dir(root);all_records=records(root);out={}
    for r in all_records:
        ident=r['episode']['id']
        if (directory/'episodes'/f'{ident}.json').exists():continue
        if ident not in out or r['attempt']>out[ident]['attempt']:out[ident]=r
    for ident,r in out.items():
        if r['freeze_sha256']!=freeze_hash:raise Stop('usage-limit freeze changed')
        snapshot=r['snapshot'];ep=r['episode']
        if snapshot['episode']!=ep or snapshot['calls']!=r['prior_calls']:raise Stop('usage-limit snapshot identity mismatch')
        from bob_audit import audit_episode
        if snapshot['calls']:
            audit_episode(root,ep,snapshot,freeze_hash)
            if any(read(directory/'calls'/f'{cid}.json')['error'] is not None for cid in snapshot['calls']):
                raise Stop('usage-limit cannot resume after generation failure')
        elif snapshot['events'] or snapshot['report'] is not None:raise Stop('unbacked usage-limit history')
        from bob_analysis import replay
        from bob_core import render,P,subholds
        truth=replay(ep,snapshot['events']);phase='report' if truth['ended'] else 'action'
        expected_cid=f"{ident}-{phase}-{len(snapshot['calls'])}"
        call_start=read(directory/'starts'/f"{r['call_id']}.json")
        prompt=render(ep,truth['history'],6-truth['decisions'],phase)
        expected_slot=6 if phase=='report' else len(snapshot['calls'])
        request=(directory/'requests'/f"{r['call_id']}.json").read_bytes()
        if r['call_id']!=expected_cid or r['slot']!=expected_slot or call_start['freeze_sha256']!=freeze_hash or call_start['request_sha256']!=sha(request) or call_start['prompt_sha256']!=sha(prompt.encode()) or call_start['reservation']!=subholds(ep)[expected_slot] or request!=canonical(dict(prompt=prompt,system=P['system'])).encode():
            raise Stop('usage-limit saved call/history mismatch')
        start=read(directory/'episode-starts'/f'{ident}.json')
        if start['episode']!=ep or start['freeze_sha256']!=freeze_hash:raise Stop('usage-limit episode start mismatch')
        if (directory/'calls'/f"{r['call_id']}.json").exists() or (directory/'usage-limit-resumes'/f"{r['id']}.json").exists():
            raise Stop('uncertain dispatch after usage-limit clearance; never resend')
    return out


def pause(root,ep,cid,slot,attempt,result,env,ledger,timer,snapshot,freeze_hash):
    root=Path(root);directory=collection_dir(root);ident=f'{cid}-usage-limit-{attempt:04d}';folder=directory/'usage-limits'
    save_bytes(folder/f'{ident}.stdout',result['stdout']);save_bytes(folder/f'{ident}.stderr',result['stderr'])
    ledger.event(event='settle',id=ident,episode=ep['id'],slot=slot,actual=0)
    stamp=now()
    record=dict(event='usage-limit pause',disposition='DEFINITE_NONSTART',id=ident,call_id=cid,episode_id=ep['id'],episode=ep,slot=slot,attempt=attempt,
                time=stamp,resume_after_utc=reset_time(env,stamp),freeze_sha256=freeze_hash,envelope=env,returncode=result['returncode'],
                response_sha256=sha(result['stdout']),stderr_sha256=sha(result['stderr']),usage=usage(env,'claude'),
                request_sha256=sha((directory/'requests'/f'{cid}.json').read_bytes()),start_sha256=sha((directory/'starts'/f'{cid}.json').read_bytes()),
                snapshot=snapshot,prior_calls=snapshot['calls'],ledger_prefixes={name:prefix(directory/name) for name in ('cost.jsonl',timer.path.name)})
    save(folder/f'{ident}.json',record)
    return dict(status='PAUSED',reason='usage-limit pause',episode_id=ep['id'],call_id=cid,resume_after_utc=record['resume_after_utc'])


def ready(record):
    return record['resume_after_utc'] is not None and dt.datetime.fromisoformat(now())>=dt.datetime.fromisoformat(record['resume_after_utc'])


def resume(root,record,ledger,amount):
    if not ready(record):raise Stop('usage-limit reset not reached/UNKNOWN')
    directory=collection_dir(Path(root))
    # Create-once clearance precedes rearming. A crash here remains conservative.
    save(directory/'usage-limit-resumes'/f"{record['id']}.json",dict(event='usage-limit clearance',time=now(),refusal_id=record['id'],
         request_sha256=record['request_sha256'],ledger_prefix=prefix(directory/'cost.jsonl'),reason='saved definite non-start; stated reset reached'))
    ledger.event(event='rearm',id=record['id'],episode=record['episode']['id'],slot=record['slot'],amount=amount)
