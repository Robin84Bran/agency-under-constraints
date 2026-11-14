"""Offline deterministic artifacts and installed-source evidence. No inference."""
import argparse
import mmap
from pathlib import Path
import platform
import random
import subprocess
import sys
from trl_core import ROOT, ACTORS, REGIMES, SYSTEM, INSTRUCTION, canonical, schema, world, ToyRNG, maximal_receipts, render, roles, sha, baseline
from trl_io import read, save, Stop
from trl_budget import reservation, maximum, episode_hold
from trl_transport import CLAUDE_BIN, claude_command, controls


def stable(path,value):
    path = Path(path)
    if path.exists():
        if read(path)!=value:
            raise Stop('existing evidence differs: '+str(path))
    else:
        save(path,value)


def design(root):
    root = Path(root)
    episodes = []
    for actor in ACTORS:
        pairs = sorted((s,r) for s in range(20 if actor=='claude' else 100) for r in REGIMES)
        random.Random(20261111).shuffle(pairs)
        episodes.extend({'id':f'{actor}-s{s:03d}-{reg}','actor':actor,'seed':s,'regime':reg} for s,reg in pairs)
    stable(root/'config/episodes.json',episodes)
    stable(root/'config/transport.json',{'claude_argv_by_regime':{reg:claude_command(CLAUDE_BIN,3 if reg=='central' else 1,maximum(reg)['micro_usd']) for reg in REGIMES},'environment_controls':controls()})
    stable(root/'config/prompts.json',{'system':SYSTEM,'instruction':INSTRUCTION,'schemas':{'worker':schema(1),'central':schema(3)}})
    stable(root/'fixtures/worlds.json',[world(s) for s in range(100)])
    vectors = read(root/'fixtures/js-vectors.json')
    if vectors['worlds']!=read(root/'fixtures/worlds.json'):
        raise Stop('Python/JS independent world mismatch')
    for row in vectors['rng']:
        r = ToyRNG(row['seed'])
        if row['values']!=[r() for _ in row['values']]:
            raise Stop('toy RNG mismatch')
    rows = []
    for regime in REGIMES:
        for r in range(1,5):
            for role in roles(regime):
                q = 3 if regime=='central' else 1
                prompt = render(regime,r,role,maximal_receipts(r))
                hold = reservation(prompt,q)
                outer = {'stdin':prompt,'argv':claude_command(CLAUDE_BIN,q,maximum(regime)['micro_usd']),
                         'environment_controls':controls()}
                rows.append({'regime':regime,'round':r,'role':role,'prompt':prompt,
                    'prompt_utf8_bytes':len(prompt.encode()),'prompt_sha256':sha(prompt.encode()),
                    'system_utf8_bytes':len(SYSTEM.encode()),'schema_utf8_bytes':len(canonical(schema(q)).encode()),
                    'outer_request':outer,'outer_utf8_bytes':len(canonical(outer).encode()),**hold})
    total = sum(episode_hold(e['regime']) for e in episodes if e['actor']=='claude')
    if total!=18083840 or total+1000000>25000000:
        raise Stop('reviewed reservation sizing changed')
    stable(root/'config/sizing.json',{'measurements':rows,'by_regime':{r:{'call':maximum(r),'episode_micro_usd':episode_hold(r)} for r in REGIMES},
        'frontier_calls':560,'frontier_episodes':60,'frontier_micro_usd':total,'including_protected_reserve_micro_usd':total+1000000,
        'basis':'SoS D1: pad(bytes(prompt)+bytes(system)+bytes(schema)+826), pad(1024); 10% upward / 64 tokens. Historical 4/20 USD per million. Conditional, not verified billing bounds.',
        'exact_input_token_status':'UNKNOWN','exact_input_tokens':None,'protected_reserve_micro_usd':1000000,
        'frontier_dispatch_envelope_micro_usd':25000000,'project_stop_micro_usd':39000000,'absolute_cap_micro_usd':40000000})
    stable(root/'config/design.json',{'protocol_revision':'v0.1-build-r1','bootstrap_replicates':10000,'bootstrap_seed':20261112,'order_seed':20261111,
        'primary_actor':'qwen7b','local_seeds':list(range(100)),'frontier_seeds':list(range(20)),
        'local_options':{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192},
        'active_time_caps_seconds':{'local':43200,'claude':10800},'timeout_seconds':{'local':180,'claude':420},
        'frontier_model':'claude-opus-5-5','requested_effort':'medium','actual_effort_status':'UNKNOWN',
        'runtime_status':'UNKNOWN','runtime_reason':'No live runtime or service access in offline build',
        'rates_status':'UNKNOWN','cash_billing_usd':None})
    from trl_analysis import score
    baselines = []
    for seed in range(100):
        for policy in ('uniform','greedy-shared','greedy-private','greedy-central','oracle','all-null'):
            reg = 'private' if policy=='greedy-private' else ('central' if policy in ('greedy-central','oracle') else 'shared')
            sim = baseline(seed,policy)
            baselines.append({'seed':seed,'policy':policy,'events':sim.events,'score':score(seed,reg,sim.events,True,False)})
    stable(root/'fixtures/baselines.json',baselines)
    stable(root/'fixtures/analysis-cases.json',[
        {'name':'all-null','seed':0,'regime':'shared','events':baseline(0,'all-null').events,
         'complete':True,'attempted':True,'expected':{'Y':0,'H':0,'coverage':0,'null_rate':1,'technical_missing_rate':0}},
        {'name':'full-information ceiling','seed':0,'regime':'central','events':baseline(0,'oracle').events,
         'complete':True,'attempted':False,'expected':{'Y':1,'H':1,'coverage':1,'null_rate':0,'technical_missing_rate':0}}])
    return total


