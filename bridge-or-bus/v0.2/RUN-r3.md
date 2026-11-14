# Bridge or Bus? v0.2 · RUN-r3

R3 is the pre-Claude schema compatibility revision requested by Claude, the
delegating reviewer agent. No Claude call has been made here; no re-disposition
is needed. Keep all 1,200 r2 local episodes, local schemas, prompts, fixtures,
settings, original receipts, ledgers and parent freezes unchanged.

Offline checks, from v0.2/:

```sh
python3 -B bob.py test
python3 -B bob.py dry-run
python3 -B bob.py rebuild
python3 -B bob.py verify
```

The builder creates freeze-r3.json once with `python3 -B bob.py freeze-r3`, after
source-bound passing tests. It binds freeze.json, freeze-r1.json, freeze-r2.json,
the r2 preservation manifest, new Claude schemas, implementation and tests.
Never overwrite a freeze. R2 build outputs are retained in
evidence/r3/parent-build/. No model calls, Git commands or pushes form part of
this build.

Claude receives config/claude-action-schema.json and
config/claude-report-schema.json: single objects, all keys required, extras
forbidden, no top-level oneOf/anyOf/allOf. The action schema projects the seven
local branches onto their individual scalar domains. It is a superset only in
cross-field combinations; the unchanged strict validator enforces branch legality
and the existing describe permission for each arm. Report acceptance is identical.
The structural projection test proves local-schema-valid ⊆ Claude-schema-valid
for every value; 67,200 sampled action combinations verify inclusion, branch
legality and both arms independently. Live provider acceptance remains UNKNOWN.

R2 schemas and conservative reservation/size fixtures remain byte-identical.
Both shorter Claude schemas fit the unchanged r2 size allowance; holds remain
USD19.179520 plus USD2 reserve, below USD25. Programme USD39 stop / strictly under
USD40, local cumulative 12h cap, frontier 2h cap, timeouts and usage-limit policy
remain unchanged. R2 local time and financial accounting are retained in place.

Future reviewer handoff only: supply a genuine post-r3 repository activity-API
push object, the pushed 40-hex commit, and the separate research clone containing
all four freezes and exact current source bytes. These commands are prepared,
not executed by this builder:

```sh
python3 -B bob.py attest --freeze freeze-r3.json --event '<SAVED_ACTIVITY_OBJECT>' --commit '<40_HEX_PUSHED_COMMIT>' --clone-root '<RESEARCH_CLONE>' --repo-path bridge-or-bus/v0.2
python3 -B bob.py collect --freeze freeze-r3.json --models claude
python3 -B bob.py analyze
```

The new receipt and push event go to collection-r3/; the original r2 receipt
remains in collection-r2/. New Claude calls append to collection-r2/, sharing
its existing accounting and frozen serial schedule. The collector verifies all
preserved local bytes and the original ledger prefix before admission. Local
calls retain their r2 freeze/push binding; new Claude calls require r3. R3
rejects requests to collect local models. Analysis audits both bindings and
continues to exclude VOID-HARNESS r1. No local rerun, pooling or cohort selection.

The r1 VOID-HARNESS disposition is unchanged. Existing push, runtime identity,
capacity, output/usage, price and accounting gates remain. A definite zero-usage
429 is still a pause/non-start and resumes only its saved request, using the
identical Claude collect command above after the saved reset time. Preserve all
other uncertain-start, unresolved-hold, transport-pause and no-repair boundaries
from RUN-r2.md. No new model error classification or automatic HTTP-400 resend.

Read-only sibling audit: useful-core, one-door-many-hands, portable-self/v0.2,
and three-rules-one-lunch all pass object-root schemas through their active
Claude commands. None passes a top-level union. Property/item-level nullable
unions are distinct from root unions. Source hashes and paths are retained in
evidence/r3/sibling-schema-audit.json; historical archived paths were excluded.
