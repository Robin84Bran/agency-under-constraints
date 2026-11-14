# The Receipt Gap · r2 + D1 runbook

This is an offline build and pre-inference freeze. **No model call, push or collection was made by Codex.** Claude owns the later push and collection. All effects are synthetic. `offline/` is conspicuously labelled fake evidence, never study results.

Python 3.9+ and Node (draw parity test only); standard library, no package install, import-time provider initialization or network dependency. Never regenerate a freeze, schedule, prompt or parser after seeing responses. `prepare`, `freeze` and `freeze-d1` create once and fail if output exists. Use a new reviewed version for changes. [D1](DEVIATIONS.md) is the Claude/Codex provenance-only agreement under `../semi_autonomous.md`, made before any model call. `freeze.json` remains the original r2 artifact; `freeze-d1.json` binds its SHA-256 and the amended inputs. `verify` and the collector select D1 automatically when present, enforce the parent binding and reject scientific-input changes.

Offline checks in the project directory:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B rg_freeze.py verify
node fixtures/draw-vectors.mjs > NEW-VECTORS.json
cmp NEW-VECTORS.json fixtures/draw-vectors.json
python3 -B rg_offline.py --output offline/recheck-UNIQUE
```

Choose a new recheck path; never overwrite evidence. `NEW-VECTORS.json` and extra recheck outputs are disposable new verification artifacts; do not add them to the registered inputs. The saved `offline/dry-run/` exercises all four adapter identities and all three toolkits: 12 fake episodes, 72 fake calls. Frozen statistical fixtures test abstention-as-miss, missing truth, inaction, ties and sampled-block multiplicity.

## Push and attest — Claude only

Work in a **separate research clone**; never commit or switch branches in RobinOS2. Copy the complete D1 package to repository `receipt-gap/`, preserving every frozen byte, including both `freeze.json` and `freeze-d1.json`. Exclude `.git`, `__pycache__`, local `collection/` outputs and any later local credential/config files. Include all manifest inputs, including toy evidence and fake dry-run records. Run tests and `verify` inside the copied directory before committing. The active freeze's SHA-256 is the identity, not a commit recorded inside itself. The earlier `059a0258b86359d2564fd1e09bf4a4867b23353b` push contains only the original package: Claude must push D1 again before attestation.

After Claude's new push to `Robin84Bran/research`, capture the exact 40-character commit from that clone and a matching full server record. Either `/events` PushEvent or `/activity` push record is accepted. For a private repository with no PushEvent, capture activity records and select the matching commit/ref into a new file (replace placeholders; `refs/heads/main` must be the actual pushed ref):

```sh
RG_PROJECT='<WORKSPACE>/06_intelligence/AI_research/research/receipt-gap'
RG_CLONE='<research-clone-root>'
RG_COMMIT='<new-pushed-commit>'
gh api --paginate repos/Robin84Bran/research/activity --jq '.[] | select(.activity_type == "push") | @json' > '<new-activity-response-jsonl>'
python3 -B -c 'import json,sys; from pathlib import Path; es=[json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()]; e=next(e for e in es if e.get("after")==sys.argv[3] and e.get("ref")==sys.argv[4]); f=Path(sys.argv[2]).open("x"); f.write(json.dumps(e)+"\n"); f.close()' '<new-activity-response-jsonl>' '<new-activity-file>' "$RG_COMMIT" refs/heads/main
python3 -B "$RG_PROJECT/rg_freeze.py" attest --root "$RG_PROJECT" --clone-root "$RG_CLONE" --repo-path receipt-gap --event '<new-activity-file>' --commit "$RG_COMMIT"
```

Keep the full API response as well as the selected full record. A PushEvent may instead be passed with `--event`, using its `repo.name`, `payload.head` (or `after`), `payload.ref`, `created_at` and id. An activity record must have `activity_type: push`, `after` equal to the supplied commit, a branch `ref`, timezone-aware past `timestamp` and id. If neither API supplies a matching record, HOLD collection; never invent a timestamp or use the commit date.

`attest` performs read-only Git checks in `--clone-root`: HEAD must match, origin must identify this GitHub repository, both committed freeze blobs must match the RobinOS2 files, and `git ls-remote` must match the exact ref and commit. It writes create-once `collection/push.json` and exact source bytes as `collection/push-event.json` **inside `--root` (this RobinOS2 folder), never inside the clone**. The retained record, timestamp, ref, id and hash are independently checked by the collector. Model calls require this receipt. For another repository layout, pass its repository-relative project directory through `--repo-path`. Codex did not execute the example Git/gh commands.

## Collect — local first, then Claude

Run from the attested **RobinOS2 project directory**, where D1's receipt was written. The exact collection commands are:

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/receipt-gap
python3 -B rg.py collect --cohort local
python3 -B rg.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

The local order is Qwen 7B, Llama 8B, Qwen 1.5B; each episode runs through its report serially. Use the existing endpoint `127.0.0.1:11435`; no pull/start/restart/reconfiguration. The collector verifies model digests, captures runtime version/template/show metadata before generation, requests 8192 context, then checks actual running model/digest/context and prompt_eval_count. A mismatch or truncation is a durable STOP. Capture preflight information as evidence, including changed runtime status; do not substitute a model. Current runtime readiness is UNKNOWN in this freeze.

Only after all 1,800 local episode records exist does the frontier gate open. It checks the installed binary against the source-inspected 2.1.312 hash. Subscription sign-in must already exist; never copy credentials. Safe/restricted mode, empty real tools/MCP, no Chrome/skills/session persistence, medium effort, JSON Schema, one main-loop turn, output max 512, zero structured-output/transport retries and no model fallback are fixed. There is no calibration call. **The first frozen scored call verifies the real object-valued `structured_output`, envelope, model identity, usage and token subhold.** An absent/string payload, wrong model/effort, missing usage or overrun saves raw stdout/stderr and stops all frontier dispatch. It never tries `result`. Missing returned effort is UNKNOWN; requested medium is preserved. Tiny 512-token reasoning budgets may fail schema generation; preserve that outcome rather than adjust settings.

60 frontier episodes × ≤11 calls. Exact total reserved: **USD15.805440**, plus **USD1 protected reserve = USD16.805440**, below USD25. Reservations use USD4 input / USD20 output per million as an explicit conservative API-equivalent accounting basis; actual cash billing is UNKNOWN. The hidden 826-token allowance is empirical, not a guaranteed tokenizer bound. Each whole episode is reserved under the lock before its first start, each actual call has a saved subhold and fsynced start, raw output is saved before parsing, and measured overruns are settled without clipping and trigger STOP. Unknown usage retains holds. No retries of started calls. This study has no previous model spend; any later amendment must carry forward all settled spend and uncertain holds before admission. Stop at USD39 operationally and remain below USD40 absolutely. No outcome-dependent seed extension.

Persistent cumulative timers: 12 hours local, 2 hours frontier. A call starts only if its timeout reservation fits. Interrupted timer segments are charged their whole 190/430-second reservation; known segments use monotonic elapsed time including between-call work. Metadata preflight has its own 40-second reservation. OS/disk stalls are not claimed to have a hard duration bound. Time/resource stops leave the mandatory cohort incomplete. Do not add workers.

## Recover and rebuild

Never remove `STOP.json`, starts, ledgers or evidence to resume. Terminal episodes are skipped; an interrupted started episode is never rerun. A durable STOP requires saved-evidence diagnosis and a reviewed amendment, not an operator override. Failed paid calls with known usage are settled; unknown calls retain their reservation. Unused holds release only after a known terminal episode without a global stop. Unstarted episodes remain UNKNOWN with an explicit default reason; a resource stop's reason is attached in the offline analysis. Keep all data when a cohort is incomplete.

After collection, in a fresh independent clone with saved data, run:

```sh
python3 -B rg_freeze.py verify
python3 -B -m unittest discover -s tests -v
python3 -B rg_analysis.py --data collection --output collection/analysis-r2.json
```

Analysis is network-free and imports no transport. It independently replays the receiver and compares effects, events, realized prompts, raw first replies, parsed values, token accounting and terminal records. It independently reconstructs ledger holds and settlements. Every planned episode is included; unavailable truth is null, with D*/S* benchmark penalties kept separate. All contrasts, ten-thousand seed-block bootstrap replicates, reporting J/R/F denominators, predictions, framing intervals, behavior and observed max prompt tokens are rebuilt. The analysis output uses create-once writes. Push collection artifacts later and let Claude verify a fresh-clone rebuild. No empirical acceptance is claimed by a successful offline dry run.

RESULTS must state: RQ1 is Qwen 7B specific; Llama is a fixed replication; frontier is descriptive; no real transfers/messages occurred; receiver atomicity is assumed; no delays/expiry/reset were tested; abstentions and missing replies are reporting misses. Scientific RQ1/RQ4 decisions and per-cell technical validity gates are separate. Report adverse, incomplete and UNKNOWN outcomes, all predictions, actual denominators, spend/holds and the conditional budget limitations.
