"""Post hoc presentation of frozen outputs; no inference or new hypothesis tests.

All inferential estimates are read from the single final analysis. Descriptive
tables expand its existing rows. Frozen scientific files are never edited.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/report-final'
ACTORS = ('qwen7b', 'llama8b', 'qwen1b', 'claude')
REGIMES = ('private', 'shared', 'central')
LABEL = dict(zip(ACTORS, ('Qwen 2.5 7B', 'Llama 3.1 8B', 'Qwen 2.5 1.5B', 'Claude Opus 5.5')))


def read(p):
    return json.loads(p.read_text())


def write(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        f.write(text)


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def f(x, n=4):
    return 'UNKNOWN' if x is None else format(x, f'.{n}f')


def pct(x):
    return f'{100*x:.1f}%'


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows]) + '\n'


def csvfile(name, rows):
    with (OUT / name).open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def headline(s):
    rows = []
    for actor in ACTORS:
        c = s['cohorts'][actor]
        for regime in REGIMES:
            m = c['regimes'][regime]
            rows.append([LABEL[actor], regime, f(m['Y']), f(m['H']), f(m['post_Y']),
                         f"{m['complete_episodes']}/{m['n']} ({pct(m['complete_episodes']/m['n'])})",
                         f(c['Y_fraction_of_baselines'][regime]['greedy-shared']['value'], 3)])
    return table(['Actor', 'Regime', 'Mean Y', 'Productive H', 'Post-relocation Y', 'Valid episodes', 'Y / greedy-shared'], rows)


def intervals(s):
    rows = []
    for actor in ACTORS:
        c = s['cohorts'][actor]
        for key, label in [('shared_minus_private_Y', 'Shared − private Y'),
                           ('shared_minus_private_H', 'Shared − private H'),
                           ('complete_pair_sensitivity_Y', 'Complete-pair Y'),
                           ('central_minus_shared_Y', 'Central − shared Y'),
                           ('central_minus_shared_H', 'Central − shared H')]:
            m = c[key]
            role = 'Descriptive' if actor == 'claude' else 'Primary' if actor == 'qwen7b' and key in (
                'shared_minus_private_Y', 'shared_minus_private_H', 'complete_pair_sensitivity_Y') else 'Secondary'
            rows.append([LABEL[actor], label, f(m['difference'], 6),
                         f"[{f(m['ci95'][0],6)}, {f(m['ci95'][1],6)}]", m['n'], role])
    return table(['Actor', 'Contrast', 'Difference', '95% interval', 'Paired seeds', 'Role'], rows)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    final = ROOT / 'build/analysis-final'
    s = read(final / 'summary.json')
    old = read(ROOT / 'reuse/v01-summary.json')
    rows = read(final / 'episodes.json')
    identity = read(ROOT / 'build/rebuild-final/byte-identity.json')
    assert identity['status'] == 'PASS'
    assert read(ROOT / 'build/analysis-completion.json')['returncode'] == 0
    assert len(rows) == 960 and sum(r['complete'] for r in rows) == 957
    assert Counter(r['source_version'] for r in rows) == {'v0.2': 900, 'v0.1-reused': 60}
    assert all(r['kind'] == 'MODEL' and r['complete'] for r in rows if r['source_version'] == 'v0.2')
    assert all(s['cohorts']['claude'][k] == old['cohorts']['claude'][k] for k in old['cohorts']['claude'])
    expected = dict(zip(('P1','P2','P3','P4','P5','P6','P7'), ('failed','met','met','met','failed','met','failed')))
    assert {k:v['status'] for k,v in s['predictions'].items()} == expected

    # Verify preserved bytes directly, including the current original v0.1 tree.
    freeze = read(ROOT / 'freeze.json')
    for name, h in freeze['files'].items():
        assert digest(ROOT / name) == h, name
    manifest = read(ROOT / 'reuse/manifest.json')
    for name, h in manifest.items():
        assert digest(ROOT.parent / name) == h, name
    baseline = list(csv.DictReader((final / 'baselines.csv').open()))
    btable = table(['Same seeds', 'Code policy (secondary)', 'Y', 'H', 'Post-Y', 'Valid code episodes', 'Y / greedy-shared'],
                   [[b['seeds'], {'uniform':'random', 'oracle':'full-information oracle'}.get(b['policy'],b['policy']),
                     f(float(b['Y'])), f(float(b['H'])), f(float(b['post_Y'])), f"{b['n']}/{b['n']} (100%)",
                     f(float(b['Y'])/s['cohorts']['claude' if b['n']=='20' else 'qwen7b']['same_seed_baseline_mean_Y']['greedy-shared'],3)]
                    for b in baseline if b['policy'] in ('greedy-shared','greedy-private','uniform','oracle')])
    descriptions = {
        'P1': ('Sharing benefits Qwen 7B under the entire joint rule', 'Y lower bound >0; H lower bound −0.001667, so the joint rule fails.'),
        'P2': ('Llama sharing ΔY>0 and ΔH>0', 'ΔY=0.020562; ΔH=0.025000; secondary intervals are positive.'),
        'P3': ('Central Y≥shared Y in Qwen 7B and Llama', '+0.142503 and +0.150046 Y respectively; unequal calls/tokens.'),
        'P4': ('Shared post-Y>private post-Y in Qwen 7B and Llama', '+0.006597 and +0.031283 respectively; fixed directional check.'),
        'P5': ('Qwen 1.5B shared Y<Qwen 7B shared Y', '0.196021 > 0.053749; the small model earns more.'),
        'P6': ('Claude shared Y>private Y, descriptive', '+0.069713; interval crosses zero; already observed in v0.1.'),
        'P7': ('Every model/regime has ≥95% valid episodes', 'Locals 900/900; retained Claude central 17/20 (85%). Already known to fail.')}
    preds = table(['ID','Prediction','v0.1','v0.2 combined','Evaluation'],
                  [[k, descriptions[k][0], 'Held' if old['predictions'][k]['status']=='met' else 'Failed',
                    'Held' if expected[k]=='met' else 'Failed', descriptions[k][1]] for k in expected])
    models, rounds, stale, resources, reasons = [], [], [], [], []
    dollars = defaultdict(int)
    starts = {}
    for line in (final / 'v01-rebuild/source/collection/cost.jsonl').read_text().splitlines():
        event = json.loads(line)['data']
        if event['event'] == 'start':
            starts[event['id']] = event['episode'].split('.d4-', 1)[0]
        elif event['event'] == 'settle':
            dollars[starts[event['id']]] += event['actual']
    for actor in ACTORS:
        c = s['cohorts'][actor]
        for regime in REGIMES:
            m = c['regimes'][regime]
            group = [r for r in rows if r['episode']['actor']==actor and r['episode']['regime']==regime]
            models.append({'actor':actor,'regime':regime,'source_version':'v0.1-reused' if actor=='claude' else 'v0.2',
                           **{k:m[k] for k in ('n','Y','H','pre_Y','post_Y','pre_H','post_H','coverage','null_rate','technical_missing_rate','complete_episodes','attempted_episodes')},
                           'Y_fraction_greedy_shared':c['Y_fraction_of_baselines'][regime]['greedy-shared']['value'],
                           'Y_fraction_greedy_private':c['Y_fraction_of_baselines'][regime]['greedy-private']['value']})
            rounds.extend({'actor':actor,'regime':regime,**b} for b in m['by_round'])
            stale.append({'actor':actor,'regime':regime,'n':m['n'],
                          'old_peak_r3_total':sum(r['stale_true_old_peak']['round_3_queries'] for r in group),
                          'old_peak_r4_total':sum(r['stale_true_old_peak']['round_4_queries'] for r in group),
                          **{'old_peak_'+k:v for k,v in m['stale_true_old_peak'].items()},
                          'observed_denominator':m['stale_best_observed_denominator'],
                          **{'observed_'+k:v for k,v in m['stale_best_observed'].items()},
                          'peak_overlap_episodes':sum(r['old_current_peak_overlap_cells']>0 for r in group),
                          'peak_overlap_cells_total':sum(r['old_current_peak_overlap_cells'] for r in group)})
            resources.append({'actor':actor,'regime':regime,**{k:m[k] for k in ('calls','input_tokens','cache_read_tokens','cache_creation_tokens','output_tokens','unknown_usage_calls','elapsed_seconds')},
                              'accounted_usd':sum(dollars[r['episode']['id']] for r in group)/1e6})
            reasons.extend({'actor':actor,'regime':regime,'reason':k,'episodes':v}
                           for k,v in Counter(k for r in group for k in r['reasons']).items())
    for name, data in [('model-metrics.csv',models),('round-metrics.csv',rounds),('stale-exploitation.csv',stale),('resources.csv',resources),('terminal-reasons.csv',reasons)]:
        csvfile(name,data)
    assert sum(r['calls'] for r in resources) == 8957
    assert abs(sum(r['accounted_usd'] for r in resources)-7.089251)<1e-10
    phases = table(['Actor','Regime','Pre-Y','Post-Y','Pre-H','Post-H','Executed','Explicit null','Technical/missing'],
                   [[LABEL[r['actor']],r['regime'],*[f(r[k]) for k in ('pre_Y','post_Y','pre_H','post_H')],
                     *[pct(r[k]) for k in ('coverage','null_rate','technical_missing_rate')]] for r in models])
    roundtable = table(['Actor','Regime','Round','Y','H','Coverage','Null','Technical/missing','Seen-cell queries','New-cell queries','Within-round repeats'],
                       [[LABEL[r['actor']],r['regime'],r['round'],f(r['Y']),f(r['H']),*[pct(r[k]) for k in ('coverage','null_rate','technical_missing_rate')],
                         *[f(r[k],2) for k in ('exploitation','new_cell_queries','within_round_repeated_cells')]] for r in rounds])
    staletable = table(['Actor','Regime','True old peak r3/r4 (total)','Old-peak rounds/episode','Last round−2 (mean)','Observed-best denominator','Observed best r3/r4 (means)','Observed-best rounds/episode','Observed-best last−2','Peak-overlap episodes'],
                       [[LABEL[r['actor']],r['regime'],f"{r['old_peak_r3_total']}/{r['old_peak_r4_total']}",
                         f(r['old_peak_rounds_with_queries'],3), f(r['old_peak_last_round_after_relocation'],3),r['observed_denominator'],
                         f(r['observed_round_3_queries'],3)+'/'+f(r['observed_round_4_queries'],3),
                         f(r['observed_rounds_with_queries'],3),f(r['observed_last_round_after_relocation'],3),r['peak_overlap_episodes']] for r in stale])
    resourcetable = table(['Actor','Regime','Calls','Input','Cache read','Cache creation','Output','Unknown usage calls','Call seconds','Accounted USD'],
                         [[LABEL[r['actor']],r['regime'],*[r[k] for k in ('calls','input_tokens','cache_read_tokens','cache_creation_tokens','output_tokens','unknown_usage_calls')],
                           f(r['elapsed_seconds'],2), f(r['accounted_usd'],6)] for r in resources])
    comparison = table(['Actor','Model sharing ΔY','Script sharing ΔY','Private Y / greedy-private','Shared Y / greedy-shared'],
                       [[LABEL[a], f(s['cohorts'][a]['shared_minus_private_Y']['difference'],6),f(s['cohorts'][a]['baseline_sharing_gain_Y'],6),
                         f(s['cohorts'][a]['Y_fraction_of_baselines']['private']['greedy-private']['value'],3),
                         f(s['cohorts'][a]['Y_fraction_of_baselines']['shared']['greedy-shared']['value'],3)] for a in ACTORS])
    frontiertable = table(['Seed','Private Y/H','Shared Y/H','Central Y/H','Valid private/shared/central'],
                         [[r['seed'],*[f(r[reg]['Y'])+'/'+f(r[reg]['H']) for reg in REGIMES],
                           '/'.join('yes' if r[reg]['complete'] else 'no' for reg in REGIMES)] for r in s['cohorts']['claude']['all_seed_rows']])
    hashes = table(['Output','Bytes','SHA-256 (original = rebuild)'],
                   [[name,v['bytes'],v['sha256']] for name,v in identity['byte_identical_outputs'].items()])
    reasons_table = table(['Actor','Regime','Preserved terminal reason','Episodes'],
                          [[LABEL[r['actor']],r['regime'],r['reason'],r['episodes']] for r in reasons])
    opportunity_counts = {k:round(sum(r[k]*12 for r in rows)) for k in ('coverage','null_rate','technical_missing_rate')}
    write(OUT/'report-facts.json',json.dumps({'predictions':expected,'valid_episodes':957,'local_valid':900,
          'scheduled_episodes':960,'scheduled_opportunities':11520,'opportunity_counts':opportunity_counts,
          'local_calls':8400,'reused_claude_calls':557,'settled_usd':7.089251,'cash_billing_usd':None,
          'preserved_v01_files':len(manifest),'frozen_v02_files':len(freeze['files']),
          'reporting':'post hoc presentation only; all intervals read from unchanged frozen outputs'},indent=2)+'\n')

    intro = """**Hypothesis:** Giving workers one another's faithful observations helps them earn more reward than keeping each worker's observations private.

