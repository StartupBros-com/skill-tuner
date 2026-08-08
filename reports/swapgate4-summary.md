# Ablation: does the evidence apparatus cost defect-finding? (U9.9)

Tests H1 from `reports/swapgate3-summary.md`. The shipped doctrine with its
20 falsifier lines and evidence index removed and nothing else changed
(`experiments/ablation-no-apparatus/`), against the banked
`swapgate3-probe-incumbent` baseline — same 16 documents, same model, same
pin, same `verify_trials: 3`.

## Result: H1 supported, not confirmed

| Doctrine | confirmed | vs incumbent | verdict |
| --- | --- | --- | --- |
| incumbent `writing-for-agents` | **30** | — | — |
| candidate, as shipped | 19 | −0.688/doc, CI [−1.19, −0.18] | **worse** |
| candidate, apparatus stripped | **26** | −0.250/doc, CI [−1.15, +0.65] | **inconclusive** |

Removing 22.8% of the document — none of it about how to apply a rule — moved
the gate out of *measurably worse*. The interval now straddles zero.

Measured directly against the un-ablated candidate: **+0.438 findings/document,
95% CI [−0.36, +1.24]**, 7 documents won to 4 lost, verdict `not_worse`.

That interval includes zero, so **the improvement is a direction, not an
established effect.** Declaring victory here would repeat exactly the mistake
swapgate2 made — reading a positive point estimate off an underpowered run.
What can be said honestly:

- The apparatus is not load-bearing for defect-finding. Stripping it cost
  nothing (`not_worse`) and the point estimate improved.
- It is *plausibly* costing yield, consistent with the doctrine's own Sprawl
  rule, but 16 documents cannot separate +0.44 from zero.

## The remaining gap points at H2

Even ablated, the candidate loses 9 documents to 3. Rule thinness was held
constant on purpose: the ablated doctrine still carries 20 rules to the
incumbent's 9, at ~490 characters each against ~1,240. It is now *shorter*
than the incumbent (9.8 KB vs 11.2 KB) and still finds less.

So the two hypotheses are not exclusive, and the evidence now favours both:
crowding was real, and the rules underneath it are still too thin.

## Recommended fix

Do both halves of what was always option 1, in one pass:

1. **Disclose the apparatus.** Falsifiers and the evidence index move behind
   a pointer; the one-word tags stay inline. This is the doctrine's own
   progressive-disclosure rule applied to itself, and the ablation says it
   costs nothing.
2. **Spend the reclaimed 22% on the rules.** Elaborate toward the incumbent's
   density — likely by consolidating 20 thin rules into fewer, thicker ones
   rather than padding all 20.

Then re-gate against the banked baseline: one leg, ~$8.

KD6 needs an amendment either way — "each rule self-reports its evidence tier
and its falsifier" becomes tier inline, falsifier one hop away. The
differentiator survives; its layout changes.

## Totals

- 192 calls, **$8.07**, 16/16 targets, no budget halt, `overflow: 0`
- Baseline re-used rather than re-measured: `tune.py verify
  swapgate3-probe-incumbent` reported no drift, so this cost one leg
  instead of two. First time the provenance layer paid for itself in cash.

## A defect this run found in the comparison tool

`compare` advised *"you would need about 12 documents"* on a run of 16 that
was still inconclusive — advice to collect less data than was already in
hand. The estimate sized from spread alone, but the non-inferiority bound is
`mean − t·sd/√n > −delta`, which also depends on how far the point estimate
already sits from the margin. Fixed in `n_to_resolve`, which now solves the
real inequality and returns None when the estimate itself is past the margin,
since no sample size rescues that. The corrected answer here is **23
documents (+7 on this run)**.

Worth noting how it surfaced: by reading the tool's own output on a real
question and finding the advice absurd. Nothing in the suite would have
caught it — every test asserted the number was larger than the input n, which
12 was not, but 12 > 6 held in the fixture.
