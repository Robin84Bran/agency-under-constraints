# A1 — pre-registration revision before push and inference

11 November 2026. This instruction came from **Claude, the delegating reviewer
agent**; Codex is the builder. The claimed write scope is this folder. No model
call, network request, push, Git operation, real attestation or live collection
was performed by this build. Claude reports that the original freeze has not
been pushed and no model was called. There is no live `collection/` evidence in
this project at revision time. This is pre-registration A1, not a post-exposure
clearance or a claim of approval by Robin.

Original `freeze.json` remains byte-identical, SHA-256
`716c5abdda450c463ca7e3a6e2df6863c7156d83bd82507e9cb6d72472811c2f`.
Create-once `freeze-a1.json` binds that exact parent and every active input.
Only the ten named original harness/test/runbook/state files in
`ps_freeze.A1_CHANGED` may differ; their exact originals are retained under
`revisions/a1/original/` and checked against the parent. All scientific and
historical inputs remain unchanged, including PROTOCOL, config/design's
historical wording, worlds, prompts, schemas, models, request settings, seeds,
schedule, reservations, scoring, statistical analysis and saved fake archives.
A1 supersedes the old first-frontier-call blanket-fatal wording in those
historical documents. RUN.md and PROJECT_STATE.md describe current execution.

## Failure scope and accounting

Every generated-content problem ends only its episode: wrong keys/types/enums,
boolean/out-of-range slots or controls, note length/ASCII violations, writing an
inaccessible keyed slot, malformed JSON, duplicate/nonfinite payload values,
missing/nonobject Claude structured_output, completed output-length stops, and
known completed schema-tool exhaustion. This study has write and act phases;
it has no independent report, done_reason argument or op/key tool API. Extra
fields such as key/report are rejected without inventing such phases. The
write phase's conditional slot rule is the local equivalent of the sibling's
conditionally illegal key. A failed return batch executes no controls. Earlier
valid writes/returns survive, remaining factual opportunities are UNKNOWN/null,
and unchanged Y/F denominators treat missing opportunities as operational misses.
There is no repair, retry, replacement episode, new report or increased allowance.

The first Claude call has the same scope as every later call. All identity,
effort, real-tool, context, outer-metadata, usage, reservation, cost and persistent
resource checks still apply immediately. The compatibility receipt now binds the
**first accepted structured payload**; earlier content-failed episodes neither
require that receipt nor prevent the next scheduled episode. Two accepted turns
still require tool_use and strict-valid structured_output; integer one is also
accepted with its existing stop reasons. Completed max_tokens/length failures
and verified schema-output exhaustion are rejected episodes, never accepted
payloads. Exhaustion accepts only the known subtype, bounded 1/2 turns, verified
identity/effort/tool/usage metadata and terminal exit code 0/1. Other execution
errors, turn counts and paid transport uncertainty stay fatal.

A lossless object-pairs parser isolates designated structured_output violations
without losing valid metadata. Duplicate keys and nonfinite values there are
model-content failures. Duplicate outer/usage/model metadata, multiple envelopes,
invalid outer JSON and byte/text disagreement remain integrity/accounting
failures for paid calls. No result fallback, substring extraction or coercion.
Known usage is settled before payload acceptance. Input tokens sum input_tokens,
cache_creation_input_tokens and cache_read_input_tokens once each; output is
aggregate, including reasoning once. Unknown paid categories retain holds and
stop dispatch. Overruns settle without clipping and stop dispatch even when
content is also invalid. Fully accounted failed episodes release only unused
future-call holds. Cash billing remains UNKNOWN.

## Local transport pause and append-only evidence

Local done != boolean true or missing/invalid eval_count is a typed transport
episode. Missing local input usage, unreadable/nonobject local envelopes, failed
requests and timeouts use the same classification; usage remains null/UNKNOWN.
Known identity/digest/context conflicts, input truncation, input sufficiency
failures, output beyond the frozen 192-token bound and unexpected completed stop
reasons remain immediately fatal. These checks precede incomplete/content
classification whenever the returned metadata allows them to be evaluated.

Three consecutive transport-failure episodes in a cohort cause a durable pause
using the existing append-only stop ledger and create-once STOP.json. The streak
is reconstructed from sealed episode terminals across invocations; skipped
historical terminals are not counted again. A completed or content-failed
episode breaks the streak. No fourth episode is dispatched. Startup also detects
a third sealed transport terminal left by a crash before STOP creation. Each
terminal retains its full failed evidence and transport classification.

