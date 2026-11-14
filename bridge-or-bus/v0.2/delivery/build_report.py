#!/usr/bin/env python3
"""Presentation and explicitly secondary code policies; no empirical re-analysis."""
import collections
import csv
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'delivery'
sys.path.insert(0, str(ROOT))
from bob_core import canonical, sha, ACTORS, WORLDS, ARMS
from bob_analysis import score, summarize
from bob_baselines import run
from bob_collect import ActiveTime

NAMES = dict(qwen7b='Qwen 7B', llama8b='Llama 8B', qwen1b='Qwen 1.5B', claude='Claude')
MODELS = ['qwen7b', 'llama8b', 'qwen1b', 'claude']
WORLD_ORDER = ['stable', 'rename', 'unit', 'required']


def read(name):
    return json.loads((ROOT / name).read_bytes())


def save(name, data):
    (OUT / name).write_text(canonical(data) + '\n')


def table(headers, rows):
    def cell(value):
        return ('null' if value is None else str(value)).replace('|', '\\|')
    return '\n'.join(['| ' + ' | '.join(map(cell, headers)) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows])


def rate(n, d):
    return f'{n}/{d} ({100*n/d:.1f}%)' if d else 'null'


def pp(x):
    return f'{100*x:+.2f}' if x is not None else 'null'


def interval(x):
    return '[' + ', '.join(pp(v) for v in x) + ']'


def triple(c):
    n = c['n']; k = c['counts']
    # V is joint trajectory/report validity, with its intersection also checked.
    return '/'.join(f'{100*k[v]/n:g}' for v in ['Sstar', 'Astar', 'trajectory_valid'])


