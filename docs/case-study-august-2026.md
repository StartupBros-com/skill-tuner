# The August 2026 campaign: what happens when you refuse to ship an unmeasured edit

Over four days in August 2026 we pointed this tool at our own production
harness — 41 always-on skills — and then at two corpora we didn't write,
including Anthropic's. Every claim below links to a receipt in this repo
that you can re-verify for $0. The refusals are published beside the wins,
because the refusals are what make the wins believable.

## Act 1 — The doctrine had to beat its ancestor, and mostly it couldn't

The tuning doctrine (the checklist the probe audits against) forked from a
popular OSS skill-writing guide. We froze the ancestor
([`doctrines/writing-for-agents-8b36d4f.md`](../doctrines/writing-for-agents-8b36d4f.md))
and required every revision to beat it on a paired, margined comparison:

- **v1: refused.** A real regression — 95% CI [−1.19, −0.18]
  ([swapgate3](../reports/swapgate3-summary.md)).
- **v2: not_worse, not shipped as better.** CI [−0.76, +0.49]
  ([swapgate5](../reports/swapgate5-summary.md)).
- **v3: better.** 42 vs 29 confirmed defects, CI [+0.03, +1.70] — quoted
  as the near-boundary win it is
  ([swapgate6](../reports/swapgate6-summary.md)).
- **v3.1: refused.** Four sentences restored from the ancestor, every one
  endorsed by expert review. 24 vs 42, CI [−2.21, −0.19]
  ([swapgate7](../reports/swapgate7-summary.md)).
- **A live hot-patch: refused.** One rule added mid-campaign measured
  CI [−1.18, −0.02] and was reverted
  ([hotpatch-gate](../reports/hotpatch-gate-001)).

Two-for-two, the gate refused doctrine additions that expert consensus
endorsed. That is the entire pitch: **the instrument dissents from its own
authors.** The full ledger, including the replication where v3's win
relaxed to not_worse on a corpus whose defects we'd fixed (+0.467/doc, CI
[−0.31, +1.25], mechanism explained), lives in
[FALSIFIERS.md](../skills/skill-tuner/FALSIFIERS.md).

## Act 2 — 96 fixes, every one with a chain of custody

The campaign probed the full canonical corpus in four batches. Every fix
descends from a finding that survived three adversarial verification
trials plus a code-level quote check; every batch landed as a reviewable
PR (dotfiles [#289](https://github.com/StartupBros-com/dotfiles/pull/289),
[#296](https://github.com/StartupBros-com/dotfiles/pull/296),
[#316](https://github.com/StartupBros-com/dotfiles/pull/316),
[#321](https://github.com/StartupBros-com/dotfiles/pull/321)) — 96
verified defects fixed in total.

What that bought, measured ([context ledger](context-ledger.md)):
**−6,089 bytes of always-loaded context, negative in every batch**, at
certified behavioral parity. (Total bytes went +1,922 — batch 1 demoted
8KB of patterns into on-demand reference files. Both numbers published.)

Descriptions — the routing surface — got their own gate: 16 prunes landed
at measured routing parity on blind batteries; 4 were refused. A pruned
description that loses a trigger noun fails the battery, so it doesn't
ship.

## Act 3 — Then we attacked our own instrument

Three validity objections, each bought down with an experiment:

1. **"The judges share a family with the generator."** All 61 confirmed
   findings from the replication legs were re-adjudicated blind and
   adversarially by a non-Claude frontier judge. Survival 47% (v3) vs 48%
   (ancestor), Fisher exact p = 1.000 — no leg asymmetry; the doctrine's
   advantage is not a claude-family artifact. The recall direction found
   no family blind spot — but did catch our own `max_findings` cap
   silently truncating defect-dense docs, now a playbook rule
   ([experiments/cross-judge](../experiments/cross-judge/README.md)).
2. **"The doctrine could be Goodharting the judges."** An authoring A/B
   with blind, order-debiased judging came back not_worse
   (CI [−0.04, +0.10]) — writing under the doctrine doesn't produce
   judge-pleasing degradation
   ([experiments/authoring-ab](../experiments/authoring-ab)).
3. **"Deduplication might change behavior."** A standing behavioral suite
   ([configs/endtask-suite](../configs/endtask-suite/README.md)) runs the
   three most invasively edited skills against their frozen pre-campaign
   ancestors on deliberately hard cases, graded by deterministic scripts
   that were themselves adversarially verified first (that pass caught a
   draft grader biased toward the current version). First run: all three
   **not_worse** at δ = 0.10 pass-rate.

On our own already-good corpus, not_worse is the win condition — a
deletion that keeps behavior is banked savings. The question "where's the
*better*?" needed ground with headroom.

## Act 4 — Leaving home

We probed samples from two OSS corpora
([experiments/external-corpus](../experiments/external-corpus/README.md)):
`davidondrej/skills` runs 2.6 confirmed defects/doc and Anthropic's
`anthropics/skills` 2.5, against 1.4 on our corpus at its own first-probe
state — the wild is ~1.8× denser. Both directions reported: Anthropic's
`skill-creator` probed completely clean.

Then the demonstration: the 5 densest external docs (23 verified
findings) were fixed and re-probed under the identical config. **Mean
reduction 2.80 defects/doc, bootstrap 95% CI [2.00, 3.60], five docs
improved out of five — 23 confirmed defects became 9 (−61%) for $2.83 of
re-probe.** On documents that still have defects, one pass removes most
of them, with an interval attached.

The fixes went upstream:
[anthropics/skills#1543](https://github.com/anthropics/skills/pull/1543)
and [davidondrej/skills#3](https://github.com/davidondrej/skills/pull/3)
— with the one description edit we couldn't battery-verify deliberately
excluded, because the discipline applies most exactly when nobody would
notice.

## What it cost

No single banked run in this story cost more than $8.30 (the v3 doctrine
leg) or less than $0.09 (a one-target dogfood probe); the priciest single
question — the two-leg replication — totaled $14.40 across its pair of
runs. Every amount is recorded in its banked report; comparisons,
verification replays, and the context ledger are $0 by construction. The sequential gate stops decisive
runs early (~49% cheaper on the v3 replay); [COSTS.md](COSTS.md) prices
every envelope, including the two we measured and demoted from their
marketing numbers.

## Steal this

The method is MIT-licensed and this repo contains all of it: the
[playbook](PLAYBOOK.md), the doctrine and its
[falsifiers](../skills/skill-tuner/FALSIFIERS.md), and every banked run.
If you take one thing: **a threshold with no interval answers every time,
and on a noisy measurement most of those answers are luck.** Make your
tooling able to say "we could not tell" — then earn the verdicts that
survive it.
