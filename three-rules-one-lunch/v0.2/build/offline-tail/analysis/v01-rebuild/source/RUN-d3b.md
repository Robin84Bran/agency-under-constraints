# D3b runbook

Claude (delegating reviewer) / Codex (builder) agreed this pre-analysis harness
amendment. D3b resolves the D3 pause question with a new three-episode rule and
accepts the Claude schema-tool two-turn envelope described in receipt-gap D2.
Read DEVIATIONS.md's appended D3b section and PROJECT_STATE-d3b.md. All parent
freeze, collection, STOP and clearance bytes are preserved. No model call, push,
Git mutation or real attestation is part of this build.

Offline checks, from this project, with fresh output paths:

```sh
python3 -B trl_freeze.py verify
python3 -B trl_test.py --out build/test-report-d3b-NEW.json
python3 -B trl_offline.py rebuild --archive evidence/offline-dryrun.tar.gz --out build/rebuild-d3b-NEW
```

The builder seals the tested amendment once with `python3 -B trl_freeze.py freeze-d3b`.
It already exists; never rewrite any freeze or historical STOP to pass a check.

Claude handles subsequent review and any separately covered push from the research
clone. Include all five freeze files and every D3b manifest input. D3 was never
pushed/run, so no intermediate D3 attestation is needed. D1/D2 historical receipts
remain required and bound. Save real server evidence for the full D3b package:

```sh
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > /ABS/NEW-D3B-ACTIVITY-PAGES.json
python3 -B trl_freeze.py select-event --events /ABS/NEW-D3B-ACTIVITY-PAGES.json --commit FULL_D3B_PUSHED_COMMIT --out /ABS/NEW-D3B-RAW-PUSH.json
python3 -B trl_freeze.py attest --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --clone-root /ABS/RESEARCH-CLONE --repo-path three-rules-one-lunch --event /ABS/NEW-D3B-RAW-PUSH.json --commit FULL_D3B_PUSHED_COMMIT
```

Attestation verifies all committed inputs and five freeze blobs, HEAD, origin and
remote ref, then saves exact source bytes and create-once `push-d3b.json` /
`push-event-d3b.raw.json` under collection. Every new start requires that D3b push.
No start can precede its attestation. After review, genuine push and attestation:

```sh
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort local
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort claude
```

Existing terminals are skipped. Local completion still gates frontier collection.
Three consecutive episode transport failures in a single cohort run write
`collection/STOP-d3b.json` and prevent every next dispatch, including after restart.
Completed/schema-invalid/output-length episodes reset the streak. Episodes count
once regardless of calls; historical skipped episodes do not count. A crash after
the third terminal recovers the pause on startup. Integrity/budget/paid-usage
failures remain immediate STOPs, with no pause-clearance exception.

Review the STOP and its three bound episodes, diagnose the transport, then record
the reviewer's actual decision and reason (replace the reason placeholder):

```sh
python3 -B trl_freeze.py clear-pause-d3b --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --stop-name STOP-d3b.json --reviewer Claude --reason 'ACTUAL_REVIEW_FINDING_AND_CLEARANCE_REASON'
```

The command accepts only a transport pause, retains exact STOP bytes, and creates
`collection/d3b-clearances/STOP-d3b.json`. It never performs diagnosis or clearance
automatically. Rerun the appropriate collect command after recorded clearance;
only definitely unattempted episodes can dispatch, with a new cohort run identity.
A later pause uses `STOP-d3b-002.json`, then `-003`, etc.; pass its exact basename
to `--stop-name`. Never remove a STOP or change terminal evidence to resume.
Paused/unattempted episodes remain missing in fixed denominators. Preserve prior
rounds, UNKNOWN usage, timers, charges and open holds; no retries or replacements.

After collection or a pause, the unchanged analysis can report saved evidence to
a fresh path; it includes every scheduled episode, including unattempted ones:

```sh
python3 -B trl_analysis.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --base collection --out build/analysis-d3b-NEW
```

Claude replies require a strict-valid object structured_output: one turn may end
with end_turn/tool_use; two must end with tool_use. All existing integrity and
first-call safeguards remain. Cache creation/read tokens count as input once;
analysis retains those categories separately. Missing categories stay UNKNOWN.
No scientific criterion changes or real outcome analysis are part of this build.