A1 adds no clearance command and clears no STOP. A pause requires diagnosis and
a separately reviewed amendment; deleting STOP or editing the ledger is never
recovery. Existing journal readers verify byte-length/SHA-256 prefix anchors and
starts' retained ledger prefixes. Appending valid entries preserves earlier
anchors; rewrites, shortened prefixes, torn tails and unanchored growth fail.
There is no whole-file historical ledger digest used as a resume clearance.
Any later clearance must bind preserved prefix lengths/digests and separately
validate appended ledger semantics; A1 grants no generic clearance authority.

## Identity, push provenance and verification

Read-only lessons: ../receipt-gap/DEVIATIONS.md (D2/D3),
../three-rules-one-lunch/DEVIATIONS.md (D3/D3b), and
../bridge-or-bus/DEVIATIONS.md (D2). Pinned manifest/layer hashes already bind the
actual Qwen system text and templates and Llama's empty system; no identity or
request defaults changed. Offline tests cover all three real retained identities
and reject template/system conflicts.

Push evidence already uses **GET /repos/Robin84Bran/research/activity**. A1
attestation additionally checks both original and A1 committed freeze blobs,
every active file, clone HEAD/origin, matching current remote ref, genuine server
push id/ref/after/timestamp, and push after A1 creation. Exact activity bytes are
retained, with hashes, and the collector requires the A1 push before every start.
Old/original hashes cannot admit an A1 start. The attester's Git/API interactions
are mocked in tests; no genuine push evidence is fabricated here.

Verification reports and all development logs are in revisions/a1/. The suite
includes strict rejection and continuation for every content validator branch,
both phases/actors, first-paid failure, known-cost settlement, fatal precedence,
1/2-turn envelopes, cache usage, output stops, transport pauses and crash recovery,
prefix preservation, identities, parent/scope/inventory binding and mocked server
provenance. A socket/HTTP/subprocess-blocked replay checks the historical fake
analysis byte-for-byte. RUN.md retains the exact later attest/collect commands.

Implicit exceptions follow the same boundary: generation exceptions are saved as
transport outcomes (local episode / paid uncertainty fatal), strict inner JSON
errors are content failures, preflight and OS/storage errors are harness-fatal,
and cost conversion/settlement errors are accounting-fatal. World.step errors
after decoder acceptance are harness inconsistencies. Collector re-raises these
non-content faults after durable stopping; there is no broad model-payload
exception that silently aborts the remaining cohort.

## Exhaustive Stop/raise/fatal audit

Counts use source sites, not unique bug causes: **9 fixed / 126 already right**, covering 131 original explicit raises and four direct fatal controls. The two replay contract sites implement the same first-content-failure correction as the collector. New guards are additional protections, not retroactively counted as original sites.

The tables include every explicit raise in all `ps*.py` modules, including core validators, journal/readers, freeze/provenance validators, independent replay and offline output protection. Built-in parser/OS/subprocess exceptions are routed as described below. `revisions/a1/audit-paths.json` is the machine-readable inventory; regression checks compare it against the AST. Original locations refer to the preserved baseline.

### Original sites and disposition

