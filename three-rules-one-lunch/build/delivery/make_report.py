"""Post-analysis presentation only; never invokes analyze or a model provider.

Reads the single final frozen analysis and evaluates its unchanged frozen code
policies to expose H/post-relocation metrics omitted from the compact export.
All report files are create-once. Not part of the scientific freeze.
"""
import csv
import html
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from trl_analysis import score
from trl_core import baseline, sha, strict_load
from trl_io import read, save, save_text
from trl_budget import Ledger

OUT = ROOT/'build/delivery'
S = read(ROOT/'build/analysis-first/summary.json')
ROWS = read(ROOT/'build/analysis-first/episodes.json')
NAMES = {'qwen7b':'Qwen 2.5 7B','llama8b':'Llama 3.1 8B',
         'qwen1b':'Qwen 2.5 1.5B','claude':'Claude Opus 5.5'}
ACTORS = tuple(NAMES)
REGIMES = ('private','shared','central')
POLICIES = ('greedy-shared','greedy-private','uniform','oracle','greedy-central','all-null')


def avg(xs):
    return sum(xs)/len(xs) if xs else None


def fmt(x, digits=4):
    return 'UNKNOWN' if x is None else f'{x:.{digits}f}'


def pct(x):
    return 'UNKNOWN' if x is None else f'{100*x:.1f}%'


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |',
                       '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(x) for x in row)+' |' for row in rows])


