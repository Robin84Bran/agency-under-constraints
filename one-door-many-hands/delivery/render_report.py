"""Post-analysis presentation only. Reads the frozen result; never calls a model."""
import argparse
import csv
import html
import io
import json
from collections import Counter
from pathlib import Path

ACTORS = {'qwen7b': 'Qwen 2.5 7B', 'llama8b': 'Llama 3.1 8B', 'qwen1b': 'Qwen 2.5 1.5B', 'claude': 'Claude Opus 5.5'}
CONDITIONS = [(m, e) for m in ('independent', 'common') for e in ('rules', 'rehearsal')]


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|'] + ['| ' + ' | '.join(str(v) for v in row) + ' |' for row in rows])


def aggregate(rows):
    n = len(rows)
    return {'assigned': n, **{k: sum(r[k] for r in rows) / n for k in ('regret', 'optimal', 'operational_value', 'schema_valid')},
            'valid_count': sum(r['schema_valid'] for r in rows), 'optimal_count': sum(r['optimal'] for r in rows),
            'null_count': sum(r['schema_valid'] and r['fleet'] is None for r in rows),
            'technical_count': sum(r['attempted'] and not r['schema_valid'] for r in rows)}


def pct(v):
    return f'{100*v:.1f}%'


def triple(r):
    return f"{r['regret']:.3f} / {pct(r['optimal'])} / {pct(r['schema_valid'])}"


def csv_text(rows):
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    for r in rows:
        w.writerow({k: json.dumps(v, sort_keys=True, separators=(',', ':')) if isinstance(v, (dict, list)) else v for k, v in r.items()})
    return f.getvalue()


def figure(headline):
    # Standalone, accessible SVG with values printed beside every bar.
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="815" viewBox="0 0 1160 815" role="img" aria-labelledby="title desc">',
             '<title id="title">One Door, Many Hands: rules and rehearsal</title>',
             '<desc id="desc">Sixteen actor and condition rows. Expected deadline regret, exact optimal choices, and schema-valid rates. Lower regret and higher optimal rates are better. All doors pooled. Claude uses ten blocks; local models use one hundred.</desc>',
             '<rect width="1160" height="815" fill="#fff"/>',
             '<style>text{font-family:Arial,sans-serif;fill:#152235;font-size:13px}.small{font-size:12px}</style>',
             '<text x="20" y="30" font-size="21">Worked examples did not improve the registered primary outcome</text>',
             '<text x="20" y="54">All assigned decisions; intentional nulls and technical failures retain their penalties</text>',
             '<text x="20" y="87">Actor / failure mode / evidence</text>',
             '<text x="425" y="87">Regret (lower is better)</text>',
             '<text x="730" y="87">Optimal choices (higher is better)</text>',
             '<text x="1050" y="87">Valid</text>']
    for i, r in enumerate(headline):
        y = 120 + i * 40
        color = '#087f8c' if r['evidence'] == 'rules' else '#c24e32'
        label = f"{ACTORS[r['actor']]} / {'indep.' if r['mode']=='independent' else 'common'} / {r['evidence']}"
        parts += [f'<text x="20" y="{y+14}">{html.escape(label)}</text>',
                  f'<rect x="425" y="{y}" width="240" height="19" fill="#f0f2f5"/>',
                  f'<rect x="425" y="{y}" width="{240*r["regret"]:.3f}" height="19" fill="{color}"/>',
                  f'<text x="675" y="{y+14}">{r["regret"]:.3f}</text>',
                  f'<rect x="730" y="{y}" width="235" height="19" fill="#f0f2f5"/>',
                  f'<rect x="730" y="{y}" width="{235*r["optimal"]:.3f}" height="19" fill="{color}"/>',
                  f'<text x="975" y="{y+14}">{pct(r["optimal"])}</text>',
                  f'<text x="1050" y="{y+14}">{pct(r["schema_valid"])}</text>']
    parts += ['<text x="20" y="782" class="small">Each row: 300 decisions per local actor; 30 per Claude condition. Failure modes and evidence are pre-registered.</text>',
              '<text x="20" y="802" class="small">Bars use 0–1 scales. Primary: Qwen 7B, independent failure; other actor and mechanism contrasts are descriptive.</text>', '</svg>']
    return '\n'.join(parts) + '\n'


