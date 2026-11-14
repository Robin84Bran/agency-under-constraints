# Review r2 · Signal or Silence protocol v0.1 draft r2

Reviewer: Claude. All four findings resolved: plain v0.3.1 instruction primary, explicit sufficiency instruction secondary, separate pass decisions, strict byte-identical reuse without peeking, forecasts per instruction, zero-reuse budget.

One decision to unblock the build: **enforceable output-token caps are not required.** The Claude CLI cannot enforce max_tokens (as the Honest Agent documented). Use the Honest Agent budget mechanism instead: before each Claude call, reserve its worst-case cost from measured per-call maxima; stop before any call whose reservation would take project spend past 39 USD; report actual spend. Record this as the cost-control method in the protocol before freezing. Projected spend (about 19–34 USD) fits the 40 USD auto-approved line.

Build order: offline build, tests, certificates and freeze; stop before any call. Claude pushes the freeze and records GitHub's time; local judges run on the project server (127.0.0.1:11435, now free); Claude calls run through the Honest Agent v0.3.1 ClaudeCLI transport.

AGREED
