#!/usr/bin/env python3
"""Post-analysis presentation only: read the single frozen analysis, never rerun it."""
import collections
import csv
import hashlib
import html
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT/'collection/analysis-claude-envelope.json'
X = json.loads(SOURCE.read_text())
ACTORS = [('qwen7b','Qwen 7B'),('llama8b','Llama 8B'),('qwen1b','Qwen 1.5B'),('claude','Claude')]
WORLDS = ['different-stable','same-stable','stale-remap']
ARMS = ['keyed','shared','discard']
BASELINES = ['uniform','last-console','keyed-ledger','oracle']
B = json.loads((ROOT/'config/baselines.json').read_text())


def write(name, text):
    with (OUT/name).open('x') as f:
        f.write(text)


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'


def pct(x):
    return 'UNKNOWN' if x is None else f'{100*x:.2f}%'


def interval(value):
    if value['mean'] is None:
        return 'UNKNOWN'
    return f"{100*value['mean']:+.3f} [{100*value['interval'][0]:+.3f}, {100*value['interval'][1]:+.3f}]"


def tokens(t):
    def n(x): return 'UNKNOWN' if x is None else f'{x:.2f}' if isinstance(x,float) else str(x)
    return '/'.join(n(t[k]) for k in ['count','sum','mean','median','max','missing_usage','unstarted_calls'])


def cell(actor,world,arm):
    c = X['cells'].get('/'.join([actor,world,arm]))
    return 'not scheduled' if c is None else f"{pct(c['Y'])} / {pct(c['F'])} / {pct(c['technical_complete']/c['episodes'])}"


def csvfile(name, fields, rows):
    with (OUT/name).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)


