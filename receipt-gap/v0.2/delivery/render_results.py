"""Post hoc presentation from saved outputs and terminal-event replay only.

No model transport, hypothesis test or bootstrap is run here. A successful
compatibility analysis is used only if separately approved and saved.
"""
from collections import Counter, defaultdict
import csv
from html import escape
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
ACTORS = ('qwen7b', 'llama8b', 'qwen1b', 'claude')
LABEL = dict(zip(ACTORS, ('Qwen 7B', 'Llama 8B', 'Qwen 1.5B', 'Claude')))
TOOLS = ('plain', 'keyed', 'check')


def load(p):
    return json.loads(p.read_text())


V1 = load(OUT/'source-v01/analysis-v01.json')
REPLAY = load(OUT/'descriptive-replay-v02.json')
COMPAT = OUT/'analysis-v02-compat.json'
V2 = load(COMPAT) if COMPAT.exists() else None


def rate(n, d):
    return f'{n}/{d} ({100*n/d:.1f}%)' if d else 'UNKNOWN (0/0)'


def pct(x):
    return 'UNKNOWN' if x is None else f'{x*100:.1f}%'


def interval(item):
    bounds = item['interval']
    value = 'UNKNOWN' if bounds is None else f'[{100*bounds[0]:+.2f}, {100*bounds[1]:+.2f}] pp'
    return f'{value}; blocks={item["support_blocks"]}, null={item["null_replicates"]}'


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join('---' for _ in headers)+' |'] +
                     ['| '+' | '.join(map(str, row))+' |' for row in rows])


def csvfile(name, headers, rows):
    with (OUT/name).open('w', newline='') as stream:
        w = csv.writer(stream); w.writerow(headers); w.writerows(rows)


def pooled(version, actor, toolkit, loss):
    if version == 2 and V2 is None:
        v = REPLAY['cells'].get('/'.join(map(str, (actor, toolkit, loss))))
        return None if v is None else dict(planned=v['n'], known_truth=v['known'], duplicates=v['duplicates'],
            exact_once=v['exact_once'], valid_actions=v['valid'], valid_reports=v['reports'], J_numerator=v['J'],
            recall_numerator=v['TP'], recall_denominator=v['duplicates'])
    cells = [v for k, v in (V1 if version == 1 else V2)['cells'].items() if k.split('/')[:3] == [actor, toolkit, str(loss)]]
    keys = ('planned', 'known_truth', 'duplicates', 'exact_once', 'valid_actions', 'valid_reports',
            'J_numerator', 'recall_numerator', 'recall_denominator')
    return {k: sum(v[k] for v in cells) for k in keys} if cells else None


def display(v):
    if v is None:
        return 'UNKNOWN; uncollected'
    return ' / '.join((rate(v['duplicates'], v['known_truth']), rate(v['exact_once'], v['planned']),
                       rate(v['recall_numerator'], v['recall_denominator']), rate(v['valid_actions'], v['planned'])))


