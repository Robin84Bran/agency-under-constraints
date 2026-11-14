# Claude review · Three Rules, One Lunch protocol v0.1 draft · 2026-11-11

**AGREED**, with two notes to fix during build (no new round needed).

1. **The primary may be close to mechanical.** Rewards are deterministic and non-depleting, so once any worker finds a high cell, sharing lets all three exploit it; a scripted greedy-shared policy will likely beat greedy-private by a wide margin. That's fine, but then the interesting result is how close models get to the scripted greedy baselines in each regime. Report model Y as a fraction of greedy-shared and greedy-private (same seeds) next to the primary, and say plainly on the page if the benefit is mostly what a simple script also gets.
2. **Relocation is where coordination is actually tested.** P4 is good; also report, descriptively, how many rounds after relocation each regime keeps querying the old peak (stale exploitation), since shared receipts could also spread outdated information.
Frontier arm (60 episodes, ≤USD 19.08 reserved within USD 25) is fine. Proceed to build, tests and freeze.
