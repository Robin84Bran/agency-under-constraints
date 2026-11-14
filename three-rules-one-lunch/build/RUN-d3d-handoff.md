# Current D3d handoff after the shared clone advanced

This operational note supplements the immutable RUN-d3d.md. It is excluded from
the freeze manifest so live external state can be recorded without changing a
sealed artifact. D3d seal: `b2c23ed1a03d50d125a6b3b06b8ca23dbb15ded10c76d89ee4fe1fd4947a1289`.

192 tests passed, zero failures/errors/skips. The archived fake rebuild matches.
All 7,348 pre-existing collection/freeze files are unchanged. The exact D3c STOP
clearance is recorded in deviations/d3c/clearance.json; no episode is rerun.

During the full suite, the shared research-push clone advanced from D3c's
`a04f06347c1282a94324bd172f766d5ac40b0e39` to
`f8f9486612d16140eb4f3e36314a6c01737efb65` (one-door-many-hands package).
The actual D3c attestation attempt therefore stops at the HEAD check. Log:
`build/attest-d3c-attempt.log`. A separate read-only remote probe also could not
resolve github.com; current remote-ref status is UNKNOWN. Neither D3c nor D3d
real receipts exist. No model call, push or Git mutation was made by the builder.

Claude must run these commands from a network-enabled session. Use a fresh clone
to avoid changing the shared clone. Publish the unchanged D3c commit on a unique
branch to obtain a new event whose ref still points to that commit. The saved
old event at trl-d3c-push.json remains evidence of the old main push, but cannot
be used when its ref or the clone's HEAD has advanced. Never weaken either check.

```sh
cd <WORKSPACE>/06_intelligence/AI_research/research/three-rules-one-lunch
trl_project="$PWD"
trl_scratch=<SCRATCH>/orchestra
trl_tag=$(date -u +%Y%m%dT%H%M%SZ)
trl_clone="$trl_scratch/research-trl-d3d-$trl_tag"
trl_branch="trl-d3c-attestation-$trl_tag"
python3 -B trl_freeze.py verify
git clone https://github.com/Robin84Bran/research.git "$trl_clone"
git -C "$trl_clone" switch --detach a04f06347c1282a94324bd172f766d5ac40b0e39
git -C "$trl_clone" push origin "HEAD:refs/heads/$trl_branch"
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > "$trl_scratch/trl-d3c-reattest-pages-$trl_tag.json"
python3 -B - "$trl_scratch/trl-d3c-reattest-pages-$trl_tag.json" "refs/heads/$trl_branch" "$trl_scratch/trl-d3c-reattest-filtered-$trl_tag.json" <<'PY'
import json, pathlib, sys
pages = json.loads(pathlib.Path(sys.argv[1]).read_text())
events = [event for page in pages for event in page] if pages and isinstance(pages[0], list) else pages
matches = [event for event in events if event.get('ref') == sys.argv[2]]
with pathlib.Path(sys.argv[3]).open('x') as output:
    json.dump(matches, output)
PY
python3 -B trl_freeze.py select-event --events "$trl_scratch/trl-d3c-reattest-filtered-$trl_tag.json" --commit a04f06347c1282a94324bd172f766d5ac40b0e39 --out "$trl_scratch/trl-d3c-reattest-push-$trl_tag.json"
python3 -B trl_freeze.py attest --freeze-file freeze-d3c.json --clone-root "$trl_clone" --repo-path three-rules-one-lunch --event "$trl_scratch/trl-d3c-reattest-push-$trl_tag.json" --commit a04f06347c1282a94324bd172f766d5ac40b0e39
```

If GitHub activity lags, retain the response and fetch/filter again to fresh
filenames until the new branch's actual event is available. Do not select an
old main event or overwrite a recorded receipt. After the D3c receipt succeeds,
publish D3d on main from this isolated clone:

```sh
git -C "$trl_clone" switch main
python3 -B - "$trl_project" "$trl_clone/three-rules-one-lunch" <<'PY'
import json, pathlib, shutil, sys
source, target = map(pathlib.Path, sys.argv[1:])
manifest = json.loads((source/'freeze-d3d.json').read_text())
for name in sorted(set(manifest['files']) | {'freeze-d3d.json'}):
    destination = target/name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source/name, destination)
PY
git -C "$trl_clone" diff --stat -- three-rules-one-lunch
git -C "$trl_clone" add -- three-rules-one-lunch
git -C "$trl_clone" commit --only -m 'Seal D3d operational continuation and D3c clearance' -- three-rules-one-lunch
git -C "$trl_clone" push origin main
trl_d3d_commit=$(git -C "$trl_clone" rev-parse HEAD)
gh api --method GET --paginate --slurp repos/Robin84Bran/research/activity > "$trl_scratch/trl-d3d-pages-$trl_tag.json"
python3 -B trl_freeze.py select-event --events "$trl_scratch/trl-d3d-pages-$trl_tag.json" --commit "$trl_d3d_commit" --out "$trl_scratch/trl-d3d-push-$trl_tag.json"
python3 -B trl_freeze.py attest --freeze-file freeze-d3d.json --clone-root "$trl_clone" --repo-path three-rules-one-lunch --event "$trl_scratch/trl-d3d-push-$trl_tag.json" --commit "$trl_d3d_commit"
python3 -B trl_collect.py --cohort claude
```

Never force a push if main advances again. Preserve concurrent work and reconcile
the isolated clone before continuing. The collector requires both attestations,
the exact bound clearance, terminal local prerequisites and all remaining
budget/time/runtime/STOP gates. It skips every already attempted episode.
