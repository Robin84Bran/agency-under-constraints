# Three Rules, One Lunch — D1 runbook

Claude (delegating reviewer) / Codex (builder) agreed D1 under
[semi_autonomous.md](../semi_autonomous.md). Robin has not reviewed or authorized
this project. This runbook supersedes the frozen `RUN.md` transport HOLD and
attestation instructions; [ERRATA.md](ERRATA.md) corrects its attribution.
No model calls, push or Git mutations occur in the D1 build. Claude performs the
subsequent push/collection. Use the RobinOS2 project as the collection root,
with a separate research clone for Git checks. Never change the original freeze,
source archives, saved calls, ledgers, or stops.

The frozen Claude binary is:
`<WORKSPACE>/<external-tooling>/tooling/node_modules/.bin/claude`.
The adapter checks its original SHA-256 before dispatch. No replacement binary,
model fallback, alternate transport or output parser is supported.

Run these verification commands from this RobinOS2 project:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B trl_freeze.py verify
python3 -B trl_offline.py rebuild --out build/rebuild-d1-NEW
```

`freeze-d1.json` selects the current manifest and binds the exact original
`freeze.json`. Original protocol, schedule, prompts/config and analysis remain
unchanged. Frozen fake evidence must rebuild to byte-identical metrics/tables.
Use new output names and retain failures.

After Claude pushes the complete D1 package from the separate clone, obtain a
real server response from `GET /repos/Robin84Bran/research/activity`. The raw record
selected for attestation must be a `push` naming the exact pushed commit and ref,
with its server id and timestamp after D1 creation. The helper accepts paginated
arrays as well as a single page. Example from this project; replace capitalized
placeholders with absolute paths, a full commit hash, and new filenames:

```sh
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > /ABS/NEW-ACTIVITY-PAGES.json
python3 -B trl_freeze.py select-event --events /ABS/NEW-ACTIVITY-PAGES.json --commit FULL_PUSHED_COMMIT --out /ABS/NEW-RAW-PUSH-RECORD.json
```

A supplied raw activity record may go directly to `--event`. Complete PushEvents
are still accepted; do not substitute a Git timestamp or create a record by hand.
From this RobinOS2 project, exact attestation command:

```sh
python3 -B trl_freeze.py attest --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --clone-root /ABS/RESEARCH-CLONE --repo-path three-rules-one-lunch --event /ABS/RAW-PUSH-RECORD.json --commit FULL_PUSHED_COMMIT
```

`--repo-path` may be replaced with the actual project-relative path in the clone.
Git checks run under `--clone-root`; all evidence writes land under `--root`:
`collection/push.json` and `collection/push-event.raw.json`. HEAD, origin, remote
ref, original and active committed freezes, and every active committed input must
match. Attestation is create-once and forbidden after any start. A partial receipt
write fails closed; retain it for review rather than deleting evidence to retry.

Only after D1 verifies and this fresh push is attested, Claude runs local first,
then the fixed frontier cohort, from this same RobinOS2 project:

```sh
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort local
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort claude
```

Local collection remains 900 episodes / 8400 maximum calls at the pinned Ollama
endpoint `http://127.0.0.1:11435`; Claude remains sixty episodes / 560 maximum
calls. All local episodes must terminate before frontier dispatch. Do not install
services, pull models, change credentials or create daemons. Requested generation
settings, timeouts, prompts, ordering, models and medium effort are unchanged.

D1 permits empirical reservations despite UNKNOWN advance transport/rate bounds.
The first scheduled Claude call itself checks one JSON envelope containing one
object `structured_output` payload; no extra probe, retry, repair, prose fallback,
replacement or resend is permitted. That call counts even if it fails. Raw bytes,
usage/settlement, parsed result and `collection/claude-contract.json` survive the
failure, which writes durable STOP before a second dispatch. The same strict
validation applies to later calls.

Measured byte reservations plus historical 826 hidden tokens and 10% margin are
unchanged: USD18.083840 scheduled, plus USD1 protected reserve. Rolling admission
uses settled + open holds + proposed hold + reserve under USD25 and the USD39
stop; the cumulative absolute cap stays strictly below USD40. Settle reported
usage at the historical 4/20 accounting basis or the greater CLI-reported
`total_cost_usd`, rounded up. Current rates, unreported internal accounting and
cash billing remain UNKNOWN. Missing/invalid usage retains holds and stops.
Overruns are charged, saved and stop; the 1024 observed-output stop is retained.
Requested 1024 output and disabled-retry controls are not claimed to prove an
aggregate provider ceiling. Cumulative time caps remain twelve local / three
frontier hours. A partial episode, uncertain start, open hold, identity drift or
STOP blocks resume. Never delete evidence or reset a ledger to continue.

After collection or a resource/integrity stop:

```sh
python3 -B trl_analysis.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --base collection --out build/analysis-d1-NEW
```

The original provider-free analysis and scientific acceptance rules are unchanged.
Claude independently rebuilds from a fresh clone with preserved collection evidence
before acceptance. No scientific result or publication is produced by this build.