| Site | Expression | Classification | Disposition / reason |
|---|---|---|---|
| `ps_analysis.py:37` | `Stop('response/event without durable start')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:40` | `Stop('call dispatched after terminal gap/failure')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:43` | `Stop('saved call identity mismatch')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:44` | `Stop('replay request/history mismatch')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:47` | `Stop('local request settings changed')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:48` | `Stop('frontier request settings changed')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:62` | `Stop('event with invalid/unavailable reply')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:63` | `Stop('event differs from strict reply replay')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:83` | `Stop('terminal summary differs from independent replay')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:179` | `Stop('start binds altered ledger prefix')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:187` | `Stop('terminal seal changed')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:190` | `Stop('episode evidence inventory changed')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:192` | `Stop('sealed episode evidence changed')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:193` | `Stop('sealed terminal missing')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:194` | `Stop('unknown sealed episode')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:196` | `Stop('paid starts differ from ledger allocations')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:198` | `Stop('settlement differs from retained usage')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:204` | `Stop('frontier first-call contract evidence mismatch')` | Fatal retained-evidence integrity; corrected scope | fixed: Contract binds earliest accepted frontier payload after any prior failed model episodes. |
| `ps_analysis.py:205` | `Stop('missing first-call contract evidence')` | Fatal retained-evidence integrity; corrected scope | fixed: An earlier model-content failure cannot require a contract marker; first accepted payload still must have one. |
| `ps_analysis.py:206` | `Stop('frontier contract exists without paid call')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:212` | `Stop('duplicate active-time start')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:215` | `Stop('invalid active-time settlement')` | Fatal retained-evidence integrity | already right: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_collect.py:16` | `Stop('episode directory already exists; never replay started/prepared work')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:24` | `Stop('renderer exceeds frozen prompt byte bound')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:44` | `fatal control: fatal=True;error='unknown paid usage; hold retained'` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:50` | `fatal control: fatal=True;error='measured reservation overrun'` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:51` | `fatal control: except Exception as exc: fatal=True;error='paid accounting: '+str(exc)` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:56` | `fatal control: fatal=fatal or isinstance(exc,Stop) or first_paid;error=error or str(exc)` | Episode model content / fatal integrity precedence | fixed: Removed first-paid promotion of EpisodeFailure to fatal; integrity/accounting still takes precedence. |
| `ps_collect.py:79` | `Stop('fake output must be isolated')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:82` | `Stop('durable stop; reviewed amendment required')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:92` | `Stop('unknown episode directory')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:97` | `Stop('unsealed terminal')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:99` | `Stop('unreconciled paid call')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:104` | `Stop('local cohort not fully accounted')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:106` | `Stop('explicit Claude binary required')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:112` | `Stop('unreconciled episode')` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:118` | `reraise` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:122` | `reraise` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:123` | `Stop(read(base / 'STOP.json')['reason'])` | Fatal harness/integrity | already right: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_core.py:36` | `ValueError('duplicate key: ' + k)` | Contextual strict parsing | already right: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:40` | `ValueError('nonfinite number: ' + v)` | Contextual strict parsing | already right: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:44` | `ValueError('nonfinite number')` | Contextual strict parsing | already right: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:47` | `ValueError('JSON text required')` | Contextual strict parsing | already right: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:53` | `ValueError('object required')` | Episode model content | already right: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:56` | `ValueError('invalid write keys/slot')` | Episode model content | already right: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:58` | `ValueError('invalid note')` | Episode model content | already right: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:60` | `ValueError('write to inaccessible slot')` | Episode model content | already right: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:63` | `ValueError('invalid action keys/length')` | Episode model content | already right: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:65` | `ValueError('invalid control')` | Episode model content | already right: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:67` | `ValueError('unknown phase')` | Fatal harness | already right: Frozen generator/phase/state guard; not generated action content. |
| `ps_core.py:77` | `ValueError('unknown world/seed')` | Fatal harness | already right: Frozen generator/phase/state guard; not generated action content. |
| `ps_core.py:83` | `ValueError('label collision; no resampling')` | Fatal harness | already right: Frozen generator/phase/state guard; not generated action content. |
| `ps_core.py:114` | `ValueError('episode ended')` | Fatal harness | already right: Frozen generator/phase/state guard; not generated action content. |
| `ps_freeze.py:30` | `Stop('frontier plan cannot fit')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:56` | `Stop('symlink freeze input')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:63` | `Stop('freeze exists; never overwrite')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:76` | `Stop('symlink freeze')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:78` | `Stop('freeze inventory changed')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:81` | `Stop('frozen file changed: ' + n)` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:83` | `Stop('reservation freeze mismatch')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:84` | `Stop('generator/schedule drift')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:92` | `Stop('invalid timestamp')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:93` | `Stop('timestamp requires timezone')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:98` | `Stop('invalid push record/commit')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:99` | `Stop('activity is not matching push')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:101` | `Stop('invalid push branch ref')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:103` | `Stop('server push timestamp is future')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:108` | `Stop('activity API response must be list')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:110` | `Stop('invalid activity API pages')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:117` | `Stop('attestation requires separate research clone')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:118` | `Stop('invalid repo path')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:122` | `Stop('clone origin/HEAD mismatch')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:128` | `Stop('commit has different frozen bytes: ' + n)` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:134` | `Stop('no matching genuine server activity push; no model dispatch')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:136` | `Stop('push precedes freeze')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:138` | `Stop('remote ref differs from pushed commit')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:150` | `Stop('push attestation mismatch')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:153` | `Stop('retained server evidence changed')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:155` | `Stop('push metadata mismatch')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:158` | `Stop('push must precede every saved start')` | Fatal provenance/integrity | already right: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_io.py:20` | `Stop('evidence symlink')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:43` | `Stop('collection directory symlink')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:47` | `Stop('collector already locked')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:55` | `Stop('journal symlink')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:59` | `Stop('unanchored journal tail or missing prefix; reconcile offline')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:62` | `Stop('partial journal event')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:64` | `Stop('journal chain mismatch')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:66` | `Stop('append-only prefix changed')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:72` | `Stop('journal concurrently changed')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:93` | `Stop('ledger durably stopped')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:95` | `Stop('invalid/duplicate episode seal')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:99` | `Stop('rolling resource gate')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:104` | `Stop('invalid subhold/start')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:108` | `Stop('invalid settlement')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:111` | `Stop('uncertain hold cannot release')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:113` | `Stop('unknown ledger event')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:125` | `Stop('invalid active-time ledger')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:131` | `Stop('active-time cap')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:139` | `Stop('measured cumulative active-time overrun')` | Fatal ledger/storage/resource | already right: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_offline.py:43` | `ValueError('offline output exists; preserve it and choose a new path')` | Fatal offline evidence preservation | already right: Refuse overwriting an existing synthetic output directory. |
| `ps_transport.py:34` | `Stop('identity inventory differs from pins')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:37` | `Stop('manifest hash mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:41` | `Stop('missing/extra identity layer')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:44` | `Stop('identity layer hash mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:45` | `Stop('template/system bytes mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:46` | `Stop('invented default system')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:60` | `Stop('live manifest mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:62` | `Stop('live template/system mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:75` | `Stop('CLI binary hash changed')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:78` | `Stop('CLI metadata changed')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:108` | `Stop('invalid reported cost')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:110` | `Stop('invalid reported cost')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:119` | `Stop('non-UTF8 transport bytes retained')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:120` | `Stop('transport text differs from raw bytes')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:122` | `(Stop if paid else EpisodeFailure)('transport failure or uncertain outcome')` | Local transport episode / paid fatal | already right: No retry/resend; local episodes count toward persistent three-failure pause; paid uncertainty remains immediately fatal. |
| `ps_transport.py:124` | `Stop('provider envelope is not strict JSON')` | Contextual payload content / metadata integrity | fixed: Local unreadable envelopes are transport episodes; invalid designated Claude payload JSON preserves strict metadata and settles known usage. |
| `ps_transport.py:125` | `Stop('provider envelope must be object')` | Local transport episode / paid fatal | fixed: Local nonobject envelopes are transport episodes; paid nonobject metadata remains fatal. |
| `ps_transport.py:128` | `Stop('frontier identity mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:129` | `Stop('frontier effort conflict')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:133` | `Stop('frontier success/turn envelope mismatch')` | Episode model content / fatal envelope metadata | fixed: Completed Claude length/schema-tool exhaustion is model content; other envelope/turn mismatches stay fatal. |
| `ps_transport.py:135` | `Stop('unexpected tool activity')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:137` | `Stop('unexpected model tool usage')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:138` | `Stop('missing frontier usage')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:139` | `Stop('frontier token reservation overrun')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:141` | `Stop('structured_output object required; no prose fallback')` | Episode model content | fixed: Missing/nonobject structured_output ends only the episode, including first paid call. |
| `ps_transport.py:143` | `Stop('local identity mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:144` | `EpisodeFailure('local transport incomplete: done/eval_count')` | Episode model content | already right: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:145` | `Stop('unknown local input usage')` | Local transport episode | fixed: Missing local input usage is UNKNOWN transport evidence; no zero substitution. |
| `ps_transport.py:146` | `Stop('input sufficiency cannot be established')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:147` | `Stop('input truncated')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:149` | `Stop('running model digest/context mismatch')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:150` | `EpisodeFailure('completed output-length stop')` | Episode model content | already right: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:151` | `Stop('unexpected local stop envelope')` | Fatal identity/transport/accounting | already right: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:153` | `EpisodeFailure('invalid inner JSON: ' + str(exc))` | Episode model content | already right: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:155` | `EpisodeFailure(str(exc))` | Episode model content / fatal harness phase | fixed: Content validator errors stay episode-local; unknown harness phase is now rejected before this wrapper. |