**Result:** The Qwen 7B primary joint criterion was **not met**: reward improved, but productive-query yield remained inconclusive. All 900 schema-constrained local episodes completed validly; many valid actions were intentional nulls. Shared Qwen 7B earned Y=0.053749, just **16.2% of greedy-shared** and below random. Llama and Qwen 1.5B had positive secondary sharing results. The retained Claude cohort remains descriptive.

These v0.2 predictions were re-registered **after seeing v0.1**, not blind predictions. P6 is carried forward from observed Claude data; P7 was already known to fail because Claude central remains 17/20 valid. No collection was repeated during this analysis task.
"""
    definitions = """Y is reward / 12,000: mean reward per allowed query divided by 1,000. H is the fraction of twelve opportunities earning ≥500; nulls and technical/missing slots count as misses. Post-Y uses six round-3/4 opportunities and denominator 6,000. Multiply Y by 1,000 for raw mean reward. Whole-episode validity requires all scheduled replies to pass the strict validator; intentional nulls are valid. Local seeds are 0–99, Claude seeds 0–19. Every ratio uses greedy-shared on that actor's exact seed set. Claude's 60 episodes are reused once, never pooled as new independent frontier evidence.
"""
    scientific = """Qwen 7B shared−private ΔY=**0.007074** [0.001811, 0.012940], while ΔH=**0.005833** [−0.001667, 0.013333]. Both regimes have 100/100 valid and attempted episodes, 100 complete pairs, and the complete-pair ΔY interval equals the primary interval. The productive-yield lower bound fails the strictly-positive requirement. This is **inconclusive joint evidence**, with a positive reward estimate; technical incompleteness no longer blocks the primary.

