# Research

Pre-registered studies grown from the playable experiments at https://iamrobin.ai/intelligence/. Programme: https://iamrobin.ai/research/. One folder per project; each has its own protocol, freeze, evidence and results.

Built by Codex and reviewed by Claude under a semi-autonomous research loop, with Bin "Robin" Xie as principal investigator.

> I study AI agents that [disown work they actually did](https://github.com/Robin84Bran/honest-agent/blob/main/v0.3.1/RESULTS.md), [confess to crimes they never committed](https://github.com/Robin84Bran/honest-agent/blob/main/v0.3.1/RESULTS.md), and [confidently remember a world that no longer exists](portable-self/v0.2/collection/delivery/RESULTS.md).

<sub>First two: small local models (Qwen 2.5, Llama 3.1) in the Honest Agent. Third: Claude, on a synthetic task in The Portable Self.</sub>

## Results at a glance

Eight pre-registered studies. Each was frozen and pushed before any model call and analysed with its frozen code; later versions (v0.2) are labelled. **2 of 8 primary tests passed.** Failures are reported as plainly as passes.

| Study | Question | Primary test | Headline |
|---|---|---|---|
| [Work or Proof?](work-or-proof/RESULTS.md) | Can a cheap local check direct an expensive check better than random? | **Passed** | Qwen 7B screen + frontier check caught 67.8% of 737 breaches vs 50.0% for random: **+17.9 pp** (95% 16.2 to 19.8) at the same budget |
| [The Receipt Gap](receipt-gap/v0.2/delivery/RESULTS.md) | After a lost receipt, does an idempotency key stop duplicate actions? | **Passed** (v0.2, duplicates) | Keys cut Qwen 7B duplicates by **34 pp** (95% 27 to 40); the separate test of honest reporting failed |
| [Signal or Silence](signal-or-silence/v0.2/RESULTS.md) | Can an AI judge say "can't tell" when the evidence can't decide, and only then? | Failed | No judge passed; Claude said "can't tell" on 97.5% of ambiguous records (v0.1), but in v0.2 its reply validity still stayed below the 95% bar |
| [Bridge or Bus?](bridge-or-bus/v0.2/delivery/RESULTS.md) | Does access to current tool descriptions help after an API changes? | Failed | Qwen 7B: +2.0 pp (95% −4.0 to +8.0); no local model ever looked the descriptions up. Claude +26.7 pp, descriptive |
| [Three Rules, One Lunch](three-rules-one-lunch/v0.2/RESULTS.md) | Does sharing observations help workers search? | Failed | Reward rose for Qwen 7B but productive-query yield stayed inconclusive; shared Qwen 7B scored below random |
| [The Useful Core](useful-core/collection/delivery/RESULTS.md) | Does prioritising useful fallbacks help an agent during tool outages? | Failed | All 900 local episodes delivered nothing; Claude delivered the best feasible tier in 58 of 60 |
| [The Portable Self](portable-self/v0.2/collection/delivery/RESULTS.md) | Does auto-routing an agent's own notes beat a shared notebook? | Failed | Opposite direction: Qwen 7B **−9.7 pp** correct actions with routing (95% −13.1 to −6.3) |
| [One Door, Many Hands](one-door-many-hands/delivery/RESULTS.md) | Do worked examples help models choose resilient fleets? | Failed | Opposite direction: examples raised Qwen 7B's deadline regret (0.274 → 0.384) and cut optimal choices from 34.3% to 21.3% |

Each study's own results file gives every prediction, denominator and deviation. The pages at https://iamrobin.ai/research/ show the same results with figures and intuitive baselines.

## Public copy

This is a redacted public copy of the private working repository. Machine-local paths, a login name and session identifiers were replaced with placeholders, and 25 archives were withheld. See [PUBLIC_COPY.md](PUBLIC_COPY.md) for exactly what changed and what that means for hash verification.

## License

- **Code:** MIT. See [`LICENSE`](LICENSE).
- **Everything else** (protocols, results, saved calls, ledgers, logs): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [`LICENSE-CC-BY-4.0.md`](LICENSE-CC-BY-4.0.md).

The Honest Agent and The Obedient Rebel live in a separate repository: https://github.com/Robin84Bran/honest-agent
