# Fresh GitHub clone reproduction

Source: Claude, delegating reviewer; offline reproducibility repair after package
commit `466cf8b0a3`. No frozen evidence, scientific source, freeze, historical
report, or existing reproduction script is changed.

From `three-rules-one-lunch`, choose a never-used output directory:

```sh
python3 -B v0.2/build/clone-reproduction/reproduce.py --out v0.2/build/rebuild-clone-NEW
```

The wrapper verifies all 10,056 original v0.1 inventory entries, 55 v0.2 frozen
source entries including the freeze, and 39,008 saved v0.2 collection entries.
Only the following exact paths may be absent. If present, their bytes must still
match the saved hash. No wildcard lock exclusion applies.

| Missing clone entry | Inventory recording it | Saved SHA-256 |
| --- | --- | --- |
| `collection/collector.lock` | `v0.2/reuse/manifest.json` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `v0.2/collection/collector.lock` | `v0.2/build/rebuild-final/byte-identity.json`, `collection_hashes` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

These are the only differences between the local and fresh-clone entries in
those saved inventories; both local files are empty. No `cost.lock` occurs in
these inventories. All 54 entries of `v0.2/freeze.json` match both folders.
The archived v0.1 tarball retains its original lock bytes and is unchanged.

The direct `v0.2/trl_analysis.py` command rejects both delivered folders because
`v0.2/README.md` and `v0.2/RESULTS.md` are post-freeze additions. Neither is a
missing frozen input. The existing `build/rebuild-frozen-results.py` projects the
exact frozen source inventory into a new tree, copies collection evidence, and
runs the unchanged CLI in a fresh interpreter. This new wrapper adds saved
inventory verification before and after that operation. The original freeze,
push-attestation, journal, raw replay, and v0.1 archive gates all remain active.

The output contains `published-inventory-verification.json` recording any absent
lock exceptions and `byte-identity.json` recording seven v0.2 output hashes and
five archived v0.1 matches. `--verify-only` checks inputs without running analysis.
No model calls, network calls, pushes, or Git commands are used.

Frozen v0.1 also classifies paid starts using `'claude-' in p.as_posix()` on
absolute paths. Running under a parent named `claude-501` falsely treats local
starts as paid and raises `paid start without reserved subhold`. The wrapper
executes the frozen projection in a new `/private/tmp/trl-clone-*` directory,
then moves its complete outputs to `--out`. Scientific files remain unchanged;
failed logs and partial outputs are retained as well. The command itself runs
from the fresh-clone copy. Python 3.9 is sufficient; no dependency install is
required. The first failed attempt remains in the requested copy at
`v0.2/build/rebuild-clone-codex/rebuild.log`.

For publication, include this directory's `reproduce.py` and `README.md` (and its
verification evidence if desired). The two lock files need not be pushed.
The existing package must retain `v0.2/build/rebuild-frozen-results.py`,
`v0.2/build/rebuild-final/byte-identity.json`, `v0.2/build/analysis-final/`,
the frozen source and reuse archive, and the collection evidence.

Verified result: the requested `cp -R` copy at `fresh-trl-codex` completed the
command with Python 3.9. All seven v0.2 files and five archived v0.1 files match
this workspace's `v0.2/build/analysis-final` byte for byte. See
[the final verification](fresh-clone-verification.json),
[exact inventory differences](inventory-differences.json), and
[failure checks](failure-checks.json). The original read-only clone and local
frozen inventories were reverified unchanged after reproduction.
