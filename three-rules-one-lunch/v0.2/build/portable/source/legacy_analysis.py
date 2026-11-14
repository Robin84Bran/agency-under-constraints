"""Frozen offline analysis. Imports no providers, network, subprocess or credentials."""
import argparse
from collections import Counter
from pathlib import Path
import random
from trl_core import (ROOT, ACTORS, REGIMES, Simulator, action, baseline, canonical,
                      generation_seed, render, roles, sha, strict_load, visible, world, PINS, SYSTEM)
from trl_io import Stop, read, save, save_text
from trl_validation import validate, usage, stdout, cost
from trl_budget import Ledger, maximum, reservation


def mean(xs):
    return sum(xs)/len(xs) if xs else None


def percentile(xs,p):
    if not xs:
        return None
    xs = sorted(xs)
    n = (len(xs)-1)*p
    i = int(n)
    return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(n-i)


def paired(a,b,replicates=10000):
    if len(a)!=len(b):
        raise ValueError('paired seed denominators differ')
    d = [x-y for x,y in zip(a,b)]
    if not d:
        return {'n':0,'difference':None,'ci95':[None,None]}
    rng = random.Random(20261112)
    # List draws retain repeated-block multiplicity. Never use set/dict on draws.
    draws = [mean([d[rng.randrange(len(d))] for _ in d]) for _ in range(replicates)]
    return {'n':len(d),'difference':mean(d),'ci95':[percentile(draws,.025),percentile(draws,.975)]}


def score(seed,regime,events,complete,attempted):
    if len(events)!=12 or [(e['round'],e['slot']) for e in events]!=[(r,s) for r in range(1,5) for s in (1,2,3)]:
        raise Stop('twelve canonical opportunities required')
    truth = world(seed)
    receipts = []
    by_round, seen_cells = [],set()
    pre_observed = []
    for r in range(1,5):
        rows = events[(r-1)*3:r*3]
        cells = []
        exploit = new = 0
        for e in rows:
            if e['status']=='executed':
                c = e['cell']
                if type(c) is not int or c not in range(48) or e['reward']!=truth['fields'][int(r>=3)][c] or type(e['reward']) is not int or e['operational_reward']!=e['reward']:
                    raise Stop('world-truth/reward mismatch')
                role = 0 if regime=='central' else e['slot']
                known = {x[2] for x in visible(regime,r,role,receipts)}
                exploit += c in known
                new += c not in known
                cells.append(c)
                if r<=2:
                    pre_observed.append((c,e['reward']))
            elif e['status'] in ('null','technical','missing'):
                if e['cell'] is not None or e['reward'] is not None or e['operational_reward']!=0:
                    raise Stop('UNKNOWN observation fabricated')
            else:
                raise Stop('unknown opportunity status')
        by_round.append({'round':r,'Y':sum(e['operational_reward'] for e in rows)/3000,
            'H':sum(e['status']=='executed' and e['reward']>=500 for e in rows)/3,
            'coverage':len(cells)/3,'null_rate':sum(e['status']=='null' for e in rows)/3,
            'technical_missing_rate':sum(e['status'] in ('technical','missing') for e in rows)/3,
            'exploitation':exploit,'new_cell_queries':new,'within_round_repeated_cells':len(cells)-len(set(cells))})
        # Append only after the full round, including for metrics.
        receipts.extend([[r,e['slot'],e['cell'],e['reward']] for e in rows if e['status']=='executed'])
        seen_cells.update(cells)
    old = {i for i,v in enumerate(truth['fields'][0]) if v==max(truth['fields'][0])}
    current = {i for i,v in enumerate(truth['fields'][1]) if v==max(truth['fields'][1])}
    best = {c for c,v in pre_observed if v==max(x[1] for x in pre_observed)} if pre_observed else None
    def stale(target):
        if target is None:
            return None
        counts = [sum(e['status']=='executed' and e['cell'] in target for e in events if e['round']==r) for r in (3,4)]
        return {'round_3_queries':counts[0],'round_4_queries':counts[1],
                'rounds_with_queries':sum(v>0 for v in counts),
                'last_round_after_relocation':max([r-2 for r,n in zip((3,4),counts) if n]+[0])}
    return {'Y':sum(e['operational_reward'] for e in events)/12000,
        'H':sum(e['status']=='executed' and e['reward']>=500 for e in events)/12,
        'coverage':sum(e['status']=='executed' for e in events)/12,
        'null_rate':sum(e['status']=='null' for e in events)/12,
        'technical_missing_rate':sum(e['status'] in ('technical','missing') for e in events)/12,
        'complete':complete,'attempted':attempted,'pre_Y':sum(e['operational_reward'] for e in events[:6])/6000,
        'post_Y':sum(e['operational_reward'] for e in events[6:])/6000,
        'pre_H':sum(e['status']=='executed' and e['reward']>=500 for e in events[:6])/6,
        'post_H':sum(e['status']=='executed' and e['reward']>=500 for e in events[6:])/6,
        'by_round':by_round,'stale_true_old_peak':stale(old),'stale_best_observed':stale(best),
        'stale_best_observed_reason':None if best is not None else 'no executed pre-relocation observations',
        'old_current_peak_overlap_cells':len(old&current),'reasons':dict(Counter(e['reason'] for e in events if e['reason']))}