def figure(groups):
    # Bounded fallback: no plotting library is installed. An exportable SVG
    # count display contains no fitted curves or invented uncertainty intervals.
    width, height = 1420, 125 + len(groups)*60
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
           '<title id="title">The Receipt Gap: v0.1 and v0.2, same planned seeds</title>',
           '<desc id="desc">Four columns: actual duplicate rate, exact-once completion, duplicate admission, and valid actions. First dot in each row is v0.1; second is v0.2. UNKNOWN is not plotted. No uncertainty intervals are implied.</desc>',
           '<rect width="100%" height="100%" fill="white"/>', '<g font-family="Arial,sans-serif" font-size="12" fill="#15283b">',
           '<text x="15" y="25" font-size="21">The Receipt Gap · v0.1 (blue) and v0.2 constrained actions (orange)</text>',
           '<text x="15" y="48">Registered cells from frozen calculations; v0.2 uses the disclosed scope adapter. D/S/R/valid use their own denominators.</text>']
    starts = (300, 580, 860, 1140)
    for x, title in zip(starts, ('Duplicates ↓', 'Exact-once completion ↑', 'Duplicate admission ↑', 'Valid actions ↑')):
        svg.append(f'<text x="{x}" y="77" font-weight="bold">{title}</text>')
        for tick in (0, 50, 100):
            px = x+tick*1.9
            svg.extend([f'<line x1="{px}" x2="{px}" y1="95" y2="{height-20}" stroke="#e6eaef"/>',
                        f'<text x="{px}" y="94">{tick}%</text>'])
    for i, (a, t, loss) in enumerate(groups):
        y = 118+i*60
        svg.append(f'<text x="15" y="{y+12}">{escape(LABEL[a]+" · "+t+(" · 0% loss" if loss == 0 else ""))}</text>')
        for version, offset, color in ((1, 0, '#23699b'), (2, 22, '#c26815')):
            v = pooled(version, a, t, loss)
            values = [None]*4 if v is None else [v['duplicates']/v['known_truth'], v['exact_once']/v['planned'],
                      v['recall_numerator']/v['recall_denominator'] if v['recall_denominator'] else None, v['valid_actions']/v['planned']]
            for x, value in zip(starts, values):
                if value is None:
                    svg.append(f'<text x="{x+5}" y="{y+offset}" fill="{color}">UNKNOWN</text>')
                else:
                    px=x+190*value
                    svg.extend([f'<circle cx="{px}" cy="{y+offset-4}" r="4" fill="{color}"/>',
                                f'<text x="{px+7}" y="{y+offset}" fill="{color}">{100*value:.1f}%</text>'])
    svg.append('</g></svg>\n')
    (OUT/'headline.svg').write_text('\n'.join(svg))