def render(root, analysis, out):
    x = json.loads(analysis.read_text())
    assert x['kind'] == 'FROZEN_ANALYSIS'
    rows = x['rows']
    headline = []
    for a in ACTORS:
        for m, e in CONDITIONS:
            rs = [r for r in rows if (r['actor'], r['mode'], r['evidence']) == (a, m, e)]
            headline.append(dict(actor=a, mode=m, evidence=e, **aggregate(rs)))
    headline_table = table(['Actor', 'Failure mode', 'Evidence', 'Assigned', 'Mean R* ↓', 'Optimal O* ↑', 'Schema-valid', 'Null', 'Technical'],
                           [[ACTORS[r['actor']], r['mode'], r['evidence'], r['assigned'], f"{r['regret']:.4f}", f"{r['optimal_count']}/{r['assigned']} ({pct(r['optimal'])})", f"{r['valid_count']}/{r['assigned']} ({pct(r['schema_valid'])})", r['null_count'], r['technical_count']] for r in headline])
    primary = x['contrasts']['qwen7b/independent']
    cells = []
    for k, c in sorted(x['cells'].items()):
        a, door, m, e = k.split('/')
        cells.append(dict(actor=a, door=int(door[4:]), mode=m, evidence=e, **c, elapsed_seconds=x['elapsed_seconds_by_cell'].get(k)))
    contrasts = [dict(actor=k.split('/')[0], mode=k.split('/')[1], **{n:v for n,v in c.items() if n != 'paired_choices'}) for k,c in sorted(x['contrasts'].items())]
    pairs = [dict(actor=k.split('/')[0], mode=k.split('/')[1], **p) for k,c in sorted(x['contrasts'].items()) for p in c['paired_choices']]
    # Registered code baselines are reused from their frozen per-episode scores.
    b = json.loads((root/'config/baselines.json').read_text())['rows']
    baseline = []
    for grid, blocks in [('local100', set(range(100))), ('claude10', {r['block'] for r in rows if r['actor']=='claude'})]:
        ep = {r['id']:r for r in rows if r['actor']=='qwen7b' and r['block'] in blocks}
        policies = dict(b)
        # Exact uniform-policy expectation, no random draw or new seed. Post hoc.
        policies['uniform_random_POST_HOC'] = [dict(id=z['id'], fleet=None, **{k:sum(b[n][i][k] for n in ('always1','always6','always24'))/3 for k in ('regret','optimal','operational_value')}) for i,z in enumerate(b['always1'])]
        for name, scored in policies.items():
            selected = [dict(ep[z['id']], **{k:v for k,v in z.items() if k != 'id'}, schema_valid=True) for z in scored if z['id'] in ep]
            for m,e in CONDITIONS:
                for door in (0,1,6,24):
                    rs = [r for r in selected if r['mode']==m and r['evidence']==e and (door==0 or r['door']==door)]
                    summary = aggregate(rs)
                    if name == 'uniform_random_POST_HOC':
                        summary['null_count'] = 0  # Every random action is a legal non-null fleet.
                    baseline.append(dict(grid=grid, policy=name, mode=m, evidence=e, door='all' if door==0 else door, **summary))
    code_tables=[]
    for grid in ('local100','claude10'):
        br=[r for r in baseline if r['grid']==grid and r['door']=='all']
        code_tables.append(f"### {'100-block local grid' if grid=='local100' else '10-block Claude grid'}\n\n" + table(['Code policy','Independent rules','Independent rehearsal','Common rules','Common rehearsal'], [[name]+[triple(next(r for r in br if r['policy']==name and (r['mode'],r['evidence'])==(m,e))) for m,e in CONDITIONS] for name in list(b)+['uniform_random_POST_HOC']]))
    predtext = [
        ['P1','Joint Qwen 7B improvement rule passes','Failed','D_R = −0.10990; D_O = −13.0 percentage points; rehearsal optimal 64/300 (21.3%)'],
        ['P2','Qwen independent door=1 rehearsal optimal ≥90%','Failed','2/100 (2%); rules 14/100 (14%); difference −12 points'],
        ['P3','Qwen independent door=6 rules chooses 24 carriers ≥10%','Held','36/100 (36%); 24 carriers cannot deliver target ≥7 through six admissions'],
        ['P4','Qwen common rehearsal optimal ≥90%','Failed','93/300 (31%)'],
        ['P5','Llama and Claude each show positive D_R and D_O','Failed','Llama −0.04868 / −10.67 points; Claude 0 / 0; 660 assigned independent decisions combined']]
    def interval(v): return '['+', '.join(f'{z:.5f}' for z in v)+']'
    contrast_table=table(['Actor / mode','Blocks / pairs','D_R [95% interval]','D_O [95% interval]','Rehearsal optimal'], [[ACTORS[r['actor']]+' / '+r['mode'],f"{r['blocks']} / {r['pairs']}",f"{r['D_R']:.5f} {interval(r['D_R_interval'])}",f"{r['D_O']:.5f} {interval(r['D_O_interval'])}",pct(r['rehearsal_optimal_rate'])] for r in contrasts])
    valid_table=table(['Actor','Assigned / attempted','Overall valid','Every cell gate','Technical gate'], [[ACTORS[a],f"{v['registered']} / {sum(r['attempted'] for r in rows if r['actor']==a)}",pct(v['overall_validity']),'PASS' if v['cell_validity'] else 'FAIL',v['status']] for a,v in x['technical_acceptance'].items()])
    resource_rows=[]
    for a in ACTORS:
        for e in ('rules','rehearsal'):
            rs=[r for r in rows if r['actor']==a and r['evidence']==e]
            us=[r['usage'] for r in rs if r['usage'] is not None]
            cs=[r for r in cells if r['actor']==a and r['evidence']==e]
            resource_rows.append(dict(actor=a,evidence=e,calls=len(rs),fresh_input=sum(u['input'] for u in us),cache_creation=sum(u['cache_creation'] for u in us),cache_read=sum(u['cache_read'] for u in us),output=sum(u['output'] for u in us),seconds=sum(r['elapsed_seconds'] for r in cs),api_equivalent_usd=sum(r['api_equivalent_micro_usd'] for r in cs)/1e6))
    resource_table=table(['Actor / evidence','Calls','Fresh input','Cache create / read','Output incl. thinking','Terminal seconds','API-equiv. USD'],[[ACTORS[r['actor']]+' / '+r['evidence'],r['calls'],r['fresh_input'],f"{r['cache_creation']} / {r['cache_read']}",r['output'],f"{r['seconds']:.3f}",f"{r['api_equivalent_usd']:.6f}"] for r in resource_rows])
    discordance=table(['Actor / mode','Wrong→wrong','Wrong→optimal','Optimal→wrong','Optimal→optimal'], [[ACTORS[r['actor']]+' / '+r['mode']]+[r['choice_discordance'].get(k,0) for k in ('0->0','0->1','1->0','1->1')] for r in contrasts])
    fullcells=table(['Actor','Door','Failure','Evidence','Assigned / attempted','R*','O*','V*','Valid','Null / technical','Choices 1 / 6 / 24','E[work] chosen','P[outage] chosen'], [[ACTORS[r['actor']],r['door'],r['mode'],r['evidence'],f"{r['assigned']} / {r['attempted']}",f"{r['regret']:.5f}",pct(r['optimal']),f"{r['operational_value']:.5f}",f"{r['schema_valid']}/{r['assigned']}",f"{r['null']} / {r['technical']}",' / '.join(str(r['choices'].get(str(n),0)) for n in (1,6,24)),f"{r['chosen_work']:.5f}" if r['chosen_work'] is not None else 'UNKNOWN',f"{r['chosen_outage']:.6g}" if r['chosen_outage'] is not None else 'UNKNOWN'] for r in cells])
    frequencies=json.loads((root/'config/oracle.json').read_text())['optimal_set_frequencies']
    oracle_table=table(['Failure / door / optimal fleet set','Cells on 100-block grid'],sorted(frequencies.items()))
    events=x['ledger']['operational_events']['events']
    event_table=table(['Operational event','Episode / attempt','Finished UTC','Reset UTC','Cost'],[[r['kind'],r['attempt_id'],r['finished_at'],r['reset_at'],'USD0'] for r in events])
    gates = table(['Registered joint component','Observed','Outcome'],[
        ['All 600 primary decisions attempted','600/600','PASS'],['Schema-valid ≥95% in each primary cell','100/100 in each of six cells','PASS'],
        ['D_R ≥0.05',f"{primary['D_R']:.5f}",'FAIL'],['D_R lower 95% bound >0',f"{primary['D_R_interval'][0]:.5f}",'FAIL'],
        ['D_O lower 95% bound >0',f"{primary['D_O_interval'][0]:.5f}",'FAIL'],['Rehearsal optimal ≥75%','64/300 = 21.3%','FAIL'],['Rehearsal null / all 600 primary ≤5%','0/600 (also 0/300 rehearsal)','PASS']])
    text=f'''# One Door, Many Hands — final D3 results

**Hypothesis:** Adding failure-free worked examples of deliveries helps models choose fleets that maximize the chance of meeting a deadline, compared with complete written rules alone.

**Joint primary: FAIL.** Rehearsal increased Qwen 7B's mean expected deadline regret from 0.27420 to 0.38410 and reduced exact optimal choices from 103/300 (34.3%) to 64/300 (21.3%) under independent damage. Its paired D_R was −0.10990, 95% interval [−0.13904, −0.08071]; D_O was −13.0 percentage points [−20.33, −6.00]. The observed change was in the opposite direction to the prediction. All four actors completed their assigned episodes and passed the registered technical-validity gates.

**The rehearsal adds no information beyond the rules. A pass would mean models use worked examples better than complete written rules in this task.** This study measures fleet planning in a fixed one-wave simulator. It does not measure real multi-agent execution or resilience.

## Predictions, registered before responses

{table(['ID','Prediction','Held / failed','Observed'],predtext)}

## Comparisons a reader asks first

R* is mean expected deadline regret (lower is better); O* is the exact optimal-choice rate with abstentions and technical failures scored as misses; schema-valid includes explicit null. All three doors receive equal weight. These are absolute outcome levels underlying the primary paired contrast. Local actors each use 100 blocks; Claude uses the preselected ten-block subset, so this table does not establish an actor ranking. Every actor × failure mechanism × evidence condition appears below.

{headline_table}

![Regret, optimal choices and validity for every actor and condition](headline.svg)

Claude made 118 valid non-null choices, all exact optima. Both penalized episodes were the same independent door=24 block (71, target=8, failure=62%): rules hit an output limit and rehearsal was rejected by the provider's structured-output machinery. The assigned scores retain both failures. They do not establish that Claude chose a wrong fleet or lacked the task knowledge. Qwen 7B's 87 intentional nulls all occurred under common damage (57 rules, 30 rehearsal); they remain separate from technical failures.

## Code baselines on the identical seeds

These are secondary code policies, not model observations or replacements for the primary. Each entry is **R* / O* / schema-valid rate**, pooled over three doors. Rules and rehearsal contain the same world, so code-policy scores are identical across evidence arms. Each local-grid condition has 300 assignments; each Claude-grid condition has 30. Constant fleets, max expected work, minimum outage, exact oracle and all-null were frozen before collection. Heuristic ties select the first ascending fleet; exact-optimum scoring accepts every tie. Uniform random is a **post hoc**, exact expectation over the three legal fleets at each frozen cell, with no sampled random sequence, model calls, or extra seeds. All-null is a valid schema object with zero useful choices. Code policies have no inference token spend; compute, hardware and electricity costs were not measured.

{chr(10).join(code_tables)}

Door-level baseline scores, including V*, are in [baseline-cells.csv](baseline-cells.csv). No oracle, rule engine or random policy was sent to a model.

## Joint rule and paired intervals

{gates}

{contrast_table}

Only Qwen 7B under independent damage is confirmatory. The other seven actor/mechanism contrasts are descriptive. Intervals reproduce the frozen paired-block percentile bootstrap: 10,000 resamples, seed 20261112, preserving repeated-block multiplicity and all three doors. They describe sensitivity over this fixed numeric grid conditional on one saved reply per prompt; they do not cover all tasks or full generation variance. Complete-valid-pair sensitivity retains all 300 Qwen independent pairs and gives identical primary point estimates and intervals. No post-result sample or alternative significance test was added.

Paired exact-choice discordance (0 means nonoptimal, null or technical miss; 1 means an exact optimum):

{discordance}

The exact paired fleet choices are in [paired-choices.csv](paired-choices.csv), and full-precision bootstrap results remain in [analysis-final-d3.json](../collection/analysis-final-d3.json).

## Full model cells

All 48 actor × door × mechanism × evidence cells follow. R*, O* and V* use assigned denominators. Factual chosen-work and chosen-outage means use only schema-valid non-null choices; unavailable choices have null factual values in the saved analysis. Work is expected delivered units and outage means all carriers fail, not the probability of missing the deadline. No unstarted episode remains. [model-cells.csv](model-cells.csv) additionally includes tokens, seconds, cost, failure reasons and full precision.

{fullcells}

## Oracle and common-damage controls

{oracle_table}

Under common damage every feasible fleet ties at success probability 1−p. Door=1 accepts only fleet 1 as feasible; door=6 accepts 1 and 6; door=24 accepts all three on this target grid. All 300 common cells therefore include fleet 1 in the optimum; 200 have ties. Independent cells have no ties. Claude's subset has 30 independent and 30 common world cells; its exact sets can be selected by blocks from [the frozen 600-cell rational oracle](../config/oracle.json). Identical values and ties apply in both evidence arms. Common-damage failures indicate objective or feasibility errors; they do not show hidden redundancy.

## Validity, failure modes and resources

{valid_table}

All local cells are 100% schema-valid. Claude is 118/120 (98.33%) valid overall; its two affected cells each have 9/10, meeting the frozen ≥90% per-cell and ≥95% overall rules. The local threshold is ≥95% per cell. Schema validity does not imply a useful decision. There were no local technical failures, no local transport failures and no unstarted decisions. The two Claude failures are retained as technical episode misses under the frozen scoring; output and schema limits do not constitute evidence about the model's preferred fleet.

{resource_table}

Settled API-equivalent spend is **USD1.925098**, open holds **USD0**, and the paid ledger has 246 events (123 reservations and 123 settlements: 120 generated episodes plus three operational nonstarts). The historical USD4/input-million and USD20/output-million planning basis and cache categories are documented in [cost-basis.json](../evidence/cost-basis.json); totals use independently decoded settled usage and reported cost, not that simple reservation alone. Thinking is already included in output and is never charged twice. Cash billed is **UNKNOWN** (`null`); these calls used subscription accounting. Local inference API spend is USD0; hardware, electricity, subscription allocation and opportunity costs are UNKNOWN.

Active collector time: local {x['ledger']['active_seconds']['local']:.3f}s / 28,800s; Claude {x['ledger']['active_seconds']['claude']:.3f}s / 7,200s. The table shows terminal-minus-start durations and excludes nonstart attempts; charged active time also includes preflight/collector activity. Waiting for quota resets is not generation latency. All calls are below the USD25 frontier envelope, USD39 project stop and USD40 absolute ceiling, with the USD1 protected reserve retained. No spending extension occurred. Frozen timeouts were 180s local and 300s Claude; generation controls were 192 local output tokens and 512 Claude accounted output tokens (576 was a padded reservation, not a scientific output cap). Rehearsal uses additional input; there is no equal-token or cost-adjusted superiority claim.

## Operational events and deviations

{event_table}

The two zero-use usage-limit refusals and one verified pre-generation ENOTFOUND/DNS failure are operational nonstarts, not model behaviour or model technical failures. Their raw bytes, request hashes, zero settlements and timer charges are retained. Only the eventual generated reply at each assigned position enters the scientific score. Resume requests preserve the original bytes. Generated attempts were never resent. The accounting clearance also records one reservation overrun: USD0.022088 actual against USD0.021248 held, an excess of USD0.000840. It is an accounting event; the separately observed missing/length-limited payload retains its technical penalty. There are no later saved accounting-excess markers.

All applied amendments are preserved in [DEVIATIONS.md](../DEVIATIONS.md) and their immutable freezes:

- **r1 / A1 before collection:** preserve the standalone study and representation claim; correct episode-content versus integrity routing, first-call handling, schema/metadata validation, no-resend recovery and push checks. Prompts, scientific scores, schedule, settings and denominators stay fixed.
- **D1 and final recovery guard after the A1 push:** classify exact zero-use limits as nonstarts, retain identical pending requests and append-only attempt evidence, and isolate later fatal stops. The sealed D1 draft was not used for calls.
- **D2 after the saved DNS stop:** classify the exact complete zero-use ENOTFOUND envelope as a verified nonstart; repair generated-envelope routing and accept supported two-turn structured replies. The saved DNS episode was not a behavioural failure. Original STOPs, raw bytes and terminals remain intact.
- **D3 after the saved reservation excess:** settle measured cumulative usage for the narrow budget-stop envelope, separate reservation overruns from scientific scores, and enlarge future holds from prior measured maxima plus 10% without changing scientific output controls. All parent evidence remains bound.
- **Analysis invocation, post-collection:** the runbook's relative `--data collection` command stopped in provenance replay because an absolute `ROOT` was compared with a relative data path. It wrote no analysis and reached no bootstrap/statistics. The invocation was corrected to absolute root/data/output paths, without editing frozen code or prompts. Exactly one completed canonical scientific analysis was produced; the required independent copy rebuild is a verification replay, not new collection.
- **Post hoc presentation:** aggregate headline levels, baseline views on the fixed Claude subset, exact uniform-random expectations and the figure are labeled descriptive presentation. They do not change any registered endpoint, interval, pass rule or prediction.

## Integrity and reproduction

All six freezes verify through their exact current or archived bytes (65 original, 86 A1, 181 D1 draft, 192 D1 final, 218 D2, 245 D3 bound files). All three collection baselines and append-only prefixes verify. The original GitHub activity receipt records commit `f8f9486612d16140eb4f3e36314a6c01737efb65`, pushed 2026-11-11 10:58:59 UTC, before collection; later local deviations have their retained attestations. No new publication or push was performed for this delivery.

The root RESULTS.md, PROJECT_STATE.md and other Markdown inputs remain frozen historical records. Final RESULTS.md, README.md, the figure and presentation/reproduction tools are under **delivery/** to preserve the input set. See [README.md](README.md) for fresh-clone commands and [rebuild-verification.json](rebuild-verification.json) for copy/rebuild byte comparisons. The package excludes only `__pycache__`, `.DS_Store`, `.git` and `*.lock` paths. Removed files and saved hashes are listed in [package-snapshot.json](package-snapshot.json). None of those paths is frozen or baseline-bound, so the ordinary frozen verifier passes after removal; no relaxed fresh-clone mode, monkey-patch, recreated lock, or skipped evidence is needed. Frozen archives retain their original internal bytes.

## Interpretation and limits

The primary prediction failed plainly. These worked examples did not help Qwen 7B; they worsened both registered outcomes on this fixed grid. Llama also has negative independent point estimates; Qwen 1.5B's descriptive independent interval spans zero. Claude is at the valid-choice ceiling on ten preselected blocks, and equal penalized failure counts leave its evidence contrast exactly zero. A tie at this ceiling cannot establish that rehearsal is universally useless, and the smaller fixed Claude subset cannot support a model ranking.

The pattern is **consistent with** smaller models misusing the failure-free delivery representation, or with prompt length, attention or objective confusion. Those mechanisms were not tested. The rehearsal contains no new world facts or future-damage evidence. This experiment has one-shot choices, a one-wave bottleneck, fixed targets/failure probabilities, seeded local sampling and one saved generation per prompt. It does not test actual teams, queuing, retries, repairs, return trips or other tasks. Independent exact input-token completeness remains UNKNOWN without an independent expected tokenizer count; retained identity/context checks show no detected loss but do not prove completeness. Missing returned effort remains UNKNOWN where absent. The study relates to The Useful Core's feasibility theme but is a separate experiment.

Scientific failure and technical completion are separate: the joint scientific claim fails, all actor technical gates pass, and independent Claude delivery acceptance remains pending. No result-dependent collection, prompt change, endpoint change or new version was introduced.
'''
    outputs={'RESULTS.md':text,'headline.csv':csv_text(headline),'headline.svg':figure(headline),'model-cells.csv':csv_text(cells),'baseline-cells.csv':csv_text(baseline),'contrasts.csv':csv_text(contrasts),'paired-choices.csv':csv_text(pairs),'resources.csv':csv_text(resource_rows),'operational-events.json':json.dumps(x['ledger']['operational_events'],indent=2,sort_keys=True)+'\n'}
    out.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        with (out/name).open('x', encoding='utf-8', newline='') as f: f.write(content)
    print(json.dumps({'rendered':list(outputs),'joint_primary':x['joint_primary']},sort_keys=True))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--analysis',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve()
    render(root,a.analysis.resolve() if a.analysis else root/'collection/analysis-final-d3.json',a.output.resolve())