def replay(ep,directory):
    """Rebuild only saved successful rounds from raw first responses, never ask a provider."""
    directory = Path(directory)
    sim = Simulator(ep['seed'])
    from trl_d4 import effective_calls, terminal_path, refusal, verify_pause
    overlay = directory.parent.parent/'d4-episodes'/directory.name
    d4 = (directory.parent.parent.parent/'deviations/d4/clearance.json').exists() or overlay.exists() or any(read(p).get('operational_event')=='DEFINITE_NON_START' for p in directory.glob('*.parsed.json'))
    effective, refusals = effective_calls(directory) if d4 else ({},[])
    d5 = (directory.parent.parent.parent/'deviations/d5/clearance.json').exists()
    validate_call = validate
    if d5:
        from trl_d5 import terminal_path, validate as validate_call
    terminal_file = terminal_path(directory) if d4 else directory/'episode.json'
    terminal = read(terminal_file) if terminal_file.exists() else None
    for prefix in refusals:
        verify_pause(directory.parent.parent,prefix)
    if d4 and any(p is None for p in effective.values()):
        return {'episode':ep,'kind':terminal['kind'] if terminal else 'UNKNOWN',
            'status':'UNKNOWN','reason':'usage-limit pause; awaiting identical request after reset',
            'paused':True,'complete':False,'calls':sum(p is not None for p in effective.values()),
            'operational_usage_limit_refusals':len(refusals)}
    if terminal and terminal['episode']!=ep:
        raise Stop('episode design drift')
    starts = [Path(str(p)+'.start.json') for p in effective.values() if p is not None] if d4 else sorted(directory.glob('*.start.json'))
    calls, failed = [],False
    used = set()
    for r in range(1,5):
        values = {}
        for role in roles(ep['regime']):
            key = f'r{r}-j{role}'
            prefix = effective.get(key,directory/key) if d4 else directory/key
            start = Path(str(prefix)+'.start.json')
            if not start.exists():
                failed = True
                break
            used.add(str(start))
            req = read(Path(str(prefix)+'.request.json'))
            prompt = render(ep['regime'],r,role,sim.receipts)
            quota = 3 if role==0 else 1
            if req['prompt']!=prompt or req['prompt_sha256']!=sha(prompt.encode()) or req['request_sha256']!=sha(canonical(req['request']).encode()) or req['generation_seed']!=generation_seed(ep['seed'],r,role) or req['reservation']!=maximum(ep['regime']) or req['sizing']!=reservation(prompt,quota):
                raise Stop('request/prompt/visibility/sizing mismatch')
            if ep['actor']=='claude':
                tc = read(ROOT/'config/transport.json')
                expected_request = {'stdin_utf8':prompt,'argv':tc['claude_argv_by_regime'][ep['regime']],
                    'environment_controls':tc['environment_controls'],'seed_supported':False,'timeout_seconds':420}
            else:
                expected_request = {'model':PINS[ep['actor']][0],'prompt':prompt,'system':SYSTEM,'format':'json','stream':False,
                    'options':{'temperature':.6,'top_k':16,'num_predict':192,'num_ctx':8192,'seed':generation_seed(ep['seed'],r,role)}}
            if req['request']!=expected_request:
                raise Stop('transport request/settings differ from frozen contract')
            if read(start).get('logical_call_id',read(start)['id'])!=ep['id']+'-'+key or req['id']!=ep['id']+'-'+key or req['round']!=r or req['role']!=role or req['quota']!=quota:
                raise Stop('call identity mismatch')
            rawpath, parsedpath = Path(str(prefix)+'.raw.json'),Path(str(prefix)+'.parsed.json')
            if not rawpath.exists() or not parsedpath.exists():
                failed = True
                break
            raw,parsed = read(rawpath),read(parsedpath)
            valid,u = None,None
            try:
                u = usage(strict_load(stdout(raw)),ep['actor'])
            except (ValueError,KeyError,TypeError):
                pass
            if parsed['usage']!=u or parsed.get('logical_call_id',parsed['id'])!=ep['id']+'-'+key or parsed['round']!=r or parsed['role']!=role or not isinstance(parsed['elapsed_seconds'],(int,float)) or parsed['elapsed_seconds']<0:
                raise Stop('parsed usage/identity/timing differs from raw contract')
            try:
                valid,env,u = validate_call(raw,ep['actor'],quota,maximum(ep['regime']))
            except (ValueError,KeyError,TypeError,Stop):
                pass
            if (parsed['error'] is None)!=(valid is not None) or parsed['value']!=valid:
                # Ledger overrun may invalidate an otherwise syntactically correct action.
                if not (parsed['error'] and parsed['value'] is None and ep['actor']=='claude'):
                    raise Stop('saved parse differs from independent validation')
            calls.append(parsed)
            if parsed['error']:
                failed = True
                break
            values[role] = valid
        if failed:
            break
        sim.execute(ep['regime'],values)
        roundpath = directory/(f'round-{r}.json')
        if d4 and not roundpath.exists():
            roundpath = overlay/f'round-{r}.json'
        if not roundpath.exists():
            # A crash after parsing, before durable round commit leaves no factual observation.
            sim.events = sim.events[:-3]
            sim.receipts = [x for x in sim.receipts if x[0]<r]
            sim.next_round = r
            failed = True
            break
        if read(roundpath)!=sim.events[-3:]:
            raise Stop('saved round differs from simulator truth')
    if {str(p) for p in starts}!=used:
        raise Stop('unexpected extra or post-failure calls')
    complete = not failed and len(sim.events)==12
    if not complete:
        reason = terminal['error'] if terminal else 'unstarted or nonterminal evidence; outcome UNKNOWN'
        slots = [1,2,3] if ep['regime']=='central' and any(p.name.startswith(f'r{sim.next_round}-') for p in starts) else [j for j in (1,2,3) if (directory/(f'r{sim.next_round}-j{j}.start.json')).exists()]
        if d4:
            attempted = [j for j in range(4) if effective.get(f'r{sim.next_round}-j{j}') is not None]
            slots = [1,2,3] if ep['regime']=='central' and attempted else [j for j in attempted if j]
        sim.terminate(reason,slots)
    if terminal and (terminal['events']!=sim.events or terminal['receipts']!=sim.receipts or terminal['complete']!=complete or terminal['attempted_calls']!=len(calls)):
        raise Stop('terminal episode does not replay')
    result = score(ep['seed'],ep['regime'],sim.events,complete,bool(starts))
    unknown_usage = len(starts)-sum(c['usage'] is not None for c in calls)
    result.update(episode=ep,kind=terminal['kind'] if terminal else 'UNKNOWN',calls=len(starts),
        input_tokens=sum(c['usage']['input'] for c in calls if c['usage']) if not unknown_usage else None,
        cache_read_tokens=sum(c['usage']['cache_read'] for c in calls if c['usage']) if not unknown_usage else None,
        cache_creation_tokens=sum(c['usage']['cache_creation'] for c in calls if c['usage']) if not unknown_usage else None,
        output_tokens=sum(c['usage']['output'] for c in calls if c['usage']) if not unknown_usage else None,
        unknown_usage_calls=unknown_usage,
        elapsed_seconds=sum(c['elapsed_seconds'] for c in calls) if len(calls)==len(starts) else None,
        elapsed_status='KNOWN' if len(calls)==len(starts) else 'UNKNOWN')
    if terminal and terminal.get('classification'):
        result['classification'] = terminal['classification']
    if refusals:
        result['operational_usage_limit_refusals'] = len(refusals)
    return result


