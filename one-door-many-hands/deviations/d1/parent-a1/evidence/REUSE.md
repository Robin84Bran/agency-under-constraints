# Reused evidence and code

Read-only sibling inspection: Receipt Gap `rg_core.py`, `rg_collect.py`, `rg_freeze.py`, `rg_analysis.py`, `rg_stats.py`, RUN.md and its D2 adapter correction; Bridge or Bus `bob_d2.py`, its archived local manifest/layer chain and cost basis; Three Rules `trl_transport.py`, `trl_validation.py`, `trl_freeze.py` and offline archive pattern. No sibling was edited.

`od_stats.py` preserves Receipt Gap's standard-library statistical helpers and its multiplicity fixture. Collector/transport/attestation patterns were adapted into task-owned modules: one decision per episode, local transport failures end one episode, two-turn strict schema replies, complete reported usage/cost, and byte-prefix checkpoints on every append. `od_contract.py` is pure so analysis never imports a provider.

`evidence/local-identity.json` and `evidence/models/` copy Bridge or Bus D2's content-addressed manifests/layers; paths alone were rewritten to the local portable archive. SHA-256 verification binds the original exact bytes and real template/default system. These are historical pins, not a live readiness claim. Live metadata will be captured, saved and validated before inference. The CLI contract/help is copied from Receipt Gap, and cost basis from Bridge or Bus; both remain dated historical evidence.

`evidence/toy-model.mjs`, `toy-README.md` and `toy-results.json` preserve the source identified in SURVEY. The old 120-round toy is independently parity-tested with Node/Python; it is explicitly separate from the study's one-wave oracle. The latter is checked against direct subset probabilities for one/six carriers and a distribution recurrence for 24, plus exact boundaries and common-mode identities.