Llama ΔY=0.020562 [0.011116, 0.030490] and ΔH=0.025000 [0.010833, 0.040000]. Qwen 1.5B ΔY=0.019900 [0.006787, 0.033862] and ΔH=0.024167 [0.001667, 0.048333]. Their unchanged secondary joint calculations pass, but neither replaces the Qwen 7B primary. Claude ΔY=0.069713 [−0.000365, 0.137209] remains descriptive and crosses zero.

Valid formatting did not ensure useful action: Qwen 7B private/shared abstained on 83.9%/82.0% of slots; Llama on 77.8%/70.7%. Qwen 1.5B shared earns more than either larger local shared model. All local regimes, including central, earn less than same-seed random Y=0.301496. Central exceeds shared in each local model while using 400 rather than 1,200 calls per regime, but the comparison also changes quota, prompt history and token use; it does not isolate planning quality or equal compute.

The simple shared greedy also gains Y=0.020583 over private on 100 seeds: essentially the same point gain as Llama and Qwen 1.5B, and more than Qwen 7B. Local sharing benefit is therefore also obtained by a simple script; no extra benefit beyond that script or reasoning mechanism is established. The Claude point gain exceeds its 20-seed script gain of 0.007671, without a registered difference-of-gains test. Greedy keeps all old receipts and is deliberately simple, not an optimal adaptive algorithm.
"""
    reproduction = f"""The primary frozen CLI ran **once**, as RUN.md specifies, into `build/analysis-final`; [invocation](build/analysis-invocation.json), [completion](build/analysis-completion.json), and [log](build/analysis-final.log) are retained. Freeze verification, saved activity-API attestation, journal/evidence admission, time prefixes, raw-response replay and original v0.1 reconstruction all passed. No model, network or Git call occurred in this task.