def group_summary(rows):
    keys = ('Y','H','coverage','null_rate','technical_missing_rate','pre_Y','post_Y','pre_H','post_H')
    return dict({k:mean([r[k] for r in rows]) for k in keys},n=len(rows),
        complete_episodes=sum(r['complete'] for r in rows),attempted_episodes=sum(r['attempted'] for r in rows),
        by_round=[dict(round=i+1,**{k:mean([r['by_round'][i][k] for r in rows]) for k in rows[0]['by_round'][i] if k!='round'}) for i in range(4)],
        stale_true_old_peak={k:mean([r['stale_true_old_peak'][k] for r in rows]) for k in rows[0]['stale_true_old_peak']},
        stale_best_observed={k:mean([r['stale_best_observed'][k] for r in rows if r['stale_best_observed'] is not None]) for k in rows[0]['stale_true_old_peak']},
        stale_best_observed_denominator=sum(r['stale_best_observed'] is not None for r in rows),
        calls=sum(r['calls'] for r in rows),input_tokens=sum(r['input_tokens'] for r in rows) if all(r['input_tokens'] is not None for r in rows) else None,
        output_tokens=sum(r['output_tokens'] for r in rows) if all(r['output_tokens'] is not None for r in rows) else None,cache_read_tokens=sum(r['cache_read_tokens'] for r in rows) if all(r['cache_read_tokens'] is not None for r in rows) else None,
        cache_creation_tokens=sum(r['cache_creation_tokens'] for r in rows) if all(r['cache_creation_tokens'] is not None for r in rows) else None,unknown_usage_calls=sum(r['unknown_usage_calls'] for r in rows),
        elapsed_seconds=sum(r['elapsed_seconds'] for r in rows) if all(r['elapsed_seconds'] is not None for r in rows) else None)


