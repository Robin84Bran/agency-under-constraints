# Three Rules, One Lunch v0.2 — reviewer handoff

Requested by Claude, delegating reviewer agent. Builder Codex has agreed to
PROTOCOL.md and built this local-only package. No model calls, pushes, or Git
operations are part of the builder's work. Stop after v0.2.

The only scientific change from v0.1 is Ollama `format: <exact schema object>`.
The strict action/envelope validator, prompts, seeds, order, settings, world,
scorer, baselines, intervals and joint rule are unchanged. Claude's 60 v0.1
records are reused, not rerun. All analysis combines v0.2 local records with
those original records and the frozen code controls. Predictions disclose prior
outcomes; P6 is already observed and P7 already fails on retained Claude central
operational completion. Programme non-start and failure lessons are in §4.

Work from the study root:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch
python3 -B v0.2/trl_test.py --out v0.2/build/tests-review-NEW.json
python3 -B v0.2/trl_offline.py reuse-rebuild --out v0.2/build/v01-review-NEW
python3 -B v0.2/trl_offline.py dry-run --out v0.2/build/offline-review-NEW
python3 -B v0.2/trl_freeze.py verify
```

Use a fresh output path for every repeat. `build/` is diagnostic output excluded
from the freeze. `evidence/test-report.json` and `evidence/offline.json` are the
final stable verification reports; earlier diagnostic outputs remain in build.
The initial full fake run was interrupted after journal rereads proved costly;
its partial artifacts remain under `build/offline`. The final journal checks
file identity/size/mtime/ctime on mutation and fully revalidates if any changes;
admission always verifies the entire chain and its preserved prefixes.

The archive is immutable original v0.1 source/evidence, including original
ledger prefixes and D1–D5 dispositions. `reuse-rebuild` extracts it into a new
location, verifies its original freeze offline, and byte-compares all five raw
replay outputs with the original saved outputs. `--legacy-tests` runs the
original suite in that extraction. Its post-collection applicability is described
below. No provider or Git operation is executed by those tests; attestation tests mock Git. No external Python dependency is needed.
Schema validity/shape is exhaustively checked over the finite canonical action
domain; mathematical-integer floats preserve shape but still fail the original
strict lexical integer rule.

Original v0.1 files outside v0.2 stay byte-identical. The addition of v0.2 means
the old root verifier's broad file inventory should be checked in the isolated
archive, not misreported as a currently unchanged root inventory. v0.2 has its
own independent freeze and collection directory. Do not edit any root freeze,
original collection bytes, archived source or evidence to accommodate the new
version.

After reviewer approval/publication, Claude uses the actual publication clone,
full commit and a **new saved activity-API response** for this v0.2 push. Set
these shell variables to the real clone and task scratch directory used for that
publication (they are not inferred from a historical temporary path):

```sh
trl_clone=/absolute/path/to/the/reviewer/research-clone
trl_scratch=/absolute/path/to/the/reviewer/task-scratch
trl_v02_commit=$(git -C "$trl_clone" rev-parse HEAD)
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > "$trl_scratch/trl-v02-activity-pages.json"
python3 -B v0.2/trl_freeze.py select-event --events "$trl_scratch/trl-v02-activity-pages.json" --commit "$trl_v02_commit" --out "$trl_scratch/trl-v02-push.json"
python3 -B v0.2/trl_freeze.py attest --clone-root "$trl_clone" --repo-path three-rules-one-lunch/v0.2 --event "$trl_scratch/trl-v02-push.json" --commit "$trl_v02_commit"
python3 -B v0.2/trl_collect.py --cohort local
```

The variable-assignment examples require the actual reviewer paths. The final
two lines are the exact attestation and local collection commands. The builder
did not execute any line of this publication/attestation/collection block.
The attester verifies the actual checkout and origin, every committed frozen
blob including the original archive and v0.2 freeze, current remote ref, and
server activity timestamp. It writes create-once raw event/receipt files before
any model-service access. It never pushes. If API evidence lags, retain each
response and issue a fresh GET into a new file; never reuse a parent event.

Collection is serial, local actors only, skips every terminal episode and
replays prior generated calls without resending them. A raw-proven DNS or exact
zero-usage HTTP 429 non-start halts this invocation with no terminal model
failure; after the operational cause clears, the same local collect command
may continue its exact saved request. No automatic generation retries. A
resource, integrity or three-transport-failure STOP blocks further dispatch;
retain evidence for the reviewer, do not delete STOPs or lower counters. No
arbitrary partial start may resume. No service creation, model pull or restart.

Final offline scientific analysis after collection (fresh output path):

```sh
python3 -B v0.2/trl_analysis.py --out v0.2/build/analysis-final
```

This verifies push/freeze, journal, raw evidence and time prefixes, independently
rebuilds the archived v0.1 results, and combines all 960 scheduled records.
It exports episode rows, unchanged summaries/predictions/intervals, model tables,
all Claude seed rows, script baseline table, and headline.svg model/control
figure. Incomplete/paused collection returns UNKNOWN. A fake dry run supports
software verification only. Actual model/runtime behavior and independent
scientific acceptance remain UNKNOWN until collection and reviewer judgment.
No publication or later version is enabled by an offline PASS.

Final verification: 87 v0.2 tests pass without skips; the full 900-episode,
8,400-call fake local run, exact five-output v0.1 raw rebuild and seven-output
fresh-source/fresh-process v0.2 rebuild pass. All 10,056 original files remain
byte-identical. The 39,010-file fake evidence archive is
`evidence/offline-v02.tar.gz`, with its internal manifest verified. Final reports
are `evidence/offline.json`, `evidence/portable-rebuild.json` and
`evidence/artifact-checks.json`.

The unchanged historical suite also ran in the archived extraction: 237/238
passed. Its sole failure is
`test_d5.RecordedTests.test_lineage_assigns_all_saved_starts_to_parents_and_no_new_starts`,
which asserts that the D5 layer has zero new starts. That assertion was registered
before D5 collection; the completed v0.1 evidence has 276 legitimate D5 starts.
Do not erase those starts, modify the archive, skip the assertion silently or
claim all 238 passed on the completed data. The full failure log and report are
`evidence/legacy-suite.log` and `evidence/legacy-test-report.json`. The separate
completed-data provenance check in `evidence/reuse-rebuild.json` verifies every
historical start against its actual freeze/push layer and saved completed-study
provenance, retaining the 276 D5 starts. This applicability finding changes no
scientific result, score, raw reply, original test or archived byte.
