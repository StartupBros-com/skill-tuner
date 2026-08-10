# Doctrine v3.1 gate: REFUSED — four expert-endorsed sentences cost 43% of yield

The strongest advertisement for gating this project has produced, and it is
a loss. v3.1 restored four ideas a 13-reviewer line-by-line audit had
identified as genuinely lost from the ancestor's text and "worth restoring":
the process-not-output framing clause, the merge-direction premature-
completion caution, the restatement-hunt imperative, and the mechanical
no-op-pruning rules. Roughly four sentences, every one plausible, every one
carrying a reviewer's endorsement, none changing a rule's meaning.

## Verdict vs v3 (banked swapgate6, same 15 documents): the additions lose

24 confirmed against v3's 42. Mean difference **−1.200 findings/document**,
95% CI **[−2.21, −0.19]** — the interval excludes zero: the regression is
confirmed; at δ = 1.0 the verdict is *inconclusive with regression
confirmed*, which fails the land bar either way. Bootstrap agrees
([−2.07, −0.33]); document record 3 won, 9 lost, 3 tied. Refuted findings
doubled (13 → 27), consistent with the additions steering probes toward
weaker framings.

Against the original incumbent (swapgate3, `--exclude design-drift`): 24 vs
29, CI [−1.16, +0.50], inconclusive — v3.1 gives back even the *better*
verdict v3 earned.

## Decision

**Reverted.** `skills/skill-tuner/SKILL.md` is byte-identical to v3 again;
the dotfiles `writing-for-agents` copy was never switched and stays v3. The
four ideas return to the ledger as refuted-at-gate, not as candidates.

## Why this run matters more than a win

Every actor in the pipeline endorsed these sentences: the ancestor carried
them, the review fleet recommended them, the author (this harness) judged
them safe enough to gate. The only dissenter was the measurement. A
doctrine that ships on expert consensus would have landed a 43% yield
regression without ever knowing; the mechanism hypothesis — added prose
diluting the high-yield terminal rules, the same finding-budget
substitution the swapgate6 forensics documented — is plausible but
unproven, and the verdict does not depend on it.

## Totals

- 180 calls, **$7.84**, 15/15 targets, no budget halt
- One leg against two banked baselines (v3 and incumbent re-used; both
  clean per `verify` at gate time)
- Doctrine investigation cumulative: swapgate3 $14.81 + swapgate4 $8.07 +
  swapgate5 $7.25 + swapgate6 $8.30 + swapgate7 $7.84 = **$46.27**
