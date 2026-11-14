# Bridge or Bus? — D1 runbook

This runbook supersedes only operational instructions in frozen RUN.md.
Decisions belong to Claude (reviewer) and Codex (builder), under
[`semi_autonomous.md`](../semi_autonomous.md); Robin has not reviewed or
authorized this project. D1 preparation includes no model calls, pushes,
network requests or Git mutations. See DEVIATIONS.md and ERRATA.md.

Run from `<WORKSPACE>/06_intelligence/AI_research/research/bridge-or-bus`:

```sh
python3 -B bob.py test
python3 -B bob.py verify
python3 -B bob.py dry-run
python3 -B bob.py rebuild
```

`freeze-d1` is create-once and has already been run for this handoff. Never
overwrite either freeze, starts, calls, raw evidence, receipts or cost/time
ledgers. The active manifest binds the unchanged original freeze.

## Attest after Claude pushes D1

The repository is the existing private `Robin84Bran/research`. Claude must push
the full amendment package from a separate clone and save one matching raw push
record from `GET /repos/Robin84Bran/research/activity` (or a complete PushEvent
from `/events`). The record must include server id, push ref, exact `after`
commit and server `timestamp`. The original commit-lookup HTTP Date workflow
is superseded. No fabricated timestamp or author/committer date is accepted.

The placeholders below are an absolute saved-record path, the full 40-character
pushed commit, an absolute separate research-clone root, and this project's
relative path inside that repository (normally `bridge-or-bus`):

```sh
python3 -B bob.py attest --event '<RAW_PUSH_RECORD_JSON>' --commit '<PUSHED_COMMIT_40_HEX>' --clone-root '<RESEARCH_CLONE_ROOT>' --repo-path '<PROJECT_PATH_IN_REPO>'
```

This checks clone HEAD/origin, committed frozen bytes and current remote branch
with read-only Git commands. It writes create-once `collection/push-event.json`
and `collection/push.json` into this RobinOS2 folder, never into the clone.
Collection uses this same canonical project root and verifies the saved receipt
offline. No Git mutation of RobinOS2 is part of attestation or collection.

## Collection

The frozen Claude binary is exactly:
`<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude`.
Its checksum must still match evidence/claude-transport.json. No model switch,
extra pilot call, retry, repair query or replacement episode is permitted.

Before local collection, coordinate existing shared-model capacity with its
operator. Metadata readiness alone cannot establish idle capacity. Existing
local pins/context/runtime checks at 127.0.0.1:11435 remain enforced; do not pull
models or start/restart a server. The frozen serial order is Qwen 7B, Llama 8B,
Qwen 1.5B, then Claude. Use the same durable collection across resumes:

```sh
python3 -B bob.py collect --models local
python3 -B bob.py collect --models claude
```

The second command requires every prior local episode to be complete. D1 clears
the blanket Claude transport hold through empirical reservations and actual
settlement. The first frozen Claude call must demonstrate one object
`structured_output` in the strict outer JSON envelope. It counts and is saved
even on failure; failure stops dispatch durably. Rates, hard aggregate output
bounds and hidden overhead remain UNKNOWN. No current-rate proof or speculative
token-cap proof is required before that call.

Existing USD15.493120 prospective frontier holds plus protected USD2 fit USD25.
Rolling admission counts all settled spend and outstanding holds plus reserve,
enforces the USD25 frontier envelope and USD39 operational stop / USD40 cap.
Full actual reported cost settles without clipping. Unknown usage retains
holds and stops dispatch; any reservation overrun also stops. Active-time caps
remain 12h local / 2h frontier; call timeouts remain 180s / 420s. Three consecutive
transport failures pause. Ambiguous starts are never resent; inspect evidence
and return to the reviewer for a scoped amendment rather than resetting costs.

After collection, offline analysis remains `python3 -B bob.py analyze`.
The unchanged scientific auditor binds the original freeze in each start;
additional D1 start hashes and the push gate bind the active amendment.
No study result, acceptance or successful live transport is claimed by D1.
