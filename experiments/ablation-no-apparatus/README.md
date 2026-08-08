# Ablation: doctrine without the evidence apparatus

`SKILL.md` here is the shipped doctrine with its evidence apparatus removed
and nothing else changed. It is an eval input, not a doctrine anyone should
install.

## What it tests

The n=16 swap gate (`reports/swapgate3-summary.md`) found the candidate
doctrine confirms fewer defects than the incumbent it forked from: 19 vs 30,
95% CI [-1.19, -0.18]. Two mechanisms could explain that, and they call for
different fixes:

- **H1 — the apparatus dilutes attention.** 22% of the doctrine is falsifier
  lines and an evidence index. Both tell a reader when to *distrust* a rule
  and neither helps apply one, so they may simply be crowding the rules out.
  Fix: disclose them behind a pointer, which is what the doctrine's own
  progressive-disclosure rule would say to do.
- **H2 — the rules are too thin.** 20 rules at ~500 characters each against
  the incumbent's 9 at ~1,240. Fix: fewer, thicker rules — a real rewrite.

Stripping the apparatus and nothing else separates them. If the gap closes,
H1. If it does not move, H2, and the rewrite is the only thing that will help.

## The transformation

Purely mechanical, so `diff` against `skills/skill-tuner/SKILL.md` shows the
whole intervention:

1. Every `Falsifier:` line removed (20 of them, one per rule).
2. The `## Evidence index` section removed.
3. One clause cut from the intro that promised falsifiers which are no longer
   present — leaving it would make the document incoherent, which is a
   different defect from the one under test.

12,742 → 9,843 characters (22.8% removed). All 20 rules and all 25 evidence
tags are kept: the tags are the confidence signal and cost a token each, so
they are not what is being ablated.

Note this holds rule thinness constant by design. The ablated doctrine is
*shorter* than the incumbent (9.8 KB vs 11.2 KB) while still carrying 20
rules to its 9, so it does not test H2 — that is the point.

## Reproducing

Compared against the banked `swapgate3-probe-incumbent` baseline rather than
re-running it: the baseline is pinned to `origin/main` and `tune.py verify`
reports it unchanged, so one leg is enough.

```
python3 skills/skill-tuner/scripts/tune.py verify swapgate3-probe-incumbent
python3 skills/skill-tuner/scripts/tune.py probe \
  --config configs/swapgate4-probe-ablated.json \
  --run-id swapgate4-probe-ablated --yes --budget-usd 11
python3 skills/skill-tuner/scripts/tune.py compare \
  --baseline swapgate3-probe-incumbent --candidate swapgate4-probe-ablated
```
