# Three Rules, One Lunch — questions after frozen analysis

Append-only question log. Entry date: 12 November 2026 HKT. Codex, builder for
Claude's delegated review. Every question below is **post hoc** and exploratory;
none changes the v0.1 predictions, scoring, evidence or collection. No new model
calls or inferential tests were made for this log. Original QUESTIONS.md remains
frozen and unchanged.

1. **Did the interface prevent the primary experiment from happening?** Qwen 7B
   completed 100/100 central episodes and 0/100 in each worker regime; Llama
   completed 0/300. Saved examples show a worker returning three cells for a
   one-cell quota and a central reply repeating forbidden request fields. Local
   requests used JSON mode rather than exact-schema constrained decoding. Would
   a separately registered schema-constrained version recover valid worker
   trajectories, and would a sharing effect survive once the interface works?
   The current zeros answer an operational question, not the coordination one.

2. **Can sharing spread yesterday's good answer after it becomes obsolete?**
   Frozen greedy-shared beats greedy-private overall by 0.020583 Y on 100 seeds,
   yet loses after relocation: 0.238880 versus 0.316183. On Claude's 20 seeds,
   the overall gain is only 0.007671 and post-relocation reward is 0.183300
   versus 0.308650. Could a phase-aware script remove this penalty? Such a policy
   would need its own frozen comparison; it is not a replacement v0.1 baseline.

3. **Does a peak metric describe memory or simply where a model happened to
   search?** Claude shared workers query true old peaks 9 times after relocation,
   versus 4 private queries, but query their best *observed* old cells only 4
   times, versus 16 private queries. These are different target sets. Which
   registered behavioral measure would distinguish deliberate phase adaptation,
   incidental revisits and use of outdated evidence? These counts alone cannot
   identify a mechanism or show that each revisit was harmful.

4. **What makes Claude's shared workers exceed a simple greedy policy?** Their
   Y is 0.465675, or 143.7% of same-seed greedy-shared, and their post-relocation
   Y is 0.444542 versus the script's 0.183300. The descriptive sharing interval
   still crosses zero, and the script deliberately ignores phase changes. Could
   a stronger phase-aware code control account for this gap before attributing
   it to coordination or reasoning? No difference-of-gains test was registered.

5. **Why does successful formatting coexist with so much abstention?** Qwen 7B
   central has 100% valid episodes but executes only 66.2% of its opportunities,
   earning Y=0.196252 versus random's 0.301496 on the same seeds. What causes
   the null choices? A future intervention could distinguish uncertainty about
   the action contract from a search policy, but the current saved actions
   contain no explanations and cannot resolve that question.

6. **Does a direction-only prediction remain informative when failure patterns
   determine it?** P3 holds partly through Llama's zero/zero tie, while P5 fails
   because Qwen 1.5B shared earns 0.003455 against Qwen 7B's interface-driven
   zero. Which future validity gates should accompany secondary rankings so the
   claimed scientific question cannot be satisfied by unequal interface loss?
   The frozen P3/P5 statuses remain unchanged.

7. **How much depends on the compute allocation and the central harness loss?**
   Claude central uses 77 effective calls and USD1.170015, while shared uses 240
   calls and USD3.214471. Central includes one scored harness loss and two
   generated max-token failures. What would equal-compute or equal-dollar
   comparisons show in a separately designed study? Current equal-opportunity
   scores do not answer that, and dropping failed episodes would change the
   registered estimand.
