"""D3 accounting-only deviation. All operations are local and create-once."""
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from od_core import ROOT,MODEL,sha,render,reserve,padded,strict_load
from od_io import Stop,read,save,now,lock,Ledger,ActiveTime
from od_usage import prefix_snapshot,verify_prefixes
from od_provenance import timestamp

PARENTS=('freeze.json','freeze-a1.json','freeze-d1.json','freeze-d1-final.json','freeze-d2.json')
D3_CHANGED=frozenset(('od_validation.py','od_collect.py','od_analysis.py','od_freeze.py','od_provenance.py','od_io.py','od_usage.py','RUN.md','PROJECT_STATE.md','DEVIATIONS.md','tests/test_d2.py'))
STOP_NAME='STOP-after-envelope-clearance.json'
CLEARANCE='accounting-stop-clearance.json'
RESERVE=1000000
FRONTIER=25000000
PROJECT=39000000


def verify_model_counters(m):
    """Thinking is a subset of output, and cache TTL counts partition creation."""
    for k in ('inputTokens','cacheReadInputTokens','cacheCreationInputTokens','outputTokens'):
        if type(m.get(k)) is not int or m[k]<0: raise Stop('invalid attributed usage')
    if 'thinkingTokens' in m and (type(m['thinkingTokens']) is not int or not 0<=m['thinkingTokens']<=m['outputTokens']): raise Stop('invalid thinking subset')
    ttl=('cacheCreationEphemeral5mInputTokens','cacheCreationEphemeral1hInputTokens')
    if any(k in m for k in ttl):
        if any(type(m.get(k)) is not int or m[k]<0 for k in ttl) or sum(m[k] for k in ttl)!=m['cacheCreationInputTokens']: raise Stop('cache creation TTL mismatch')