The saved push was `2026-11-11T19:21:47Z`, commit `f9954e14b91d4ce86ea74cfd2d2806f8333f68ba`, activity event `49905222869`; attestation was `19:22:21.000814Z` and the collection session began `19:22:56.779583Z`. Offline verification checks preserved server evidence and its hashes, not a new live query to GitHub. v0.2 freeze SHA-256: `{digest(ROOT/'freeze.json')}`. Historical final D5 freeze SHA-256: `{manifest['freeze-d5.json']}`.

An independent source/evidence copy into `build/rebuild-final/source`, using a fresh Python process and the original gated CLI, reproduced **all seven v0.2 outputs byte for byte**. Both executions also extracted the immutable v0.1 archive and reproduced all five original outputs byte for byte. The direct preservation check additionally matched **{len(manifest):,} original v0.1 files** in the current root and all {len(freeze['files'])} frozen v0.2 inputs. [Full rebuild evidence](build/rebuild-final/byte-identity.json) records hashes of {identity['collection_files']:,} collection files, source hashes and output identity. This builder reproduction does not replace Claude's independent fresh-clone scientific review or establish acceptance.

{hashes}
The explicitly requested `README.md` and `RESULTS.md` are **post-freeze additions**. No frozen file or hash is edited. The original verifier compares the entire non-build inventory, so running it directly in this delivery-expanded folder rejects these two added documents. Do not weaken it or rewrite the freeze. The reproduction utility projects exactly the recorded frozen inventory into a new tree and runs the unchanged verifier and CLI there; report additions remain outside scientific inputs. The [delivery integrity manifest](build/report-final/delivery-integrity.json) distinguishes frozen bytes from additive documents. Frozen RUN.md and PROJECT_STATE.md remain historical build handoffs; current task state is [build/report-final/PROJECT_STATE.md](build/report-final/PROJECT_STATE.md).

