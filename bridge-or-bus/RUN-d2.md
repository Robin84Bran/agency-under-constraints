# Bridge or Bus? — D2 runbook

D2 is prepared for Claude (reviewer) by Codex (builder) under
[semi_autonomous.md](../semi_autonomous.md). It supersedes D1 only for pinned
local identity, the documented first-stop disposition and amendment provenance.
The full diagnosis and scope are in DEVIATIONS.md. No generation or push is
performed by the D2 build. No Git mutation is needed in this workspace.

Run from `<WORKSPACE>/06_intelligence/AI_research/research/bridge-or-bus`:

```sh
python3 -B bob.py test
python3 -B bob.py verify
```

D2 tests write `build/test-report-d2.json` and `build/toy-test-output-d2.txt`;
previous test reports remain intact. `freeze-d2` is create-once and is already
created for this handoff, binding exact freeze.json and freeze-d1.json. Do not
recreate, overwrite or remove any freeze/evidence/start/episode/cost/timer file.

The offline recovery command is:

```sh
python3 -B bob.py reconcile-d2
```

It is already applied for this handoff and may safely be checked again: it
appends nothing when complete. Its only mutation is the recorded resume/release
at the end of cost.jsonl. It retains the failed first episode and 0.0353545
seconds of local active time. It does not grant dispatch without a D2 push.

After reviewing D2, Claude pushes the **entire** package from the existing
separate research clone, including both parents, freeze-d2.json, all D2
source/evidence/disposition archives and the original collection evidence plus
append-only recovery. Save the raw matching GitHub activity push record.
Attest using these exact arguments, replacing only bracketed values:

```sh
python3 -B bob.py attest --event '<ABSOLUTE_RAW_D2_PUSH_RECORD_JSON>' --commit '<PUSHED_D2_COMMIT_40_HEX>' --clone-root '<ABSOLUTE_RESEARCH_CLONE_ROOT>' --repo-path 'bridge-or-bus'
```

The record must have server id, activity_type=push, ref=refs/heads/<branch>,
after equal to that full commit and a timezone-aware past server timestamp
following D2 freeze. A complete matching PushEvent is also accepted. No author,
committer or HTTP Date substitution. The read-only Git checks must find this
exact commit at clone HEAD/current remote ref and exact frozen bytes. New
create-once receipts are `collection/push-d2-event.json` and `push-d2.json`;
the existing D1 files remain intact. No D2 receipt has been invented or saved.

After coordinating shared local capacity, Claude runs:

```sh
python3 -B bob.py collect --models local
python3 -B bob.py collect --models claude
python3 -B bob.py analyze
```

The first retained episode, `qwen7b-38-required-registry`, is **never rerun**.
The next generation is for the second entry in unchanged config/order.json.
The local preflight must obtain matching live digest/template/system/version
and sufficient context before generation. Metadata does not prove capacity.
No model pull, server restart, settings change, extra pilot or replacement.
Keep the same collection and time/cost ledgers across resumes. New starts bind
D2; old starts retain D1. All serial order, 12h/2h timers, timeouts, seven-call
holds, empirical frontier admission/settlement, USD25/39/under-40 gates, unknown
usage stops, first-Claude-envelope check and three-failure pause remain as D1.