def summarize(rows,replicates=10000):
    results = {}
    for actor in ACTORS:
        group = [r for r in rows if r['episode']['actor']==actor]
        if not group:
            continue
        per = {reg:sorted([r for r in group if r['episode']['regime']==reg],key=lambda r:r['episode']['seed']) for reg in REGIMES}
        seeds = [r['episode']['seed'] for r in per['shared']]
        if any([r['episode']['seed'] for r in per[reg]]!=seeds for reg in REGIMES) or len(seeds)!=len(set(seeds)):
            raise Stop('missing/duplicate paired seed block')
        s,p,c = per['shared'],per['private'],per['central']
        dy = paired([r['Y'] for r in s],[r['Y'] for r in p],replicates)
        dh = paired([r['H'] for r in s],[r['H'] for r in p],replicates)
        complete = [(a,b) for a,b in zip(s,p) if a['complete'] and b['complete']]
        sensitivity = paired([a['Y'] for a,b in complete],[b['Y'] for a,b in complete],replicates)
        n = 20 if actor=='claude' else 100
        guards = len(seeds)==n and all(r['attempted'] for r in s+p) and sum(r['complete'] for r in s)>=.95*n and sum(r['complete'] for r in p)>=.95*n and len(complete)>=.95*n
        passed = guards and dy['ci95'][0]>0 and dh['ci95'][0]>0 and sensitivity['ci95'][0]>0
        metrics = {reg:group_summary(per[reg]) for reg in REGIMES}
        controls = {}
        for pol in ('uniform','greedy-shared','greedy-private','greedy-central','oracle','all-null'):
            regime = 'private' if pol=='greedy-private' else ('central' if pol in ('greedy-central','oracle') else 'shared')
            controls[pol] = mean([score(seed,regime,baseline(seed,pol).events,True,False)['Y'] for seed in seeds])
        ratios = {reg:{pol:{'value':metrics[reg]['Y']/controls[pol] if controls[pol] else None,
                            'reason':None if controls[pol] else 'zero baseline Y denominator'} for pol in ('greedy-shared','greedy-private')} for reg in REGIMES}
        results[actor] = {'regimes':metrics,'shared_minus_private_Y':dy,'shared_minus_private_H':dh,
            'complete_pair_sensitivity_Y':sensitivity,'complete_pairs':len(complete),'technical_guardrails':guards,
            'joint_status':'descriptive' if actor=='claude' else ('passes' if passed else 'joint criterion not met'),
            'evidence_status':'incomplete' if not guards else ('positive' if passed else ('negative point estimate' if dy['difference']<0 or dh['difference']<0 else 'inconclusive')),
            'central_minus_shared_Y':paired([r['Y'] for r in c],[r['Y'] for r in s],replicates),
            'central_minus_shared_H':paired([r['H'] for r in c],[r['H'] for r in s],replicates),
            'same_seed_baseline_mean_Y':controls,'Y_fraction_of_baselines':ratios,
            'baseline_sharing_gain_Y':controls['greedy-shared']-controls['greedy-private'],
            'all_seed_rows':[{'seed':seed,**{reg:{k:per[reg][i][k] for k in ('Y','H','complete','stale_true_old_peak','stale_best_observed')} for reg in REGIMES}} for i,seed in enumerate(seeds)]}
    def pred(condition,needed,denominator):
        known = not any(r['kind']=='FAKE' for r in rows) and all(a in results and all(results[a]['regimes'][r]['attempted_episodes']==results[a]['regimes'][r]['n'] for r in REGIMES) for a in needed)
        return {'status':('met' if condition() else 'failed') if known else 'UNKNOWN',
                'reason':None if known else 'mandatory attempted model evidence unavailable','denominator':denominator}
    predictions = {
        'P1':pred(lambda:results['qwen7b']['joint_status']=='passes',['qwen7b'],100),
        'P2':pred(lambda:all(results['llama8b']['shared_minus_private_'+k]['difference']>0 for k in ('Y','H')),['llama8b'],100),
        'P3':pred(lambda:all(results[a]['central_minus_shared_Y']['difference']>=0 for a in ('qwen7b','llama8b')),['qwen7b','llama8b'],{'qwen7b':100,'llama8b':100}),
        'P4':pred(lambda:all(results[a]['regimes']['shared']['post_Y']>results[a]['regimes']['private']['post_Y'] for a in ('qwen7b','llama8b')),['qwen7b','llama8b'],{'qwen7b':100,'llama8b':100}),
        'P5':pred(lambda:results['qwen1b']['regimes']['shared']['Y']<results['qwen7b']['regimes']['shared']['Y'],['qwen1b','qwen7b'],100),
        'P6':pred(lambda:results['claude']['shared_minus_private_Y']['difference']>0,['claude'],20),
        'P7':pred(lambda:all(v['complete_episodes']>=.95*v['n'] for a in results.values() for v in a['regimes'].values()),list(ACTORS),960)}
    return {'kind':'FAKE' if any(r['kind']=='FAKE' for r in rows) else 'MODEL_OR_UNAVAILABLE',
        'primary_model':'qwen7b','cohorts':results,'predictions':predictions,
        'bootstrap':{'replicates':replicates,'seed':20261112,'unit':'paired seed block, multiplicity retained'},
        'limitations':'Fixed first replies, synthetic deterministic non-depleting worlds; equal observations do not imply equal compute. Frontier descriptive only. No model inference in this analysis.'}


