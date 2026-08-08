# Doctrine v2 gate: not worse than the ancestor (U10)

Doctrine v2 — evidence apparatus disclosed to `FALSIFIERS.md`, the reclaimed
budget spent on section framing and detection cues — against the banked
`swapgate3-probe-incumbent` baseline. 15 documents, `verify_trials: 3`, every
input pinned to `origin/main`. `design-drift` excluded from both sides: it
drifted on dotfiles `origin/main` after the baseline was banked, and `verify`
caught it.

## Verdict: **not_worse** at δ = 1.0 findings/document

27 confirmed against the incumbent's 29. Mean difference **−0.133
findings/document**, 95% CI **[−0.76, +0.49]**. Document record 6 won, 6
lost, 3 tied.

The interval's lower bound clears −δ, so any regression is smaller than the
margin declared tolerable. This is the first time this doctrine has cleared a
bar it was measured against.

## The progression, on identical documents

Every candidate re-scored against the same baseline and the same 15
documents, so these three rows are directly comparable:

| Doctrine | confirmed | mean diff | 95% CI | verdict | W/L/T |
| --- | --- | --- | --- | --- | --- |
| v1, as originally gated | 18 | −0.733 | [−1.27, −0.20] | **worse** | 1/8/6 |
| v1 with apparatus stripped | 22 | −0.467 | [−1.30, +0.37] | inconclusive | 2/9/4 |
| **v2** | **27** | **−0.133** | **[−0.76, +0.49]** | **not_worse** | 6/6/3 |

Totals rise 18 → 22 → 27. The mean moves toward zero at every step, the
interval tightens and lifts, the verdict class improves, and the document
record goes from 1-won/8-lost to dead even. Three points moving together is a
good deal more than one positive run, which is the standard this project
learned the hard way at swapgate2.

Roughly: disclosing the apparatus bought about +4 confirmed findings, and
spending that budget on framing bought about +5 more.

## What this is not

**Not `better`.** The point estimate is still negative and the interval still
contains zero. On raw counts 27 < 29, so R13 as literally worded —
"equal-or-better" — is not satisfied. What is satisfied is R13's stated
intent, the stop condition *"never ship a loser"*: v2 is measurably not a
loser.

Whether `not_worse` clears the launch bar is a product decision, not a
measurement one. The argument for yes: the raw-count rule is the one this
project already replaced for being unable to say *we could not tell*;
demanding a positive result on a measurement this noisy needs ~23+ documents
and might never resolve; and the doctrine carries value the probe does not
measure at all — evidence tags, falsifiers, and the runner itself. The
argument for no: R13 was written to mean strictly better, and the ancestor
still finds two more defects.

**Not a claim that prose beats bullets.** v2 raised prose from 21% to 30% of
the document, well short of the incumbent's 77%. The correction recorded in
`swapgate4-summary.md` stands: that observation rests on two documents and
was deliberately not over-fitted to. If a v3 is wanted, pushing further toward
prose-dominant form is the next identified lever, and it is a hypothesis, not
a finding.

## Totals

- 168 calls, **$7.25**, 15/15 targets, no budget halt, `overflow: 0`
- One leg, not two: the baseline was re-used after `verify` reported it
  clean, and `--exclude` handled the one drifted document instead of forcing
  a re-baseline
- Cumulative across the doctrine investigation: swapgate3 $14.81 + swapgate4
  $8.07 + swapgate5 $7.25 = **$30.13**

## If the swap goes ahead

R13's promise is that what ships is what the authors switched to, so the
dotfiles fork at `claude/skills-local/writing-for-agents/` gets replaced by
v2 in a separate PR, and KD6 needs its amendment recorded: *"each rule
self-reports its evidence tier and its falsifier"* becomes tier inline,
falsifier one hop away behind a pointer. The differentiator survives; its
layout changed, and the change is what made the doctrine competitive.
