"""Network-free integration run. Fake transports are never production CLI options."""
import argparse
from pathlib import Path
from rg_core import ACTORS, PINS, canonical, strict_load
from rg_collect import ActiveTime, Ledger, read, run_episode, save
from rg_analysis import score, replay, summarize


class Fake:
    def __init__(self, kind='normal'):
        self.kind, self.calls = kind, 0

    def generate(self, ep, prompt, phase, budget, work):
        self.calls += 1
        p=strict_load(prompt)
        if phase=='report':
            value={'all_done':None,'any_duplicate':None}
        else:
            j=len(p['history'])+1
            value={'op':'send','job':j,'key':('k'+str(j)) if ep['toolkit']=='keyed' else None} if j<=4 else {'op':'finish','job':None,'key':None}
        if ep['actor']=='claude':
            e={'type':'result','subtype':'success','is_error':False,'num_turns':1,'stop_reason':'end_turn',
               'structured_output':value,'result':'deliberately ignored prose','modelUsage':{'claude-opus-5-5':{}},
               'usage':{'input_tokens':200,'cache_read_input_tokens':0,'cache_creation_input_tokens':0,'output_tokens':20}}
            if self.kind=='overrun':
                e['usage']['input_tokens']=100000
            if self.kind=='missing_usage':
                del e['usage']['output_tokens']
            if self.kind=='wrong_model':
                e['modelUsage']={'unverified':{}}
            if self.kind=='wrong_effort':
                e['effort']='high'
            if self.kind=='missing_payload':
                del e['structured_output'];e['result']=canonical(value)
            if self.kind=='string_payload':
                e['structured_output']=canonical(value)
        else:
            e={'response':canonical(value),'model':PINS[ep['actor']][0],'done':True,'done_reason':'stop',
               'prompt_eval_count':200,'eval_count':20}
            if self.kind=='truncated':
                e['done_reason']='length'
            if self.kind=='invalid_action':
                e['response']='{"op":"send","job":true,"key":null}'
            if self.kind=='bad_report' and phase=='report':
                e['response']='{}'
        if self.kind=='timeout':
            return {'stdout':'','stderr':'partial timeout evidence','returncode':None,'transport_error':'timeout'}
        return {'stdout':canonical(e),'stderr':'','returncode':0,'fake_transport':True}


def dry_run(root, output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    save(output/'OFFLINE-FAKE.json',{'real_model_calls':0,'notice':'fake transports only'})
    ledger=Ledger(output/'ledger.jsonl');timer=ActiveTime(output/'time.jsonl',100000)
    schedule=read(Path(root)/'config/episodes.json');transport=Fake();results=[]
    for actor in ACTORS:
        for toolkit in ('plain','keyed','check'):
            ep=next(e for e in schedule if e['actor']==actor and e['toolkit']==toolkit and e['receipt_loss']==.5)
            saved=run_episode(ep,transport,output,ledger,timer,'OFFLINE-FAKE',True)
            if replay(ep,saved['events'])[0]!=saved['counts']:
                raise AssertionError('dry-run replay differs')
            results.append(score(ep,saved,True))
    summary={'kind':'OFFLINE FAKE TRANSPORT; NOT MODEL RESULTS','real_model_calls':0,'fake_calls':transport.calls,
             'episodes':len(results),'all_replays_match':True,'fake_accounting_micro_usd':ledger.exposure,
             'outstanding_holds_micro_usd':sum(ledger.holds.values()),'summary':summarize(results,100)}
    save(output/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(canonical(dry_run(Path(__file__).resolve().parent,a.output)))

if __name__=='__main__':
    main()
