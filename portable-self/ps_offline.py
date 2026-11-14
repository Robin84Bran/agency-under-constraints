"""Fake transports with synthetic, labeled envelopes; no providers or credentials."""
from pathlib import Path
import json
from ps_core import World, DIRECTIONS, canonical, sha
from ps_io import read, save
from ps_transport import MODEL

class Fake:
    def __init__(self,turns=2,mode='literal',mutate=None):
        self.turns=turns;self.mode=mode;self.mutate=mutate;self.calls=0
    def request(self,ep,prompt,phase,bound,index):
        from ps_transport import local_request, claude_command, clean_env, CLAUDE_BIN
        self.ep=ep;self.index=index
        if ep['actor']=='claude':
            return {'argv':claude_command(CLAUDE_BIN,phase,bound['micro_usd']),'stdin':prompt,
                    'environment_controls':{k:v for k,v in clean_env().items() if k not in ('HOME','PATH','TMPDIR','LANG','USER','LOGNAME','SHELL')}}
        return local_request(ep,prompt,index)
    def generate(self,request,work):
        self.calls+=1;prompt=request.get('stdin',request.get('prompt'));payload=json.loads(prompt.split('\n',1)[1]);phase=payload['mode']
        if phase=='write':
            note=' '.join(f'{k}={d}' for k,d in payload['calibration'])
            value={'slot':payload['writable_slot'] or 1,'note':note}
        else:
            from ps_core import literal_map
            # This fake deliberately uses only the currently visible first nonempty note.
            mapping=next((literal_map(m['note']) for m in payload['memory'] if literal_map(m['note'])),None)
            value={'controls':[next((k for k,v in mapping.items() if v==d),None) if mapping else None for d in payload['targets']]}
        if self.mode=='null' and phase=='act': value={'controls':[None]*4}
        if self.ep['actor']=='claude':
            e={'type':'result','subtype':'success','is_error':False,'num_turns':self.turns,'stop_reason':'tool_use' if self.turns==2 else 'end_turn',
               'structured_output':value,'modelUsage':{MODEL:{'inputTokens':100,'outputTokens':30,'cacheReadInputTokens':3,'cacheCreationInputTokens':2,'webSearchRequests':0}},
               'usage':{'input_tokens':100,'cache_creation_input_tokens':2,'cache_read_input_tokens':3,'output_tokens':30},'total_cost_usd':.00102}
        else:
            from ps_core import PINS
            e={'model':PINS[self.ep['actor']][0],'done':True,'done_reason':'stop','prompt_eval_count':300+len(prompt)//4,'eval_count':30,'response':canonical(value)}
        raw={'stdout':canonical(e),'stderr':'','returncode':0}
        if self.mutate: raw=self.mutate(raw,self.ep,self.index)
        return raw


def dry_run(root,output):
    root=Path(root);output=Path(output)
    if output.exists(): raise ValueError('offline output exists; preserve it and choose a new path')
    schedule=read(root/'config/episodes.json');small=[e for e in schedule if e['seed']==0]
    from ps_collect import collect
    local=collect(root,'local',fake_transport=Fake(),output=output,episodes=small)
    frontier=collect(root,'claude',fake_transport=Fake(),output=output,episodes=small)
    from ps_analysis import score, audit_accounting, load_timing
    timing=load_timing(output)
    rows=[score(e,output,True,timing) for e in small]
    report={'kind':'OFFLINE-FAKE','real_model_calls':0,'fake_episodes':len(rows),'fake_calls':sum(r['calls_started'] for r in rows),
            'all_schema_valid':all(r['technical_complete'] for r in rows),'local':local,'frontier':frontier,
            'accounting':audit_accounting(output,rows),'scores':[{k:r[k] for k in ('id','Y','F','nulls','technical_missing')} for r in rows]}
    save(output/'verification.json',report)
    return report