def cli_evidence(root):
    root = Path(root)
    binary = Path(CLAUDE_BIN).resolve()
    digest = sha(binary.read_bytes())
    if digest!='6b5ec691195e551b02c41df9f7d723f4ea61eaa03c2df90acefe3736f1aeb620':
        raise Stop('CLI hash differs from reviewed binary')
    helptext = subprocess.check_output([str(binary),'--help'],timeout=30)
    p = root/'evidence/claude-help.txt'
    if p.exists():
        if p.read_bytes()!=helptext:
            raise Stop('CLI help drift')
    else:
        with p.open('xb') as f:
            f.write(helptext)
    needles = [
        'function nTt(e)', 'function nqt(e,n,r,s)', 'let gT=Math.min', 'max_tokens:gT',
        'MAX_STRUCTURED_OUTPUT_RETRIES??', 'function t7e()',
        'CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES??', 'result:Cs,structured_output:Ps',
        'structured_output:oe().optional()', '--max-turns <turns>',
        'querySource:"model_validation"', 'max_tokens:1,maxRetries:0',
        'source:"verify_api_key"', 'source:"quota_check"', 'function HSt(e)']
    snippets = []
    with binary.open('rb') as f:
        b = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
        for needle in needles:
            pos = b.find(needle.encode(),217000000)
            if pos<0:
                raise Stop('missing source evidence: '+needle)
            snippets.append({'needle':needle,'offset':pos,'text':b[max(0,pos-120):pos+900].decode(errors='replace')})
    stable(root/'evidence/cli-contract.json',{'version':'2.1.312','binary_sha256':digest,
        'help_sha256':sha(helptext),'payload_field':'structured_output','payload_type':'object',
        'controls':controls(),'readiness':'UNKNOWN','accounting_rates_status':'UNKNOWN',
        'reason':'Individual output/retry controls found offline. Combined coverage of startup/model-validation/auth/quota requests, absence of unaccounted requests, schema scaffolding bound, and current price/cache-creation premiums are not established. No inference probe allowed. Both local and frontier dispatch HOLD until reviewed amendment/new freeze before first study call.',
        'output_limit_candidate':1024,'enforced_total_output_status':'UNKNOWN',
        'actual_effort_status':'UNKNOWN','hidden_overhead_hard_bound_status':'UNKNOWN',
        'snippets':snippets})
    stable(root/'evidence/build-environment.json',{'python':sys.version,'platform':platform.platform(),
        'node_version':subprocess.check_output(['node','--version'],text=True).strip(),
        'model_calls':0,'provider_commands_executed':['claude --help'],'dependency_policy':'Python standard library; Node only for independent toy parity fixture'})


def main():
    p = argparse.ArgumentParser();p.add_argument('command',choices=['design','cli-evidence']);p.add_argument('--root',type=Path,default=ROOT)
    a = p.parse_args()
    print(design(a.root) if a.command=='design' else cli_evidence(a.root))

if __name__=='__main__':
    main()
