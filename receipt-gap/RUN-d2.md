# Receipt Gap r2 + D1 + D2

D2 is a **pre-analysis harness amendment after response exposure**, agreed by
Claude/Codex under `../semi_autonomous.md`. Read D2 in `DEVIATIONS.md` for the
terminal-episode decision and exact exposure. D1 and this amendment retain every
original freeze and collection file. Builder Codex makes no model calls, pushes,
Git changes or real attestations. Claude owns those later actions.

D2 accepts integer `num_turns: 2` only with `stop_reason: "tool_use"`, an
object-valued `structured_output`, and the unchanged strict action/report
validator. All identity, effort, envelope, usage, reservation and transport gates
remain required. Integer `num_turns: 1` remains supported. There is no `result`
fallback and no extra turn, retry, prompt or output allowance.

The existing `claude-s00-notification-r50-check` episode is already terminal:
retain its action technical failure and reporting miss, without resending,
continuing, or applying the saved send. Attribute the failure to the harness.
The frozen scorer keeps its actual zero effects distinct from D*=1/S*=0/J=0.
The remaining 59 frontier episodes stay scheduled in their original order.
Carry forward USD0.016788 settled spend, USD0.240896 outstanding holds and
4.083595125 seconds of charged frontier time; never reset or release them here.

## Offline verification

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/receipt-gap
python3 -B -m unittest discover -s tests -v
python3 -B rg_freeze.py verify
```

`freeze-d2.json` is create-once and already produced by the builder. Do not
regenerate it. It binds `freeze.json`, `freeze-d1.json`, the D2 implementation,
and `evidence/d2-baseline.json`. That baseline records the stopped episode,
original receipts/STOP, ledger/timer prefixes, all 1,800 local terminal records,
and the aggregate checksum of the 44,890 pre-D2 collection files.

## Push, attest and collect — Claude only

Copy the complete D2 package into a separate claimed research clone, preserving
all three freezes and manifest inputs. Exclude collection outputs from the code
commit and preserve their canonical local originals. Verify and test the copied
package, then commit/push under the existing programme agreement. No Git commands
are to run against RobinOS2. Capture the new commit and full server PushEvent or
activity push record exactly as in RUN.md, using new output filenames.

```sh
RG_PROJECT='<WORKSPACE>/06_intelligence/AI_research/research/receipt-gap'
RG_CLONE='<separate-research-clone-root>'
RG_COMMIT='<new-D2-pushed-40-character-commit>'
python3 -B "$RG_PROJECT/rg_freeze.py" attest --root "$RG_PROJECT" --clone-root "$RG_CLONE" --repo-path receipt-gap --event '<new-full-D2-server-record.json>' --commit "$RG_COMMIT"
cd "$RG_PROJECT"
python3 -B rg.py collect --cohort claude --claude-bin <WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude
```

Attestation checks the clone HEAD/origin, all three committed freezes, and remote
ref, then creates `collection/push-d2.json` and exact-byte
`collection/push-event-d2.json`. It never replaces D1's receipt/event. D1 starts
must retain D1 provenance and precede D2's creation; new starts bind D2 and must
follow its new push. A pre-D2 receipt cannot open the D2 gate.

The collector acknowledges only the original STOP bound in the frozen baseline,
requires that terminal episode's files to remain unchanged, and preserves the
ledger/timer prefixes. It skips terminal episodes. New fatal errors create
`collection/STOP-d2.json`; this STOP always blocks further dispatch. Missing or
changed evidence, an unknown started episode, or provenance/accounting failures
remain fatal. There is no general STOP override and no new reservation for the
failed episode. The old hold is conservatively retained.

After collection, copy saved data for the independent fresh-clone rebuild:

```sh
python3 -B rg_freeze.py verify
python3 -B -m unittest discover -s tests -v
python3 -B rg_analysis.py --data collection --output collection/analysis-r2-d2.json
```

Choose an unused analysis output path. Replay recognizes each saved call's D1
or D2 provenance and applies the two-turn allowance only to D2 calls. Scientific
scoring, prompts, schemas, world, schedules and bootstrap rules are unchanged.
Report the retained harness failure, actual denominators and any incomplete or
UNKNOWN outcomes. No study-wide empirical analysis was run by the D2 builder.