From the study root, reproduce into a never-used output directory:

```sh
python3 -B v0.2/build/rebuild-frozen-results.py --out v0.2/build/rebuild-review-NEW
```

This is reproduction of saved evidence, never new collection. The utility preserves source bytes, copies collection, runs the frozen CLI in a fresh process, and checks seven-file identity. Carry `build/analysis-final/`, `build/report-final/`, `build/rebuild-final/byte-identity.json`, both post-analysis utility scripts, and the original v0.1 delivery explicitly into the reviewer package; do not assume excluded build artifacts are published automatically.
"""
    deviations = """v0.2 changes only local transport `format:"json"` to the exact quota JSON Schema object; prompts, seeds, order, world, strict validator, scoring, intervals and baselines remain frozen. There were no v0.2 local terminal failures or recorded definite non-starts. One **historical** zero-use usage-limit refusal is retained separately from 557 effective Claude calls (558 dispatch attempts). The combined frozen summary reports `definite_non_starts:0` alongside `usage_limit_refusals:1` because reused Claude rows retain the historical refusal field rather than v0.2's local non-start counter; neither means an extra v0.2 event.

The original v0.1 failed interface results remain beside v0.2. v0.1 used local JSON mode rather than exact-schema constrained decoding: Qwen 7B/Llama worker arms had zero valid episodes, Qwen 1.5B workers 0/100 private and 1/100 shared. Comparing versions is a **post hoc descriptive comparison**, not a randomized interface experiment or permission to discard v0.1.

| Historical disposition | Timing / retained consequence |
| --- | --- |
| D1 | Before first inference: push attestation and empirical CLI accounting; cost uses the larger of historical token rates and reported CLI cost, without a verified cash invoice. |
| D2 | After starts, before final analysis: local generated output-length failure ends only the episode, keeping prior observations and fixed denominators. |
| D3 | After starts: ledger-prefix and incomplete-envelope disposition; one original local usage record remains UNKNOWN. |
| D3b | After starts: three-transport-failure pause and two-turn schema envelope; schema tool is not actual external tool activity. |
| D3c | After starts: corrected all-zero nested subagent-statistics handling; Claude seed 0 central keeps its harness-caused loss, Y=H=0, with no regenerated reply or retroactive execution. |
| D3d | Bound operational continuation/attestation; no scientific change or generated replay. |
| D4 | Exact zero-use/zero-cost HTTP 429 is a non-start; one identical request continued later, preceding generated calls replayed only from bytes. |
| D5 | Generated Claude failures end episodes; seeds 7 and 17 central retain max-token failures and nine earlier observations each. |

Original sources: [DEVIATIONS.md](../DEVIATIONS.md), [ERRATA.md](../ERRATA.md), archived unchanged inside reuse/v01.tar.gz. D2–D5 were adopted after inference began and are not claimed as blind pre-inference registrations. The raw historical reason “unexpected real tool/subagent activity” is a known harness misclassification, not evidence of actual tool use. No threshold, failed episode or denominator was adjusted for this delivery.

