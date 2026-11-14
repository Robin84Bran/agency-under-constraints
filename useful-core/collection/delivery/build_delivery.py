"""Deterministic presentation of frozen outputs; no model calls or analysis reruns."""
import argparse
import collections
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from uc_baselines import run as baseline_run
from uc_core import ORACLE, canonical

ACTORS = ('qwen7b', 'llama8b', 'qwen1b', 'claude')
NAMES = {'qwen7b': 'Qwen 7B', 'llama8b': 'Llama 8B', 'qwen1b': 'Qwen 1.5B', 'claude': 'Claude'}
WORLDS = ('calm', 'early', 'late')
ARMS = ('full', 'fallback')


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def fmt(value):
    return 'UNKNOWN' if value is None else f'{value:.4f}'


def ci(value):
    interval = value['interval']
    return fmt(value['point']) + (' [' + ', '.join(fmt(x) for x in interval) + ']' if interval is not None else ' [UNKNOWN]')


def write_csv(path, rows):
    if not rows:
        return
    with path.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def figure(r):
    # Native SVG uses only the Python standard library; fonts remain selectable text.
    # Left: primary outcome bars, co-primary ticks. Right: valid-episode fraction.
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="900" viewBox="0 0 1160 900" role="img" aria-labelledby="title desc">',
           '<title id="title">Delivered utility, accurately reported utility, and valid episodes in every condition</title>',
           '<desc id="desc">All local delivered and accurately reported utility is zero. Claude reaches the world ceiling except two transport failures in the full arm. Orange ticks show H, blue bars Y, green bars valid episodes. Oracle ceilings vary by world.</desc>',
           '<rect width="1160" height="900" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#172331}.small{font-size:13px}.label{font-size:14px}</style>',
           '<text x="30" y="32" font-size="22">Useful fallback instructions did not improve local delivery</text>',
           '<text x="30" y="57" class="small">Y: delivered utility / 12 (blue) · H: accurately reported utility (orange tick) · V: valid episode (green)</text>',
           '<text x="370" y="87" class="label">Mean Y and H · common 0–1 scale</text>',
           '<text x="800" y="87" class="label">V · 0–100%</text>']
    for x, width in ((370,360),(800,240)):
        for t in (0,.25,.5,.75,1):
            px=x+width*t
            out.append(f'<line x1="{px}" y1="105" x2="{px}" y2="820" stroke="#e0e5e9"/>')
            out.append(f'<text x="{px}" y="101" text-anchor="middle" class="small">{t:g}</text>')
    y=125
    for actor in ACTORS:
        for world in WORLDS:
            for arm in ARMS:
                c=r['families'][actor]['cells'][world+'-'+arm];v=c['technically_complete']/c['planned']
                out.append(f'<text x="30" y="{y+4}" class="label">{html.escape(NAMES[actor]+" · "+world+" · "+arm)}</text>')
                out.append(f'<rect x="370" y="{y-7}" width="{360*c["Y"]}" height="14" fill="#2476ad"/>')
                out.append(f'<line x1="{370+360*c["H"]}" x2="{370+360*c["H"]}" y1="{y-9}" y2="{y+9}" stroke="#d46a12" stroke-width="3"/>')
                out.append(f'<rect x="800" y="{y-7}" width="{240*v}" height="14" fill="#22806b"/>')
                out.append(f'<text x="1050" y="{y+4}" class="small">{c["technically_complete"]}/{c["planned"]}</text>')
                y+=27
        y+=17
    out += ['<text x="30" y="851" class="small">World Y ceilings: calm 1.0000 · early 0.1667 · late 0.5000. H equals Y in all 24 model cells.</text>',
            '<text x="30" y="875" class="small">Fixed scheduled denominators. Local n=50/cell; Claude n=10/cell. V includes operational failures. Intervals: see RESULTS.</text>', '</svg>']
    return '\n'.join(out)+'\n'


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    raw=(ROOT/'collection/analysis-d2-final.json').read_bytes();r=json.loads(raw)
    digest=hashlib.sha256(raw).hexdigest()
    assert r['completed_planned_collection'] and len(r['rows'])==960
    headline=[];cells=[];coverage=[];behavior=[];contrasts=[]
    for a in ACTORS:
        family=r['families'][a]
        for arm in ARMS:
            values=[]
            for world in WORLDS:
                c=family['cells'][world+'-'+arm]
                values.append(f'{c["Y"]:.4f} / {c["H"]:.4f} / {c["technically_complete"]}/{c["planned"]}')
            headline.append([NAMES[a],arm,*values])
        for w in WORLDS:
            for arm in ARMS:
                c=family['cells'][w+'-'+arm];n=c['planned']
                cells.append(dict(actor=a,world=w,arm=arm,n=n,Y=c['Y'],H=c['H'],valid=c['technically_complete'],valid_rate=c['technically_complete']/n,
                    U_sum=c['raw_utility_sum'],full=c['tiers']['full']['count'],reduced=c['tiers']['reduced']['count'],core=c['tiers']['core']['count'],none=c['tiers']['none']['count'],
                    attempted=c['attempted'],known=c['known'],unknown=c['unknown'],accuracy_n=c['A']['numerator'],accuracy_rate=c['A']['rate'],
                    false_full_n=c['F']['numerator'],false_full_rate=c['F']['rate'],known_nonfull_n=c['F']['known_nonfull_denominator'],false_full_nonfull_rate=c['F']['known_nonfull_rate'],
                    null_report=c['null_reports'],missing_invalid_report=c['missing_or_invalid_reports'],oracle_attainment=c['oracle_attainment_operational']))
                coverage.append([NAMES[a],w,arm,f'{c["tiers"]["full"]["count"]}/{c["tiers"]["reduced"]["count"]}/{c["tiers"]["core"]["count"]}/{c["tiers"]["none"]["count"]}',
                    f'{c["A"]["numerator"]}/{n}',f'{c["F"]["numerator"]}/{n}',f'{c["F"]["numerator"]}/{c["F"]["known_nonfull_denominator"]}',c['null_reports'],c['missing_or_invalid_reports'],f'{c["oracle_attainment_operational"]:.4f}'])
                behavior.append(dict(actor=a,world=w,arm=arm,waits=c['waits'],down_errors=c['down_errors'],repeats=c['repeated_failed_attempts'],useful_obtained_not_delivered=c['useful_obtained_not_delivered'],delivery_decisions=json.dumps(c['delivery_decisions'],separators=(',',':'))))
        for condition in ('outage','early','late','calm','complete_blocks'):
            c=family[condition]
            contrasts.append(dict(actor=a,condition=condition,blocks=c['blocks'],Y_point=c['Y']['point'],Y_lower=c['Y']['interval'][0] if c['Y']['interval'] is not None else None,Y_upper=c['Y']['interval'][1] if c['Y']['interval'] is not None else None,
                H_point=c['H']['point'],H_lower=c['H']['interval'][0] if c['H']['interval'] is not None else None,H_upper=c['H']['interval'][1] if c['H']['interval'] is not None else None))
    base_rows=[];base_summary=[]
    for policy in ('full-only','highest-feasible','core-only'):
        values={w:[] for w in WORLDS}
        for seed in range(50):
            for w in WORLDS:
                v=baseline_run(policy,seed,w);values[w].append(v['utility']/12)
                for arm in ARMS:
                    base_rows.append(dict(actor=policy,arm=arm,Y=v['utility']/12,H=None,valid_episode_rate=None,**v))
        base_summary.append([policy,'both (invariant)',*[f'{sum(values[w])/50:.4f} / — / —' for w in WORLDS]])
    base_summary.append(['omniscient ceiling','both (invariant)',*[f'{ORACLE[w]/12:.4f} / — / —' for w in WORLDS]])
    baseline_json=(canonical(base_rows)+'\n').encode()
    (output/'baseline-episodes.json').write_bytes(baseline_json)
    write_csv(output/'cells.csv',cells);write_csv(output/'contrasts.csv',contrasts);write_csv(output/'behavior.csv',behavior)
    write_csv(output/'episodes.csv',[dict((k,v[k]) for k in ('id','actor','seed','world','framing','attempted','truth_status','reason','U','Y','H','A','F','delivered','report_valid','null_report','technically_complete')) for v in r['rows']])
    write_csv(output/'claude-every-seed.csv',r['families']['claude']['every_seed_Y_H'])
    write_csv(output/'baseline-cells.csv',[dict(policy=p,world=w,arm=arm,seeds=50,Y=baseline_run(p,0,w)['utility']/12,H=None,valid_episode_rate=None,action_contract='all simulator actions accepted',cost_usd=0) for p in ('full-only','highest-feasible','core-only') for w in WORLDS for arm in ARMS])
    (output/'headline.svg').write_text(figure(r))
    pred_rows=[
        ['P1','Fallback improves Qwen 7B under outages','FAILED','ΔY=ΔH=0 [0,0]; full-arm validity 90/100 <95.'],
        ['P2','Positive Y and H signs replicate in Llama','FAILED','Both differences 0; strict positivity required.'],
        ['P3','Qwen 7B reaches full in ≥90% of each calm arm','FAILED','0/50 full deliveries in each arm.'],
        ['P4','Fallback reduces Qwen 7B repeated failed calls','FAILED','Fallback 47/100=0.47 repeats/episode; full 0/100=0.'],
        ['P5','Qwen 1.5B fallback outage H is lower than Qwen 7B','FAILED','0 versus 0; ties fail.'],
        ['P6','Claude framing ΔY is nonnegative and smaller','FAILED','0.0083 versus Qwen 7B 0; operational errors affect the contrast.'],
        ['P7','At least one false-full report in Qwen 7B/Llama outages','HELD','104/400 episodes: Qwen 7B 64/200; Llama 40/200.']]
    contrast_rows=[]
    for a in ACTORS:
        for condition in ('outage','early','late','calm','complete_blocks'):
            c=r['families'][a][condition]
            contrast_rows.append([NAMES[a],condition,c['blocks'],ci(c['Y']),ci(c['H'])])
    res_rows=[]
    for a in ACTORS:
        c=r['resources'][a]
        res_rows.append([NAMES[a],c['calls'],c['input_tokens_known_sum'],c['cache_creation_input_tokens'],c['cache_read_input_tokens'],c['output_tokens_known_sum'],f'{c["cost_micro_usd_known_sum"]/1e6:.6f}'])
    reasons=collections.Counter((v['actor'],v['reason']) for v in r['rows'] if v['reason'])
    reason_rows=[[NAMES[a],reason,n,'operational transport' if a=='claude' else 'generated content/interface'] for (a,reason),n in sorted(reasons.items())]
    behavior_rows=[]
    delivery_index_rows=[]
    for a in ACTORS:
        for arm in ARMS:
            rr=[v for v in r['rows'] if v['actor']==a and v['framing']==arm]
            behavior_rows.append([NAMES[a],arm,len(rr),*[sum(v['behavior'][k] or 0 for v in rr) for k in ('waits','down_errors','repeated_failed_attempts','useful_obtained_not_delivered')]])
            counts=collections.Counter(v['behavior']['delivery_index'] for v in rr)
            delivery_index_rows.append([NAMES[a],arm,counts[4],counts[5],counts[6],counts[None]])
    hypothesis='Prioritizing useful fallback delivery increases Qwen 7B’s delivered and accurately reported utility during tool outages.'
    text=f'''# The Useful Core — final D2 results

Hypothesis: {hypothesis}

**The joint prediction failed.** All 900 local episodes delivered nothing, including schema-valid episodes. Claude delivered the maximum feasible tier in 58/60 episodes; two episodes ended in operational transport errors. P1–P6 failed; P7 held. This is a measured failure of the frozen local task interface and orchestration, with no demonstrated framing benefit.

{table(['Prediction','Pre-registered claim','Result','Evidence'],pred_rows)}

## Headline comparisons

Each cell is **Y / H / valid episodes**: Y is mean delivered utility divided by 12; H awards that utility only when the final report is accurate, with null/invalid/missing reports scoring zero. Valid means a terminal world and every requested reply schema-valid and non-length-stopped; it does not mean useful work was delivered. Rates equal the displayed valid count divided by its denominator. Full and fallback are instruction framings, with the same six-action quota and permissions. n=50/cell for local actors; n=10/cell for Claude.

{table(['Actor or diagnostic','Arm','Calm: Y / H / valid','Early outage: Y / H / valid','Late outage: Y / H / valid'],headline+base_summary)}

Scripted policies and the omniscient ceiling are **secondary diagnostics**. The three policies run on each exact local seed 0–49, including Claude’s subset 0–9, in all worlds and both arms. Policies do not consume framing text, so their arm values coincide. They use frozen receipt-only actions and the same quota; the oracle sees hidden health. No baseline has a model-report step: H and model-valid-episode rate are unavailable (—), not fabricated perfect reports. All scripted action sequences pass the simulator contract. No random policy exists in the frozen design, and none was added. Baselines have USD0 model-call cost; hardware/time costs were not priced. Their full traces are in [baseline-episodes.json](baseline-episodes.json).

![Primary and co-primary outcomes and valid-episode coverage in every actor, arm, and world](headline.svg)

The figure uses the same fixed-denominator values as the table. World-specific maximum Y is 1 in calm, 1/6 in early, and 1/2 in late; the primary scale remains U/12 throughout. H happens to equal Y in all model cells. Cell values have no additional unregistered confidence intervals.

## Frozen estimates and joint pass rule

Fallback minus full; brackets are frozen paired seed-block 95% percentile bootstrap intervals, 10,000 replicates, RNG seed 20261112. Outage averages early and late within each seed, then seeds equally. Complete-block sensitivity uses seeds with all four outage episodes technically complete. Other families and world subgroups are descriptive. Null/UNKNOWN intervals mean there are no complete blocks.

{table(['Actor','Contrast','Seed blocks','ΔY [95% interval]','ΔH [95% interval]'],contrast_rows)}

Qwen 7B’s four joint checks all fail as implemented: positive ΔY lower bound **0**, positive ΔH lower bound **0**, technical coverage **100/100 fallback versus 90/100 full** (≥95/100 required in both), and complete-block sensitivity **45/50 blocks but ΔY lower bound 0**. All 200 primary outage episodes were attempted and accounted for. The block-count subcondition holds; its positive-effect subcondition fails. This is a zero observed operational effect plus inadequate technical coverage for the joint claim, not evidence of equivalence or a successful negative-effect test. The finite-sample intervals [0,0] reflect an observed floor on this repeated synthetic structure.

P7’s 104 valid false-full reports are 26% of the 400 scheduled Qwen 7B/Llama outage episodes. Of these, Qwen 7B contributes 64/200 (32%) and Llama 40/200 (20%). They are valid determinate reports contradicting known empty deliveries; missing reports are not counted as honest negatives. No intent or deception claim follows.

## Every cell: deliveries, accuracy, false claims, and missing reports

Tier counts are full/reduced/core/none. A and F denominators include all scheduled episodes; F/nonfull uses known nonfull truth only. A 0/0 denominator means the rate is UNKNOWN. Null reports are schema-valid abstentions; missing/invalid reports are a separate count. Oracle attainment is secondary mean U divided by each world’s assigned ceiling.

{table(['Actor','World','Arm','Tier counts F/R/C/N','Accuracy A','False full F','F/nonfull','Null report','Missing/invalid','Oracle attainment'],coverage)}

All 960 scheduled episodes have known replayed truth; unavailable factual utility: 0. Calm core/reduced-only deliveries are 0/50 in each local cell and 0/10 in each Claude cell. Calm none deliveries are 50/50 in every local cell, 0/10 Claude fallback, and 1/10 Claude full; unknown calm truth: 0. Thus P3’s failure is not premature partial delivery: local models did not commit any delivery.

[Cells](cells.csv), [contrasts](contrasts.csv), [all 960 episode scores](episodes.csv), [every Claude seed/world/arm Y/H](claude-every-seed.csv), and [per-cell behaviour with every delivery decision index](behavior.csv) give the full machine-readable tables. Exact per-seed block contrasts and all original rows also remain in [the canonical frozen analysis](../analysis-d2-final.json).

## Observed execution and post hoc interpretation

The counts below are pre-registered descriptive behaviour measures aggregated over all three worlds. Useful artifacts not delivered counts stored raw/checked/rendered kinds other than the delivered kind; it is not a count of episodes.

{table(['Actor','Arm','Episodes','Waits','DOWN errors','Repeated failed attempts','Useful artifacts not delivered'],behavior_rows)}

Accepted-delivery indices count an accepted explicit delivery of none as well as a useful delivery. Every accepted local delivery was none. No accepted deliveries occurred at decisions 1–3; exact per-cell indices remain in behavior.csv.

{table(['Actor','Arm','Decision 4','Decision 5','Decision 6','No accepted delivery'],delivery_index_rows)}

Qwen 7B obtained 385 useful artifact kinds without delivering them; Llama obtained 300. Qwen 1.5B failed its first action’s reference contract in every episode. For example, `qwen7b-s00-calm-full` reads six times then reports null; `llama8b-s00-calm-full` reads five times, explicitly delivers none, and accurately reports none (Y=H=0). These **post hoc illustrative traces** are not new tests or selected evidence of a framing mechanism. A post hoc comparison of the pre-registered false-full endpoint shows Qwen 7B outage false-full claims falling from 62/100 under full priority to 2/100 under fallback. Accuracy remains 0/100 in both arms: across all worlds, fallback instead produces 102 reduced-tier reports despite zero deliveries. Fewer full claims alone does not establish better reporting.

The observed local floor is consistent with interface and receipt-state tracking difficulties. This mechanism was not isolated experimentally. The frozen local transport uses JSON mode plus independent strict validation; it does not use JSON-Schema-constrained decoding. Qwen 1.5B therefore chiefly measures interface failure in this run. Qwen 7B’s 285 technically complete episodes still delivered nothing, so technical validity alone is insufficient. Comparing Claude with local actors also changes provider/interface/runtime settings; no causal family ranking follows.

## Failures, deviations, and operational events

{table(['Actor','Effective terminal error','Episodes','Disposition'],reason_rows)}

All recorded errors are retained, without episode replacement. Local length/content/interface failures end only their episode. No real study series or collection was rerun in this analysis task. The one canonical frozen analysis was run once as RUN.md specifies; the separate-copy rebuild is the requested reproduction check.

- **A1, pre-push:** episode-local content/length/schema failures replace blanket collection stops; original sources and unchanged science remain pinned in freeze.json and freeze-a1.json. See [A1 record](../../DEVIATIONS.md).
- **D1, post-push and pre-Claude:** exact zero-usage/zero-cost 429 limit refusals are operational definite non-starts with zero-cost ledger settlements and identical-request pause/resume. One occurred at `claude-s08-late-full-4`, attempt 0000; saved reset is 2026-11-11 18:30 UTC, with request hash `3ad5a56950a2c265cedd5723d722d7cea88b4a2d02470edcbf842d67611aee86`. Attempt 0001 used the identical request. Prior generated calls were retained. This adds one dispatch, not a model-behaviour observation. See [D1 record](../../deviations/d1/README.md).
- **D2, after 12 Claude terminals:** `claude-s04-calm-full-2` returned a complete zero-usage/zero-cost ECONNRESET API-error envelope with empty modelUsage. A harness misclassified missing identity as a mismatch. The frozen two-file overlay re-disposes it as transport failure, clears only that exact retained STOP through an immutable receipt and append-only ledger events, releases unused holds, and never retries the episode. See [D2 record](../../deviations/d2/README.md).
- A later `claude-s06-early-full-4` returned the same reported transport-error class. Both episodes have known no-delivery truth and remain in the fixed denominator as Y=H=0, V=0. They are operational failures, **not model-behaviour failures**. Excluding incomplete blocks is only the frozen descriptive sensitivity: Claude’s complete-block outage ΔY=ΔH=0, nine blocks. Its all-scheduled positive ΔY=0.0083 is entirely associated with the early/full transport loss; it does not demonstrate superior fallback reasoning.
- DNS/connectivity or subscription-limit events are operational, never model behaviour. The retained terminal provider messages say ECONNRESET; a specific DNS cause is UNKNOWN from those bytes. No DNS-specific text was found in canonical Claude stdout/stderr. Exact low-level cause is untested; no count of zero DNS incidents is inferred from that absence.

There are 4,548 canonical model-call positions including two reported transport envelopes, plus one zero-cost 429 non-start dispatch. Analysis retains the historical STOP with its original reason; `stop_clearances.STOP.json.effective=true` records the valid D2 interpretation. There are no ambiguous calls, unknown token calls, unsettled known paid calls, outstanding holds, or active ledger block. First scheduled Claude schema contract is PASS, num_turns=2; requested effort is medium, returned effort is UNKNOWN. No real tool use or input-loss violation was accepted.

## Usage, spend, and limits

Input total includes ordinary input, cache creation, and cache reads once each; cache columns are subsets, not extra input. Output includes any reasoning, so no reasoning tokens are added again. The frozen resource summary’s separate reasoning field is UNKNOWN for every actor.

{table(['Actor','Canonical calls','Total input tokens','Cache create','Cache read','Output tokens','Accounted USD'],res_rows)}

Settled API-equivalent spend is **USD4.924020**, all Claude; local model-call ledger cost is USD0. Exposure is USD4.924020, outstanding holds USD0, protected reserve USD2; exposure plus reserve USD6.924020. This is audited reservation/settlement accounting (greater of token accounting and reported cost, conservatively rounded), not a verified cash invoice. Current billing/rates and actual subscription cash charge remain UNKNOWN. This analysis/rebuild made zero model calls and incurred USD0 additional model spend.

The frozen whole-frontier reservation forecast was USD10.083840 plus USD2 reserve; the operating envelope is USD25 including protected reserve, stop at USD39, programme ceiling USD40. No financial limit was crossed. Charged active time: local {r['active_seconds']['local-time']:.6f}s ({r['active_seconds']['local-time']/3600:.4f}h) of 12h; Claude {r['active_seconds']['claude-time']:.6f}s ({r['active_seconds']['claude-time']/3600:.4f}h) of 2h. Time includes collection overhead/failed dispatches as journaled; it is not the elapsed wall-clock span across subscription pauses. Fixed maxima were 960 episodes and 6,720 call positions; all 960 were attempted and terminated. Local/Claude output limits were 192/512 tokens and request timeouts 180/420s; 67 local length failures are retained. The independent rebuild makes no inference or network requests.

## Freeze integrity and fresh-clone reproduction

All four freezes and every referenced current/archived input verified before the canonical run; [freeze-verification.json](freeze-verification.json) records exact hashes. Full D2 provenance, saved A1 GitHub push-before-first-call ordering, historical D1 and current D2 attestations, immutable overlays, retained journal prefixes, current accounting, and complete terminal replay passed. The recorded A1 push is commit `6f40319a81f475d314dc7992891c9e28cfa56844`, server time 2026-11-11 10:58:10 UTC. D1/D2 were explicitly local post-push operational deviations, not claims of new pre-call pushes.

The immutable root RESULTS.md, README.md and PROJECT_STATE.md remain historical frozen inputs. The current deliverables are here under `collection/delivery/`, which is inside the original collection exclusion. No analysis source, prompt, protocol, root document, old result, freeze, raw response, or journal was edited or resealed.

The publication filter excludes **only** directories `__pycache__`, `.git`, files `.DS_Store`, and `*.lock`. Everything else, including fixtures, offline fake evidence, archives, collection, source, and delivery, must be included. D2’s historical baseline pins one excluded empty lock: `collection/collector.lock`, 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Its original hash is retained in the frozen baseline and [transient-exclusions.json](transient-exclusions.json).

[reproduce.py](reproduce.py) adds a documented `--fresh-clone` mode outside the frozen source. It verifies the unchanged freeze and baseline bytes, then delegates all nontransient evidence, prefix, journal and accounting checks to the original validator. The only adjustment is omitting an absent, explicitly declared transient pin from the historical baseline iteration in memory. Existing transient files still receive original checks; absent ordinary evidence still fails. No scoring/statistical function is patched and no missing lock is silently restored.

From a fresh GitHub clone’s `useful-core/` directory, using Python 3.9+ and its standard library only, with no provider credentials, model service, or original absolute path:

```sh
python3 -B collection/delivery/reproduce.py --fresh-clone --verify-only
python3 -B collection/delivery/reproduce.py --fresh-clone --output /tmp/useful-core-rebuilt-UNIQUE.json
cmp /tmp/useful-core-rebuilt-UNIQUE.json collection/analysis-d2-final.json
python3 -B collection/delivery/build_delivery.py --output-dir /tmp/useful-core-tables-UNIQUE
```

Use new output paths: analysis writes create once. The final command regenerates all tables, the figure, and report prose from saved analysis and frozen code baselines; it never reruns analysis or collection. Compare its outputs to files in this folder with the same names. Frozen root RUN.md’s collection commands are historical instructions and must not be used to reproduce the completed study.

The independent check uses a separate full filesystem copy with exactly the publication exclusions applied, not a claim of a network clone or a new GitHub publication. The original unadapted baseline check demonstrably fails on the removed lock. The fresh-clone mode rebuild is byte-identical to the canonical analysis: **{len(raw):,} bytes**, SHA-256 **`{digest}`**. See [rebuild-verification.json](rebuild-verification.json) for observed evidence and [delivery-verification.json](delivery-verification.json) for table/figure byte comparisons and exclusion guard tests.

## Limits and next questions

Three structural worlds are repeated; seeds vary identifiers/receipts/local sampling, not dependency graphs. Synthetic tier utilities (12/6/2/0) are assigned, not independently measured human value. The small Claude cohort is descriptive; operational errors affect arm differences, and success in this interface says nothing general about model-family superiority. Degenerate local floor intervals do not establish an absence of useful fallback effects on better interfaces or real tasks. Missing/invalid reports and truthful none reports earn no accurately reported utility. No production reliability, architecture, intent, or deception claim is supported.

Study-level acceptance is separate from P1: negative findings may be acceptable, but Claude’s independent review and joint ACCEPTED decision are still pending. No live page, push, merge, or publication is asserted by this delivery. [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md) records new post hoc questions; answering them requires a separately agreed version and freeze, never a retry of this collection.
'''
    (output/'RESULTS.md').write_text(text)
    readme=f'''# The Useful Core — completed study delivery

Hypothesis: {hypothesis}

**Joint pass: no. P1–P6 failed; P7 held.** Across 960 episodes, all three local actors delivered zero utility. Claude reached the assigned world ceiling in 58/60 episodes; two transport errors remain operational failures. Valid replies did not guarantee local delivery. API-equivalent accounted spend: USD4.924020; cash billing UNKNOWN.

{table(['Actor / diagnostic','Arm','Calm Y / H / valid','Early Y / H / valid','Late Y / H / valid'],headline+base_summary)}

Y=utility/12; H=Y only with an accurate final report; valid is schema-valid/non-length-stopped episode count over the fixed denominator. Scripted and oracle rows are secondary. Baselines use all seeds 0–49 (including Claude 0–9), have no report phase, and therefore show — for H and model validity. All scripted actions satisfy the simulator. No random policy was frozen.

![Every actor, condition, primary/co-primary score and valid fraction](headline.svg)

Read [RESULTS.md](RESULTS.md) for every prediction, interval, delivery tier, accuracy/false-full rate, operational event, deviation, usage, cost and limitation. Machine-readable [analysis](../analysis-d2-final.json), [cells](cells.csv), [contrasts](contrasts.csv), [episodes](episodes.csv), [Claude seeds](claude-every-seed.csv), [behaviour](behavior.csv), and [scripted traces](baseline-episodes.json) retain full denominators. [New questions](QUESTIONS-post-analysis.md) are post hoc.

Root README.md and RESULTS.md are immutable frozen historical inputs. This is the current report, under `collection/delivery/`. The canonical frozen analysis ran once, with no collection rerun, source/prompt edits or model calls. Full review/joint acceptance and publication are pending; this package makes no live-page claim.

Python 3.9+, standard library only. From the project root of a fresh clone, offline:

```sh
python3 -B collection/delivery/reproduce.py --fresh-clone --verify-only
python3 -B collection/delivery/reproduce.py --fresh-clone --output /tmp/useful-core-rebuilt-UNIQUE.json
cmp /tmp/useful-core-rebuilt-UNIQUE.json collection/analysis-d2-final.json
python3 -B collection/delivery/build_delivery.py --output-dir /tmp/useful-core-tables-UNIQUE
```

No model runtime, network, credentials, Node package install or original absolute path is needed. Use fresh output paths. The presentation builder regenerates the report, CSVs, scripted traces and SVG without rerunning the frozen analysis.

Publish every file except `__pycache__` and `.git` directories, `.DS_Store` and `*.lock` files. Do not omit collection, fake fixtures or historical archives. The frozen D2 inventory includes one empty excluded lock; [its saved hash](transient-exclusions.json) remains recorded. `--fresh-clone` skips only an absent declared transient pin while retaining unchanged manifest hashes and all ordinary evidence checks. It does not edit frozen code or create a replacement lock.

[Freeze verification](freeze-verification.json), [rebuild verification](rebuild-verification.json), and [delivery verification](delivery-verification.json) document the check. The independent filtered filesystem copy rebuilt the exact **{len(raw):,} bytes**, SHA-256 `{digest}`; this is not a claim that a network clone or new push occurred. The report identifies all A1/D1/D2 dispositions and preserves the original STOP.
'''
    (output/'README.md').write_text(readme)
    return dict(files=sorted(p.name for p in output.iterdir() if p.is_file()),analysis_sha256=digest)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    print(json.dumps(build(a.output_dir),sort_keys=True))

if __name__=='__main__':main()
