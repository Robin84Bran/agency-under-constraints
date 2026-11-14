"""Fake transports only. No production fake flag and no provider initialization."""
import argparse
from pathlib import Path
from uc_core import ROOT,ACTORS,PINS,canonical,strict_load,baseline_action
from uc_transport import local_request,claude_command
from uc_store import Ledger,ActiveTime,save,read
from uc_collect import run_episode
from uc_analysis import analyze


class Fake:
    def __init__(self,actor,kind='normal',policy='highest-feasible'):
        self.actor,self.kind,self.policy=actor,kind,policy;self.calls=0;self.current=None

    def request(self,ep,prompt,phase,decision,bound):
        self.current=(ep,prompt,phase,decision)
        if ep['actor']=='claude':
            return dict(stdin=prompt,argv=claude_command('FAKE-CLAUDE',phase,bound['micro_usd']),environment={})
        return local_request(ep,prompt,phase,decision)

    def generate(self,request,work):
        self.calls+=1
        ep,prompt,phase,decision=self.current;p=strict_load(prompt)
        if phase=='action':
            value=baseline_action(self.policy,p['history'])
        else:
            delivered='none'
            for h in p['history']:
                if h['action']['op']=='deliver' and h['observation']['code']=='OK':delivered=h['action']['tier']
            value={'delivered':delivered}
        if ep['actor']=='claude':
            e=dict(type='result',subtype='success',is_error=False,num_turns=2,stop_reason='tool_use',structured_output=value,
                result='ignored; must never be parsed',modelUsage={'claude-opus-5-5':{}},total_cost_usd=.001,
                usage=dict(input_tokens=200,cache_creation_input_tokens=10,cache_read_input_tokens=5,output_tokens=20))
            if self.kind=='one_turn':e.update(num_turns=1,stop_reason='end_turn')
            if self.kind=='missing_payload':del e['structured_output'];e['result']=canonical(value)
            if self.kind=='string_payload':e['structured_output']=canonical(value)
            if self.kind=='missing_usage':del e['usage']['output_tokens']
            if self.kind=='missing_cost':del e['total_cost_usd']
            if self.kind=='wrong_model':e['modelUsage']={'other':{}}
            if self.kind=='wrong_effort':e['effort']='high'
            if self.kind=='bad_turns':e['num_turns']=3
            if self.kind=='overrun':e['usage']['input_tokens']=100000
            if self.kind=='cost_overrun':e['total_cost_usd']=45
            if self.kind=='length':e['stop_reason']='max_tokens'
            if self.kind=='tools':e['tool_calls']=[{'name':'Bash'}]
            if self.kind=='invalid_action' and phase=='action':e['structured_output']={}
            if self.kind=='bad_report' and phase=='report':e['structured_output']={}
        else:
            e=dict(model=PINS[ep['actor']][0],done=True,done_reason='stop',prompt_eval_count=200,eval_count=20,response=canonical(value))
            if self.kind=='length':e['done_reason']='length'
            if self.kind=='missing_eval':del e['eval_count']
            if self.kind=='not_done':e['done']=False
            if self.kind=='wrong_model':e['model']='other'
            if self.kind=='overrun':e['eval_count']=193
            if self.kind=='input_loss':e['input_truncated']=True
            if self.kind=='invalid_action' and phase=='action':e['response']='{}'
            if self.kind=='duplicate_action' and phase=='action':e['response']='{"op":"read","op":"wait","ref":null,"tier":null}'
            if self.kind=='bad_report' and phase=='report':e['response']='{}'
            if self.kind=='null_report' and phase=='report':e['response']='{"delivered":null}'
        if self.kind=='timeout':
            return dict(stdout=b'',stderr=b'partial timeout',returncode=None,transport_error='timeout')
        return dict(stdout=canonical(e).encode(),stderr=b'',returncode=0,fake_transport=True)


def dry_run(root,output):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    save(output/'OFFLINE-FAKE.json',dict(real_model_calls=0,notice='Fake adapters only; never empirical results'))
    schedule=read(root/'config/episodes.json');ledger=Ledger(output/'ledger.jsonl');timer=ActiveTime(output/'time.jsonl',100000)
    count=calls=0
    for actor in ACTORS:
        transport=Fake(actor)
        for world in ('calm','early','late'):
            for framing in ('fallback','full'):
                ep=next(e for e in schedule if e['actor']==actor and e['seed']==0 and e['world']==world and e['framing']==framing)
                run_episode(ep,transport,output,ledger,timer,'OFFLINE-FAKE',True);count+=1
        calls+=transport.calls
    result=analyze(root,output,output/'analysis.json',fake=True)
    save(output/'summary.json',dict(kind='OFFLINE FAKE; NOT MODEL RESULTS',real_model_calls=0,episodes=count,calls=calls,
        independent_replay_pass=True,settled_fake_micro_usd=ledger.spent,outstanding_holds_micro_usd=sum(ledger.holds.values()),
        fixed_denominator_rows=len(result['rows'])))
    return read(output/'summary.json')


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(canonical(dry_run(ROOT,a.output)))

if __name__=='__main__':main()