The saved v0.2 offline suite passed 87/87, with fake-transport verification clearly separated from real results. The archived historical suite had **237/238** passing: its pre-collection D5 test expects zero new starts, whereas completed evidence has 276 legitimate D5 starts. This disclosed applicability failure is retained; the completed-data provenance check and both raw reconstructions pass. No test or archived byte was changed to obtain a pass. See frozen RUN.md and evidence/legacy-test-report.json.
"""
    spend = """**New v0.2 paid spend: USD0. Total historical project settled model accounting: USD7.089251**, reused once, not charged again. This is conservative saved CLI/token accounting; cash billing remains **UNKNOWN** (`null`). Open holds USD0, unsettled calls none, cost-stop false. Paid failed calls and the original Claude harness loss remain charged. Local hardware, energy, build/subscription effort and opportunity costs are unpriced.

""" + resourcetable + """
Input, cache read, cache creation and output are separate; charged output includes reasoning. Local uncached token totals are observed counters; Claude uncached counts alone are not full prompt size because cache use is substantial. No usage is missing in these v0.2 local or reused Claude rows. Original v0.1 local usage retains one unknown call and is not substituted into the v0.2 totals.

v0.2 collection used 8,400 local calls and **1,032.609 seconds (0.287 h)** of its 43,200-second ceiling. Reused historical v0.1 local active time was 569.595 seconds, frontier 2,864.674 seconds; these are reported separately, not new v0.2 consumption. Active sessions include collector overhead, so call-seconds differ. Historical frontier envelope USD25 includes a protected USD1 reserve; its operational stop is USD39 and absolute cap strictly below USD40. Historical available envelope after settlement/reserve is USD16.910749, but no additional call or version is scheduled. Stop after v0.2.
"""
    limitations = """The worlds are synthetic, deterministic, smooth and non-depleting: 48 cells, four rounds, twelve opportunities, announced relocation and no movement cost/collisions. Duplicate queries earn reward again. Workers are stateless calls of the same model, not independently trained agents. Shared/private manipulate receipt visibility; central also changes call count and output quota. Cross-model costs and compute are unequal. The three local families reuse the same worlds; Claude covers twenty worlds and is retained from an earlier collection, not contemporaneously recollected.

Intervals are the frozen 10,000-draw paired seed-block percentile bootstrap (RNG seed 20261112, multiplicity retained, linear percentile interpolation). They describe variation over this generator and saved first responses, not all model-sampling variance or real deployments. No pooled-family primary, equivalence claim, new inferential test or outcome-based extension is made. Llama/small-model successes cannot rescue the failed primary. Nulls have zero operational score while unobserved factual rewards remain null. Validity is an interface measure, not a success rate.

**Post hoc presentation:** version comparison, descriptive counts/ratios expanded from saved rows, narrative on abstention and stale-cell behavior, questions, report layout and selected headline contrasts. The baseline policies, baseline reward fractions and stale metrics themselves were registered; no new adaptive control was introduced. Mechanistic interpretations remain hypotheses. No acceptance, publication, website change or later study is claimed. Decisions follow Claude/Codex agreement under [semi_autonomous.md](../../semi_autonomous.md); Claude is the delegating reviewer.
"""
    result = '# Three Rules, One Lunch — v0.2 results with preserved v0.1\n\n12 November 2026 HKT. Codex, builder for Claude’s delegated review.\n\n' + intro + '\n' + preds + '\n' + headline(s) + '\n' + definitions + '\n' + btable + """
Code controls are secondary, use identical seed sets and scheduled observation quotas, and cost zero model calls. Their 100% validity is guaranteed by code, not measured model behavior. The oracle sees the whole current field and is a privileged ceiling. Random uses the frozen uniform policy. Greedies repeat the best visible receipt, without phase reset or decay. Additional greedy-central/all-null rows remain in [baselines.csv](build/analysis-final/baselines.csv).

![All model regimes and same-seed code controls on a common reward axis](build/analysis-final/headline.svg)

""" + scientific + '\n' + comparison + '\n## Frozen intervals and joint guardrails\n\n' + intervals(s) + """
The primary intersection rule requires strictly positive lower bounds for both all-slot ΔY and ΔH, ≥95 valid episodes per worker regime, ≥95 complete pairs, all 200 attempted, and a positive complete-pair ΔY lower bound. All technical gates pass in v0.2; only the Qwen 7B ΔH lower bound prevents joint success. Secondary local joint calculations use the same rule and pass; Claude remains descriptive.

## Phase, opportunities and round tables