def analyze(root,base,out):
    root,base,out = Path(root),Path(base),Path(out)
    rows = [replay(e,base/'episodes'/e['id']) for e in read(root/'config/episodes.json')]
    ledger = Ledger(base/'cost.jsonl')
    paid_starts = {read(p)['id'] for folder in ('episodes','d4-episodes') for p in (base/folder).rglob('*.start.json') if 'claude-' in p.as_posix()}
    # A crash between allocation and durable start conservatively retains the hold.
    if not paid_starts.issubset(set(ledger.starts)):
        raise Stop('paid start without reserved subhold')
    known_cost = {}
    for p in [p for folder in ('episodes','d4-episodes') for p in (base/folder).rglob('*.raw.json') if 'claude-' in p.as_posix()]:
        try:
            u = usage(strict_load(stdout(read(p))),'claude')
        except (ValueError,TypeError,KeyError):
            u = None
        ident = read(Path(str(p)[:-9]+'.start.json'))['id']
        if u is not None:
            known_cost[ident] = cost(u)
    if any(known_cost.get(k)!=v['actual'] for k,v in ledger.settled.items()):
        raise Stop('usage/settlement mismatch')
    paused = [r['episode']['id'] for r in rows if r.get('paused')]
    operational = sum(r.get('operational_usage_limit_refusals',0) for r in rows)
    summary = ({'kind':'MODEL_OR_UNAVAILABLE','status':'UNKNOWN','reason':'usage-limit pause; study remains pending',
        'pending_episodes':paused,'cohorts':{}} if paused else summarize(rows))
    if operational:
        summary['operational_events'] = {'usage_limit_refusals':operational,'classification':'definite non-starts; excluded from model behaviour and technical failures'}
    summary['accounting'] = {'settled_micro_usd':ledger.spent,'open_holds_micro_usd':sum(ledger.holds.values()),
        'unsettled_calls':sorted(set(ledger.starts)-set(ledger.settled)),
        'cost_stop':ledger.stopped,'cash_billing_usd':None,'cash_billing_status':'UNKNOWN',
        'usage_categories':'Input, cache-read, cache-creation and output saved separately; output includes charged reasoning.',
        'actual_active_time':{p.name:[strict_load(x) for x in p.read_text().splitlines()] for p in base.glob('time-*.jsonl')},
        'stop':read(base/'STOP.json') if (base/'STOP.json').exists() else None}
    save(out/'episodes.json',rows)
    save(out/'summary.json',summary)
    if paused:
        save_text(out/'RESULTS.md', '# Pending collection\n\nUsage-limit refusals: '+str(operational)+' operational non-start event(s). Model results remain UNKNOWN until collection resumes; these events are not model technical failures.\n')
    else:
        export_tables(summary,out)
    return summary


