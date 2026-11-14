"""Fixture production and fake-transport dry run. No live transport is constructed."""
from pathlib import Path
import subprocess
import tempfile

from bob_core import ROOT,ACTORS,ARMS,WORLDS,canonical,sha,strict_load,schedule,sizing,render,SCHEMAS,P
from bob_baselines import run
from bob_collect import Ledger,ActiveTime,run_episode,request_for
from bob_analysis import analyze,replay


def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(canonical(value)+'\n')


class FakeTransport:
    """Explicit fixture actor. Responses include no network or subprocess invocation."""
    def __init__(self,ep,policy='oracle',mode=None):
        self.ep,self.mode=ep,mode
        self.script=run(ep,policy)
        self.actions=iter(e['action'] for e in self.script['events'])
        self.calls=0

    def generate(self,request,phase,budget):
        self.calls+=1
        value=next(self.actions) if phase=='action' else self.script['report']
        if self.mode=='all_null' and phase=='report':
            value={'submitted':None}
        if self.ep['model']=='claude':
            env=dict(type='result',subtype='success',is_error=False,num_turns=1,effort=None,
                     modelUsage={'claude-opus-5-5':{}},structured_output=value,
                     usage=dict(input_tokens=0,output_tokens=0,cache_read_input_tokens=0,cache_creation_input_tokens=0),total_cost_usd=0)
            if self.mode=='missing_payload':
                del env['structured_output']; env['result']=canonical(value)
            if self.mode=='missing_usage':
                del env['usage']
            if self.mode=='overrun':
                env['total_cost_usd']=budget/1000000+.001
            if self.mode=='wrong_identity':
                env['modelUsage']={'wrong-model':{}}
        else:
            env=dict(model=request['model'],response=canonical(value),done=True,done_reason='stop',prompt_eval_count=0,eval_count=0)
            if self.mode=='malformed':
                env['response']='```json\n'+canonical(value)+'\n```'
            if self.mode=='truncated':
                env['done_reason']='length'
        return dict(stdout=canonical(env).encode(),stderr=b'',returncode=0)


def dry_run(output=None):
    with tempfile.TemporaryDirectory(prefix='bob-offline-') as temp:
        root=Path(temp)
        ledger=Ledger(root/'collection/cost.jsonl')
        timer=ActiveTime(root/'collection/fake-time.jsonl',43200)
        results=[]
        for model in ACTORS:
            for world in WORLDS:
                for arm in ARMS:
                    ep=dict(id=f'{model}-00-{world}-{arm}',model=model,seed=0,world=world,arm=arm)
                    fake=FakeTransport(ep)
                    saved=run_episode(root,ep,fake,ledger,timer,'OFFLINE_FIXTURE_NOT_A_REAL_FREEZE')
                    truth=replay(ep,saved['events'])
                    assert truth['committed'] and saved['report']=={'submitted':True}
                    results.append(dict(episode=ep,events=saved['events'],decisions=saved['decisions'],calls=fake.calls,committed=truth['committed']))
        result=dict(status='PASS',kind='FAKE_TRANSPORT_ONLY',episodes=len(results),generations=sum(x['calls'] for x in results),
                    real_model_calls=0,ledger_spent_micro_usd=ledger.spent,outstanding_micro_usd=ledger.exposure-ledger.spent,results=results)
        if output:
            write(output,result)
        return result


def fixture_records(plan,kind):
    records={}
    for ep in plan:
        policy='oracle' if kind=='oracle' or ep['arm']=='registry' else 'fixed_v0'
        records[ep['id']]=run(ep,policy)
    return records


def prepare(root=ROOT):
    root=Path(root)
    if (root/'freeze.json').exists():
        raise RuntimeError('frozen inputs may not be regenerated in place')
    plan=schedule()
    write(root/'config/order.json',plan)
    write(root/'config/sizing.json',sizing())
    initial=[]
    for ep in plan:
        prompt=render(ep,[],6,'action')
        req=request_for(ep,prompt)
        initial.append(dict(id=ep['id'],prompt=prompt,prompt_sha256=sha(prompt.encode()),request=req,request_bytes=len(canonical(req).encode()),request_sha256=sha(canonical(req).encode())))
    write(root/'config/initial-requests.json',initial)
    max_requests=[]
    from bob_core import maximal_history,reserve,bound_prompt
    for arm in ARMS:
        ep=dict(arm=arm,seed=49,model='claude')
        for phase in ('action','report'):
            for depth in range(7):
                prompt=bound_prompt(ep,depth,phase)
                max_requests.append(dict(arm=arm,phase=phase,depth=depth,prompt=prompt,
                  stdin_bytes=len(prompt.encode()),schema_argv_bytes=len(canonical(SCHEMAS[phase]).encode()),
                  system_argv_bytes=len(P['system'].encode()),
                  harness_request_bytes=len(canonical(request_for(ep,prompt)).encode()),
                  **reserve(prompt,phase)))
    write(root/'fixtures/maximal-prompts.json',max_requests)
    vectors=subprocess.run(['node',str(root/'fixtures/vectors.mjs')],capture_output=True,check=True)
    write(root/'fixtures/cross-language.json',strict_load(vectors.stdout))
    expected=[]
    for seed in (0,1,9,49):
        for world in WORLDS:
            for arm in ARMS:
                ep=dict(id=f'qwen7b-{seed:02d}-{world}-{arm}',model='qwen7b',seed=seed,world=world,arm=arm)
                for policy in ('fixed_v0','reactive','oracle'):
                    expected.append(dict(policy=policy,record=run(ep,policy)))
    write(root/'fixtures/worlds.json',expected)
    records=fixture_records(plan,'positive')
    write(root/'fixtures/analysis-input.json',dict(kind='SYNTHETIC_CODE_POLICIES_NOT_MODEL_RESULTS',plan=plan,records=records))
    # Production analysis settings, including all 10,000 registered replicates.
    result=analyze(plan,records,set(records))
    write(root/'fixtures/analysis-expected.json',result)
    dry=dry_run()
    write(root/'fixtures/dry-run-expected.json',dry)
    return dict(schedule=len(plan),world_fixtures=len(expected),cross_language_draws=len(strict_load(vectors.stdout)['draws']),dry_run_episodes=dry['episodes'],sizing=sizing()['total_micro_usd'])


def rebuild(root=ROOT):
    root=Path(root)
    data=strict_load((root/'fixtures/analysis-input.json').read_bytes())
    rebuilt=analyze(data['plan'],data['records'],set(data['records']))
    expected=strict_load((root/'fixtures/analysis-expected.json').read_bytes())
    if canonical(rebuilt)!=canonical(expected):
        raise ValueError('frozen analysis fixture rebuild differs')
    dry=dry_run()
    if dry!=strict_load((root/'fixtures/dry-run-expected.json').read_bytes()):
        raise ValueError('fake transport rebuild differs')
    return dict(status='PASS',kind='OFFLINE_FIXTURES_ONLY',analysis_sha256=sha(canonical(rebuilt).encode()),
                dry_run_episodes=dry['episodes'],fake_generations=dry['generations'],model_calls=0)