""" + phases + f"""
All 960 scheduled episodes have effective terminals; 957 are valid (900/900 new locals + 57/60 reused Claude). Across 11,520 scheduled opportunities there are {opportunity_counts['coverage']:,} executed, {opportunity_counts['null_rate']:,} explicit null and {opportunity_counts['technical_missing_rate']:,} technical/missing slots. Every local technical/missing rate is zero. Seen-cell counts mean visible in that role's earlier receipts, not necessarily a good cell. Round Y/H/coverage rates use three scheduled slots; seen/new/repeat columns are mean query counts per episode.

""" + roundtable + '\n## Stale exploitation after relocation\n\n' + staletable + """
True old peaks include all tied global maxima of phase 1, including unobserved ones. Observed best means the best executed pre-relocation cell(s); its conditional denominator is shown and is UNKNOWN if no such observations exist. Counts concern rounds 3–4. Last−2 is 0 if absent, 1 if last used in round 3, 2 if round 4. CSV retains all per-round means and overlap-cell totals. Two of 100 local worlds have a peak shared by both phases, versus none in Claude's twenty; old-peak revisits are therefore not automatically harmful.

Qwen 7B workers make no true-old-peak queries after relocation, yet shared post-Y is only 0.011347 and private 0.004750. Avoiding old peaks alone does not show successful adaptation; the high null rate matters. Qwen 1.5B shared revisits its best observed old cells more than private (2.97 versus 2.03 queries/episode) while earning higher post-Y. Claude shared has 9 true-old-peak queries versus 4 private, but 4 observed-old-best queries versus 16 private. These are distinct descriptive targets, not identified causes of reward differences.

The frozen greedy-shared overall gain hides weaker post-relocation reward: 0.238880 versus greedy-private 0.316183 on 100 seeds, and 0.183300 versus 0.308650 on twenty seeds. This is consistent with a stale-memory weakness in that particular script; no new phase-aware policy was tested.

## Preserved v0.1 beside v0.2

""" + headline(old) + """
v0.1: 188/960 valid overall; 131/900 locals and 57/60 Claude. Qwen 7B and Llama shared/private had zero validity, so v0.1's primary was interface-limited and not informative about successful receipt use. Its exact original outputs remain in [reuse/](reuse/) (`v01-episodes.json`, `v01-summary.json`, `v01-tables.csv`, `v01-tables.md`, `v01-frontier-seeds.csv`); the earlier human write-up remains [../build/delivery/RESULTS.md](../build/delivery/RESULTS.md). v0.2 exports remain separately under [build/analysis-final/](build/analysis-final/). Claude's complete cohort summary is equal in both versions; it is never counted as 120 independent frontier episodes.

v0.1 frozen intervals (kept as operational outcomes, not repaired):

""" + intervals(old) + '\n## Deviations, failures and non-starts\n\n' + deviations + '\n' + reasons_table + '\n## Spend, usage and resource limits\n\n' + spend + '\n## Independent reconstruction and preservation\n\n' + reproduction + '\n## All twenty Claude seeds (descriptive)\n\n' + frontiertable + '\n## Limits and post hoc labels\n\n' + limitations
    readme = '# Three Rules, One Lunch — v0.2 and v0.1\n\n' + intro + '\n' + preds + '\n' + headline(s) + '\n' + definitions + '\n' + btable + """
These are secondary code controls on the same seeds; oracle uses privileged full information. All local arms remain below random reward. Local sharing gains are also obtained by a simple greedy script, so they establish no special reasoning mechanism.

![Model and same-seed code-control reward](build/analysis-final/headline.svg)

The primary reward interval is positive: ΔY=0.007074 [0.001811, 0.012940]. Co-primary productive yield is inconclusive: ΔH=0.005833 [−0.001667, 0.013333]. All 100 complete worker pairs pass the technical gate. Llama and Qwen 1.5B pass their secondary joint calculations; Claude's descriptive reward interval includes zero. All 960 scheduled rows remain: 900 v0.2 locals and 60 v0.1 Claude, with 957 valid whole episodes.

**v0.1 remains visible:** its local primary had no valid Qwen 7B worker episodes; shared Y was 0 versus v0.2's 0.053749. v0.1 Llama shared Y was 0 versus 0.087218; Qwen 1.5B 0.003455 versus 0.196021. Original Claude scores are identical. These version comparisons are post hoc and do not prove a causal interface effect. [RESULTS.md](RESULTS.md) contains the full v0.1 table and intervals beside v0.2, all phases/rounds, stale exploitation, twenty Claude seed rows, deviations, resources and limits.

