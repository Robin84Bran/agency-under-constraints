"""Offline provenance/accounting checks. No provider or collector imports."""
from decimal import Decimal, ROUND_CEILING
from bob_paths import collection_dir,prior_path
from pathlib import Path

from bob_core import P,PINS,canonical,sha,strict_load,render,action,report,subholds,SCHEMAS
from bob_analysis import replay
from bob_validation import envelope,claude_contract


def read(path):
    return strict_load(Path(path).read_bytes())


def audit_episode(root,ep,saved,freeze_hash):
    directory=collection_dir(Path(root))
    if (Path(root)/'freeze-r3.json').exists() and ep['model']!='claude':
        freeze_hash=sha((Path(root)/'freeze-r2.json').read_bytes())
    calls=saved['calls']
    if not 1<=len(calls)<=7 or len(set(calls))!=len(calls):
        raise ValueError('invalid episode call sequence')
    events=saved['events']
    used=0
    history=[]
    observed_report=None
    for i,cid in enumerate(calls):
        if cid!=ep['id']+'-'+('report' if '-report-' in cid else 'action')+'-'+str(i):
            raise ValueError('call identifier/order mismatch')
        start=read(directory/'starts'/f'{cid}.json')
        receipt=read(directory/'calls'/f'{cid}.json')
        reqraw=(directory/'requests'/f'{cid}.json').read_bytes()
        request=strict_load(reqraw)
        phase=start['phase']
        truth=replay(ep,events[:used])
        expected_phase='report' if truth['ended'] else 'action'
        if phase!=expected_phase or start['episode_id']!=ep['id'] or receipt['episode_id']!=ep['id'] or receipt['id']!=cid or start['id']!=cid:
            raise ValueError('call phase/identity mismatch')
        if start['freeze_sha256']!=freeze_hash or start['request_sha256']!=sha(reqraw):
            raise ValueError('call freeze/request mismatch')
        if ep['model']=='claude':
            from bob_claude_schema import CLAUDE_SCHEMAS
            from bob_collect import claude_command
            argv=start.get('candidate_claude_argv')
            if (start.get('schema_sha256')!=sha(canonical(CLAUDE_SCHEMAS[phase]).encode()) or
                not argv or argv!=claude_command(argv[0],phase,start['reservation']['micro_usd'])):
                raise ValueError('Claude schema/argv mismatch')
        prompt=render(ep,history,6-used,phase)
        if start['prompt_sha256']!=sha(prompt.encode()) or request.get('prompt')!=prompt:
            raise ValueError('realized prompt/history mismatch')
        expected_request=dict(prompt=prompt)
        if ep['model']=='claude':
            expected_request['system']=P['system']
        if ep['model']!='claude':
            expected_request.update(model=PINS[ep['model']][0],system=P['system'],stream=False,format=SCHEMAS[phase],options=dict(temperature=.6,top_k=16,num_predict=192,num_ctx=8192,seed=ep['seed']))
        if request!=expected_request:
            raise ValueError('realized request/settings mismatch')
        slot=6 if phase=='report' else i
        if start['slot']!=slot or receipt['slot']!=slot or start['reservation']!=subholds(ep)[slot]:
            raise ValueError('call reservation mismatch')
        raw_path=directory/'raw'/f'{cid}.stdout'
        if receipt['response_sha256'] is not None:
            raw=raw_path.read_bytes()
            if sha(raw)!=receipt['response_sha256']:
                raise ValueError('raw stdout hash mismatch')
            try:
                env,problem=envelope(raw)
            except (ValueError,UnicodeError):
                if receipt['error'] is None or receipt['envelope'] is not None:
                    raise ValueError('invalid raw envelope without saved parse failure')
                env=None
            if env!=receipt['envelope']:
                raise ValueError('saved envelope differs from raw')
        else:
            env=None
        if receipt['stderr_sha256'] is not None and sha((directory/'raw'/f'{cid}.stderr').read_bytes())!=receipt['stderr_sha256']:
            raise ValueError('raw stderr hash mismatch')
        if receipt['error'] is None:
            if receipt['returncode']!=0 or type(env) is not dict:
                raise ValueError('invalid successful call')
            if ep['model']=='claude':
                if claude_contract(env) is not None:
                    raise ValueError('Claude rejected model content recorded as success')
                v=env.get('structured_output')
            else:
                if env.get('model')!=PINS[ep['model']][0] or env.get('done') is not True or env.get('done_reason')!='stop':
                    raise ValueError('local identity/stop mismatch')
                v=strict_load(env['response'])
            value=action(v,ep['arm']) if phase=='action' else report(v)
            if receipt['parsed']!=value:
                raise ValueError('parsed response differs from raw')
            if phase=='action':
                if used>=len(events) or value!=events[used]['action']:
                    raise ValueError('event not backed by model output')
                if events[used]['observation'] is not None:
                    history.append(events[used])
                used+=1
            else:
                observed_report=value
        elif i!=len(calls)-1:
            raise ValueError('generation continued after failure')
        if phase=='report' and i!=len(calls)-1:
            raise ValueError('call after report')
        stats=receipt['usage']
        if stats is not None and type(env) is dict:
            if ep['model']=='claude':
                if type(env.get('usage')) is not dict:
                    raise ValueError('saved usage without raw usage')
                for k in ('input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens'):
                    if stats[k]!=env['usage'].get(k) or type(stats[k]) is not int or stats[k]<0:
                        raise ValueError('usage differs from raw')
                raw_cost=env.get('total_cost_usd')
                if type(raw_cost) not in (int,float):
                    raise ValueError('missing raw dollar cost')
                actual=int((Decimal(str(raw_cost))*1000000).to_integral_value(rounding=ROUND_CEILING))
                api=4*sum(env['usage'][k] for k in ('input_tokens','cache_creation_input_tokens','cache_read_input_tokens'))+20*env['usage']['output_tokens']
                if stats['micro_usd']!=max(actual,api):
                    raise ValueError('saved dollar cost differs from raw')
            else:
                if stats['micro_usd']!=0 or stats['input_tokens']!=env.get('prompt_eval_count') or stats['output_tokens']!=env.get('eval_count'):
                    raise ValueError('local usage differs from raw')
    if used!=len(events) or observed_report!=saved.get('report'):
        raise ValueError('unbacked event/report')
    return dict(calls=len(calls),events=used)


