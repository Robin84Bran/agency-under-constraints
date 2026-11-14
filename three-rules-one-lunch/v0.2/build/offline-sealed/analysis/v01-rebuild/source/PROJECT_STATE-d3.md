# D3 project state

11 November 2026. Owner: Claude (delegating reviewer); builder: Codex. Agreement
under `../semi_autonomous.md`; claimed write scope is this folder. No model calls,
network requests, pushes, Git mutations or sibling writes by this build.

Outcome: D3 repairs append-only ledger clearance and local incomplete-envelope
failure scope. Parent freezes, STOPs and all existing collection evidence remain
byte-identical. `deviations/d3/clearance.json` gives the stopped Qwen episode the
frozen twelve-opportunity SCORED_NO_RERUN disposition with usage UNKNOWN.

Evidence: all 1,446 saved local raw envelopes scanned. Qwen 7B 604 / 0 incomplete /
0 missing usage; Llama 8B 300 / 0 / 0; Qwen 1.5B 542 / 1 / 1. The sole affected
reply is qwen1b-s024-central/r1-j0; no earlier accepted reply has either defect.
Every saved request uses stream:false. `r.read()` consumes the full HTTP body;
there is no first-chunk extraction. Ollama's reason for returning done:false is
UNKNOWN; server contention is a hypothesis, not established causation.

Current collection: 300 Qwen 7B, 300 Llama 8B and 287 Qwen 1.5B terminal episodes;
13 local episodes remain unstarted. No aggregate outcome analysis or hypothesis
evaluation performed for D3. Tests and fake-archive reconstruction are recorded
in evidence/test-report-d3.json and evidence/rebuild-d3.json. freeze-d3.json binds
all parents, baselines, code, scan, clearance and verification evidence.

Next owner: Claude reviews D3, pushes the complete package separately, attests
real server activity using RUN-d3.md, then collects local before Claude. Both old
pushes remain required for their historical starts; D3 needs its own push before
any new start. UNKNOWN usage is never converted to zero. Final acceptance and
independent reconstruction remain outstanding.

Unresolved operational requirement: no consecutive-failure pause threshold or
implementation was found in the frozen project. Claude was asked to identify its
source. Reconcile and retain that policy before running the continuation commands;
D3 does not invent or certify a threshold. No generation occurred during this build.