**Rebuild:** the frozen primary analysis ran once. A fresh copied source/evidence tree and fresh Python process reproduced seven v0.2 outputs byte for byte; both also reproduced five original v0.1 outputs byte for byte. All 10,056 original v0.1 files and 54 frozen v0.2 inputs remain unchanged. [Byte-identity evidence](build/rebuild-final/byte-identity.json).

**Spend:** USD0 new paid calls; historical settled project accounting USD7.089251, no open holds or unsettled calls. Cash billing UNKNOWN. Local hardware/time unpriced. 8,400 local calls, 1,032.609 active seconds in v0.2. No collection, network call, Git operation or publication occurred during this analysis/report task.

**Reproduce after delivery:** these two documents are requested post-freeze additions. The exact-inventory verifier rejects additions in the expanded folder; frozen scientific files and verifier remain unchanged. Run it through a fresh projection of the recorded inventory:

```sh
python3 -B v0.2/build/rebuild-frozen-results.py --out v0.2/build/rebuild-review-NEW
```

Run from the study root and choose a never-used output path. This invokes only the unchanged frozen analysis, never model collection. [Delivery integrity](build/report-final/delivery-integrity.json) identifies the two additions; [current state](build/report-final/PROJECT_STATE.md) supersedes the frozen build-only state operationally. See [report CSVs](build/report-final/) for unrounded presentation values and [frozen outputs](build/analysis-final/) for inferential source values. Carry excluded build artifacts explicitly into the review package.

New questions: [QUESTIONS-post-analysis.md](../QUESTIONS-post-analysis.md). Delegating reviewer Claude still owns independent acceptance. Work stops after v0.2; no later study, web change, push or publication is included here. Decisions follow [semi_autonomous.md](../../semi_autonomous.md).
"""
    # Reports are added only after successful independent reconstruction.
    write(ROOT/'RESULTS.md',result)
    write(ROOT/'README.md',readme)
    write(OUT/'PROJECT_STATE.md',"""# v0.2 analysis/report state — 12 November 2026 HKT

Source: Claude, delegating reviewer, under the Claude/Codex agreement. Task:
offline frozen final analysis once; combined v0.1/v0.2 reports; independent
reproduction; post-analysis questions. No collection, network, Git or publication.

Complete: 900 new valid local episodes plus 60 unchanged original Claude rows;
primary joint criterion not met (productive-yield interval crosses zero), positive
reward interval. P2/P3/P4/P6 held; P1/P5/P7 failed. All seven v0.2 and five v0.1
outputs reproduce byte-identically in fresh copied source/evidence and process.
Historical settled accounting USD7.089251; new paid spend USD0; cash UNKNOWN.

README.md/RESULTS.md are explicit additive post-freeze reports. Frozen scientific
files remain unchanged. Exact-inventory verification must use the provided fresh
frozen-inventory projection; do not amend freeze or verifier for documentation.
Original 10,056 v0.1 files and 54 frozen v0.2 inputs verified unchanged. Original
frozen PROJECT_STATE/RUN remain historical handoff records. See RESULTS for the
237/238 historical test applicability disclosure and operational deviations.

Next: Claude independently reviews a fresh package and judges acceptance. Include
excluded build outputs/scripts in that package. No v0.3 or more model calls.
The delegating reviewer owns the existing shared path claim/release.
""")
    additions = sorted(set(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and not any(
        x in ('build','collection','__pycache__','.git','.agents','.codex','.aws') or x.startswith('.') for x in p.relative_to(ROOT).parts)) - set(freeze['files']) - {'freeze.json'})
    assert additions == ['README.md','RESULTS.md'], additions
    write(OUT/'delivery-integrity.json',json.dumps({'status':'PASS','frozen_files_unchanged':len(freeze['files']),
          'original_v01_files_unchanged':len(manifest),'freeze_sha256':digest(ROOT/'freeze.json'),
          'post_freeze_additions':{n:digest(ROOT/n) for n in additions},'original_verifier_on_expanded_delivery':'rejects additive documents; intentional inventory boundary, not edited',
          'verification_method':'frozen byte hashes; unchanged CLI verifies exact-inventory copy in independent rebuild',
          'scientific_outputs':identity['byte_identical_outputs']},indent=2,sort_keys=True)+'\n')
    print('Wrote v0.2/RESULTS.md, README.md and descriptive report tables; original scientific bytes preserved.')


if __name__ == '__main__':
    main()
