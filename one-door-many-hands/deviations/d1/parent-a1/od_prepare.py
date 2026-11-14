"""One-time offline preparation. No inference or network."""
from collections import Counter
from pathlib import Path
from od_core import *
from od_io import save
from od_contract import request
from od_identity import identity


def prepare(root=ROOT):
    root=Path(root);jobs=schedule();identity(root)
    save(root/'config/episodes.json',jobs)
    save(root/'config/prompts.json',{'system':SYSTEM,'instruction':INSTRUCTION,'schema_text':SCHEMA_TEXT,'schema':SCHEMA})
    sizing=[]
    for ep in jobs:
        if ep['actor']!='claude': continue
        prompt=render(ep);bound=reserve(prompt);outer=request(ep,prompt,bound)
        sizing.append({'id':ep['id'],'prompt':prompt,'prompt_bytes':len(prompt.encode()),'prompt_sha256':sha(prompt.encode()),
           'system_bytes':len(SYSTEM.encode()),'schema_bytes':len(SCHEMA_TEXT.encode()),'outer_request':outer,'outer_bytes':len(canonical(outer).encode()),**bound})
    total=sum(r['micro_usd'] for r in sizing)
    if total+1000000>25000000 or total+1000000>=39000000: raise ValueError('full plan exceeds cap')
    save(root/'config/sizing.json',{'status':'CONDITIONAL_EMPIRICAL_RESERVATION','exact_token_counts':None,'cash_billing_usd':None,
       'frontier_micro_usd':total,'protected_reserve_micro_usd':1000000,'including_reserve_micro_usd':total+1000000,
       'basis':'pad(prompt UTF8 bytes + system bytes + schema bytes + historical 826); pad(512); USD4/20 per million; see evidence/cost-basis.json',
       'measurements':sizing})
    table=[];frequencies=Counter()
    for b in range(100):
        for B in (1,6,24):
            for mode in ('common','independent'):
                p=payload({'block':b,'door':B,'mode':mode,'evidence':'rules'})
                rows,best,optimal=oracle(p['target'],p['failure_percent'],B,mode)
                table.append({'block':b,'door':B,'mode':mode,'target':p['target'],'failure_percent':p['failure_percent'],
                  'values':{str(n):{k:fraction(v) if isinstance(v,Fraction) else v for k,v in r.items()} for n,r in rows.items()},'best':fraction(best),'optimal':list(optimal)})
                frequencies[f'{mode}/door{B}/'+','.join(map(str,optimal))]+=1
    save(root/'config/oracle.json',{'cells':table,'optimal_set_frequencies':dict(frequencies)})
    baseline={name:[] for name in ('always1','always6','always24','max_expected_work','min_outage','exact_oracle','all_null')}
    for ep in jobs[:1200]:
        p=payload(ep);rows,best,optimal=oracle(p['target'],p['failure_percent'],ep['door'],ep['mode'])
        for name in baseline:
            if name.startswith('always'): n=int(name[6:])
            elif name=='max_expected_work': n=max(FLEETS,key=lambda n:rows[n]['work'])
            elif name=='min_outage': n=min(FLEETS,key=lambda n:rows[n]['outage'])
            elif name=='exact_oracle': n=optimal[0]
            else: n=None
            baseline[name].append(dict(id=ep['id'],fleet=n,**score(ep,n,True)))
    save(root/'config/baselines.json',{'kind':'CODE_BASELINES_NOT_MODELS','tie_rule':'first ascending fleet for heuristic baseline only; evaluator accepts all exact optima','rows':baseline})
    save(root/'config/design.json',{'revision':'v0.1-r1','local_episodes':3600,'frontier_episodes':120,'bootstrap_replicates':10000,'bootstrap_seed':20261112,
       'runtime_status':'UNKNOWN','input_completeness':'UNKNOWN','rates_status':'HISTORICAL_API_EQUIVALENT','cash_billing_usd':None,
       'local_active_seconds':28800,'claude_active_seconds':7200,'local_timeout_seconds':180,'claude_timeout_seconds':300,
       'dispatch_envelope_micro_usd':25000000,'project_stop_micro_usd':39000000,'absolute_ceiling_micro_usd':40000000})
    return total

if __name__=='__main__': print(prepare())
