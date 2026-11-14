# D5 saved-envelope repair

Requested by Claude, delegating reviewer. Builder scope: saved bytes, harness
implementation, offline tests, create-once STOP clearance and a new freeze. No
model calls, pushes or Git operations. All earlier freezes and collection bytes
are retained; scientific inputs and budget limits remain frozen.

The latest reply is MODEL-CAUSED (generated max-token truncation), caused to stop
the cohort by a harness exit-code check. Its effective nonfatal terminal is
saved separately under deviations/d5/episode.json. It is scored without rerun.
Analysis uses this disposition; collection skips it and all generated terminals.
Exact zero-cost, zero-usage 429 refusals still pause until reset and resend only
the identical request. Unparseable uncertain starts, actual wrong identities,
real tools/subagents, unknown accounting and overruns retain their fatal guards.

Executed once by the builder (do not repeat if the clearance exists):

```sh
python3 -B trl_freeze.py clear-d5 --reviewer Claude --reason 'Claude programme rules: saved generated max-token reply is MODEL-CAUSED; correct harness fatal disposition, preserve all evidence and settlements, score without rerun, continue unattempted episodes only.'
```

Offline validation, with fresh output paths for repeats:

```sh
python3 -B trl_test.py --out build/test-report-d5-NEW.json
python3 -B trl_offline.py rebuild --archive evidence/offline-dryrun.tar.gz --out build/rebuild-d5-NEW
python3 -B trl_freeze.py verify
```

Seal once with `python3 -B trl_freeze.py freeze-d5`. D4 parent SHA-256:
`0edd0a6944e82fa2ac3b2669fdc41e88a8586f5019d75428028f49b48d0799d4`.
Clearance validates full original evidence and ledger prefixes. New or modified
STOPs block admission. Every historical push receipt remains required, including
D4 for its starts and continuation attempts. Starts are assigned by preserved
inventories, never by a start's claimed freeze hash. New starts require the D5
receipt and must follow attestation. Exact committed blobs and the current
remote ref must match the reviewed push. The builder performs no publication.

After Claude reviews and publishes the sealed D5 package, Claude's exact
attestation and resume commands (the full commit and event must be from that
real D5 push, never a parent or a fabricated time):

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch
trl_clone=<SCRATCH>/orchestra/research-push
trl_scratch=<SCRATCH>/orchestra
trl_d5_commit=$(git -C "$trl_clone" rev-parse HEAD)
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > "$trl_scratch/trl-activity-d5-pages.json"
python3 -B trl_freeze.py select-event --events "$trl_scratch/trl-activity-d5-pages.json" --commit "$trl_d5_commit" --out "$trl_scratch/trl-d5-push.json"
python3 -B trl_freeze.py attest --freeze-file freeze-d5.json --clone-root "$trl_clone" --repo-path three-rules-one-lunch --event "$trl_scratch/trl-d5-push.json" --commit "$trl_d5_commit"
python3 -B trl_collect.py --cohort claude
```

These publication/attestation/resume commands are instructions for Claude; they
were not executed by the builder. If server activity lags, retain each saved
response and repeat the GET to a fresh file. Never reuse a parent push event.

D5 also preserves D4's orphan-continuation admission guard by reusing D4
admission. An exact parseable zero-use/zero-cost limit refusal remains decisive
evidence of a non-start even if the wrapper exits abnormally after receiving it.
A present modelUsage object with the correct identity and exclusively zero
usage/cost counters is also accepted; positive model counters are never ignored.

Final verification: all 238 offline tests passed, with zero failures, errors or
skips, and unchanged tested input hashes. The 960-episode archived fake-study
rebuild exactly matches its original summary, episode rows and tables. All
8,624 pre-existing collection files remain exact (ledgers verify their recorded
prefixes and complete tails). Current code, fixtures and configurations are bound
by evidence/test-report-d5.json; rebuild evidence is evidence/rebuild-d5.json.
The final suite log is build/test-d5-final.log. Initial logs are retained under
build/test-d5-initial.log and build/test-d5-full.log. The intermediate full run
passed 237 assertions but its report was rejected because source inputs changed
while the last boundary fixes were added; only the final stable report is used.
No model calls, pushes or Git operations were performed by the builder.
