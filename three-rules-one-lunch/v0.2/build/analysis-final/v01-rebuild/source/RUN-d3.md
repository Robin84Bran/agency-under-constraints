# D3 runbook — preserved ledger prefixes and local transport failure

D3 is a harness-only, pre-analysis amendment agreed by Claude (delegating reviewer)
and Codex (builder) under `../semi_autonomous.md`. Read the appended D3 section of
DEVIATIONS.md and PROJECT_STATE-d3.md. The builder performs no model generation,
network request, push or Git mutation. All three parent freezes, collection bytes,
terminal fatal flags and both existing STOP records are preserved.

Offline checks from this folder, always choosing fresh output paths:

```sh
python3 -B trl_freeze.py verify
python3 -B trl_d3.py scan --out build/scan-d3-NEW.json
python3 -B trl_test.py --out build/test-report-d3-NEW.json
python3 -B trl_offline.py rebuild --archive evidence/offline-dryrun.tar.gz --out build/rebuild-d3-NEW
```

Builder preparation uses these create-once commands. Their outputs are included;
never delete, rewrite or repeat them to get around a failed check:

```sh
python3 -B trl_freeze.py clear-d3
python3 -B trl_freeze.py freeze-d3
```

`qwen1b-s024-central` is SCORED_NO_RERUN: one attempted call, three technical
opportunities, nine missing, incomplete, operational Y=H=0; input/output tokens
remain null with usage UNKNOWN. The original error text and fatal flag remain.
The earlier D2 Llama clearance remains bound. Neither episode is dispatched again.
D3 accepts growth only after preserved byte prefixes of the allowlisted time/cost
ledgers; changed prefixes, truncation or torn tails fail closed. All other
preserved files require exact full-file hashes; historical episodes cannot gain
new files. Do not reset timers or cost holds.

Claude handles review and any separately covered push from the research clone.
The complete package includes freeze.json, freeze-d1.json, freeze-d2.json,
freeze-d3.json, all manifest inputs, both clearances and the envelope scan. Save
real server evidence for the actual D3 push, then run:

```sh
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > /ABS/NEW-D3-ACTIVITY-PAGES.json
python3 -B trl_freeze.py select-event --events /ABS/NEW-D3-ACTIVITY-PAGES.json --commit FULL_D3_PUSHED_COMMIT --out /ABS/NEW-D3-RAW-PUSH.json
python3 -B trl_freeze.py attest --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --clone-root /ABS/RESEARCH-CLONE --repo-path three-rules-one-lunch --event /ABS/NEW-D3-RAW-PUSH.json --commit FULL_D3_PUSHED_COMMIT
```

Attestation checks all committed inputs and four freeze blobs, HEAD, origin and
remote branch. It retains exact raw event bytes and writes only create-once
`collection/push-d3.json` and `collection/push-event-d3.raw.json`. D1 starts remain
checked against the original push; D2 starts remain checked against the D2 push;
new starts require D3 and its later server push. No start is relabeled, and a new
D3 start before D3 attestation blocks attestation.

After review, a genuine D3 push and attestation, resume in the fixed order:

```sh
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort local
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort claude
```

Terminal episodes are skipped. Thirteen local episodes remain unstarted; local
completion still gates Claude. Local incomplete/missing-usage envelopes terminate
only their episode, preserve completed earlier rounds and UNKNOWN token totals,
and never trigger a retry, repair or replacement. Paid Claude missing usage,
first-call contract failure and all budget/hold safeguards remain fatal. Wrong
model/digest/context, input/output overruns, unknown completed stop reason,
runtime drift, resource caps and other integrity failures remain fatal. A later
fatal stop writes `collection/STOP-d3.json` without changing either prior STOP.

After collection or a later stop, analyze saved first replies to a fresh path:

```sh
python3 -B trl_analysis.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --base collection --out build/analysis-d3-NEW
```

No model outcome analysis was used to choose D3. Aggregate usage must remain
UNKNOWN wherever a call lacks usage; this amendment does not establish study
acceptance. Independent reconstruction and Claude review remain required.

Operational gap: the request refers to a frozen consecutive-failure pause, but
this package contains no threshold or implementation for it. Claude must identify
and retain the actual source/supervisor or agree an explicit operational rule
before executing continuation commands. D3 does not certify an absent guard or
choose a threshold. The source/threshold question was sent during preparation.
