# D2 runbook — output-length episode failure and preserved STOP

D2 is a pre-analysis harness amendment agreed by Claude (reviewer) and Codex
(builder) under `../semi_autonomous.md`. Read the D2 section in DEVIATIONS.md.
This build makes no model calls, pushes, network requests or Git changes.
Original protocol/runbooks and both parent freezes remain historical evidence.

From this project folder, offline verification:

```sh
python3 -B trl_freeze.py verify
python3 -B trl_offline.py rebuild --archive evidence/offline-dryrun.tar.gz --out build/rebuild-d2-NEW
python3 -B trl_test.py --out build/test-report-d2-NEW.json
```

The original archive is named `evidence/offline-dryrun.tar.gz`. Rebuild and test
output paths must be new. Frozen D2 build evidence is in `evidence/`.

Builder preparation has already run these create-once operations; do not repeat
or delete their output to try again:

```sh
python3 -B trl_freeze.py clear-d2
python3 -B trl_freeze.py freeze-d2
```

The clearance preserves all prior collection bytes and scores the stopped Llama
episode: one received reply, three technical slots, nine missing slots, Y=H=0,
validity incomplete. It is never rerun. `collection/STOP.json`, its old fatal
terminal flag, both old push files and every old start remain unchanged. A later
fatal failure writes `collection/STOP-d2.json`; that stop is not cleared by D2.

Claude reviews the package and handles any separately authorized push from the
research clone. Push the complete D2 package, including the clearance and both
parents. No original model evidence is generated again. Save real GitHub push
activity from that push; no synthetic timestamps or commit dates may substitute.
Example commands run by Claude after the actual push:

```sh
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > /ABS/NEW-D2-ACTIVITY-PAGES.json
python3 -B trl_freeze.py select-event --events /ABS/NEW-D2-ACTIVITY-PAGES.json --commit FULL_D2_PUSHED_COMMIT --out /ABS/NEW-D2-RAW-PUSH.json
python3 -B trl_freeze.py attest --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --clone-root /ABS/RESEARCH-CLONE --repo-path three-rules-one-lunch --event /ABS/NEW-D2-RAW-PUSH.json --commit FULL_D2_PUSHED_COMMIT
```

Attestation checks HEAD, origin, remote ref, all frozen committed inputs and all
three committed freezes. Writes land only in this project's collection folder:
`push-d2.json` and exact-byte `push-event-d2.raw.json`. Both are create-once.
The original D1 push remains required for preserved starts. Future starts require
the fresh D2 push and D2 hash. Partial new attestation writes fail closed.

Only after D2 verifies and this fresh push is attested, Claude resumes the fixed
schedule from this same canonical folder:

```sh
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort local
python3 -B trl_collect.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --cohort claude
```

The collector skips all terminal historical episodes, including the cleared
Llama failure. It proceeds with the next frozen episode. An output-length reply
terminates its episode with technical/missing penalties and no retry. Input
truncation, identity/digest/context mismatch, envelope errors and all existing
runtime/resource/usage checks remain fatal. Independent exact input token counts
remain UNKNOWN where unavailable; see the explicit limitation in DEVIATIONS.md.
D1 frontier safeguards remain unchanged. Timers and ledgers are cumulative;
never reset them. All local episodes must terminate before frontier collection.

After collection or a later stop, run the unchanged scientific analysis from
saved first replies, using a new output directory:

```sh
python3 -B trl_analysis.py --root <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch --base collection --out build/analysis-d2-NEW
```

No favorable-results stopping, replacement evidence, prompt change or scientific
threshold change is permitted. Independent fresh-clone reconstruction and Claude
review precede acceptance or publication.
