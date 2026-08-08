# Swap-gate, powered re-run (R13, UNIT U9.8)

Gate: skill-tuner replaces the incumbent `writing-for-agents` fork only if it
scores equal-or-better on the same pipeline. Model pin `claude-sonnet-5`,
resolved `claude-sonnet-5`; claude CLI 2.1.224; every input pinned to
`origin/main`. Supersedes `swapgate2-summary.md`, which recorded WON.

## Verdict: **WORSE — do not swap**

> **Correction, 2026-08-08.** A statistics review found `compare`'s worse
> verdict anchored at zero rather than −δ, so it fired on any confirmed
> regression, even one inside the declared-tolerable band. Recomputed under
> the corrected rule, this run's verdict is **inconclusive with regression
> confirmed**: the interval [−1.19, −0.18] excludes zero (the regression is
> real — the sign test agrees, p=0.039) but straddles −δ = −1.0, so its size
> against the margin is unresolved. The do-not-swap decision stands either
> way; the record below is preserved as originally published.

Leg (a) probe, 16 shared documents, three independent skeptics per finding:

| | incumbent | candidate |
| --- | --- | --- |
| confirmed | **30** | **19** |
| raised | 59 | 51 |
| confirm rate | 51% | 37% |

Paired by document: mean difference **−0.688 findings/document**, 95% CI
**[−1.19, −0.18]**. The interval excludes zero. Document record: candidate
won 1, lost 8, tied 7.

This is the first measurement in the series with the power to be believed,
and it says the candidate doctrine finds fewer defects than the ancestor it
was meant to improve on.

## The series, and why only this one counts

| Run | n | Verdict | What it actually was |
| --- | --- | --- | --- |
| swapgate (U7) | 1 | LOST | noise, plus a markdown-blind quote guard |
| swapgate2 (U8) | 6 | WON | noise — a lucky candidate draw |
| swapgate3 (U9) | 16 | **WORSE** | CI excludes zero |

The same two doctrines produced all three answers. A raw-count rule cannot
say "we could not tell", so it answered every time, and two of those three
answers were luck.

The lucky draw is visible directly. On the six documents swapgate2 used,
measured again here:

| Document | n=6 (inc/cand) | n=16 (inc/cand) |
| --- | --- | --- |
| browser-console-setup | 1 / 0 | 1 / 1 |
| agent-swarm | 3 / 1 | 3 / 2 |
| design-drift | 1 / 0 | 1 / 1 |
| cli-doctor-mode | 1 / **3** | 2 / **1** |
| branch-harmonization | 1 / **3** | 1 / **1** |
| curl-bash-installer | 2 / **4** | 3 / **1** |

The incumbent is stable across runs (1,3,1,1,1,2 → 1,3,1,2,1,3). The
candidate swung 3,3,4 → 1,1,1 on the three documents that carried swapgate2's
+2 margin. swapgate2 did not measure a better doctrine; it caught a better
afternoon. (`design-drift` also differs legitimately: swapgate2 read a stale
151-line working copy, this run pinned the 189-line `origin/main` version.)

Note the variance estimate itself moved: sd of the paired differences was
1.862 at n=6 and is 0.946 here. The earlier run was noisy *and* its noise
estimate was inflated by the same lucky draw.

## Why the candidate under-finds

Two independent lines point the same way.

**Structure.** The candidate carries 20 rules in ~12.8 KB, of which 22% is
evidence apparatus (17.5% falsifier lines, 4.4% evidence index). The
incumbent carries 9 rules in ~11.2 KB with no apparatus. Operational
elaboration per rule: roughly 500 characters against 1,240 — **2.5× thinner**.

**Confirm rate.** The candidate raises a similar volume of findings (51 vs
59) but only 37% survive adversarial verification against the incumbent's
51%. Thinner rules produce more findings that a skeptic can talk down —
exactly what a rule stated without room to say when it applies would predict.

The doctrine's own `Sprawl` rule anticipates this: *"a document can be too
long even when every line is live and unique; attention thins across the
excess."*

This hypothesis was raised during the U8 investigation and **retracted on the
swapgate2 result**. That retraction was wrong — it traded a structural
argument for six noisy documents. It is reinstated here on better evidence.

## Leg (b): routing

Not re-run. `routing_parity` is unchanged by U9 and the descriptions compared
are unchanged, and it passed at full parity (16/16 both conditions, verdict
`land`) in swapgate2. It is not the contested leg: the candidate description
routes fine, it is the doctrine body that under-finds.

## Totals

- 361 live `claude -p` calls (169 candidate + 192 incumbent), **$14.81**
- Neither run halted on budget; `overflow: 0` on both, so no finding was cut
  by the `max_findings` cap
- Both runs `tune.py verify` clean: inputs and CLI unchanged since the run
- Configs: `configs/swapgate3-probe-{incumbent,candidate}.json` — generated
  from one target list and asserted identical except `doctrine_file`
- Target rule, fixed before the run: every
  `claude/skills-local/*/SKILL.md` on dotfiles `origin/main` except the
  incumbent, sorted by path, first 16

## Disposition

R13 blocks the swap. The plan's stop condition — *"never ship a loser"* — now
has a measurement behind it rather than a coin flip.

What this does **not** condemn is the runner. The provenance layer, the
skeptic panel, the pinned inputs, and the paired verdict are what turned a
launch decision from "WON" into "measurably worse", on a candidate that had
already cleared the old gate twice. The eval half of skill-tuner just earned
its place by refusing its own doctrine.

Three ways forward, in order of preference:

1. **Fix the doctrine, then re-gate.** Move the falsifiers and evidence index
   behind a pointer — progressive disclosure, the doctrine's own rule —
   returning ~22% of the budget to rule elaboration, and re-run this gate.
   This touches KD6 (evidence tags and falsifiers stated in place are the
   session-settled differentiator), so it is a product decision, not an
   implementation one.
2. **Ship the runner, hold the doctrine.** The eval half stands on its own
   and its attribution story stays honest.
3. **Hold launch entirely** until 1 lands.

## Standing caveat

Each document's probe call is still n=1 per run, and the cross-run table
above shows that single draw is genuinely noisy at the document level. The
paired interval accounts for variation between documents, not for a document
being re-measured. The direction here is well supported — 8 documents lost
against 1 won, CI clear of zero — but the point estimate of −0.688 should be
read as "meaningfully worse", not as a precise effect size.