def export_tables(summary,out):
    import csv
    import io
    columns = ['actor','regime','n','attempted_episodes','complete_episodes','Y','H','coverage',
               'Y_fraction_greedy_shared','Y_fraction_greedy_private','stale_rounds','stale_last_round']
    stream = io.StringIO(newline='')
    writer = csv.writer(stream,lineterminator='\n');writer.writerow(columns)
    text = ['# '+summary['kind']+' · offline table',
            '', 'Operational scores use all twelve opportunities. Missing factual rewards remain null. '
            'Fake evidence is a software check and supports no scientific finding.', '',
            '| Actor | Regime | Y | H | Y / greedy-shared | Y / greedy-private | Complete / planned |',
            '|---|---|---:|---:|---:|---:|---:|']
    def fmt(v):
        return 'UNKNOWN' if v is None else format(v,'.6f')
    for actor,cohort in summary['cohorts'].items():
        for reg,m in cohort['regimes'].items():
            ratios = cohort['Y_fraction_of_baselines'][reg]
            a,b = ratios['greedy-shared']['value'],ratios['greedy-private']['value']
            writer.writerow([actor,reg,m['n'],m['attempted_episodes'],m['complete_episodes'],m['Y'],m['H'],m['coverage'],a,b,
                             m['stale_true_old_peak']['rounds_with_queries'],m['stale_true_old_peak']['last_round_after_relocation']])
            text.append(f"| {actor} | {reg} | {fmt(m['Y'])} | {fmt(m['H'])} | {fmt(a)} | {fmt(b)} | {m['complete_episodes']}/{m['n']} |")
        text.extend(['',f"{actor}: shared−private ΔY {cohort['shared_minus_private_Y']}; ΔH {cohort['shared_minus_private_H']}. "
                     f"Scripted greedy sharing gain Y: {cohort['baseline_sharing_gain_Y']:.6f}. "
                     f"Joint status: {cohort['joint_status']} ({cohort['evidence_status']}).",''])
    if summary.get('operational_events'):
        text.extend(['', 'Usage-limit refusals: '+str(summary['operational_events']['usage_limit_refusals'])+' operational non-start event(s), excluded from model behaviour and technical failures.'])
    text.extend(['','Any eventual page must explain when sharing benefits are mostly also obtained by a simple script. '
                 'This table cannot establish how a model reasons. Central uses fewer calls per round; observations are equal, compute is not.'])
    save_text(Path(out)/'tables.csv',stream.getvalue())
    save_text(Path(out)/'tables.md','\n'.join(text)+'\n')
    frontier = io.StringIO(newline=''); w = csv.writer(frontier,lineterminator='\n')
    w.writerow(['seed','regime','Y','H','complete','stale_rounds','stale_last_round'])
    for row in summary['cohorts'].get('claude',{}).get('all_seed_rows',[]):
        for reg in REGIMES:
            m = row[reg]
            w.writerow([row['seed'],reg,m['Y'],m['H'],m['complete'],m['stale_true_old_peak']['rounds_with_queries'],m['stale_true_old_peak']['last_round_after_relocation']])
    save_text(Path(out)/'frontier-seeds.csv',frontier.getvalue())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--base',type=Path);p.add_argument('--out',type=Path,required=True)
    a = p.parse_args()
    analyze(a.root,a.base or a.root/'collection',a.out)

if __name__=='__main__':
    main()
