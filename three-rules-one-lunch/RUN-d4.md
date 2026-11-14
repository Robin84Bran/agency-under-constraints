# D4 usage-limit continuation

Requested by Claude, delegating reviewer, for this project only. Builder scope:
implementation, offline tests, saved-evidence clearance and freeze. No model
calls, pushes or Git operations. Scientific protocol, schedule, prompts, models,
budget caps, and handling of every other error remain frozen.

The historical claude-s014-private/r3-j1 reply is DEFINITE_NON_START under D4.
Its previous technical/transport-failure disposition is superseded by a separate
record. Original STOP, parsed result, terminal, request, start, raw envelope,
prior history and zero settlement are preserved. Resume sends its identical
request bytes after the reported 2026-11-11 21:30 Asia/Hong_Kong reset. Six earlier
calls are replayed from saved bytes, never dispatched again.

The following create-once clearance was executed by the builder. Do not repeat
it if deviations/d4/clearance.json exists:

```sh
python3 -B trl_freeze.py clear-d4 --reviewer Claude --reason 'Claude reviewer decision D4: exact saved 429 usage-limit refusal with zero tokens and zero cost is a definite non-start; preserve evidence, re-disposition the historical technical failure, resume only identical request bytes after reset.'
```

It validates the saved raw refusal, simulator replay, zero settlement, closed
holds, other fatal episodes, exact STOP inventory, and prior clearances. It saves
collection hashes and ledger prefix lengths/hashes. Prefix growth is allowed;
rewrites or torn ledger tails block. A new unrelated integrity STOP remains
blocking. The clearance itself is sealed by D4.

Offline validation (use new output paths for repeats):

```sh
python3 -B trl_test.py --out build/test-report-d4-NEW.json
python3 -B trl_offline.py rebuild --archive evidence/offline-dryrun.tar.gz --out build/rebuild-d4-NEW
python3 -B trl_freeze.py verify
```

The builder seals with `python3 -B trl_freeze.py freeze-d4`. Parent D3d SHA-256:
`b2c23ed1a03d50d125a6b3b06b8ca23dbb15ded10c76d89ee4fe1fd4947a1289`.
Existing D3c/D3d push receipts must continue to verify. The new D4 receipt must
precede every new start, including continuation attempts. A start's claimed hash
cannot assign it to a historical parent. Any changed committed file, missing
parent receipt, late start or remote-ref mismatch blocks attestation/dispatch.

Claude reviews and publishes the sealed D4 manifest through its existing review
and push process; the builder performs neither operation. After that push, save
its actual server activity event. Exact commands in Claude's session:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch
trl_clone=<SCRATCH>/orchestra/research-push
trl_scratch=<SCRATCH>/orchestra
trl_d4_commit=$(git -C "$trl_clone" rev-parse HEAD)
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > "$trl_scratch/trl-activity-d4-pages.json"
python3 -B trl_freeze.py select-event --events "$trl_scratch/trl-activity-d4-pages.json" --commit "$trl_d4_commit" --out "$trl_scratch/trl-d4-push.json"
python3 -B trl_freeze.py attest --freeze-file freeze-d4.json --clone-root "$trl_clone" --repo-path three-rules-one-lunch --event "$trl_scratch/trl-d4-push.json" --commit "$trl_d4_commit"
python3 -B trl_collect.py --cohort claude
```

`trl_d4_commit` must identify the reviewed D4 push, with clone HEAD and server
remote ref still equal to it. Never substitute a parent event or invent a time.
If activity lags, retain the saved response and repeat GET to a fresh filename.
Attestation writes create-once collection/push-d4.json and the raw event file.

Before reset, collection prints the durable pause and exits zero without service
access. After reset it resumes the refused position; there is no automatic
sleep/retry loop. Another exact refusal creates a separate zero-cost operational
pause and clean exit. Every other reply retains frozen validation/accounting and
terminal handling. An interrupted uncertain start is never resent. The active
time ledger closes on each pause, and budget holds are released only when all
allocated calls have known settlements.

Analysis counts refusals separately as operational events. A pending pause emits
UNKNOWN and RESULTS.md explaining the operational event; it does not publish a
model score from the old terminal. A completed continuation yields effective
model calls and twelve simulator opportunities, plus a separate refusal count
in summary/tables. Raw historical results remain inspectable as old evidence.

Final verification: 214 offline tests pass, with zero failures, errors or skips.
The archived 960-episode fake-study rebuild matches its original summary and
tables. All 7,956 pre-existing collection and parent-freeze files retain their
exact hashes. Current saved collection analysis reports one operational limit
refusal and UNKNOWN pending results in build/analysis-d4-current. No model calls,
pushes or Git operations were performed by the builder. The initial regression
log is retained under build/test-d4-initial.log; its historical fixture failures
were resolved by reconstructing exact frozen source bytes before the final run.