def budget_usage(e):
    """Narrow cumulative recovery; other aggregate/model conflicts remain fatal."""
    if not (e.get('type')=='result' and e.get('is_error') is True and e.get('subtype')=='error_max_budget_usd' and e.get('terminal_reason')=='budget_exhausted'): return None
    u=e.get('usage',{})
    if any(type(u.get(k)) is not int or u[k]!=0 for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens','output_tokens')): return None
    mu=e.get('modelUsage')
    if type(mu) is not dict or set(mu)!={MODEL} or type(mu[MODEL]) is not dict: return None
    m=mu[MODEL]
    try:
        verify_model_counters(m)
        a,b=Decimal(str(e['total_cost_usd'])),Decimal(str(m['costUSD']))
        if not a.is_finite() or not b.is_finite() or a<=0 or abs(a-b)>Decimal('0.000000001'): return None
        if m.get('canonicalModel',MODEL)!=MODEL: return None
    except (Stop,KeyError,ValueError,ArithmeticError): return None
    return [m[k] for k in ('inputTokens','cacheReadInputTokens','cacheCreationInputTokens','outputTokens')]


def accounting_event(u,bound):
    from od_validation import cost
    actual=cost(u)
    flags={'cost':actual>bound['micro_usd'],'input':sum(u[k] for k in ('input','cache_read','cache_creation'))>bound['input_tokens'],'output':u['output']>bound['output_tokens']}
    return {'kind':'reservation exceeded; accounting event','actual_micro_usd':actual,'reservation':bound,'exceeded':flags} if any(flags.values()) else None


def measured_bound(prompt,usages):
    """Retain original floors; round token margins up to 64, cost to a microdollar."""
    from od_validation import cost
    b=reserve(prompt)
    if not usages: return b
    i=max(b['input_tokens'],padded(max(sum(u[k] for k in ('input','cache_read','cache_creation')) for u in usages)))
    o=max(b['output_tokens'],padded(max(u['output'] for u in usages)))
    c=max(b['micro_usd'],4*i+20*o,(max(cost(u) for u in usages)*11+9)//10)
    return {'input_tokens':i,'output_tokens':o,'micro_usd':c}


def prior_usages(base,before=None):
    """Only earlier settled attempts can influence a reservation (no look-ahead)."""
    from od_validation import accounting
    result=[]
    for e in Ledger(Path(base)/'ledger.jsonl').log.events:
        if e['event']=='reserve' and e['id']==before: break
        if e['event']!='settle': continue
        ident,sep,index=e['id'].partition('@usage-resume-')
        p=Path(base)/'episodes'/ident
        if sep:p=p/'usage-resumes'/index
        u=accounting(read(p/'raw.json'),'claude',d3=True)
        if u is None: raise Stop('D3 measured accounting UNKNOWN')
        result.append(u)
    return result


def dispatch_bound(base,prompt,before=None): return measured_bound(prompt,prior_usages(base,before))


def cap_check(exposure,reservations=0):
    total=exposure+reservations+RESERVE
    if total>FRONTIER or total>PROJECT: raise Stop('frontier/project envelope exceeded')
    return total


def forecast(root,base):
    from od_usage import episode_state
    ledger=Ledger(Path(base)/'ledger.jsonl');usages=prior_usages(base)
    pending=[e for e in read(Path(root)/'config/episodes.json') if e['actor']=='claude' and episode_state(base,e['id'])[0] is None]
    remaining=sum(measured_bound(render(e),usages)['micro_usd'] for e in pending)
    total=cap_check(ledger.exposure,remaining)
    return {'settled_micro_usd':ledger.spent,'open_holds_micro_usd':sum(ledger.holds.values()),'remaining_calls':len(pending),'remaining_reservations_micro_usd':remaining,'protected_reserve_micro_usd':RESERVE,'total_micro_usd':total,'frontier_envelope_micro_usd':FRONTIER,'project_stop_micro_usd':PROJECT}


@lru_cache(maxsize=4)
def baseline_bytes(path,digest):
    data=Path(path).read_bytes()
    if sha(data)!=digest: raise Stop('D3 baseline changed')
    return strict_load(data)


def baseline(root):
    root=Path(root);p=root/'evidence/d3-baseline.json';f=root/'freeze-d3.json'
    return baseline_bytes(str(p.resolve()),read(f)['files']['evidence/d3-baseline.json']) if f.exists() else read(p)


def verify_baseline(root):
    base=Path(root)/'collection';b=baseline(root);verify_prefixes(base,b['prefixes'])
    for n,h in b['files'].items():
        p=base/n
        if p.is_symlink() or not p.resolve().is_relative_to(base.resolve()) or sha(p.read_bytes())!=h: raise Stop('D3 baseline evidence changed: '+n)
    Ledger(base/'ledger.jsonl')
    for name,cap in (('local',28800),('claude',7200)):
        if ActiveTime(base/(name+'-time.jsonl'),cap).breaches: raise Stop('D3 timer breach')


def lineage(root,f):
    root=Path(root)
    if set(f['parents'])!=set(PARENTS) or f['revision']!='D3' or set(f['changed_originals'])!=D3_CHANGED: raise Stop('D3 lineage/scope mismatch')
    for n,h in f['parents'].items():
        if (root/n).is_symlink() or sha((root/n).read_bytes())!=h: raise Stop('D3 parent freeze mismatch: '+n)
    parent=read(root/'freeze-d2.json')
    from od_d2 import lineage as parent_lineage
    parent_lineage(root,parent)
    for n,h in parent['files'].items():
        expected='deviations/d3/parent-d2/'+n if n in D3_CHANGED else n
        if f['files'].get(expected)!=h: raise Stop('D3 forbidden science/evidence change: '+n)
    inherited=set(parent)-{'revision','kind','created_at','files','parents','changed_originals'}
    if any(f.get(k)!=parent[k] for k in inherited): raise Stop('D3 metadata drift')
    if timestamp(f['created_at'])<=timestamp(parent['created_at']): raise Stop('D3 chronology mismatch')


def verify_d3(root):
    from od_freeze import inputs
    root=Path(root);p=root/'freeze-d3.json';f=read(p);lineage(root,f)
    if p.is_symlink() or set(f['files'])!=set(inputs(root)): raise Stop('D3 input set drift')
    for n,h in f['files'].items():
        p=root/n
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or sha(p.read_bytes())!=h: raise Stop('D3 frozen input changed: '+n)
    return sha((root/'freeze-d3.json').read_bytes())


def freeze_d3(root=ROOT):
    from od_freeze import inputs
    root=Path(root);parent=read(root/'freeze-d2.json')
    f=dict(parent,revision='D3',kind='harness-only accounting settlement/reservation deviation; no model calls',created_at=now(),changed_originals=sorted(D3_CHANGED),parents={n:sha((root/n).read_bytes()) for n in PARENTS},files={n:sha((root/n).read_bytes()) for n in inputs(root)})
    lineage(root,f);verify_baseline(root);forecast(root,root/'collection')
    save(root/'freeze-d3.json',f);return verify_d3(root)


def clearance_valid(base):
    base=Path(base);p=base/CLEARANCE
    if not p.exists() or {p.name for p in base.glob('STOP*.json')}!={'STOP.json',STOP_NAME}: return False
    c=read(p);root=base.parent;b=baseline(root)
    if c['freeze_sha256']!=sha((root/'freeze-d3.json').read_bytes()): raise Stop('D3 clearance freeze mismatch')
    if c['prefixes']!=b['prefixes']: raise Stop('D3 clearance prefix binding mismatch')
    verify_prefixes(base,c['prefixes'])
    names={'STOP.json',STOP_NAME,'envelope-stop-clearance.json'}|{b['target']+'/'+n for n in ('request.json','start.json','raw.json','episode.json')}
    if set(c['evidence'])!=names: raise Stop('D3 clearance evidence set mismatch')
    for n,h in c['evidence'].items():
        if n not in b['files'] or h!=b['files'][n] or sha((base/n).read_bytes())!=h: raise Stop('D3 clearance evidence mismatch')
    if c['path']!=b['target']: raise Stop('D3 clearance target mismatch')
    p=base/b['target']
    decoded=decode_reply(read(p/'raw.json'),read(p/'request.json')['reservation'])
    if c['decoded']!=decoded or c['accounting_event']!=accounting_event(decoded['usage'],read(p/'request.json')['reservation']): raise Stop('D3 clearance disposition mismatch')
    for p in (base/'episodes').rglob('episode.json'):
        if p.relative_to(base).as_posix() not in b['files'] and read(p).get('fatal'): return False
    cap_check(Ledger(base/'ledger.jsonl').exposure)
    for name,cap in (('local',28800),('claude',7200)):
        if ActiveTime(base/(name+'-time.jsonl'),cap).breaches: raise Stop('D3 clearance timer breach')
    return True


def decode_reply(raw,bound):
    from od_validation import validate,accounting,ReplyFailure
    try:return validate(raw,'claude',bound,d3=True)
    except ReplyFailure as exc:return {'fleet':None,'schema_valid':False,'status':'REPLY_FAILURE','reason':str(exc),'usage':accounting(raw,'claude',d3=True)}


def recovered_terminal(root,base,p):
    """Only the exact bound historical terminal is superseded for scoring."""
    base=Path(base);p=Path(p)
    if not (base/CLEARANCE).exists(): return None
    c=read(base/CLEARANCE)
    if p.relative_to(base).as_posix()!=c['path']: return None
    b=baseline(root)
    for n in ('request.json','start.json','raw.json','episode.json'):
        q=p/n;key=q.relative_to(base).as_posix()
        if sha(q.read_bytes())!=b['files'].get(key): raise Stop('D3 recovery bytes changed')
    if not clearance_valid(base): raise Stop('D3 accounting clearance invalid')
    return c['decoded']


def clear_accounting_stop(root=ROOT):
    root=Path(root);h=verify_d3(root);base=root/'collection'
    with lock(base):
        verify_baseline(root)
        if clearance_valid(base): return read(base/CLEARANCE)
        if (base/CLEARANCE).exists(): raise Stop('D3 cannot unlock a later STOP')
        if {p.name for p in base.glob('STOP*.json')}!={'STOP.json',STOP_NAME}: raise Stop('D3 STOP set mismatch')
        from od_analysis import replay
        replay(root,base) # Verify historical disposition before superseding it.
        b=baseline(root);p=base/b['target'];terminal=read(p/'episode.json')
        if read(base/STOP_NAME)['reason']!=terminal.get('fatal') or terminal.get('fatal')!='frontier reservation/accounting overrun': raise Stop('D3 STOP/terminal mismatch')
        from od_validation import accounting,cost,validate,ReplyFailure
        raw=read(p/'raw.json');bound=read(p/'request.json')['reservation'];u=accounting(raw,'claude',d3=True)
        if u is None or accounting_event(u,bound) is None: raise Stop('D3 requires measured overrun')
        ledger=Ledger(base/'ledger.jsonl')
        if ledger.settlements.get(p.name)!=cost(u) or ledger.reservations.get(p.name)!=bound['micro_usd']: raise Stop('D3 actual settlement mismatch')
        if set(ledger.reservations)!=set(ledger.settlements): raise Stop('D3 unresolved holds')
        try: decoded=validate(raw,'claude',bound,d3=True)
        except ReplyFailure as exc: decoded={'fleet':None,'schema_valid':False,'status':'REPLY_FAILURE','reason':str(exc),'usage':u}
        # Integrity errors deliberately propagate and cannot be cleared.
        names=['STOP.json',STOP_NAME,'envelope-stop-clearance.json']+[b['target']+'/'+n for n in ('request.json','start.json','raw.json','episode.json')]
        c={'kind':'D3 accounting STOP clearance; actual settled, reply retained','time':now(),'freeze_sha256':h,'path':b['target'],'evidence':{n:b['files'][n] for n in names},'prefixes':prefix_snapshot(base),'decoded':decoded,'accounting_event':accounting_event(u,bound),'forecast':forecast(root,base)}
        save(base/CLEARANCE,c);return c


def attest_d3(root=ROOT):
    root=Path(root);h=verify_d3(root);base=root/'collection'
    with lock(base):
        verify_baseline(root)
        if not clearance_valid(base): raise Stop('D3 requires recorded accounting clearance')
        from od_provenance import parent_receipt_gate
        parent_receipt_gate(root)
        from od_analysis import replay
        replay(root,base)
        p=base/'d3-attestation.json'
        if p.exists(): d3_gate(root);return read(p)
        a={'kind':'local D3 attestation; original push retained','freeze_sha256':h,'parents':read(root/'freeze-d3.json')['parents'],'parent_attestation_sha256':sha((base/'d2-attestation.json').read_bytes()),'parent_push_sha256':sha((base/'push.json').read_bytes()),'clearance_sha256':sha((base/CLEARANCE).read_bytes()),'prefixes':prefix_snapshot(base),'attested_at':now()}
        save(p,a);return a


def d3_gate(root):
    root=Path(root);base=root/'collection';a=read(base/'d3-attestation.json');f=read(root/'freeze-d3.json')
    if a['freeze_sha256']!=sha((root/'freeze-d3.json').read_bytes()) or a['parents']!=f['parents'] or a['parent_attestation_sha256']!=sha((base/'d2-attestation.json').read_bytes()) or a['parent_push_sha256']!=sha((base/'push.json').read_bytes()) or a['clearance_sha256']!=sha((base/CLEARANCE).read_bytes()): raise Stop('D3 attestation binding mismatch')
    if timestamp(a['attested_at'])<=timestamp(f['created_at']): raise Stop('D3 attestation predates freeze')
    verify_prefixes(base,a['prefixes']);verify_baseline(root)
    if not clearance_valid(base): raise Stop('D3 clearance invalid')
    forecast(root,base)
    return timestamp(a['attested_at'])