def csvfile(name, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    save_text(OUT/name,stream.getvalue())


def ci(m):
    return f"{fmt(m['difference'],6)} [{fmt(m['ci95'][0],6)}, {fmt(m['ci95'][1],6)}] (n={m['n']})"


def group(actor, regime):
    return [r for r in ROWS if r['episode']['actor']==actor and r['episode']['regime']==regime]


def main():
    assert len(ROWS)==960 and all(r['attempted'] and r['kind']=='MODEL' for r in ROWS)
    assert read(ROOT/'build/rebuild-final/byte-identity.json')['status']=='PASS'
    ledger=Ledger(ROOT/'collection/cost.jsonl')
    dollars=defaultdict(int)
    scheduled_ids={r['episode']['id'] for r in ROWS}
    for ident, entry in ledger.settled.items():
        episode_id=ledger.starts[ident]['episode'].split('.d4-',1)[0]
        assert episode_id in scheduled_ids
        dollars[episode_id]+=entry['actual']
    assert sum(dollars.values())==ledger.spent
    baseline_rows=[]
    for n in (100,20):
        for policy in POLICIES:
            regime='private' if policy=='greedy-private' else ('central' if policy in ('oracle','greedy-central') else 'shared')
            rows=[score(seed,regime,baseline(seed,policy).events,True,False) for seed in range(n)]
            entry={'seed_set':f'0–{n-1}','n':n,'policy':policy,
                   **{k:avg([r[k] for r in rows]) for k in ('Y','H','pre_Y','post_Y','pre_H','post_H','coverage')},
                   'valid_episode_rate':1.0,'model_calls':0,'model_cost_usd':0.0}
            expected=S['cohorts']['claude' if n==20 else 'qwen7b']['same_seed_baseline_mean_Y'][policy]
            assert entry['Y']==expected
            baseline_rows.append(entry)
    csvfile('baselines.csv',baseline_rows)
    save(OUT/'baselines.json',{'status':'secondary descriptive tabulation of unchanged frozen policies',
                              'source':'trl_core.baseline and trl_analysis.score; no new inference or hypothesis tests',
                              'rows':baseline_rows})
    baselines={(r['n'],r['policy']):r for r in baseline_rows}
    headline=[];models=[];phases=[];rounds=[];stales=[];resources=[];reasons=[]
    for actor in ACTORS:
        c=S['cohorts'][actor]
        for regime in REGIMES:
            m=c['regimes'][regime];rs=group(actor,regime)
            ratio=c['Y_fraction_of_baselines'][regime]['greedy-shared']['value']
            valid=m['complete_episodes']/m['n']
            headline.append([NAMES[actor],regime,fmt(m['Y']),fmt(m['H']),fmt(m['post_Y']),
                             f"{m['complete_episodes']}/{m['n']} ({pct(valid)})",fmt(ratio,3)])
            models.append({'actor':actor,'regime':regime,'n':m['n'],
                           **{k:m[k] for k in ('Y','H','pre_Y','post_Y','pre_H','post_H','coverage','null_rate','technical_missing_rate','attempted_episodes','complete_episodes','calls')},
                           'valid_episode_rate':valid,'Y_fraction_greedy_shared':ratio,
                           'Y_fraction_greedy_private':c['Y_fraction_of_baselines'][regime]['greedy-private']['value']})
            phases.append([NAMES[actor],regime,fmt(m['pre_Y']),fmt(m['post_Y']),fmt(m['pre_H']),fmt(m['post_H']),
                           pct(m['coverage']),pct(m['null_rate']),pct(m['technical_missing_rate'])])
            for br in m['by_round']:
                rounds.append({'actor':actor,'regime':regime,**br})
            stale={'actor':actor,'regime':regime,'n':m['n'],
                   'true_peak_r3_queries':sum(r['stale_true_old_peak']['round_3_queries'] for r in rs),
                   'true_peak_r4_queries':sum(r['stale_true_old_peak']['round_4_queries'] for r in rs),
                   **{'true_peak_mean_'+k:v for k,v in m['stale_true_old_peak'].items()},
                   'best_observed_denominator':m['stale_best_observed_denominator'],
                   **{'best_observed_mean_'+k:v for k,v in m['stale_best_observed'].items()},
                   'peak_overlap_episodes':sum(r['old_current_peak_overlap_cells']>0 for r in rs),
                   'peak_overlap_cells_total':sum(r['old_current_peak_overlap_cells'] for r in rs)}
            stales.append(stale)
            cash=sum(dollars[r['episode']['id']] for r in rs)/1e6
            resources.append({'actor':actor,'regime':regime,'calls':m['calls'],
                              **{k:m[k] for k in ('input_tokens','cache_read_tokens','cache_creation_tokens','output_tokens','unknown_usage_calls','elapsed_seconds')},
                              'accounted_model_usd':cash})
            counter=Counter(reason for r in rs for reason in r['reasons'])
            reasons.extend({'actor':actor,'regime':regime,'terminal_reason':reason,'episodes':count}
                           for reason,count in sorted(counter.items()))
    csvfile('model-metrics.csv',models);csvfile('round-metrics.csv',rounds)
    csvfile('stale-exploitation.csv',stales);csvfile('resources.csv',resources)
    csvfile('terminal-reasons.csv',reasons)
    csvfile('headline.csv',[dict(zip(('actor','regime','Y','H','post_Y','valid_episodes','Y_fraction_greedy_shared'),row)) for row in headline])
    headline_table=table(['Actor','Regime','Mean Y','Productive H','Post-relocation Y','Valid episodes','Y / greedy-shared'],headline)
    baseline_table=table(['Seeds','Frozen code policy (secondary)','Mean Y','Productive H','Post-relocation Y','Valid episodes','Y / greedy-shared'],
                         [[b['seed_set'],('random' if b['policy']=='uniform' else 'full-information oracle' if b['policy']=='oracle' else b['policy']),
                           fmt(b['Y']),fmt(b['H']),fmt(b['post_Y']),f"{b['n']}/{b['n']} (100%)",
                           fmt(b['Y']/baselines[(b['n'],'greedy-shared')]['Y'],3)]
                          for b in baseline_rows if b['policy'] in POLICIES[:4]])
    predictions=[
        ('P1','Shared receipts help Qwen 7B','failed','Joint rule not met: ΔY=ΔH=0; neither worker arm has a complete episode.'),
        ('P2','Positive Y and H signs replicate in Llama','failed','Both differences are zero; all episodes fail the interface.'),
        ('P3','Central Y ≥ shared Y in both 7B/8B models','met','Qwen: +0.196253; Llama: 0 (tie). Interface failures prevent a planning interpretation.'),
        ('P4','Shared post-relocation Y > private in both 7B/8B models','failed','Both differences are zero, with no executed worker queries.'),
        ('P5','1.5B shared Y < Qwen 7B shared Y','failed','0.003455 is above 0; different validity rates dominate this ranking.'),
        ('P6','Claude shared Y > private Y (descriptive)','met','+0.069713 over 20 seeds; 95% interval [−0.000365, 0.137209].'),
        ('P7','At least 95% valid episodes in every model/regime','failed','Only Qwen 7B central and Claude private/shared meet 95%; Claude central is 85%.'),
    ]
    assert all(S['predictions'][pid]['status']==status for pid,_,status,_ in predictions)
    pred_table=table(['ID','Registered prediction','Held?','Frozen evaluation'],
                     [[pid,label,'Held' if status=='met' else 'Failed',detail] for pid,label,status,detail in predictions])
    contrasts=[]
    for actor in ACTORS:
        c=S['cohorts'][actor]
        for key,label in [('shared_minus_private_Y','Shared − private Y'),('shared_minus_private_H','Shared − private H'),
                          ('complete_pair_sensitivity_Y','Complete-pair shared − private Y'),
                          ('central_minus_shared_Y','Central − shared Y'),('central_minus_shared_H','Central − shared H')]:
            contrasts.append([NAMES[actor],label,ci(c[key]),'Primary' if actor=='qwen7b' and key in ('shared_minus_private_Y','shared_minus_private_H','complete_pair_sensitivity_Y') else 'Descriptive' if actor=='claude' else 'Secondary'])
    comparison=table(['Actor','Model sharing gain ΔY','Scripted sharing gain ΔY','Private Y / greedy-private','Shared Y / greedy-shared'],
                     [[NAMES[a],fmt(S['cohorts'][a]['shared_minus_private_Y']['difference'],6),fmt(S['cohorts'][a]['baseline_sharing_gain_Y'],6),
                       fmt(S['cohorts'][a]['Y_fraction_of_baselines']['private']['greedy-private']['value'],3),
                       fmt(S['cohorts'][a]['Y_fraction_of_baselines']['shared']['greedy-shared']['value'],3)] for a in ACTORS])
    round_table=table(['Actor','Regime','Round','Y','H','Coverage','Null','Technical/missing','Seen-cell queries','New-cell queries','Repeated cells within round'],
                      [[NAMES[r['actor']],r['regime'],r['round'],fmt(r['Y']),fmt(r['H']),pct(r['coverage']),pct(r['null_rate']),pct(r['technical_missing_rate']),fmt(r['exploitation'],2),fmt(r['new_cell_queries'],2),fmt(r['within_round_repeated_cells'],2)] for r in rounds])
    stale_table=table(['Actor','Regime','True old peak queries r3 / r4 (total)','True-peak rounds / episode','True-peak last round − 2 (mean)','Best observed denominator','Best observed queries r3 / r4 (mean)','Best observed rounds / episode','Best observed last round − 2 (mean)'],
                      [[NAMES[r['actor']],r['regime'],f"{r['true_peak_r3_queries']} / {r['true_peak_r4_queries']}",
                        fmt(r['true_peak_mean_rounds_with_queries'],3),fmt(r['true_peak_mean_last_round_after_relocation'],3),r['best_observed_denominator'],
                        fmt(r['best_observed_mean_round_3_queries'],3)+' / '+fmt(r['best_observed_mean_round_4_queries'],3),
                        fmt(r['best_observed_mean_rounds_with_queries'],3),fmt(r['best_observed_mean_last_round_after_relocation'],3)] for r in stales])
    resource_table=table(['Actor','Regime','Effective calls','Input (uncached)','Cache read','Cache creation','Output','Unknown usage calls','Call seconds','Accounted USD'],
                        [[NAMES[r['actor']],r['regime'],r['calls'],*['UNKNOWN' if r[k] is None else r[k] for k in ('input_tokens','cache_read_tokens','cache_creation_tokens','output_tokens')],
                          r['unknown_usage_calls'],fmt(r['elapsed_seconds'],2),fmt(r['accounted_model_usd'],6)] for r in resources])
    active={name:sum(row['seconds'] for row in events if row['event']=='end') for name,events in S['accounting']['actual_active_time'].items()}
    assert not S['accounting']['unsettled_calls'] and S['accounting']['open_holds_micro_usd']==0
    assert abs(sum(r['accounted_model_usd'] for r in resources)-7.089251)<1e-10
    assert sum(r['calls'] for r in resources)==2020
    frontier=table(['Seed','Private Y / H','Shared Y / H','Central Y / H','Valid P / S / C'],
                   [[r['seed'],*[fmt(r[reg]['Y'])+' / '+fmt(r[reg]['H']) for reg in REGIMES],
                     ' / '.join('yes' if r[reg]['complete'] else 'no' for reg in REGIMES)] for r in S['cohorts']['claude']['all_seed_rows']])
    provenance=read(OUT/'provenance.json')
    prov_table=table(['Freeze','Saved push time (UTC)','Assigned starts','First start (UTC)','Commit'],
                    [[r['freeze'],r['pushed_at'],r['starts'],r['first_start'] or 'None',r['commit']] for r in provenance['layers']])
    identity=read(ROOT/'build/rebuild-final/byte-identity.json')
    hash_table=table(['Output','Bytes','SHA-256 (original = rebuild)'],
                     [[name,entry['bytes'],entry['first_sha256']] for name,entry in identity['files'].items()])
    nulls=sum(round(r['null_rate']*12) for r in ROWS)
    executed=sum(round(r['coverage']*12) for r in ROWS)
    technical=sum(round(r['technical_missing_rate']*12) for r in ROWS)
    assert nulls+executed+technical==11520
    results=f'''# Three Rules, One Lunch — results

12 November 2026 HKT. Builder: Codex. Delegating reviewer: Claude. Decisions follow the Claude/Codex agreement under [semi_autonomous.md](../../../semi_autonomous.md); independent scientific acceptance remains Claude's next review step.

**Hypothesis:** Giving workers one another's faithful observations helps them earn more reward than keeping each worker's observations private.

**Registered verdict:** The Qwen 7B joint criterion was **not met**, with incomplete technical evidence: all 200 primary worker episodes were attempted, but none completed, so both operational scores were zero. P1, P2, P4, P5 and P7 failed; P3 and descriptive P6 held. These are interface-limited operational results, not evidence that sharing has no value. All 960 episodes reached effective terminal dispositions; collection completeness is distinct from episode validity.

{pred_table}

## Headline comparisons

Y is total reward / 12,000 (equivalently mean reward per allowed query / 1,000); H is queries earning at least 500 / twelve. Post-relocation Y uses rounds 3–4 and denominator 6,000. Valid episodes have all scheduled replies accepted, with explicit nulls allowed. Every model score includes all scheduled opportunities, including zero operational penalties for failures; unobserved factual rewards remain null. Y/H are proportions, not raw reward units. To recover mean reward units, multiply Y or post-Y by 1,000.

{headline_table}

Local models use seeds 0–99 (100 episodes per regime); Claude uses seeds 0–19 (20 per regime). Ratios always use the same seed set. Claude is descriptive only. Exact unrounded values: [model-metrics.csv](model-metrics.csv).

{baseline_table}

These are **secondary frozen code controls**, with zero model calls and zero model-call dollars. Their 100% validity is guaranteed by code, not measured model format performance. Random draws and greedies have the same observation quotas/round boundaries as their declared regimes; the full-information oracle is an intentionally privileged ceiling. Random uses worker/shared visibility (its policy ignores observations). Greedy-central and all-null are also preserved in [baselines.csv](baselines.csv): their Y is 0.334887 / 0 on 100 seeds and 0.340408 / 0 on Claude's 20 seeds. The same 100-seed controls apply separately to all three local actors; these are shared worlds, not independent replications of the baselines.

![Mean reward and productive yield for every actor/regime; dashed ticks mark same-seed greedy-shared reward; right labels show valid episodes and model calls.](headline.svg)

The figure uses a common 0–1 axis and reports benefit alongside interface validity and model-call cost. Central has one call per round; worker regimes have three. Equal query opportunities do not mean equal tokens, time or dollars.

## What the comparisons support

Claude shared workers earned Y=0.465675 versus private Y=0.395963 and central Y=0.424771. The shared-minus-private difference was +0.069713, with a descriptive 95% paired interval [−0.000365, 0.137209]; H differed by +0.075000 [−0.045833, 0.191667]. The point-sign prediction P6 held, while these intervals include zero. No frontier superiority claim follows. All 20 private and 20 shared Claude episodes completed; central completed 17/20, retaining one harness-caused first-episode loss and two generated output-limit failures.

The local arms largely measured interface adherence. Qwen 7B completed every central episode but neither worker arm; Llama completed none of its 300 episodes. Qwen 1.5B completed 30 central and one shared episode. The executed requests used Ollama `format:"json"`, not an exact JSON Schema for constrained decoding, despite the programme's schema rule. Strict independent validation remained in place. This mismatch is a material protocol/programme limitation; the frozen inputs and results are preserved rather than repaired after observing outcomes. Examples from saved first responses: Qwen 7B worker seed 0 returned three cells for a one-cell quota; Llama central seed 0 included extra request fields. Those examples are **post hoc diagnostics**, not tested mechanisms or a causal explanation for every failure.

Qwen 7B central Y is only 59.2% of greedy-shared and below random's 0.301496. Its 100% valid-episode rate coexists with 66.2% executed-query coverage because intentional nulls are legal. Small-model ranking and central-versus-worker results cannot isolate search ability from validity, abstention, and the one-versus-three-call interface change. P3 holds literally, including a zero/zero Llama tie; it supplies no evidence of equal or better planning in that failed arm.

{comparison}

The simple script also obtains a sharing gain: +0.020583 Y on 100 seeds and +0.007671 on Claude's 20 seeds. Models show no local gain beyond that control under this interface. Claude's point gain is larger than the scripted gain and its shared Y is 143.7% of greedy-shared; that descriptive comparison has no registered difference-of-gains test and does not establish a reasoning mechanism. Greedies retain stale receipts without decay/reset, so this deliberately simple policy is not an optimal algorithm.

## Registered intervals and guardrails

All intervals below are the **unchanged frozen output**: 10,000 paired seed-block bootstrap draws, RNG seed 20261112, repeated-block multiplicity retained, percentile interpolation at (n−1)p. They cover the fixed synthetic generator and saved responses, not all future model sampling or tasks. Complete-pair intervals with n=0 are UNKNOWN, never zero.

{table(['Actor','Contrast','Difference [95% interval] (paired seeds)','Role'],contrasts)}

Primary guardrails require at least 95/100 valid episodes in each worker regime, at least 95 valid paired seeds, all 200 attempted, and positive lower bounds for ΔY, ΔH and complete-pair ΔY. Qwen has 0/100 valid shared, 0/100 private and 0 complete pairs, with ΔY=ΔH=0 [0,0]; guardrails fail and complete-pair sensitivity is UNKNOWN. Llama and Qwen 1.5B likewise have zero complete worker pairs. Claude has 20 complete worker pairs but remains descriptive; its negative lower interval bounds prohibit interpreting the point-sign prediction as a confirmed benefit.

## Full phase and opportunity tables

{table(['Actor','Regime','Pre Y','Post Y','Pre H','Post H','Executed coverage','Explicit null','Technical/missing'],phases)}

Across all actors there were 11,520 scheduled opportunities: {executed:,} executed, {nulls:,} explicit nulls and {technical:,} technical/missing. All 960 planned episodes were attempted. Failures terminate the whole episode; a valid response from another role in an uncommitted round creates no observation. Local missing usage affects one Qwen 1.5B central call; totals depending on that usage remain UNKNOWN.

Round-level quantities are means per episode; Y/H/coverage use three scheduled slots, while seen-cell/new-cell/repeat counts are query counts. A seen cell means visible in that role's prior receipts, not necessarily the best cell; within-round duplication is permitted by non-depleting rewards and is not automatically waste.

{round_table}

Exact values: [round-metrics.csv](round-metrics.csv). Mean totals retain failed episodes and their unexecuted rounds.

## Stale exploitation after relocation

True old peaks are all tied maxima of the phase-1 field, including unobserved cells; best observed peaks are maxima among that episode's executed rounds 1–2. These are registered descriptive summaries, not additional tests. True-peak means use every planned episode; best-observed means use only episodes with pre-relocation observations, whose denominator is explicit. Last round − 2 is 0 if never revisited, 1 for round 3 only, 2 if revisited in round 4; it is an index, not a measured continuous adaptation delay. A zero in an arm with no observations is not evidence of adaptation.

{stale_table}

In the common 100-seed set, 2 seeds have overlapping pre/post peak sets (4 overlapping cells); Claude's 20-seed set has no overlap. Exact overlap totals per regime are retained in [stale-exploitation.csv](stale-exploitation.csv); queries at an overlapping cell are not automatically harmful.

Claude's shared workers made 9 queries at true old peaks (6 in round 3, 3 in round 4), versus 4 private queries (3,1). Yet they revisited the best *observed* old cells less: 4 shared versus 16 private queries. These metrics describe different targets, and neither alone demonstrates that stale evidence caused a reward loss. Qwen central revisited observed old best cells in 1.13 post-relocation rounds per episode; Claude shared averaged 0.20. Cross-family differences are confounded by task performance and interface validity.

## Failures, deviations and operational events

{table(['Actor','Regime','Recorded terminal reason','Episodes'],[[NAMES[r['actor']],r['regime'],r['terminal_reason'],r['episodes']] for r in reasons])}

This table counts episodes once per terminal reason, not opportunities. The historical Claude first-call label “unexpected real tool/subagent activity” was a harness misclassification of all-zero subagent statistics, not evidence of actual tool use. D3c kept that episode scored with no rerun. The D4 usage-limit episode completed through append-only continuation and is not a current technical failure. Original STOP/FAIL files remain audit records; their existence alone does not mean an unresolved current stop.

{table(['Deviation','Timing and scope','Effect on this report'],[
 ['D1','Before first inference; saved server activity attestation, empirical CLI accounting/readiness','Larger of historical token cost and CLI reported cost; no claim of proven hidden-request coverage.'],
 ['D2','After starts, before analysis; local output length ends episode','Keep failed output, earlier observations and fixed-denominator penalties; no replacement.'],
 ['D3','After starts, before analysis; ledger-prefix verification and local incomplete-envelope disposition','One missing-usage local reply remains UNKNOWN for usage and incomplete for scoring; original bytes retained.'],
 ['D3b','After starts, before analysis; three-episode transport pause and two-turn schema envelope','Clearances retain failed terminals; CLI schema tool is not real external tool activity.'],
 ['D3c','After starts, before analysis; all-zero nested subagent statistics accepted','Claude seed 0 central retains Y=H=0; valid payload was not retroactively executed.'],
 ['D3d','Operational continuation of D3c','Separate bound clearance/attestation; no scientific change or replay generation.'],
 ['D4','After starts, before final analysis; exact zero-use/zero-cost 429 is a definite non-start','One refusal excluded from model behavior/failure counts; identical saved request resumed once, prior calls replayed only from bytes.'],
 ['D5','After starts, before final analysis; generated Claude failures end the episode','Seed 7 central max-token failure retained without rerun; seed 17 also fails at max_tokens. Both retain nine prior observations.'],
 ])}

See [DEVIATIONS.md](../../DEVIATIONS.md) and [ERRATA.md](../../ERRATA.md) for exact decisions and historical attribution corrections. D2–D5 were made after collection had begun and are not described as pre-inference registrations. No final outcome-dependent threshold, exclusion, prompt adjustment or replacement was introduced by this delivery. One definite non-start refusal at zero cost is reported separately from the 557 effective Claude model calls; 558 Claude dispatch attempts are preserved. The earlier first-call harness loss remains a penalty, so the central architecture comparison includes harness error.

## Spend, usage and limits

**Settled project model accounting: USD7.089251**, all frontier; local model-call accounting USD0. This is the conservative D1 accounting basis, not a verified cash invoice. Subscription cash billing is **UNKNOWN**. Open holds: USD0; unsettled paid calls: none; cost-stop flag: false. No model call occurred during this analysis/report/rebuild task. Paid failed calls and the no-score first Claude call remain charged. Build/subscription effort, hardware, energy and opportunity cost are not estimated here.

{resource_table}

Input here is uncached input; total input is uncached + cache read + cache creation. Output includes charged reasoning once. All categories for the one missing-usage local call remain null in machine-readable metrics; UNKNOWN is not zero. Effective model calls total 2,020 (1,463 local + 557 Claude), plus one zero-use operational non-start dispatch. Known paid usage reconciles with every ledger settlement. The original plan allowed up to 8,960 calls, but invalid episodes terminate early.

Persisted active local time: {fmt(active['time-local.jsonl'],3)} seconds ({fmt(active['time-local.jsonl']/3600,3)} h) of the 12-hour ceiling; frontier: {fmt(active['time-claude.jsonl'],3)} seconds ({fmt(active['time-claude.jsonl']/3600,3)} h) of 3 hours. These include collector/preflight overhead and waits within active sessions, excluding the wall-clock reset pause. Per-call elapsed totals above differ for that reason. The frontier envelope remains USD25 including USD1 protected reserve, the operational stop USD39, and the absolute project cap strictly below USD40. Remaining headroom does not authorize extra calls. Observed settlement is USD17.910749 below the USD25 envelope before reserve (USD16.910749 after reserving USD1).

## Reproducibility and preservation

The latest scientific lineage is original → D1 → D2 → D3 → D3b → D3c → D3d → D4 → D5. Latest RUN-d5 supplies dispositions and inherits RUN.md's final analysis command. Freeze verification passed before analysis. Active freeze SHA-256: `{identity['freeze_sha256']}`. Frozen root README/state files are preserved historical build records; the current delivery is in `build/delivery/` because the verifier inventories all other non-hidden files, including additions under a root `delivery/` folder. This existing excluded `build/` location avoids altering that inventory. Claude must explicitly include these delivery files and final analysis in the handoff package; they are not scientific freeze inputs.

Offline provenance checks passed for saved server-event bytes, receipt-to-freeze bindings and start order. These do not constitute a new network verification of the current remote ref or an independent fresh-clone reviewer check.

{prov_table}

The final primary execution was exactly once:

```sh
python3 -B trl_analysis.py --base collection --out build/analysis-first
```

Its stdout/stderr log is [analysis-first.log](analysis-first.log) (empty on success). Development/fake and earlier pending D4 analyses are historical, not replacement final runs. For the requested independent rebuild, a new source/evidence tree was copied under `build/rebuild-final/source`, each of its 10,056 files checked against [preflight.json](preflight.json), its freeze verified, and the frozen analysis run once there in a fresh Python process into `build/rebuild-final/analysis`. All five outputs are **byte-identical**. Original and copied input/evidence bytes remained unchanged before and after rebuilding. This is a source-isolated builder rebuild, not a claim that Claude's independent fresh-clone review is complete.

{hash_table}

Evidence: [byte-identity.json](../rebuild-final/byte-identity.json), [rebuild.log](rebuild.log), [provenance.json](provenance.json). To repeat the read-only rebuild, choose a new directory:

```sh
python3 -B build/delivery/rebuild.py --out build/rebuild-review-NEW
```

Full frozen outputs: [summary.json](../analysis-first/summary.json), [episodes.json](../analysis-first/episodes.json), [tables.csv](../analysis-first/tables.csv), [tables.md](../analysis-first/tables.md), [frontier-seeds.csv](../analysis-first/frontier-seeds.csv). New report formatting and the expansion of frozen code controls to H/post-Y are descriptive presentation work after analysis; registered predictions, contrasts and intervals come directly from the unchanged frozen summary. No scientific analysis source or prompt was changed. The latest sealed software suite had 238 passing tests (evidence/test-report-d5.json); this delivery checked reporting consistency, preservation and the actual final-data rebuild rather than rerunning collection.

## Frontier seed table (descriptive)

Every registered Claude seed is shown; none is excluded for failure. Three central episodes are invalid (seeds 0, 7, 17); all worker episodes are valid.

{frontier}

## Limits and post hoc labels

The intended receipt-sharing primary did not receive usable local worker trajectories. Null operational scores in invalid arms do not establish a null coordination effect; even a degenerate [0,0] bootstrap interval measures only those failed operational records. The programme's exact-schema requirement was not implemented for local constrained decoding, which materially limits scientific acceptance. The preserved evidence is complete in scheduled terminals, not complete in valid trajectories or all local usage.

The task uses 48-cell deterministic, smooth, non-depleting worlds, four rounds, twelve queries, announced relocation, no movement cost and no collisions. Repetition is rewarded. Stateless calls of one model receive role-specific histories; this is neither independently trained multi-agent cooperation nor a real search deployment. Models know relocation occurs but are not given its direction, seed, field formula or hidden peaks. Shared/private differ in receipt visibility; central additionally changes output quota and call count. Models are not matched for tokens, dollars or elapsed time. The same worlds are reused across local families, and Claude covers only twenty distinct worlds. Frontier has no generation seed support; actual effort is UNKNOWN if not returned. Hidden/internal provider request completeness and cash billing are not independently established by saved CLI accounting.

**Post hoc:** the diagnostic response examples, the narrative contrasts of true versus observed old peaks, the figure layout, and report-only code-control column expansion were chosen after seeing the frozen results. They add no confirmatory test or rescue. New questions are appended in [QUESTIONS-post-analysis.md](QUESTIONS-post-analysis.md). Any new schema-constrained study or stronger adaptive baseline requires a separate version, protocol/agreement/freeze and new authority; it cannot replace these v0.1 records. No publication, web change, new collection, or scientific acceptance is claimed by this delivery.
'''
    save_text(OUT/'RESULTS.md',results)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="570" viewBox="0 0 1120 570" role="img" aria-labelledby="title desc">',
         '<title id="title">Three Rules, One Lunch: reward, productive yield and validity</title>',
         '<desc id="desc">Twelve actor and regime rows on shared zero to one axes. Reward bars have same-seed greedy-shared ticks. Right-hand labels report valid episodes and effective model calls. Invalid local worker rows are zeros and cannot establish sharing effects.</desc>',
         '<rect width="1120" height="570" fill="#fcfcfa"/>',
         '<g font-family="Arial, sans-serif" fill="#182522">',
         '<text x="24" y="30" font-size="21" font-weight="bold">The local primary was limited by the interface</text>',
         '<text x="24" y="52" font-size="13">Claude shared workers have the highest model reward; their descriptive sharing interval includes zero.</text>',
         '<text x="280" y="82" font-size="14">Mean reward Y</text><text x="640" y="82" font-size="14">Productive yield H</text>',
         '<text x="950" y="82" font-size="14">Valid; model calls</text>']
    for index,a in enumerate(ACTORS):
        for j,reg in enumerate(REGIMES):
            m=S['cohorts'][a]['regimes'][reg];y=112+(index*3+j)*32
            color={'private':'#778d84','shared':'#126d5c','central':'#b9792d'}[reg]
            svg.append(f'<text x="24" y="{y+5}" font-size="13">{html.escape(NAMES[a])} · {reg}</text>')
            for x,w,key in ((280,290,'Y'),(640,240,'H')):
                svg.append(f'<rect x="{x}" y="{y-10}" width="{w}" height="17" fill="#e9ede9"/>')
                svg.append(f'<rect x="{x}" y="{y-10}" width="{w*m[key]:.3f}" height="17" fill="{color}"/>')
                svg.append(f'<text x="{x+w+7}" y="{y+4}" font-size="12">{m[key]:.3f}</text>')
            tick=280+290*S['cohorts'][a]['same_seed_baseline_mean_Y']['greedy-shared']
            svg.append(f'<line x1="{tick:.3f}" x2="{tick:.3f}" y1="{y-14}" y2="{y+11}" stroke="#192b25" stroke-width="2" stroke-dasharray="3 2"/>')
            svg.append(f'<text x="950" y="{y+4}" font-size="13">{m["complete_episodes"]}/{m["n"]}; {m["calls"]}</text>')
    for x,w in ((280,290),(640,240)):
        for t in (0,.5,1):
            svg.append(f'<text x="{x+w*t}" y="510" font-size="12">{t:g}</text>')
    svg.extend(['<text x="24" y="540" font-size="12">Dashed ticks: frozen greedy-shared Y on the same seeds (0.331 on 100 local seeds; 0.324 on 20 Claude seeds).</text>',
                '<text x="24" y="558" font-size="12">Equal query opportunities; unequal calls and compute. Oracle Y = H = 1. Data: headline.csv and baselines.csv.</text>',
                '</g></svg>'])
    save_text(OUT/'headline.svg','\n'.join(svg)+'\n')
    readme=f'''# Three Rules, One Lunch — empirical delivery

**Hypothesis:** Workers earn more when they can read one another's faithful observations.

**Result:** The registered Qwen 7B joint criterion was not met: neither worker arm completed a valid episode. The primary is interface-limited and cannot establish whether sharing improves search. Claude's shared workers earned more than private workers by 0.069713 Y over 20 seeds, with descriptive 95% interval [−0.000365, 0.137209]. P1/P2/P4/P5/P7 failed; P3/P6 held, with the limitations stated in [RESULTS.md](RESULTS.md).

{headline_table}

{baseline_table}

Y is mean reward per scheduled query / 1,000; H is the proportion earning ≥500, with abstention/failure as misses. Post-Y uses rounds 3–4. Local models use seeds 0–99 and Claude seeds 0–19. Code baselines are secondary, make no model calls and have guaranteed code validity; the oracle has privileged full information. All comparisons use the same seeds within each cohort.

![Reward, productive yield, valid episodes and calls](headline.svg)

Read [RESULTS.md](RESULTS.md) for all predictions, paired intervals, phase/round metrics, stale exploitation, failures, deviations D1–D5, usage, spend and all twenty frontier seed rows. Exact descriptive tables: [model-metrics.csv](model-metrics.csv), [baselines.csv](baselines.csv), [round-metrics.csv](round-metrics.csv), [stale-exploitation.csv](stale-exploitation.csv), [resources.csv](resources.csv), [terminal-reasons.csv](terminal-reasons.csv). Frozen final outputs live in [../analysis-first/](../analysis-first/).

All 960 episodes were attempted and have effective terminals (900 local + 60 Claude), with 188 valid episodes. Local requests used JSON mode rather than exact-schema constrained decoding; the resulting interface failures dominate local outcomes. Claude has 57/60 valid episodes, with one preserved harness loss and two generated max-token failures. One zero-use subscription-limit refusal is a separate operational non-start, resumed only through the approved identical-request disposition. No collection was rerun.

Settled model accounting is **USD7.089251**, with no open holds or unsettled calls; cash billing remains UNKNOWN. Local hardware/time is not priced. No model call, Git mutation, push or web publication occurred in this delivery task.

The frozen final analysis ran once at its inherited RUN.md output path. A separate source/evidence copy and fresh process reproduced all five output files **byte for byte**; [byte-identity.json](../rebuild-final/byte-identity.json) gives their hashes. All 10,056 preserved files were unchanged. This builder rebuild does not substitute for Claude's independent fresh-clone scientific review. [preflight.json](preflight.json) and [provenance.json](provenance.json) retain offline verification evidence.

To verify frozen inputs, from the project root:

```sh
python3 -B trl_freeze.py verify
```

To rebuild into a new directory without collection or network access:

```sh
python3 -B build/delivery/rebuild.py --out build/rebuild-review-NEW
```

This report is under `build/delivery/` because root README.md and state files are frozen, and the exact-input verifier rejects new files outside excluded directories. Preserve the frozen root documents; they describe historical build state, superseded operationally by RUN-d1 through RUN-d5 and the attribution errata. Claude should explicitly carry `build/delivery/` and `build/analysis-first/` into the review package; do not assume excluded build files are automatically published. Delivery decisions follow the Claude/Codex agreement under [semi_autonomous.md](../../../semi_autonomous.md). Next step: Claude's independent review, including the local-schema limitation and acceptance judgment. This delivery makes no acceptance or live-page claim.
'''
    assert sum(r['complete'] for r in ROWS)==188
    save_text(OUT/'README.md',readme)
    save(OUT/'report-facts.json',{'scheduled_episodes':960,'valid_episodes':188,'scheduled_opportunities':11520,
                               'executed_opportunities':executed,'null_opportunities':nulls,'technical_missing_opportunities':technical,
                               'effective_model_calls':2020,'local_model_calls':1463,'claude_model_calls':557,
                               'operational_usage_limit_refusals':1,'settled_micro_usd':7089251,
                               'actual_active_seconds':active,'predictions':S['predictions'],
                               'presentation_only':True,'frozen_analysis_modified':False})
    print('Created reports, figure and descriptive CSV/JSON tables; 960 episodes and all registered predictions reconciled.')


if __name__=='__main__':
    main()
