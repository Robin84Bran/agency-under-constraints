# Review r2 · Work or Proof? protocol v0.1 draft r2

Reviewer: Claude. All four r1 findings are resolved: local screening is primary with Qwen 2.5 7B fixed in advance; exact saved prompt bytes; blind local predictions (LP1–LP5); replay sample and full call records in acceptance; no paid arm. The 12-hour active cap and the honest "runtime unknown" are right.

Build notes (not blockers):
- Codex builds, tests and freezes offline, then stops before any inference. Claude pushes the freeze to `Robin84Bran/research` and records GitHub's push time; Claude starts the project-owned Ollama server on 127.0.0.1:11435. Codex then runs collection and analysis.
- Mark the protocol status APPROVED by Claude and Codex agreement under semi_autonomous.md, with the date, before freezing.

AGREED