def reconcile_ledger(root,records):
    directory=collection_dir(Path(root))
    path=directory/'cost.jsonl'
    if not path.exists():
        if records:
            raise ValueError('saved episodes without ledger')
        return dict(status='UNKNOWN',spent_micro_usd=None,held_micro_usd=None,reason='collection unstarted')
    raw=path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise ValueError('torn ledger')
    from bob_usage_limit import records as usage_records
    refusals={r['id']:r for r in usage_records(root)}
    originals={};rearmed=set();settlement_slots={}
    holds={}; spent=0; prior_held=0; carried=False; settled={}; finished=set(); stopped=False
    for line in raw.splitlines():
        e=strict_load(line); op=e['event']; ident=e['id']
        if op=='carry':
            prior=read(prior_path(root))
            if carried or holds or settled or spent or e['spent']!=prior['settled_micro_usd'] or e['held']!=prior['unresolved_hold_micro_usd'] or e['ledger_sha256']!=prior['ledger_sha256']:
                raise ValueError('invalid historical exposure carry')
            spent=e['spent'];prior_held=e['held'];carried=True
        elif op=='reserve':
            if ident in holds or len(e['subholds'])!=7 or any(type(v) is not int or v<0 for v in e['subholds']):
                raise ValueError('bad reservation')
            if stopped or spent+prior_held+sum(sum(v.values()) for v in holds.values())+sum(e['subholds'])+2000000>25000000:
                raise ValueError('admission after stop/over cap')
            originals[ident]=list(e['subholds'])
            holds[ident]={str(i):v for i,v in enumerate(e['subholds'])}
        elif op=='settle':
            episode=e['episode']; slot=str(e['slot']); actual=e['actual']
            if ident in settled or episode not in holds or slot not in holds[episode] or episode in finished or type(actual) is not int or actual<0:
                raise ValueError('invalid settlement')
            receipt=refusals[ident] if ident in refusals else read(directory/'calls'/f'{ident}.json')
            if receipt['usage'] is None or receipt['usage']['micro_usd']!=actual or receipt['episode_id']!=episode or receipt['slot']!=e['slot']:
                raise ValueError('settlement not backed by saved usage')
            held=holds[episode].pop(slot)
            spent+=actual; settled[ident]=actual;settlement_slots[ident]=(episode,slot)
            stopped |= actual>held
        elif op=='rearm':
            episode,slot=e['episode'],str(e['slot'])
            if ident not in refusals or ident in rearmed or settled.get(ident)!=0 or settlement_slots.get(ident)!=(episode,slot) or episode in finished or episode not in holds or slot in holds[episode] or e['amount']!=originals[episode][int(slot)] or stopped:
                raise ValueError('invalid usage-limit rearm')
            clearance=read(directory/'usage-limit-resumes'/f'{ident}.json')
            from bob_usage_limit import verify_prefix
            verify_prefix(path,clearance['ledger_prefix'])
            if clearance['refusal_id']!=ident or clearance['request_sha256']!=refusals[ident]['request_sha256'] or clearance['time']<refusals[ident]['resume_after_utc']:
                raise ValueError('invalid usage-limit clearance')
            if spent+prior_held+sum(sum(v.values()) for v in holds.values())+e['amount']+2000000>25000000:
                raise ValueError('usage-limit rearm over cap')
            holds[episode][slot]=e['amount'];rearmed.add(ident)
        elif op=='release':
            if ident not in records or ident not in holds or ident in finished:
                raise ValueError('release without known terminal evidence')
            if records[ident]['episode']['model']=='claude' and any(c not in settled for c in records[ident]['calls']):
                raise ValueError('unresolved paid call reservation released')
            holds[ident]={}; finished.add(ident)
        elif op=='stop':
            stopped=True
        else:
            raise ValueError('unknown ledger operation')
    held=prior_held+sum(sum(v.values()) for v in holds.values())
    return dict(status='PASS' if not held and not stopped else 'UNKNOWN',spent_micro_usd=spent,held_micro_usd=held,exposure_micro_usd=spent+held,protected_micro_usd=2000000,stopped=stopped,reason=None if not held and not stopped else 'outstanding hold or durable stop')