### Final sites and failure scope

| Site | Expression | Classification | Disposition / reason |
|---|---|---|---|
| `ps_analysis.py:37` | `Stop('response/event without durable start')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:40` | `Stop('call dispatched after terminal gap/failure')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:43` | `Stop('saved call identity mismatch')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:44` | `Stop('replay request/history mismatch')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:47` | `Stop('local request settings changed')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:48` | `Stop('frontier request settings changed')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:62` | `Stop('event with invalid/unavailable reply')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:63` | `Stop('event differs from strict reply replay')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:83` | `Stop('terminal summary differs from independent replay')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:179` | `Stop('start binds altered ledger prefix')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:187` | `Stop('terminal seal changed')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:190` | `Stop('episode evidence inventory changed')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:192` | `Stop('sealed episode evidence changed')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:193` | `Stop('sealed terminal missing')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:194` | `Stop('unknown sealed episode')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:196` | `Stop('paid starts differ from ledger allocations')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:198` | `Stop('settlement differs from retained usage')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:205` | `Stop('contract without accepted frontier payload')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:207` | `Stop('frontier first-call contract evidence mismatch')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:208` | `Stop('missing first-call contract evidence')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:209` | `Stop('frontier contract exists without paid call')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:215` | `Stop('duplicate active-time start')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_analysis.py:218` | `Stop('invalid active-time settlement')` | Fatal retained-evidence integrity | Current: Independent replay/accounting mismatch; never a model-content rejection route. |
| `ps_collect.py:16` | `Stop('episode directory already exists; never replay started/prepared work')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:24` | `Stop('renderer exceeds frozen prompt byte bound')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:44` | `fatal control: fatal=True;error='unknown paid usage; hold retained'` | Fatal accounting / typed integrity precedence | Current: Unknown paid usage, measured overrun or accounting failure is fatal; typed content/transport failures alone are not promoted. |
| `ps_collect.py:50` | `fatal control: fatal=True;error='measured reservation overrun'` | Fatal accounting / typed integrity precedence | Current: Unknown paid usage, measured overrun or accounting failure is fatal; typed content/transport failures alone are not promoted. |
| `ps_collect.py:51` | `fatal control: except Exception as exc: fatal=True;error='paid accounting: '+str(exc)` | Fatal accounting / typed integrity precedence | Current: Unknown paid usage, measured overrun or accounting failure is fatal; typed content/transport failures alone are not promoted. |
| `ps_collect.py:56` | `fatal control: fatal=fatal or isinstance(exc,Stop);transport_failure=isinstance(exc,TransportFailure);error=error or str(exc)` | Fatal accounting / typed integrity precedence | Current: Unknown paid usage, measured overrun or accounting failure is fatal; typed content/transport failures alone are not promoted. |
| `ps_collect.py:82` | `Stop('transport streak terminal seal changed')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:88` | `Stop('durable transport-failure pause; reviewed amendment required')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:93` | `Stop('fake output must be isolated')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:96` | `Stop('durable stop; reviewed amendment required')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:106` | `Stop('unknown episode directory')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:111` | `Stop('unsealed terminal')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:113` | `Stop('unreconciled paid call')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:119` | `Stop('local cohort not fully accounted')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:121` | `Stop('explicit Claude binary required')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:127` | `Stop('unreconciled episode')` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:133` | `reraise` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:137` | `reraise` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_collect.py:138` | `Stop(read(base / 'STOP.json')['reason'])` | Fatal harness/integrity | Current: Admission, state/history, resources, preflight, durable STOP or re-raised non-content harness exception. |
| `ps_core.py:36` | `ValueError('duplicate key: ' + k)` | Contextual strict parsing | Current: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:40` | `ValueError('nonfinite number: ' + v)` | Contextual strict parsing | Current: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:44` | `ValueError('nonfinite number')` | Contextual strict parsing | Current: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:47` | `ValueError('JSON text required')` | Contextual strict parsing | Current: Model response -> episode content; configuration/evidence or paid outer metadata -> fatal integrity/accounting. |
| `ps_core.py:53` | `ValueError('object required')` | Episode model content | Current: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:56` | `ValueError('invalid write keys/slot')` | Episode model content | Current: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:58` | `ValueError('invalid note')` | Episode model content | Current: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:60` | `ValueError('write to inaccessible slot')` | Episode model content | Current: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:63` | `ValueError('invalid action keys/length')` | Episode model content | Current: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:65` | `ValueError('invalid control')` | Episode model content | Current: Strict write/act validation; decoder contains failure to this episode. World.step failure after decoder acceptance would be harness-fatal. |
| `ps_core.py:67` | `ValueError('unknown phase')` | Fatal harness | Current: Frozen generator/phase/state guard; not generated action content. |
| `ps_core.py:77` | `ValueError('unknown world/seed')` | Fatal harness | Current: Frozen generator/phase/state guard; not generated action content. |
| `ps_core.py:83` | `ValueError('label collision; no resampling')` | Fatal harness | Current: Frozen generator/phase/state guard; not generated action content. |
| `ps_core.py:114` | `ValueError('episode ended')` | Fatal harness | Current: Frozen generator/phase/state guard; not generated action content. |
| `ps_freeze.py:24` | `Stop('A1 parent freeze changed')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:26` | `Stop('A1 original input missing')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:30` | `Stop('A1 original baseline changed: ' + name)` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:31` | `Stop('A1 scientific or historical input changed: ' + name)` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:34` | `Stop('undeclared A1 input: ' + name)` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:39` | `Stop('A1 freeze exists; never overwrite')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:40` | `Stop('A1 pre-registration requires no collection evidence')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:66` | `Stop('frontier plan cannot fit')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:92` | `Stop('symlink freeze input')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:99` | `Stop('freeze exists; never overwrite')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:113` | `Stop('symlink freeze')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:116` | `Stop('A1 parent binding mismatch')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:118` | `Stop('freeze inventory changed')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:121` | `Stop('frozen file changed: ' + n)` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:123` | `Stop('reservation freeze mismatch')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:124` | `Stop('generator/schedule drift')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:132` | `Stop('invalid timestamp')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:133` | `Stop('timestamp requires timezone')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:138` | `Stop('invalid push record/commit')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:139` | `Stop('activity is not matching push')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:141` | `Stop('invalid push branch ref')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:143` | `Stop('server push timestamp is future')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:148` | `Stop('activity API response must be list')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:150` | `Stop('invalid activity API pages')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:157` | `Stop('attestation requires separate research clone')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:158` | `Stop('invalid repo path')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:162` | `Stop('clone origin/HEAD mismatch')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:169` | `Stop('commit has different frozen bytes: ' + n)` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:175` | `Stop('no matching genuine server activity push; no model dispatch')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:177` | `Stop('push precedes freeze')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:179` | `Stop('remote ref differs from pushed commit')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:191` | `Stop('push attestation mismatch')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:194` | `Stop('retained server evidence changed')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:196` | `Stop('push metadata mismatch')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_freeze.py:199` | `Stop('push must precede every saved start')` | Fatal provenance/integrity | Current: Pinned input/parent/inventory, create-once, identity, timestamp, committed-byte or server-push gate. |
| `ps_io.py:23` | `Stop('evidence symlink')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:46` | `Stop('collection directory symlink')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:50` | `Stop('collector already locked')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:58` | `Stop('journal symlink')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:62` | `Stop('unanchored journal tail or missing prefix; reconcile offline')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:65` | `Stop('partial journal event')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:67` | `Stop('journal chain mismatch')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:69` | `Stop('append-only prefix changed')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:75` | `Stop('journal concurrently changed')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:96` | `Stop('ledger durably stopped')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:98` | `Stop('invalid/duplicate episode seal')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:102` | `Stop('rolling resource gate')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:107` | `Stop('invalid subhold/start')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:111` | `Stop('invalid settlement')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:114` | `Stop('uncertain hold cannot release')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:116` | `Stop('unknown ledger event')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:128` | `Stop('invalid active-time ledger')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:134` | `Stop('active-time cap')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_io.py:142` | `Stop('measured cumulative active-time overrun')` | Fatal ledger/storage/resource | Current: Evidence, append-only prefix, lock, seal, persistent accounting/time or admission integrity. |
| `ps_offline.py:43` | `ValueError('offline output exists; preserve it and choose a new path')` | Fatal offline evidence preservation | Current: Refuse overwriting an existing synthetic output directory. |
| `ps_transport.py:36` | `Stop('identity inventory differs from pins')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:39` | `Stop('manifest hash mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:43` | `Stop('missing/extra identity layer')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:46` | `Stop('identity layer hash mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:47` | `Stop('template/system bytes mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:48` | `Stop('invented default system')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:62` | `Stop('live manifest mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:64` | `Stop('live template/system mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:77` | `Stop('CLI binary hash changed')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:80` | `Stop('CLI metadata changed')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:110` | `Stop('invalid reported cost')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:112` | `Stop('invalid reported cost')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:125` | `ValueError('duplicate key: ' + key)` | Contextual envelope parsing | Current: Invalid designated structured_output is isolated as episode content; invalid provider metadata is fatal (local unreadable envelope -> transport episode). |
| `ps_transport.py:130` | `ValueError('nonfinite number')` | Contextual envelope parsing | Current: Invalid designated structured_output is isolated as episode content; invalid provider metadata is fatal (local unreadable envelope -> transport episode). |
| `ps_transport.py:132` | `ValueError('provider envelope must be object')` | Contextual envelope parsing | Current: Invalid designated structured_output is isolated as episode content; invalid provider metadata is fatal (local unreadable envelope -> transport episode). |
| `ps_transport.py:135` | `ValueError('duplicate envelope key: ' + key)` | Contextual envelope parsing | Current: Invalid designated structured_output is isolated as episode content; invalid provider metadata is fatal (local unreadable envelope -> transport episode). |
| `ps_transport.py:145` | `Stop('unknown harness phase')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:149` | `Stop('non-UTF8 transport bytes retained')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:150` | `Stop('transport text differs from raw bytes')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:153` | `(Stop if paid else TransportFailure)('transport failure or uncertain outcome')` | Local transport episode / paid fatal | Current: No retry/resend; local episodes count toward persistent three-failure pause; paid uncertainty remains immediately fatal. |
| `ps_transport.py:155` | `(Stop if paid else TransportFailure)('transport failure or uncertain outcome')` | Local transport episode / paid fatal | Current: No retry/resend; local episodes count toward persistent three-failure pause; paid uncertainty remains immediately fatal. |
| `ps_transport.py:158` | `(Stop if paid else TransportFailure)('provider envelope is not strict JSON object')` | Local transport episode / paid fatal | Current: No retry/resend; local episodes count toward persistent three-failure pause; paid uncertainty remains immediately fatal. |
| `ps_transport.py:161` | `Stop('frontier identity mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:162` | `Stop('frontier effort conflict')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:170` | `Stop('frontier success/turn envelope mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:172` | `Stop('unexpected tool activity')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:174` | `Stop('unexpected model tool usage')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:175` | `Stop('missing frontier usage')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:176` | `Stop('frontier token reservation overrun')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:177` | `EpisodeFailure('completed schema-output exhaustion')` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:178` | `EpisodeFailure('completed output-length stop')` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:179` | `EpisodeFailure('invalid structured_output JSON: ' + payload_error)` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:181` | `EpisodeFailure('structured_output object required; no prose fallback')` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:183` | `Stop('local identity mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:184` | `Stop('input sufficiency cannot be established')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:185` | `Stop('input truncated')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:187` | `Stop('running model digest/context mismatch')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:188` | `Stop('local output reservation overrun')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:190` | `TransportFailure('local transport incomplete: done/usage')` | Local transport episode | Current: No retry/resend; local episodes count toward persistent three-failure pause; paid uncertainty remains immediately fatal. |
| `ps_transport.py:191` | `EpisodeFailure('completed output-length stop')` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:192` | `Stop('unexpected local stop envelope')` | Fatal identity/transport/accounting | Current: Pinned identity, tool/effort/context/envelope/bytes, known resource bounds or accounting metadata. |
| `ps_transport.py:194` | `EpisodeFailure('invalid inner JSON: ' + str(exc))` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |
| `ps_transport.py:196` | `EpisodeFailure(str(exc))` | Episode model content | Current: Frozen technical/missing scoring, prior effects retained; no event for rejected reply; continue cohort. |


Final A1 verification: **109 Python tests pass**, zero failures/errors/skips;
9 Node tests pass; all 640 toy worlds / 3,200 policy outcomes and 12 independent
generator vectors verify. Historical fake analysis is byte-identical, SHA-256
`7244311ea1aa38d27bedf6d2b947015c0fed297cfe29d7510c95d8bafd2cd845`, with
sockets/HTTP/subprocesses blocked and no Git operations. `revisions/a1/test-report.json`
binds the tested source and logs. All 4,151 unamended original inputs are byte-identical;
the ten allowed changed originals have parent-verified archived baselines.