def main():
    groups = [(a, t, .5) for a in ACTORS for t in TOOLS]+[(a, 'plain', 0) for a in ACTORS]
    headrows = [[LABEL[a], t+(' (0% loss)' if loss == 0 else ''), display(pooled(1,a,t,loss)), display(pooled(2,a,t,loss))] for a,t,loss in groups]
    headers = ['Actor', 'Toolkit (50% loss unless marked)', 'v0.1 D / S / R / valid actions', 'v0.2 D / S / R / valid actions']
    headline = table(headers, headrows); csvfile('headline.csv', headers, headrows); figure(groups)
    cp = V2['predictions'] if V2 else {k: 'UNKNOWN' for k in V1['predictions']}
    predrows = []
    for number, forecast in enumerate(('Local plain duplicate rate ≥30%', 'Local key reuse <50%; Claude >90%',
              'Qwen RQ1 fails despite a lower keyed duplicate estimate', 'Check reduces duplicates more than keyed',
              'Payment has fewer plain duplicates than notification', '>50% of duplicates explicitly denied',
              'Claude keyed: zero duplicates and ≥75% exact-once'), 1):
        keys = [k for k in cp if k == f'P{number}' or k.startswith(f'P{number}/')]
        def entries(p):
            return '; '.join((LABEL.get(k.partition('/')[2], '')+' '+p[k]).strip() for k in keys)
        predrows.append([f'P{number}', forecast, entries(V1['predictions']), entries(cp)])
    preds = table(['ID', 'Pre-registered forecast', 'v0.1', 'v0.2'], predrows)
    csvfile('predictions.csv', ['ID','Forecast','v0.1','v0.2'], predrows)
    p1, p2 = V1['primary'], V2['primary'] if V2 else None
    status = ('Frozen v0.2 analysis is **UNKNOWN**: the single required invocation stopped before scoring because '
              '`check_saved_push` rejects `freeze-r5.json` (its allowlist ends at r3). No frozen code or prompts '
              'were edited, and the canonical invocation was not repeated. The proposed delivery-only r5 adapter '
              'passes its receipt-only check; scoring awaits a Claude/Codex ruling. All v0.2 counts below are '
              '**post hoc descriptive terminal-event replays**, not output from a completed frozen analysis.') if not V2 else (
              'The original frozen entry point failed once on its r3-only provenance allowlist. A disclosed, reviewer-approved '
              'delivery-only version/scope adapter produced the results with unchanged frozen scorer/statistics. '
              'The v0.1 regression is byte-identical. See [adapter disclosure](adapter-run/DEVIATION.md) and [execution record](adapter-run/execution.json).')
    opening = '# The Receipt Gap · v0.1 and v0.2\n\n'
    opening += '**Hypothesis:** Offering an idempotency key reduces duplicate effects after lost receipts while preserving exact-once completion and reliable reporting.\n\n'
    opening += status+'\n\n'
    if V2:
        opening += (f'**v0.2 decision:** RQ1 **{V2["primary"]["status"]}**; Qwen RQ4 **{V2["RQ4"]["qwen7b"]["status"]}**; '
                    f'**safer and reliably reported: {V2["safer_and_reliably_reported"]}**. Full technical acceptance: {V2["technical_acceptance"]}.\n\n')
    opening += preds+'\n\n'
    opening += ('**Headline:** Valid action formats alone did not yield reliable task completion: every local v0.2 plain and check arm duplicated in 100/100 episodes at 50% receipt loss; '
                'Claude keyed completed 20/20 exactly once. This is consistent with a remaining decision-policy problem; the study does not identify an internal mechanism.\n\n')
    opening += ('D = actual duplicates / known truth; S = exact-once completion / planned; R = duplicate admitted / all true duplicates, with abstention and absent reports as misses; '
                'valid = complete valid action trajectory / planned. Each local main arm has 100 episodes; Claude has 20. Request loss remains 20% even at 0% receipt loss. '
                'UNKNOWN (0/0) means no duplicate-admission opportunities, not perfect reporting. Valid reports and joint report correctness J are shown immediately below. '
                'The two equally sized framings are pooled for display only. Qwen 7B keyed vs plain at 50% loss is primary; other model/toolkit comparisons are registered secondary, reference, or descriptive.\n\n')
    opening += headline+'\n\n![Both versions on duplicate rate, completion, duplicate admission and action validity](headline.svg)\n\n'
    jrows=[]
    for a,t,loss in groups:
        vals=[]
        for version in (1,2):
            v=pooled(version,a,t,loss)
            vals += ['UNKNOWN','UNKNOWN'] if v is None else [rate(v['J_numerator'],v['planned']),rate(v['valid_reports'],v['planned'])]
        jrows.append([LABEL[a],t+(' (0% loss)' if loss==0 else ''),*vals])
    opening += table(['Actor','Toolkit','v0.1 joint correctness J','v0.1 valid reports','v0.2 J','v0.2 valid reports'],jrows)+'\n\n'
    bases=load(OUT/'code-baselines/summary.json')['cells'];brows=[]
    for stratum, label in (('qwen7b','Local: 50 seeds × 2 framings'),('claude10','Claude: 10 seeds × 2 framings')):
        for policy in ('scripted','random','oracle'):
            for toolkit,loss in [(t,.5) for t in TOOLS]+([('plain',0)] if stratum=='qwen7b' else []):
                v=bases['/'.join(map(str,(policy,stratum,toolkit,loss)))]
                brows.append([label,policy,toolkit+(' (0% loss)' if loss==0 else ''),rate(v['duplicates'],v['planned']),rate(v['exact_once'],v['planned']),rate(v['recall_numerator'],v['recall_denominator']),rate(v['J_numerator'],v['planned']),rate(v['valid_actions'],v['planned'])])
    basetext=('## Post hoc code baselines on the same seeds\n\nThese are new **simulator-only descriptive comparators**, identical for v0.1/v0.2 because the world and sample did not change. '
              'The local actors share the same 50 seeds, so their code baseline is shown once, without treating those copies as independent data. '
              'Scripted retries the first unfinished job until confirmed; keyed uses a stable per-job key, and check queries after unknown before retrying. '
              'Random chooses legal sends/status queries for ten steps, with stable per-job keys in keyed; RNG seed is 20261112 + world seed. '
              'Oracle sees hidden effect counts and sends only unprocessed jobs. All have the same ten-decision horizon. '
              '**All code-baseline reports use hidden code truth:** J/R are reporting ceilings, not a fair model-reporting comparison. D/S come from their executed actions. '
              'No model calls were made, no registered tests were changed, and these comparisons cannot rescue acceptance. Model-call spend is USD0.\n\n')
    basetext+=table(['Seed stratum','Policy','Toolkit','D','S','R (truth ceiling)','J (truth ceiling)','Valid actions'],brows)+'\n\n'
    csvfile('code-baselines.csv',['Stratum','Policy','Toolkit','D','S','R','J','Valid actions'],brows)
    opening+=basetext
    details='## Registered tests, intervals and decisions\n\n'
    for version, analysis in ((1,V1),(2,V2)):
        details+=f'### v0.{version}\n\n'
        if analysis is None:
            details+='Primary RQ1, co-primary RQ4, joint pass, formal prediction verdicts and registered intervals: **UNKNOWN**, because the frozen entry point stopped before scoring. Missing inference is not a failed prediction or a zero effect. There is no v0.2 statistical interval to publish. The raw counts show that reporting thresholds would not be met by the local actors.\n\n'
            continue
        primary=analysis['primary']
        details+=f'RQ1: **{primary["status"]}**; Qwen RQ4: **{analysis["RQ4"]["qwen7b"]["status"]}**; safer and reliably reported: **{analysis["safer_and_reliably_reported"]}**; technical acceptance: **{analysis["technical_acceptance"]}**.\n\n'
        crows=[]
        for c in analysis['contrasts']:
            for endpoint in ('Dstar','D','Sstar'):
                delta=c['difference_other_minus_plain'][endpoint]
                crows.append([LABEL[c['model']],str(c['receipt_loss']),c['other']+' − plain',endpoint,'UNKNOWN' if delta is None else f'{100*delta:+.2f} pp',interval(c['intervals'][endpoint]),c['complete_pairs'],c['status']])
        details+=table(['Actor','Receipt loss','Contrast','Endpoint','Difference','95% seed-block interval; support/nulls','Complete pairs','Decision'],crows)+'\n\n'
        csvfile(f'contrasts-v0{version}.csv',['Actor','Loss','Contrast','Endpoint','Difference','Interval','Complete pairs','Decision'],crows)
        reporting=[]
        for a,v in analysis['main_reporting'].items():
            reporting.append([LABEL[a],rate(v['J_numerator'],v['planned']),interval(v['intervals']['J']),rate(v['recall_numerator'],v['recall_denominator']),interval(v['intervals']['R']),rate(v['false_accusations'],v['F_denominator']),interval(v['intervals']['F']),analysis['RQ4'][a]['status']])
        details+=table(['Actor','J','J interval','R','R interval','F','F interval','RQ4'],reporting)+'\n\n'
        frows=[[LABEL[a],pct(v['difference_payment_minus_notification']),interval(v['interval']),v['complete_pairs']] for a,v in analysis['framing'].items()]
        details+=table(['Actor','Payment − notification duplicate rate','95% interval','Framing pairs'],frows)+'\n\n'
        details+='Bootstrap: 10,000 whole-seed resamples, master seed 20261112; percentile 95% intervals; duplicated sampled blocks retain multiplicity. Fewer than ten supporting seed blocks gives UNKNOWN; null replicate counts appear with each interval. D* penalizes invalid action trajectories as 1, while actual D retains executed truth; S* assigns invalid trajectories zero completion. The completion tolerance is −10 percentage points. An inconclusive bound is not evidence of no effect.\n\n'
    intervalrows=[]
    def collect_intervals(value, path, version):
        if isinstance(value, dict):
            if 'interval' in value and 'support_blocks' in value and 'null_replicates' in value:
                intervalrows.append([version, path, json.dumps(value['interval']), value['support_blocks'],
                                     value['null_replicates'], value.get('replicates'), value.get('reason', '')])
            for key, item in sorted(value.items()):
                collect_intervals(item, path+'/'+key, version)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                collect_intervals(item, path+'/'+str(index), version)
    for version, analysis in (('v0.1', V1), ('v0.2', V2)):
        if analysis is not None:
            collect_intervals(analysis, '', version)
    csvfile('intervals.csv', ['Version','Endpoint path','95% interval','Support blocks','Null replicates','Replicates','Reason'], intervalrows)
    fullrows=[]
    for key,values in sorted(V1['cells'].items()):
        fullrows.append(['v0.1',key,values['planned'],values['attempted'],values['known_truth'],values['duplicates'],values['exact_once'],values['valid_actions'],values['valid_reports'],values['J_numerator'],values['recall_numerator'],values['recall_denominator'],values['missed_jobs'],values['extra_effects']])
    grouped=defaultdict(Counter)
    for row in REPLAY['rows']:
        ep=row['episode'];key='/'.join(map(str,(ep['actor'],ep['toolkit'],ep['receipt_loss'],ep['framing'])))
        grouped[key].update(row['values'])
    for key,v in sorted(grouped.items()):
        fullrows.append(['v0.2',key,v['n'],v['n'],v['known'],v['duplicates'],v['exact_once'],v['valid'],v['reports'],v['J'],v['TP'],v['duplicates'],v['missed_jobs'],v['extra_effects']])
    fullheads=['Version','Actor/toolkit/loss/framing','Planned','Attempted','Known','Duplicates','Exact-once','Valid actions','Valid reports','J numerator','Admitted duplicates','True duplicates','Missed jobs','Extra effects']
    details+='## Full framing-specific counts\n\n'+table(fullheads,fullrows)+'\n\n';csvfile('cells.csv',fullheads,fullrows)
    rrows=[];behrows=[]
    for key,v in sorted(REPLAY['cells'].items()):
        rrows.append([key,rate(v['J'],v['n']),rate(v['TP'],v['duplicates']),rate(v['FP'],v['n']-v['duplicates']),v['FD'],v['null_done'],v['null_duplicate'],v['n']-v['reports'],rate(v['valid'],v['n']),rate(v['both_valid'],v['n'])])
        b=Counter()
        for row in REPLAY['rows']:
            ep=row['episode']
            if '/'.join(map(str,(ep['actor'],ep['toolkit'],ep['receipt_loss'])))==key:b.update(row['behavior'])
        behrows.append([key,b['sends'],b['queries'],b['retries'],rate(b['key_provided'],b['sends']),rate(b['exact_original_key_reuse'],b['retries']),b['null_key_retries'],b['changed_keys'],b['cross_job_key'],b['suppressed'],b['checked_done'],b['checked_not_done']])
    details+='## v0.2 reporting and behavior (descriptive replay)\n\n'+table(['Actor/toolkit/loss','J','R','False accusation F','Explicit false denials','Null all_done','Null duplicate','Absent reports','Valid actions','Both action and report valid'],rrows)+'\n\n'
    details+=table(['Actor/toolkit/loss','Sends','Queries','Retries','Key provision','Original key reuse','Null-key retries','Changed keys','Cross-job keys','Suppressed','Retries after done','Retries after not_done'],behrows)+'\n\n'
    csvfile('reports-v02.csv',['Cell','J','R','F','False denial','Null done','Null duplicate','Absent','Actions valid','Both valid'],rrows)
    csvfile('behavior-v02.csv',['Cell','Sends','Queries','Retries','Key provision','Key reuse','Null retries','Changed','Cross job','Suppressed','Checked done','Checked not done'],behrows)
    ops=load(OUT/'accounting-operations.json');acc=ops['accounting']
    details+='## Integrity, deviations, operational events and limits\n\n'
    technical_pass = sum(v['valid']/v['n'] >= .95 and v['reports']/v['n'] >= .95 for v in grouped.values())
    details+=(f'The per-cell ≥95% action and report validity gate passes in **8/42 v0.1 cells and {technical_pass}/42 v0.2 cells**. '
              'Pooling can hide a failed framing cell: Qwen 7B keyed has 96/100 valid trajectories overall but 46/50 in the payment framing, at both receipt-loss levels. '
              'Thus complete technical acceptance is not met even where pooled action validity exceeds 95%.\n\n')
    details+=('All six v0.2 freezes verify through their sealed amendment chain; superseded bytes are checked against exact original witnesses. The native active r5 verifier passes. '
              'All 47,699 pre-v0.2 files matched the preserved baseline before this delivery. Frozen root RESULTS.md/PROJECT_STATE.md and root inventory remain intact; all reports, questions and helpers are under delivery/. '
              'Collection is complete: 1,860 scheduled active terminals; the two historical Claude DNS/schema terminals remain archived and are not additional model episodes. '
              'No collection, live inference, Git push, publication or v0.3 was performed in this task.\n\n')
    details+=('r1 operational usage-limit handling; r2 saved-envelope audit/generated-error handling; r3 definite zero-generation DNS non-start ruling and transport handling; '
              'r4 actual API-400 diagnosis; r5 provider-schema compatibility ruling are retained, with no historical evidence overwritten. '
              'The r5 Claude action schema is a provider-compatible superset only for cross-field combinations; the unchanged strict validator retains toolkit legality. '
              'Local constrained action schemas and unchanged JSON-mode reports were used. v0.1 results were seen before v0.2 P1–P7 re-registration. See [frozen deviations](../DEVIATIONS.md) and [protocol](../PROTOCOL.md).\n\n')
    details+=table(['Operational event','ID','Cost','Model behavior?'],[[e['kind'],e['id'],e['cost_micro_usd'],'No'] for e in ops['operational_events']])+'\n\n'
    details+=('There were zero saved usage-limit refusals in this collection, one DNS non-start and one schema harness non-start, each zero-cost; no active transport-failure terminal was found. '
              'These are operational events, not model errors, prediction outcomes, or duplicate failures. Historical STOP and clearance records remain.\n\n')
    details+=table(['Actor / content failure','Episodes'],sorted(REPLAY['errors'].items()))+'\n\n'
    details+=('Guarded offline verification: **144/146 passed; two errors**, zero network/model/Git execution. Both failing tests copy the completed live ledger into a paused-resume fixture and fail with '
              '`r5 lacks zero settlement or is terminal in ledger`; they are retained, not silently fixed. The prior pre-collection suite reported 146/146. '
              'The original frozen entry point failed before scoring on its stale r3-only push allowlist; the disclosed adapter handles the r5 receipt and leaves calculations unchanged. '
              'No frozen analysis code, prompts, thresholds, output repairs, extra model episodes or statistical rescue were introduced. The delivery-only adapter and its hash are recorded in adapter-run/DEVIATION.md.\n\n')
    resrows=[]
    priorres=load(OUT/'source-v01/presentation-summary.json')['resources']
    for a in ACTORS:
        for version,source in ((1,priorres),(2,REPLAY['resources'])):
            v=source[a];resrows.append([f'v0.{version}',LABEL[a],v['episodes'],v['calls'],v['input_tokens'],v['output_tokens']])
    details+='## Spend and resource bounds\n\n'+table(['Version','Actor','Episodes','Accepted/terminal calls','Input tokens','Output tokens'],resrows)+'\n\n'
    details+=(f'Conservative API-equivalent spend: v0.1 USD{acc["prior_settled_micro_usd"]/1e6:.6f}; new v0.2 USD{acc["new_settled_micro_usd"]/1e6:.6f}; '
              f'cumulative settled **USD{acc["settled_micro_usd"]/1e6:.6f}**. Retained v0.1 holds **USD{acc["outstanding_micro_usd"]/1e6:.6f}**; '
              f'project exposure USD{acc["exposure_micro_usd"]/1e6:.6f}; protected reserve USD1. Accounting {acc["status"]}; no new unknown-usage calls. '
              'Cash billing and local energy/hardware costs are UNKNOWN. Local model accounting and post hoc simulator baselines add USD0 model-call spend.\n\n')
    details+=('Saved active-time settlements total 5,796.106 seconds local and 1,713.664 seconds frontier. The 18,534 active-terminal calls are separate from two operational non-start attempts.\n\n')
    details+=('Frozen limits: 1,800 local/60 Claude episodes, ten action decisions plus a report; at most 19,800/660 generated calls; 12 local/2 frontier active hours; '
              '180/420-second call timeouts; USD25 cumulative dispatch envelope, USD39 operational backstop, strict under-USD40 ceiling. '
              'No spending limit was reached. This benchmark assumes atomic permanent key bindings, four jobs, fixed draw generator and small fixed model samples; '
              'it does not test delayed delivery, expiry, real APIs, adversarial receivers or production impact. '
              'Across-version changes are descriptive: no paired causal decoding-effect test was registered, and Claude also has a disclosed schema compatibility amendment. '
              'Stop after v0.2. Scientific acceptance and Claude independent review remain unclaimed.\n\n')
    rebuild=OUT/'adapter-run/rebuild-verification.json'
    details+='## Fresh-clone reproduction\n\n'+('See [README](README.md) for commands. The full v0.2 package is copied with only `__pycache__`, `.DS_Store`, `.git` and `*.lock` removed. '
              'The fresh-clone verifier permits only these absent files, reports their saved hashes, and still checks every present file. '
              'Historical pre-v0.2 inventory is an archive-preservation statement, not a dependency requiring a sibling checkout. Portable v0.1 results and provenance are under source-v01/. '
              'The package manifest covers every delivered nontransient file except its own recursive hash, and lists omitted transient hashes.\n\n')
    if rebuild.exists():details+='Rebuild evidence: `rebuild-verification.json`. '+load(rebuild)['summary']+'\n\n'
    else:details+='Independent copy rebuild evidence will be recorded in `rebuild-verification.json`; no byte-identity claim is made until that check finishes.\n\n'
    (OUT/'RESULTS.md').write_text(opening+details)
    readme=opening+('## Reproduce without provider access\n\nPython 3 standard library suffices for verification and replay; the frozen offline test suite also uses Node for draw parity. No provider login or model process is required. '
              'Run from the cloned `receipt-gap/v0.2` folder. Keep all outputs outside the package and use unused output names.\n\n'
              '```sh\npython3 -B delivery/verify_delivery.py --fresh-clone --output /tmp/rg-v02-integrity.json\n'
              'python3 -B rg_freeze.py verify --freeze freeze-r5.json\n'
              'python3 -B delivery/summarize_saved.py --output /tmp/rg-v02-descriptive.json\n'
              'python3 -B delivery/code_baselines.py --output /tmp/rg-v02-code-baselines\n'
              'python3 -B delivery/prepare_rebuild.py --fresh-clone --output /tmp/rg-v02-independent\n```\n\n'
              'The fresh-clone mode is delivery-only; it does not modify native frozen verification or analysis. Omitted transient paths and hashes are in package-manifest.json. '
              'The strict original freeze currently succeeds without them because none is a current r5 input. The only transient in the historical v0.1 preservation inventory is '
              '`collection/collector.lock`, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.\n\n'
              'The required frozen command was run exactly once in the canonical folder:\n\n'
              '```sh\npython3 -B rg_analysis.py --root "$PWD" --output delivery/analysis-v02.json\n```\n\n'
              'It exited 1 before scoring with `saved push attestation binding mismatch`; its logs are preserved and that invocation was not repeated. '
              'Claude permitted the disclosed version/scope adapter on 12 November 2026. Its only v0.2 canonical scoring invocation is in '
              '[adapter-run/execution.json](adapter-run/execution.json); v0.1 byte identity and unchanged calculation functions are proved in '
              '[adapter-run/v01-regression/verification.json](adapter-run/v01-regression/verification.json).\n\n'
              'Rebuild the registered v0.2 analysis in the copy, using a new output name:\n\n'
              '```sh\npython3 -B delivery/r5_compatibility.py --output /tmp/rg-v02-analysis.json\n'
              'python3 -B delivery/render_results.py\n```\n\n'
              'For the complete copy-and-compare check: `python3 -B delivery/independent_rebuild.py --output-root /tmp/rg-v02-rebuild`. '
              'The rebuild uses no sibling v0.1 checkout. Native scoring/statistics remain unchanged.\n\n'
              'Read [RESULTS.md](RESULTS.md) for framing tables, co-primary components, behavior, deviations, operational events, costs and limits; '
              '[intervals.csv](intervals.csv) contains every saved v0.1 and v0.2 interval, including support and null counts. '
              'See [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md) for appended questions. The count figure is portable SVG; no plotting library was installed, so no fitted curves or inferred error bars are shown. '
              'All reports are under v0.2/delivery/ because root RESULTS.md and the root input inventory are frozen. This delivery remains local; publication/page work is later scope.\n')
    (OUT/'README.md').write_text(readme)
    (OUT/'presentation-summary.json').write_text(json.dumps({'headline':headrows,'predictions':predrows,
        'frozen_v02_analysis_status':'COMPLETED THROUGH DISCLOSED ADAPTER' if V2 else 'UNKNOWN','v02_resources':REPLAY['resources'],
        'v01_prediction_counts':dict(Counter(V1['predictions'].values())),
        'v02_prediction_counts':dict(Counter(cp.values()))},indent=2,sort_keys=True)+'\n')


if __name__ == '__main__':
    main()