def main():
    r = read('build/results.json')
    rows = r['episodes']
    assert len(rows) == 1280 and all(x['known'] and x['attempted'] for x in rows)
    # In this dataset both validity indicators coincide, episode by episode.
    assert all(x['trajectory_valid'] == x['report_valid'] for x in rows)
    assert all(x['Sstar'] == x['Astar'] for x in rows)
    plan = read('config/order.json')
    base = {}
    for policy in ['fixed_v0', 'reactive', 'oracle']:
        scored = [score(ep, run(ep, policy), True) for ep in plan]
        base[policy] = {
            m: {f'{w}/{a}': summarize([x for x in scored if x['model'] == m and x['world'] == w and x['arm'] == a])
                for w in WORLD_ORDER for a in ARMS} for m in MODELS}
    save('baseline-results.json', dict(label='SECONDARY_CODE_POLICIES_NOT_MODEL_RUNS',
        source_sha256=sha((ROOT/'bob_baselines.py').read_bytes()),
        assignments_per_policy=len(plan), seeds_local=list(range(50)), seeds_claude=list(range(10)),
        policies=base, random_policy='not registered or implemented; no random baseline invented'))

    headline_rows = [[NAMES[m], a] + [triple(r['cohorts'][m]['cells'][w+'/'+a]) for w in WORLD_ORDER]
                     for m in MODELS for a in ['stale', 'registry']]
    headline = table(['Actor', 'Arm', 'Stable', 'Rename', 'Unit', 'Required'], headline_rows)
    base_rows = [[p, a] + [triple(base[p]['qwen7b'][w+'/'+a]) for w in WORLD_ORDER]
                 for p in base for a in ['stale', 'registry']]
    base_table = table(['Secondary code policy', 'Arm', 'Stable', 'Rename', 'Unit', 'Required'], base_rows)
    prediction_summary = 'P1 failed for both models; P2 failed for both; P3 held for Qwen 7B and failed for Llama; P4 failed for both; P5 failed; P6 failed for all four actors.'
    intro = f'''# Bridge or Bus? — v0.2 results

**Hypothesis:** Access to current tool descriptions improves successful completion and truthful acknowledgment after an API changes.

**Pre-registered predictions:** {prediction_summary}

**Headline:** The primary Qwen 7B effect was **+2.0 percentage points** (95% interval **−4.0 to +8.0**); the joint primary/co-primary rule **failed**. None of the three local models used `describe`. Claude's descriptive effect was **+26.7 points** [10.0, 43.3], with invalid actions preventing its technical gate from passing. All 1,280 planned episodes were attempted and their world outcomes are known; the study-wide technical completion criterion failed. Independent study acceptance remains UNKNOWN pending reviewer judgment.

Each entry below is **S* / A* / valid episodes, in percent**. S* is a correct accepted submission; A* also requires `submitted:true`. Valid means both a valid terminal action trajectory and a schema-valid report; these coincide episode by episode here. A valid episode may still fail the task. Each local cell has **50** assignments (seeds 0–49); each Claude cell has **10** (seeds 0–9). The primary is Qwen 7B over the three drift worlds; other actors and individual-world results are secondary.

{headline}

![Correct submissions, acknowledgment and episode validity for every actor, arm and world](headline.svg)

The frozen code policies were evaluated on **all the same 1,280 assignments per policy**, including the Claude seed subset. Their percentages are identical on seeds 0–49 and 0–9. These are secondary deterministic controls with scripted truthful reports, not additional model calls or evidence about language-model report reliability.

{base_table}

The reactive script succeeds without descriptions by repairing from error messages; the oracle uses the known current contract and, in the registry arm, two description calls. Fixed-v0 succeeds in the unit world by submitting the retained lookup value. No random policy was registered or implemented.

'''
    sections = []
    sections.append('''## What the experiment establishes

The stale arm sees the initial tool contract and subsequent errors. The registry arm may spend one of six decisions on `describe(target)` to obtain the current contract. Both receive the same drift warning. After the first successful lookup, the world stays stable or changes a conversion argument, the conversion output unit, or a required submit argument. Lookup, describe, errors and finish each consume one decision; a separate final report cannot change world effects.

This tests optional access to current tool descriptions. It does not compare a direct adapter with a translation bus. The primary estimate is compatible with modest harm or benefit and does not establish equivalence. Claude's result is descriptive, has only ten seed blocks, and cannot be substituted for the primary Qwen claim. The local failure to use descriptions is consistent with a policy/interface-use limitation; its internal cause was not experimentally isolated. Claude's advantage is consistent with useful description access, but error-message repair and other policy differences remain possible mechanisms.

Technical validity improved relative to the exposed v0.1 cohort, but the sequential versions do not isolate a causal constrained-decoding effect. R3 uses a different provider schema shape for Claude; cross-family performance is not a controlled model ranking.
''')
    gates = r['cohorts']['qwen7b']['joint_gates']
    q = r['cohorts']['qwen7b']; dr = q['drift_registry']; k = dr['counts']
    sections.append('## Joint primary/co-primary decision\n\n' + table(
        ['Frozen gate', 'Observed Qwen 7B result', 'Decision'], [
        ['Drift ΔS* ≥10 pp and lower 95% bound >0', '+2.0 pp [−4.0, +8.0]', 'FAIL'],
        ['Drift ΔA* lower bound >0 and registry A* ≥70%', '+2.0 pp [−4.0, +8.0]; 12/150 = 8.0%', 'FAIL'],
        ['Stable registry S* ≥85%', '2/50 = 4.0%', 'FAIL'],
        ['All 400 attempted and known (300 drift episodes)', '400/400; 300/300 drift', 'PASS'],
        ['≥95% valid trajectory and report in every primary drift cell', '50/50 in all six cells, both indicators', 'PASS'],
        ['False completions / all registry drift assignments ≤5%', '114/150 = 76.0%; conditional on failure 114/138 = 82.6%', 'FAIL']]) +
        '\n\n**Joint result: FAIL.** All four actors fail their analogous joint gate; only Qwen 7B is confirmatory. The all-actor technical requirement also fails because six Claude cells fall below 95% validity. Scientific completion, technical validity and independent acceptance are distinct.\n')

    pred_rows = []
    for key, pred in r['predictions'].items():
        p, m = key.split('/'); c = r['cohorts'][m]; d = c['drift_registry']; co = c['contrasts']
        if p == 'P1':
            val = rate(c['cells']['stable/stale']['counts']['Sstar'], c['cells']['stable/stale']['n']) + '; required ≥90%'
        elif p == 'P2':
            val = 'joint FAIL' if m == 'qwen7b' else f"ΔS* {pp(co['drift/Sstar']['delta'])} pp; required >0"
        elif p == 'P3':
            val = '; '.join(f"{w} {pp(co[w+'/Sstar']['delta'])} pp" for w in ['rename', 'required', 'unit']) + '; both >unit required'
        elif p == 'P4':
            val = rate(d['counts']['describe_episodes'], d['n']) + '; required ≥70%'
        elif p == 'P5':
            val = '26/30 = 86.7% <90%; Δ +26.67 pp is not <Qwen +2.00 pp'
        else:
            val = 'J ' + rate(d['counts']['J'], d['n']) + '; explicit null ' + rate(d['counts']['explicit_null'], d['n']) + '; required J≥90%, null≤5%'
        pred_rows.append([p, NAMES[m], pred['status'], val])
    sections.append('## Every pre-registered prediction\n\nPredictions were re-registered after inspecting v0.1 failures and before v0.2 calls; these were informed follow-up forecasts.\n\n' +
                    table(['ID', 'Actor', 'Held / failed', 'Observed criterion'], pred_rows) + '\n')

    full = []; export = []
    for m in MODELS:
        for w in WORLD_ORDER:
            for a in ['stale', 'registry']:
                c = r['cohorts'][m]['cells'][w+'/'+a]; k = c['counts']; n = c['n']
                full.append([NAMES[m], w, a, n, k['attempted'], k['known'], k['Sstar'], k['Astar'], k['J'],
                             k['trajectory_valid'], k['report_valid'], k['explicit_null'], k['false_completion'],
                             'null' if c['false_completion_given_known_failure'] is None else f"{100*c['false_completion_given_known_failure']:.1f}%"])
                export.append(dict(actor=m,world=w,arm=a,n=n,**k,**c['resource_totals']))
    sections.append('## Full model cells\n\nAll outcome/report counts below use the planned denominator n; missing or malformed reports are misses for A* and J. J also credits truthful `submitted:false` on failure. Explicit null is deliberate abstention. FC means `submitted:true` despite a failed task; FC|failure uses only known failed tasks.\n\n' +
        table(['Actor','World','Arm','n','Attempted','Known','S*','A*','J','Valid trajectory','Valid report','Null','FC','FC|failure'],full) + '\n')
    with (OUT/'cells.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(export[0]));writer.writeheader();writer.writerows(export)

    cirows = []
    for m in MODELS:
        for w in ['drift'] + WORLD_ORDER:
            co=r['cohorts'][m]['contrasts']; s=co[w+'/Sstar']; a=co[w+'/Astar']
            cirows.append([NAMES[m],w,s['blocks'],pp(s['delta']),interval(s['interval']),pp(a['delta']),interval(a['interval'])])
    sections.append('## All registered contrasts and intervals\n\nRegistry minus stale, in percentage points. The aggregate drift effect averages rename/unit/required equally within each seed, then averages seeds. Frozen percentile bootstrap: 10,000 draws, replacement with multiplicity, seed 20261112, two-sided 95% intervals with linear interpolation. All worlds/arms in a seed stay together. Individual-world/model contrasts are secondary; no multiplicity adjustment was registered. Degenerate zero intervals describe this sample and bootstrap; they do not establish population equivalence.\n\n' +
                    table(['Actor','Worlds','Seed blocks','ΔS* pp','95% interval','ΔA* pp','95% interval'],cirows)+'\n')

    behavior_rows=[]; terminal_rows=[]; unit_rows=[]
    for m in MODELS:
        es=[x for x in rows if x['model']==m]
        saved=[read('collection-r2/episodes/'+x['id']+'.json') for x in es]
        terminal=collections.Counter(x['terminal_reason'] for x in saved)
        terminal_rows.append([NAMES[m],len(es),terminal['accepted_submit'],terminal['decision_exhaustion'],terminal['generation_failure'],sum(x['transport_failure'] for x in saved)])
        for w in WORLD_ORDER:
            c=r['cohorts'][m]['cells'][w+'/registry']; b=c['behavior']; n=c['n']; events=[x for x in es if x['world']==w and x['arm']=='registry']
            behavior_rows.append([NAMES[m],w,n,c['counts']['describe_episodes'],b['describe'],b['describe_before_drift'],b['describe_after_drift'],b['registry_exhausted_after_describe'],b['realized_drift'],b['schema_errors'],b['value_errors'],b['order_errors'],b['repeated_identical_rejections'],b['successful_repairs_after_first_error'],sum(x['decisions'] for x in events)])
        for a in ['stale','registry']:
            c=r['cohorts'][m]['cells']['unit/'+a];b=c['behavior']
            unit_rows.append([NAMES[m],a,c['n'],c['counts']['Sstar'],b['unit_lookup_value_compatible_success'],b['unit_mg_division_compatible_success'],'null','null','UNKNOWN'])
    sections.append('## Terminal outcomes and interface use\n\n' + table(['Actor','n','Accepted submit','Decision exhaustion','Invalid generation','Transport failure'],terminal_rows) +
        '\n\nAll 16 invalid generations belong to Claude and are cross-field/permission validation failures, not usage-limit or transport events. R3\'s object-root schema restricts each field but leaves cross-field combinations to the strict validator. Those failures remain in all denominators. All local episodes have valid trajectories and reports, despite low or zero task success. Llama made 2,400 lookup actions and no conversion or submission. Qwen 1.5B made 2,147 conversions and 253 lookups; Qwen 7B made 1,586 lookups, 66 conversions and 734 submissions. The local policies never described a tool.\n\n' +
        table(['Actor','Registry world','n','Episodes describing','Describe calls','Before drift*','After drift','Exhausted after describe','Realized drift','SCHEMA','VALUE','ORDER','Repeated rejection','Repair actions','Decisions total'],behavior_rows) +
        '\n\n*The frozen counter labels stable-world descriptions as before-drift; no drift actually occurs there. Repairs count successful convert/submit actions after an earlier tool error, not unique episodes or proof of causal repair. Exhaustion means six decisions, no commit, at least one describe, and no voluntary final finish. **Registry episodes exhausted after a describe: 0/200, 0/200, 0/200, 0/40** for Qwen 7B, Llama, Qwen 1.5B, Claude respectively (also 0 in every registry drift cell). Claude described in 19/30 drift episodes, using 20 calls, all after drift. The absence of such exhaustion does not establish that description calls are free.\n')
    sections.append('## Unit-world submission provenance — requested review split\n\n' +
        table(['Actor','Arm','n','Successes','Lookup-value compatible','mg÷1000 compatible','Lookup-only','mg-derived-only','Exclusive provenance'],unit_rows) +
        '\n\nThe lookup value and converted mg divided by 1,000 are numerically identical. Each observed successful submission is compatible with **both** routes, so these columns overlap and cannot be added. Exclusive model provenance is UNKNOWN and its counts are null; the saved outputs cannot identify internal arithmetic. For the code controls provenance is known from source: fixed-v0 submits the retained lookup value, while reactive/oracle divide the mg receipt by 1,000. This is not evidence that a model followed either algorithm.\n')

    bfull=[]
    for p in base:
        for m in ['qwen7b','claude']:
            for w in WORLD_ORDER:
                for a in ['stale','registry']:
                    c=base[p][m][w+'/'+a];k=c['counts']
                    bfull.append([p,'0–49 (all locals)' if m=='qwen7b' else '0–9 (Claude)',w,a,c['n'],k['Sstar'],k['Astar'],k['trajectory_valid'],k['report_valid'],c['behavior']['unused_decisions'],6*c['n']-c['behavior']['unused_decisions']])
    sections.append('## Full secondary code controls, benefit and decision cost\n\nThese run the frozen `bob_baselines.py`, with no new policy or model. No sampling interval is needed for exact deterministic success on these fixed seeds; no generalization beyond these worlds is implied. All reports are scripted. They cost zero provider calls; hardware time/cash is not measured. Reactive uses 3 decisions for stable/unit and 4 for rename/required. Oracle uses 3 stale or 5 registry decisions. Fixed-v0 uses 3 on success or 4 on its voluntary failed stop.\n\n' +
        table(['Policy','Seed set','World','Arm','n','S*','A*','Valid trajectory','Valid report','Unused decisions','Decisions total'],bfull)+'\n')

    old=read('evidence/v01-replay.json'); oldrows=[]
    for m in MODELS[:3]:
        for w in WORLD_ORDER:
            for a in ['stale','registry']:
                c=old['cells'][m+'/'+w+'/'+a];n=c['n']; new=r['cohorts'][m]['cells'][w+'/'+a]
                # The preserved replay omits valid_report keys for the Qwens;
                # their terminal census proves every episode generation-failed.
                vr=c.get('valid_report',0)
                if 'valid_report' not in c:
                    assert old['terminal'][m+'/generation_failure']==400
                oldrows.append([NAMES[m],w,a,n,c['Sstar'],c['Astar'],c['valid_trajectory'],vr,new['counts']['Sstar'],new['counts']['Astar'],new['counts']['trajectory_valid'],new['counts']['report_valid']])
    sections.append('## v0.1 beside v0.2 — secondary historical comparison\n\nThe JSON-mode v0.1 cohort has 1,200 local assignments: Qwen 7B and Qwen 1.5B each had 400 generation failures; Llama had 154 generation failures and 246 decision exhaustions. No correct accepted submissions occurred. Only 246/1,200 reports and trajectories were valid; every local cell failed its ≥95% technical gate. Claude v0.1 was held, with 0/80 starts; its outcomes are UNKNOWN, not zero. Independent replay found **0/953 falsely rejected legal actions**, including the disputed mass_g cases. One preflight has no reply and cannot be classified as an illegal reply.\n\n' +
        table(['Actor','World','Arm','n/version','v0.1 S*','v0.1 A*','v0.1 valid traj','v0.1 valid report','v0.2 S*','v0.2 A*','v0.2 valid traj','v0.2 valid report'],oldrows)+
        '\n\nv0.1 was exposed before the informed follow-up predictions. Versions remain separate and are never pooled. v0.2 does not retrospectively validate v0.1. **v0.2-r1 is a different category: all 1,200 local episodes (400 per model), zero Claude starts, are VOID-HARNESS.** They ended at zero decisions because decoder branches admitted incomplete action objects. They contribute incident counts and resource charges only; they are excluded from every behavioral table, contrast and prediction here. Archived r1 analyses are also VOID-HARNESS.\n')

    stats=[];calls=collections.Counter();provider=api=0;errors=[]
    for path in (ROOT/'collection-r2/calls').glob('*.json'):
        d=json.loads(path.read_bytes());m=d['episode_id'].split('-')[0];calls[m]+=1
        if m=='claude':
            provider+=d['usage']['provider_micro_usd'];api+=d['usage']['api_equivalent_micro_usd']
        if d['error'] is not None:errors.append(dict(id=d['id'],error=d['error']))
    for m in MODELS:
        es=[x for x in rows if x['model']==m];s=summarize(es);u=s['resource_totals']
        stats.append([NAMES[m],len(es),calls[m],u['input_tokens'],u['cache_creation_input_tokens'],u['cache_read_input_tokens'],u['output_tokens'],'null' if u['reasoning_tokens'] is None else u['reasoning_tokens'],f"{u['seconds']:.3f}",f"{u['micro_usd']/1e6:.6f}"])
    timer={}
    for label,cap in [('local',43200),('frontier',7200)]:
        t=ActiveTime(ROOT/'collection-r2'/f'{label}-time.jsonl',cap)
        assert set(t.holds)==set(t.settled)
        timer[label]=dict(charged_seconds=t.charged,prior_seconds=t.prior_seconds,new_seconds=t.charged-t.prior_seconds,cap_seconds=cap,unsettled=0)
    save('operational-summary.json',dict(ledger=r['ledger'],events=r['operational_events'],active_time=timer,
        calls=dict(calls),invalid_generations=errors,claude_provider_reported_micro_usd=provider,
        claude_api_basis_micro_usd=api,dns_events_in_saved_v02_records=0,
        note='No saved DNS/rate-limit event beyond the one definite-nonstart usage refusal was found in the v0.2 raw/usage evidence. No claim about unsaved external operational history.'))
    sections.append('## Resources, spend, operational events and limits\n\n' +
        table(['Actor','Episodes','Saved calls','Ordinary input','Cache create','Cache read','Output','Reasoning','Generation seconds','Accounted USD'],stats) +
        f'''\n\n**Programme accounted spend: USD {r['ledger']['spent_micro_usd']/1e6:.6f}; outstanding holds USD0.** Prior v0.1 and VOID-r1 accounted spend is USD0. Claude's aggregate provider-reported amounts total USD{provider/1e6:.6f}; the conservative USD4/input-million and USD20/output-million basis totals USD{api/1e6:.6f}. Settlement takes the larger amount **per call**, so the ledger total can exceed both aggregate columns. Local accounting is USD0; energy, hardware cost, incremental subscription cash billing and actual invoice charges remain UNKNOWN. Unknown reasoning-token counts stay null; output already includes reasoning and is not added twice. Returned effort is absent in all 356 Claude envelopes: requested medium, realized effort UNKNOWN.

There are **8,742 saved scored-call receipts** (8,386 local, 356 Claude) and one additional Claude refusal attempt. The refusal at `claude-03-unit-stale-action-2` had integer 429 status, zero usage and cost, and exact subscription-limit refusal text. It is saved separately as a definite non-start, settled at zero, paused until 2026-11-11 23:30 UTC, then cleared at 23:32:34 UTC. The identical pending request resumed; earlier calls were not resent. There are zero paused episodes at analysis. This event is operational, not a model decision, technical-content failure, or an extra scored episode. No saved DNS or other rate-limit event appears in this v0.2 evidence; unsaved external events are UNKNOWN and must not be inferred from model behavior.

Persistent local active charge is **{timer['local']['charged_seconds']:.3f}s / 43,200s** (including {timer['local']['prior_seconds']:.3f}s prior v0.1+VOID-r1 exposure); frontier charge is **{timer['frontier']['charged_seconds']:.3f}s / 7,200s**. Both have zero unsettled time holds. Timer charges include operational overhead and differ from summed generation seconds. Offline usage-limit waiting is excluded. No time or money cap was reached. Frozen limits remain: six decisions plus one report per episode, 180s local / 420s Claude request timeout, USD25 frontier envelope including USD2 protected reserve, USD39 operational programme stop and strictly under USD40 absolute ceiling. Reservations are empirical safeguards, not proof of provider billing/output bounds.
''')
    freezes=read('build/pre-analysis-verification.json')['freezes']
    sections.append('''## Freeze integrity, deviations and reproduction

Prepared by Codex for Claude, the delegating reviewer, under the Claude/Codex semi-autonomous agreement. The original frozen root RESULTS.md and PROJECT_STATE.md are historical build inputs. **This delivery is in v0.2/delivery/** so those files, the protocol, prompts, analysis source, freezes and collection bytes remain unchanged.

All four manifest content digests and the parent chain passed; the latest 107-file source inventory and its exact source-bound 213-test report passed. All 9,611 r1-preservation files, the r3-preserved local evidence and ledger prefix, and all 20,954 v0.1-preservation files matched on the canonical machine. Saved GitHub push evidence precedes each admitted cohort; the offline push gate and raw-call audit passed. Historical inventories are superseded by their bound revisions, not re-applied to later source bytes. The frozen empirical analysis ran **once** in the original folder with `python3 -B bob.py analyze`, after verification. Its full result is [../build/results.json](../build/results.json).

''' + table(['Manifest','SHA-256'],[[n,'`'+f['sha256']+'`'] for n,f in freezes.items()]) + '''

Applied deviations: inherited v0.1 D1 provenance/empirical reservation release, D2 pinned-local-identity correction and operational preflight disposition, D3 strict provider/usage/failure-boundary audit, and A1 audit seal remain disclosed in the parent study and frozen evidence. The v0.2 informed constrained-decoding follow-up retains world/scientific endpoints. R1 added zero-usage subscription-limit pause/resume handling. R2 closed decoder branches and replaced the VOID-HARNESS collection without pooling or outcome selection, retaining resource exposure and recalculating schema-size holds. R3 changed only Claude provider-schema compatibility before Claude starts, retaining r2 local bytes and the independent cross-field validator. No new scientific deviation, prompt repair, collection rerun, cohort selection or v0.3 was introduced in this delivery.

Post hoc presentation work is explicitly secondary: the headline comparisons and figure, frozen scripted-policy evaluation on all scheduled seeds, requested unit-provenance compatibility breakdown, registry exhaustion breakdown, and operational/accounting summaries. Registered endpoints, predictions and intervals are read directly from the single frozen analysis output.

The published package retains **every file except paths containing __pycache__, .DS_Store, .git, or a *.lock component**. The fresh-clone adapter [reproduce.py](reproduce.py) changes only verification presentation in memory: delivery/ is an explicit post-freeze output namespace; absent documented transient files are permitted and listed with saved hashes. A present transient must still match. Every other frozen/preserved/package file and ledger prefix is verified. No frozen source is edited, lock recreated, hash replaced or schema relaxed. The four omitted preservation locks and their hashes are listed in [transient-files.json](transient-files.json). Plain frozen `bob.py verify` predates delivery/ and cannot accept newly added deliverables; use the documented adapter.

An independent rebuild in a separate filtered COPY verifies all saved package hashes, runs the unchanged empirical loader and the registered synthetic fixture rebuild, and compares canonical output bytes with the original. The saved proof is [rebuild-proof.json](rebuild-proof.json). The empirical output must be byte-identical: SHA-256 `daec3a018eac0db5bd7d031274da07dd91c62221f647e69e5901bfd12c5ff9f5`. The original frozen suite passed 213/213; four additive verifier-boundary checks passed. The filtered copy simulates the specified GitHub publication exclusions; this task does not claim a network clone, GitHub push, website deployment or completed independent reviewer acceptance.

Follow the exact commands in [README.md](README.md). No installed models, Ollama service, provider CLI, credentials, parent study directory or network are required to rebuild saved empirical results. Python 3.9+ suffices; Node is required only for the optional frozen cross-language test suite. The empirical rebuild, presentation generation and four adapter tests use the Python standard library.

**Stop:** v0.2 is final for this task. Failed forecasts and the technical completion failure remain visible. Interesting questions are appended in [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md); none authorizes new collection.
''')
    (OUT/'RESULTS.md').write_text(intro + '\n'.join(sections))
    (OUT/'README.md').write_text(intro.replace('# Bridge or Bus? — v0.2 results','# Bridge or Bus? — reproducible v0.2 delivery',1) + '''## Read and reproduce

Prepared for Claude, the delegating reviewer. Root `RESULTS.md`, `PROJECT_STATE.md`, RUN files, protocol and analysis code are frozen historical inputs; current documents are here under `delivery/`. [RESULTS.md](RESULTS.md) contains every registered prediction, all 32 model cells, all paired intervals, code controls, v0.1 comparison, deviations, operational events, spend and limits. [cells.csv](cells.csv) and [baseline-results.json](baseline-results.json) provide machine-readable tables. [PROJECT_STATE.md](PROJECT_STATE.md) records the delivery state.

From a fresh clone of `Robin84Bran/research`, enter `bridge-or-bus/v0.2` and run:

```sh
python3 -B delivery/test_reproduce.py
python3 -B delivery/reproduce.py --fresh-clone --fixtures
```

The second command verifies the package, all four freeze digests/chain, the current source-bound freeze, r1/r2 preservation and r2 ledger prefix, and saved push provenance; audits all saved raw calls; rebuilds `build/reproduced-results.json`; compares it **byte for byte** with `build/results.json`; then rebuilds the unchanged synthetic analysis and fake-transport fixtures. It writes `build/reproduction-report.json`. It never collects or edits frozen code. Use a fresh copy per run, or choose new `--output` and `--report` paths, because reproduction outputs are create-once.

Python 3.9+ and its standard library are sufficient for these commands. No credentials, provider runtime, network or parent folder is needed. The existing Node executable is only needed for the optional full frozen test suite's toy-vector cross-language check. The original suite passed 213/213 before delivery; original saved evidence remains in `build/delivery-test-output.txt`.

`--fresh-clone` permits absence only of documented transient patterns: `__pycache__`, `.DS_Store`, `.git`, `*.lock`. Present files are still hash checked. Four empty preservation locks are listed, with original hashes, in [transient-files.json](transient-files.json). Without `--fresh-clone` the adapter requires them. Neither mode weakens raw data, manifest, prompt, schema or analysis hashes. Plain `bob.py verify/analyze` predates the post-freeze delivery namespace, so use the adapter for the published package. Registered scoring and bootstrap code remain the unchanged frozen modules.

The publication/copy filter removes **only** those transient patterns and retains original source, evidence, void evidence, ledgers, historical build outputs, current result and this delivery. [package-manifest.json](package-manifest.json) binds the retained package; the manifest itself and the derived rebuild proof are necessarily outside its self-hash inventory and are still included in the package. New reproduction outputs live under build/. [rebuild-proof.json](rebuild-proof.json) records the independently rebuilt result SHA-256, byte count, omission hashes, package verification and synthetic fixture pass. This demonstrates an actual separate filesystem COPY; no GitHub push, network clone, website release or reviewer acceptance is claimed here.

To regenerate presentation only (no bootstrap, no model calls):

```sh
python3 -B delivery/build_report.py
```

The report generator reads `build/results.json` and evaluates only the already-frozen deterministic code controls. `headline.svg` is a portable standalone figure, with source data in the CSV/JSON tables. Post hoc breakdowns and controls are secondary, with no changes to the primary. Unit-world lookup reuse and mg-derived submissions are observationally indistinguishable for models; exclusive counts remain null/UNKNOWN. Exhaustion after describe is zero in every registry cell. All 1,200 r1 local episodes are VOID-HARNESS and excluded; v0.1 is shown separately.

Accounted cumulative spend is **USD4.667178**, outstanding holds **USD0**; cash billing, hardware and energy remain UNKNOWN. One zero-cost subscription-limit refusal/resume is operational, not model behavior. Study-wide technical completion failed, and independent acceptance remains UNKNOWN. **Stop after v0.2; do not run collection commands.**
''')

    # Portable SVG plot. No external fonts, JS, images, model calls or packages.
    # All plotted values are the table's actual counts; validity uses a separate
    # annotation and never changes the success bar denominator.
    plotrows=[(NAMES[m]+' · '+a,[r['cohorts'][m]['cells'][w+'/'+a] for w in WORLD_ORDER])
              for m in MODELS for a in ['stale','registry']]
    plotrows += [(p+' · '+a,[base[p]['qwen7b'][w+'/'+a] for w in WORLD_ORDER])
                 for p in base for a in ['stale','registry']]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="850" viewBox="0 0 1120 850" role="img" aria-labelledby="title desc">',
         '<title id="title">Bridge or Bus v0.2: correct submissions, acknowledgment and validity</title>',
         '<desc id="desc">Each bar shows percent correct accepted submissions on planned assignments. Acknowledgment equals success throughout. Text also shows valid episode percent. Local cells n=50; Claude n=10. Script policies are secondary controls.</desc>',
         '<rect width="1120" height="850" fill="white"/>',
         '<g font-family="Arial, sans-serif" fill="#17202a">',
         '<text x="25" y="33" font-size="22">Bridge or Bus? · v0.2</text>',
         '<text x="25" y="57" font-size="14">Correct submission = acknowledged success here. Bar: S* / A*; annotation: valid episodes.</text>',
         '<text x="25" y="80" font-size="13">Local n=50/cell; Claude n=10/cell. Scripts evaluated on both seed sets; results identical.</text>']
    for j,w in enumerate(WORLD_ORDER):
        svg.append(f'<text x="{260+j*210}" y="113" font-size="17">{w.title()}</text>')
    for i,(label,cells) in enumerate(plotrows):
        y=144+i*45
        color='#1768ac' if i<8 else '#5e6b75'
        svg.append(f'<text x="25" y="{y+10}" font-size="13">{html.escape(label)}</text>')
        for j,c in enumerate(cells):
            x=260+j*210;k=c['counts'];n=c['n'];value=100*k['Sstar']/n;v=100*k['trajectory_valid']/n
            svg.append(f'<rect x="{x}" y="{y}" width="160" height="14" fill="#eef1f4"/>')
            svg.append(f'<rect x="{x}" y="{y}" width="{1.6*value:g}" height="14" fill="{color}"/>')
            svg.append(f'<text x="{x}" y="{y+30}" font-size="12">{value:g}% S*/A* · {v:g}% valid</text>')
        if i==7:svg.append(f'<line x1="25" x2="1090" y1="{y+39}" y2="{y+39}" stroke="#9ca7b0"/>')
    svg += ['<text x="25" y="799" font-size="14">Primary Qwen drift Δ: +2.0 pp [−4.0, +8.0]. Joint rule: FAIL.</text>',
            '<text x="25" y="824" font-size="13">Code controls are secondary. VOID-r1 excluded; historical v0.1 appears separately in RESULTS.md.</text>','</g></svg>']
    (OUT/'headline.svg').write_text('\n'.join(svg)+'\n')
    print(canonical(dict(status='PASS',source_result_sha256=sha((ROOT/'build/results.json').read_bytes()),
                         model_cells=32,baseline_assignments=3*len(plan),empirical_analysis_calls=0,model_calls=0)))


if __name__=='__main__':
    main()