def main():
    headline=[]
    baseline_rows=[]
    for actor,label in ACTORS:
        for world in WORLDS:
            c=X['cells'].get('/'.join([actor,world,'keyed']))
            headline.append([label,world,c['episodes'] if c else '0',*[cell(actor,world,a) for a in ARMS]])
            if c:
                n=c['episodes'];parts=[]
                for kind in BASELINES:
                    rs=[r for r in B if r['world']==world and r['kind']==kind and r['seed']<n]
                    assert len(rs)==n
                    parts.append(f"{pct(statistics.mean(r['Y'] for r in rs))} / {pct(statistics.mean(r['F'] for r in rs))} / 100%")
                baseline_rows.append([label,world,f'0–{n-1}',*parts])
    headline_table=table(['Actor','Condition','N / arm','Keyed Y / F / valid','Shared Y / F / valid','Discard Y / F / valid'],headline)
    baseline_table=table(['Matched actor seeds','Condition','Seeds','Uniform Y / F / executable','Last-console Y / F / executable','Keyed-ledger Y / F / executable','Oracle Y / F / executable'],baseline_rows)
    hypothesis='Automatically routing a model’s own notes to the right console improves its later actions compared with letting it manage a shared notebook.'
    predictions='P1 failed; P2 failed; P3 held; P4 failed; P5 held; P6 failed; P7 failed. These are re-registered v0.2 predictions informed by the stopped v0.1 cohort.'
    intro=f'''# The Portable Self v0.2 — results

Hypothesis: {hypothesis}

Predictions: **{predictions}**

**The joint primary claim failed.** On distinct stable mappings, Qwen 7B scored **6.125% keyed versus 15.8125% shared** correct actions: ΔY = **−9.6875 percentage points**, 95% interval **[−13.1266, −6.3125]**. Complete-return performance was **0.75% versus 3.00%**, ΔF = **−2.25 points [−4.25, −0.50]**. All four joint conditions failed. Low technical validity also prevents the agreed full-study acceptance; this delivery does not assert ACCEPTED.

All 1,080 scheduled episodes were attempted and sealed: 1,020 local and 60 Claude. Whole-episode validity is 695/1,080 (64.35%); it measures eight compliant replies, not task correctness. Claude’s shared and keyed stable scores both reached 100%, so routing had no advantage there; both fell to zero after remapping.

Each entry below is **Y / F / valid-episode rate**. Y counts correct actions out of 16 planned; F counts fully correct four-action returns out of four planned. Abstentions and missing actions are operational misses; their factual correctness stays null. N is the number of seed blocks per arm. Every model/condition/arm is shown; Claude same-stable was never scheduled.

{headline_table}
![Primary outcome by actor, condition and arm](headline.svg)

Secondary, frozen code-only references on **the same seeds as each actor** follow. They do not make model calls. “Executable” is 100% deterministic policy execution, not model schema validity. The uniform policy is a seeded sample (25% expected per action; 1/256 expected complete random return), not a fitted chance line. The last-console buffer uses only the last demonstration; keyed-ledger uses only each console’s demonstrations. Oracle alone sees remapped truth and is a ceiling. They are standalone policies, not extra memory arms.

{baseline_table}
These comparisons concern a synthetic four-console task. They are consistent with useful persistent memory in Claude and stale-note use after remapping, but no semantic-memory or causal mediation mechanism was tested. Routing changes visible context as well as storage access; the prompt-token confound remains.

'''
    detail='''## Joint primary test and predictions

The frozen analysis uses 100 Qwen 7B different-stable seed pairs, equal weights, 10,000 paired bootstrap replicates, Python RNG seed 20261112 and two-sided 95% percentile intervals with linear interpolation. Units are seed blocks, not individual actions. Intervals describe these generated tasks and saved first replies, not population-wide model rankings or real-world tasks. All secondary contrasts below are descriptive; no multiplicity correction or superiority promotion was added.

'''
    p=X['primary'];s=p['complete_pair_sensitivity']
    detail+=table(['Joint condition','Observed','Decision'],[
        ['ΔY ≥10 points; lower bound >0',interval(p['contrast']['Y']),'failed'],
        ['ΔF >0; lower bound >0',interval(p['contrast']['F']),'failed'],
        ['200 attempted; ≥95 valid episodes in each arm','200 attempted; keyed 62/100, shared 87/100','failed'],
        ['≥95 complete pairs; complete-pair ΔY lower bound >0',f"53 pairs; {interval(s['Y'])}",'failed']])
    detail+=f"\nComplete-pair ΔF: {interval(s['F'])}; this predeclared sensitivity does not rescue the primary. Complete-pair prompt summaries (count/sum/mean/median/max/missing/unstarted): keyed **{tokens(s['prompt_tokens']['left'])}**, shared **{tokens(s['prompt_tokens']['right'])}**.\n\n"
    detail+=table(['ID','Pre-registered prediction','Observed evidence','Decision'],[
        ['P1','Qwen 7B joint primary passes','All four conditions false','failed'],
        ['P2','Llama stable ΔY>0 and ΔF>0','ΔY +0.250 points; ΔF 0 (tie fails)','failed'],
        ['P3','Stable keyed beats discard in Qwen 7B and Llama','ΔY +2.125 and +0.875 points','held'],
        ['P4','Same-stable advantage smaller, matched seeds 0–19','Qwen: −41.250 vs −8.750 points (held); Llama: +1.250 vs +0.9375 (failed)','failed'],
        ['P5','Stale keyed Y below stable keyed Y, seeds 0–19','Qwen: 3.4375% <4.6875%; Llama: 0.9375% <1.2500%','held'],
        ['P6','Claude stable keyed-minus-shared Y>0','100% −100%=0 (tie fails)','failed'],
        ['P7','≥95% whole-episode validity in every cell','Only 6/33 cells meet ≥95%; 27 fail','failed']])
    # Derive the cell count rather than trusting presentation literals.
    assert sum(c['technical_complete']/c['episodes']>=.95 for c in X['cells'].values())==6
    detail+='\nP5 is evaluated using the frozen episode-level Y rule, despite its short “first-return” wording. No new first-return test was substituted. Full return-position data are in episodes.csv and the frozen JSON.\n\n## Full cell tables\n\n'
    rows=[]
    for k,c in X['cells'].items():
        rs=[r for r in X['episodes'] if '/'.join([r['actor'],r['world'],r['arm']])==k]
        answered=sum(r['answered'] for r in rs);correct=sum(r['Y']*16 for r in rs)
        rows.append([k,c['episodes'],c['attempted'],c['technical_complete'],pct(c['Y']),pct(c['F']),answered,pct(correct/answered) if answered else 'UNKNOWN',c['nulls'],c['known_wrong'],c['technical_missing']])
    detail+=table(['Actor / condition / arm','N','Attempted','Valid','Y','F','Answered /16N','Answered-only accuracy','Explicit nulls','Known wrong','Technical/missing'],rows)
    detail+='\nAnswered-only accuracy is conditional and cannot replace Y or F. Null factual values were not converted to known failures. Across 17,280 targets: 1,160 correct, 2,089 known wrong, 7,871 explicit abstentions and 6,160 technical/missing.\n\n'
    assert sum(r['known_wrong'] for r in X['episodes'])==2089
    detail+=table(['Actor / condition / arm','Input count/sum/mean/median/max/missing/unstarted','Output tokens','Call wall seconds (known only)','Accounted model-call USD'],[
        [k,tokens(c['prompt_tokens']),c['output_tokens'],f"{c['wall_seconds']:.6f}",f"{c['model_call_micro_usd']/1e6:.6f}"] for k,c in X['cells'].items()])
    detail+='\n## Every frozen contrast, with prompt context\n\nAll effects and interval bounds below are **percentage points**. The input summaries beside each effect are **count / sum / mean / median / maximum / missing-usage calls / unstarted calls**. Prompt sums exclude unavailable usage; missing values are not zeros. Left/right correspond to the contrast name. Stale-minus-stable uses the paired intersection of seeds (0–19 local, 0–9 Claude), not the full stable denominator. P4 uses stable seeds 0–19 as specified above.\n\n'
    detail+=table(['Frozen contrast','Pairs','Complete pairs','ΔY [95% interval]','ΔF [95% interval]','Left input summary','Right input summary'],[
        [k,c['Y']['n'],c['complete_pairs'],interval(c['Y']),interval(c['F']),tokens(c['prompt_tokens']['left']),tokens(c['prompt_tokens']['right'])] for k,c in X['contrasts'].items()])
    detail+='\n## Interface outcomes and operational events\n\n'
    errors=collections.Counter(c['error'] for r in X['episodes'] for c in r['calls'] if c['error'])
    detail+=table(['Saved replay diagnosis','Episodes','Classification'],[
        [k,v,'operational; retain fixed scoring denominator' if ('length' in k or 'transport incomplete' in k or 'DNS' in k) else 'generated schema/content failure; episode-local'] for k,v in errors.items()])
    detail+='''
There are **164 generated schema/content failures**, **215 completed output-length stops**, **five local transport-incomplete events**, and **one pre-generation DNS terminal**. Length caps, DNS and usage limits are operational events, not observations of model behavior. The frozen denominator still includes affected opportunities; no alternative denominator replaces the primary. The older terminal’s saved “identity mismatch” is retained, with its HARNESS BUG correction reported by replay.

One exact 429 subscription refusal had zero usage and cost: it was a **definite non-start**, paused until reset, then continued with identical request bytes. It is additional to the 6,411 scored call starts (5,938 local, 473 Claude); there were 6,412 durable starts including that refusal. Claude’s 473 scored starts include one DNS non-generation, leaving 472 generated Claude calls. No collection was rerun during analysis or delivery.

The saved STOP was cleared once through the recorded harness correction; its original bytes and journal prefixes remain. All 1,080 terminals are sealed, all call settlements and time holds are resolved, the current ledger is unblocked, and no episode is pending or operationally paused. These facts do not cure low validity.

## Versions, deviations and exposure

The original **v0.1 outcome-informed stop** is a separate, failed interface cohort: the reviewer saw 287 episodes; disk retained 288 terminals (282 invalid control; six invalid action keys/length) and one partial with four valid writes and one unanswered durable return start. Timing of the extra terminal is UNKNOWN. Of 1,080 planned episodes, 289 were attempted, 791 never started; none is wholly technically valid. All 289 saved Y/F values are zero operationally, and all their return facts remain null. The full planned cohort contains 17,280 unavailable factual targets; no model effect is inferred. There was no saved paid exposure, and one unsettled local-time hold remains in v0.1 (1,077.466577334 charged seconds including its conservative hold). Do not pool versions or retry the partial. The immutable stopped-cohort inventory and hashes are bundled under evidence/v01-*.json; raw parent v0.1 files are a separate historical package, not required to reproduce v0.2.

'''
    v1=json.loads((ROOT/'evidence/v01-inventory.json').read_text())
    gr=collections.defaultdict(list)
    for r in v1['episodes']: gr[(r['actor'],r['world'],r['arm'])].append(r)
    planned=json.loads((ROOT/'config/episodes.json').read_text())
    v1rows=[]
    for k,c in X['cells'].items():
        rs=gr[tuple(k.split('/'))];n=c['episodes']
        v1rows.append([k,n,len(rs),sum(r['state']=='terminal' for r in rs),sum(r['state']=='partial' for r in rs),n-len(rs),'0% / 0% / 0%'])
    detail+=table(['v0.1 actor / condition / arm','Planned','Attempted','Terminal','Partial','Unstarted','Operational Y / F / valid (planned)'],v1rows)
    detail+='''
v0.2 changed only provider-side phase-specific JSON Schema decoding, with exposure and unchanged P1–P7 re-registered before its calls. It was not a blind follow-up. Two reviewed operational deviations followed: the exact-zero 429 pause/resend rule (freeze-usage-limit.json), and the pre-generation DNS/envelope diagnosis/STOP correction (freeze-claude-envelope.json). Both preserve predecessor source, freezes, push receipts and scientific fields. The original DNS episode was never replayed or replaced. See revisions/usage-limit/DEVIATION.md and revisions/claude-envelope/DEVIATION.md. Their saved scientific comparisons matched at all 1,080 scheduled positions at the time of each correction; they are historical diagnostics, not additional analysis runs in this delivery.

## Spend and limits

'''
    acc=X['accounting']
    spend=[]
    for actor,label in ACTORS:
        calls=[c for r in X['episodes'] if r['actor']==actor for c in r['calls']]
        spend.append([label,len(calls),sum(c['input_tokens'] or 0 for c in calls),sum(c['output_tokens'] or 0 for c in calls),sum(c['input_tokens'] is None or c['output_tokens'] is None for c in calls),f"{sum(c['actual_micro_usd'] or 0 for c in calls)/1e6:.6f}"])
    detail+=table(['Actor','Scored starts','Known input tokens','Known output tokens','Missing usage calls','Accounted USD'],spend)
    detail+=f'''
Total accounted spend/exposure is **USD {acc['settled_micro_usd']/1e6:.6f}**, held **USD {acc['held_micro_usd']/1e6:.6f}**, no unsettled calls. v0.1 saved paid exposure is zero, so recorded programme exposure is the same. This is conservative API-equivalent accounting (USD4/million complete input categories, USD20/million output, larger reported CLI cost controls separately for each call), **not a cash invoice**. The raw CLI cost sum is USD4.3031008 and the aggregate token-basis sum is USD4.177688; the ledger takes the larger basis call by call, with micro-dollar rounding, so its total can exceed both aggregate sums. Actual cash payment and current authoritative provider prices are **UNKNOWN (null)**. Local model-call accounting is zero; hardware, energy, subscription and opportunity costs were not priced.

Planning reserve: USD10.690560 plus USD1 protected reserve = USD11.690560. Spend is below the USD25 frontier envelope, USD39 programme stop and USD40 outer line. Local active time **{acc['active_time']['local']['seconds']:.9f}s / 86,400s**, Claude **{acc['active_time']['claude']['seconds']:.9f}s / 10,800s**, both zero unsettled time holds. The separate retained v0.1 conservative time charge remains disclosed above; even cumulatively local charged time is below 24 hours. Per-call caps were 180s local / 420s Claude; output settings were local num_predict 192 / Claude requested 512, which are not claimed aggregate output guarantees. Operational cap events are tabulated, not hidden as behavioral failures.

## Reproduction and verification

Analysis was invoked once in the source folder with the latest RUN command: `python3 -B ps.py analyze --output collection/analysis-claude-envelope.json`. Output SHA-256: `{hashlib.sha256(SOURCE.read_bytes()).hexdigest()}`. Analysis code, prompts, all three freezes and collection evidence were left unchanged. `python3 -B ps.py verify` passed before and after delivery; its active hash is `eeacae1853e959be9bc8ccf2a70abdac7eb2b0b6ab487c16d5950652acf6341d`. The lineage check reconstructs both predecessor generations from saved source bytes and checks their parents, plus the original scientific baseline. Push-gate verification checks all three saved GitHub activity receipts and every saved start against its proper freeze/push generation, without contacting GitHub.

The frozen offline suite ran once: **138 passed, one failed, zero errors** (139 total), with network/subprocess execution denied. See [the exact log](../post-analysis-offline-check.log). The failing `RealClearanceTests.test_full_saved_collection_clearance_is_idempotent_and_never_replays_terminal` tries to reconstruct the historical STOP using the current completed collection and then asserts a blocked ledger; later collection evidence makes that pre-clearance fixture assumption stale. This is a test/fixture compatibility failure, not a silently waived successful check. The frozen test and harness were not edited; no full-suite green claim is made. The actual frozen analysis, collection seals, accounting, receipt lineage and independent rebuild are checked separately.

New delivery documents live in **collection/delivery/** because the exact freeze inventories forbid new root inputs. This location was already excluded by the original freezer. The publication package excludes **only** `__pycache__`, `.DS_Store`, `.git` and `*.lock`; no provider envelopes, prefix anchors, fixtures, deviations, offline evidence or failed logs are omitted. One bound transient, `offline/dry-run/collector.lock`, is an empty lock with SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; the unbound collection lock has the same hash. Both are listed with exact saved bytes in transient-files.json.

The fresh-clone adapter validates the exact substantive inventory, then copies the frozen inputs to a private temporary validation view and reconstructs only the saved empty transient lock there. The **unmodified original verifier** checks that view, including all three freezes and preserved ancestors. Nothing is restored into the clone or omitted from substantive verification. The adapter substitutes this certified verification function for push_gate’s call in memory only, then invokes the unchanged frozen analyze() directly on the clone’s saved collection. There is no fake-data mode, changed prompt, altered denominator or edited analysis. Network and subprocesses are denied.

From a fresh clone, from the v0.2 folder:

```sh
python3 -B collection/delivery/reproduce.py --fresh-clone
python3 -B collection/delivery/reproduce.py --fresh-clone --output /private/tmp/portable-self-analysis-rebuilt.json
```

Choose a new output path; outputs are create-once. The independent rebuild was executed in a full COPY with exactly the publication exclusions removed; see rebuild-report.json for byte equality, copy inventory, output digest and guard checks. Reproduction is a verification replay in that copy, not a rerun of collection or the source analysis invocation.

## Detailed evidence and limits

- [Frozen replay JSON](../analysis-claude-envelope.json): all 1,080 rows, per-target facts, raw note text, slot choices/retention, literal-map fidelity flags, returns, parsed errors, token usage, elapsed times, accounting, contrasts and prediction decisions.
- [episodes.csv](episodes.csv), [facts.csv](facts.csv), [calls.csv](calls.csv), [notes.csv](notes.csv): flat exports of those exact saved fields for inspection; no new scores.
- [baseline-seeds.csv](baseline-seeds.csv): pre-frozen code policies on each actor’s exact planned seed set, with per-return hits. Zero model-call spend; CPU time unpriced.
- [freeze-verification.json](freeze-verification.json), [rebuild-report.json](rebuild-report.json), [transient-files.json](transient-files.json): verification and packaging receipts.
- [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md): explicitly post hoc questions, not new predictions or permission for more calls.

All presentation aggregates and plots are post-analysis descriptive views of the frozen JSON or the pre-frozen baseline table. No new statistical test, semantic note judge or post hoc exclusion was introduced. Literal-map fidelity is defined only by the frozen exact four-pair matcher; other encodings remain UNKNOWN. Stable Claude saturation does not demonstrate keyed/shared equivalence; ten seed blocks cannot rank frontier models. Differing technical validity, abstentions, strict storage constraints and context size limit mechanism attribution. The schema follow-up does not erase the stopped v0.1 failure. Claude’s independent empirical review remains required; no further cohort, v0.3, tuning, publication or acceptance is claimed here.
'''
    write('RESULTS.md',intro+detail)
    write('README.md',intro.replace('# The Portable Self v0.2 — results','# The Portable Self v0.2')+'''Read [RESULTS.md](RESULTS.md) for joint criteria, every prediction, full cells, all paired intervals with prompt tokens, operational events, v0.1, deviations, spend and limitations. The package is Python-standard-library-only and needs no model service, credential or network for reproduction.

From the v0.2 folder in a fresh GitHub clone:

```sh
python3 -B collection/delivery/reproduce.py --fresh-clone
python3 -B collection/delivery/reproduce.py --fresh-clone --output /private/tmp/portable-self-analysis-rebuilt.json
```

The output must be a new path. The frozen exact verifier needs an omitted empty lock, so fresh-clone mode supplies its hash-bound saved bytes only in a disposable validation view, then runs the original verifier and unchanged analysis against the real clone. [transient-files.json](transient-files.json) lists saved hashes; [rebuild-report.json](rebuild-report.json) records the independent copy and byte comparison. Only __pycache__, .DS_Store, .git and *.lock are excluded from the published package.

The source analysis ran once; the independent copy replay is verification only. Do not rerun collection. Three freezes and the raw evidence are immutable. Delivery files are under collection/delivery/ to preserve exact root inventory. The offline suite passed 138/139 tests: one historical STOP fixture fails against completed collection state; the exact failure is disclosed in RESULTS, not repaired in frozen code. The independent rebuild verifies actual collection integrity separately.

Accounted exposure: **USD4.775331**, held **USD0**; actual cash billing **UNKNOWN**. Full-study acceptance criteria are not met because technical validity is low. Work was delegated by Claude under the Claude/Codex agreement; independent reviewer acceptance and later publication remain separate steps.
''')
    eps=[];facts=[];notes=[];calls=[]
    for r in X['episodes']:
        key={k:r[k] for k in ['id','actor','seed','world','arm']}
        ep={**key,**{k:r[k] for k in ['attempted','calls_started','valid_calls','technical_complete','Y','F','answered_only_accuracy','answered','nulls','known_wrong','technical_missing']},'returns':json.dumps(r['returns']),'return_complete':json.dumps(r['return_complete'])}
        eps.append(ep)
        facts.extend({**key,'target_position':i+1,**f} for i,f in enumerate(r['facts']))
        notes.extend({**key,**n} for n in r['notes'])
        calls.extend({**key,'episode_id':r['id'],**c} for c in r['calls'])
    csvfile('episodes.csv',list(eps[0]),eps)
    csvfile('facts.csv',list(facts[0]),facts)
    csvfile('notes.csv',list(notes[0]),notes)
    csvfile('calls.csv',list(calls[0]),calls)
    br=[]
    for actor,_ in ACTORS:
        for world in WORLDS:
            seeds=sorted({r['seed'] for r in X['episodes'] if r['actor']==actor and r['world']==world})
            br.extend({'matched_actor':actor,**r,'returns':json.dumps(r['returns']),'executable':True} for r in B if r['world']==world and r['seed'] in seeds)
    csvfile('baseline-seeds.csv',['matched_actor','seed','world','kind','Y','F','executable','ceiling','model_result','returns'],br)
    # Standalone vector chart, with no charting dependency required by a clone.
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="730" viewBox="0 0 1120 730" role="img" aria-labelledby="title desc">',
         '<title id="title">Correct planned return actions by actor, condition and memory arm</title>',
         '<desc id="desc">Bars show Y, with fixed denominators. The adjacent table gives exact values, complete-return performance and technical validity. Claude same-stable is unscheduled.</desc>',
         '<rect width="1120" height="730" fill="white"/>',
         '<g font-family="Arial,sans-serif" font-size="13" fill="#17212b">',
         '<text x="25" y="26" font-size="20">Correct return actions (Y); all planned targets</text>']
    colors=['#1967a3','#d56a16','#65747e']
    for i,(arm,color) in enumerate(zip(ARMS,colors)):
        svg.append(f'<rect x="{560+i*155}" y="12" width="16" height="16" fill="{color}"/><text x="{582+i*155}" y="25">{arm}</text>')
    for tick in [0,25,50,75,100]:
        xx=350+tick*6.2
        svg.append(f'<line x1="{xx}" y1="62" x2="{xx}" y2="680" stroke="#e4e8eb"/><text x="{xx}" y="53" text-anchor="middle">{tick}%</text>')
    for i,(actor,label) in enumerate(ACTORS):
        for j,world in enumerate(WORLDS):
            yy=80+(i*3+j)*50
            svg.append(f'<text x="25" y="{yy+12}">{html.escape(label+" / "+world)}</text>')
            if actor=='claude' and world=='same-stable':
                svg.append(f'<text x="355" y="{yy+12}">not scheduled</text>');continue
            for ai,(arm,color) in enumerate(zip(ARMS,colors)):
                y=X['cells']['/'.join([actor,world,arm])]['Y'];by=yy-7+ai*12
                svg.append(f'<rect x="350" y="{by}" width="{620*y:.3f}" height="9" fill="{color}"/><text x="{355+620*y:.3f}" y="{by+8}" font-size="10">{100*y:.2f}</text>')
    svg.append('<text x="25" y="714">Descriptive frozen scores; abstentions and technical/missing actions are operational misses. No error bars on these cell means.</text></g></svg>')
    write('headline.svg','\n'.join(svg)+'\n')
    write('headline-table.md',headline_table)


if __name__=='__main__':
    main()
