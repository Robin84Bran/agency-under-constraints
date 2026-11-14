# Bridge or Bus? — D3 / A1 runbook

Prepared by Codex for Claude, the delegating reviewer, 11 November 2026.
Harness-only work: no model calls, pushes, Git mutations or sibling writes.
The 1,200 local terminal episodes remain intact; the 80 Claude episodes have
not started. Do not rerun local collection or any started episode.

Run in `<WORKSPACE>/06_intelligence/AI_research/research/bridge-or-bus`:

```sh
python3 -B bob.py test
python3 -B bob.py verify
```

Tests use mocked providers/Git and the copied real saved sibling envelope.
`build/test-report-d3.json` binds source; earlier reports remain unchanged.
`freeze-d3.json` binds the original, D1 and D2 freezes and preserved collection
bytes. `freeze-a1.json` binds D3, the exhaustive raise audit and source-bound
passing tests. Both are already created for handoff, exclusively; do not replace.

Claude reviews and pushes the entire package from the existing separate research
clone, including all five freezes, exact source archives and preserved evidence.
To obtain server push evidence after that push, use this read-only command
in that clone (the explicit 40-hex commit is the pushed HEAD):

```sh
gh api --method GET 'repos/Robin84Bran/research/activity?activity_type=push&per_page=100' --jq '.[] | select(.after == "<PUSHED_D3_COMMIT_40_HEX>" and .ref == "refs/heads/main")' > /private/tmp/bridge-or-bus-d3-activity.json
```

The saved file must contain exactly one unmodified API record, with server id,
activity_type=push, full after commit, branch ref and timezone-aware timestamp.
If the pushed branch differs, substitute its exact ref. Empty/multiple records
are rejected. Commit/author dates and HTTP Date are not push-time evidence.
Attestation reads the clone and current remote ref; it never changes Git or pushes.
Run the following from the canonical project folder, replacing only placeholders:

```sh
python3 -B bob.py attest --event /private/tmp/bridge-or-bus-d3-activity.json --commit '<PUSHED_D3_COMMIT_40_HEX>' --clone-root '<ABSOLUTE_RESEARCH_CLONE_ROOT>' --repo-path bridge-or-bus
python3 -B bob.py collect --models claude
```

Attestation writes create-once `collection/push-d3-event.json` (raw bytes) and
`collection/push-d3.json`. The record must postdate both new freezes. All committed
manifest files and all five freeze blobs must match; HEAD/origin/remote ref must
match. Historical D1/D2 starts retain their original receipts and freezes.
An old receipt cannot admit a D3 call. Every new start follows D3 attestation.
No attestation or live compatibility claim is created by this builder.

Keep the same money/time ledgers, sample, order, prompts, schemas, settings,
model pins, six-action/seven-call limits, no retries/replacements, USD25 frontier
admission, USD2 protected reserve, USD39 stop/under-USD40 cap and 2h frontier timer.
Input usage includes ordinary + cache_creation + cache_read input once each;
output already includes reasoning. Actual aggregate dollars settle in full.
Missing paid usage retains holds and stops dispatch, as do identity, integrity,
budget, source, runtime, ambiguous paid transport or accounting failures.

A model-invalid action/report, illegal argument, invalid designated payload or
length stop ends only that episode with unchanged frozen scoring. No action,
repair, final-report query, resend or replacement follows a failed generation.
Ollama done != true or missing/invalid counts ends one episode as transport
failure; three consecutive transport failures create a durable pause. Startup
reconstructs the streak from terminal order, closing the crash-before-pause gap.
A saved pause has no automatic override. Diagnose it offline; any future clearance
must bind exact evidence and ledger prefixes, and needs a scoped amendment.

The real sibling reply has two envelope turns, tool_use, valid structured_output,
and all-zero subagent_stats. It passes metadata/accounting validation. Its
`send/job/key` payload belongs to the sibling schema and is correctly rejected
by this study's action validator. Regression fixtures substitute this study's
valid payload to verify successful collection and independent auditing of the
same real metadata. No sibling action is transplanted into the live study.

After collection, the existing analyze command remains available. Scientific
acceptance is separate from harness verification; no real-outcome analysis was
run during this amendment. Historical RUN-d1/RUN-d2 and archived RUN.md describe
prior operating contracts, superseded by D3 where stated.
