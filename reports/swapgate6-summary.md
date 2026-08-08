# Doctrine v3 gate: better than the ancestor — the first time

Doctrine v3 against the banked `swapgate3-probe-incumbent` baseline. 15
documents, `verify_trials: 3`, model pin `claude-sonnet-5` resolved
`claude-sonnet-5`, claude CLI 2.1.224 on both legs, `design-drift` excluded
from both sides (drifted after the baseline was banked; `verify` caught it).
Run from the v0.2.0 campaign worktree with working-tree inputs; every input
content-hashed in the manifest, `tune.py verify swapgate6-probe-doctrine-v3`
reported **No drift** at banking time, and the doctrine file is byte-identical
to the v3 committed on this branch. All 15 targets verified unchanged against
the baseline's recorded hashes before the run.

## Verdict: **better** at δ = 1.0 findings/document

42 confirmed against the incumbent's 29. Mean difference **+0.867
findings/document**, 95% CI **[+0.03, +1.70]** — the interval excludes zero
on the high side. Document record 8 won, 3 lost, 4 tied.

Robustness: bootstrap 95% CI [+0.13, +1.60] agrees; paired effect size dz
+0.58; the exact sign test alone (p = 0.227) would **not** resolve at this n
— it reads only signs, and the win is carried partly by magnitude (+3
documents). Read honestly: the lower bound clears zero by 0.03, so this is a
near-boundary win a re-run could plausibly soften to `not_worse`. It is not
a landslide and should not be quoted as one.

## Why it is more than one lucky draw

The standard this project set at swapgate2 — one positive run is not a
trend — is met by four points moving together on identical documents and an
identical baseline:

| Doctrine | confirmed | mean diff | 95% CI | verdict | W/L/T |
| --- | --- | --- | --- | --- | --- |
| v1, as originally gated | 18 | −0.733 | [−1.27, −0.20] | inconclusive, regression confirmed* | 1/8/6 |
| v1, apparatus stripped | 22 | −0.467 | [−1.30, +0.37] | inconclusive | 2/9/4 |
| v2 | 27 | −0.133 | [−0.76, +0.49] | not_worse | 6/6/3 |
| **v3** | **42** | **+0.867** | **[+0.03, +1.70]** | **better** | 8/3/4 |

\* originally published as *worse*; corrected 2026-08-08 when the review
found the worse anchor at zero rather than −δ (`swapgate3-summary.md`).

v3 over v2 directly: +1.000/document, 95% CI [+0.19, +1.81], sign test
p = 0.039, verdict **better**.

## The mechanism, verified

The v3 rewrite targeted one forensic finding: the ancestor gap was
concentrated in duplication-hunting (single-source-of-truth was 41% of the
incumbent's confirmed yield and 4% of v2's), and the cause was positional —
v2 had demoted the rule from the terminal section and diluted its section
with self-referential material. v3 restored it to the last section at
incumbent paragraph depth with a named polarity-duplication cue, re-merged
Negation into Leading words with the worked examples, and left the rules v2
already wins on (Demand, cut-identity) untouched.

Confirmed findings by rule bucket, v2 → v3, incumbent for reference:

| bucket | incumbent | v2 | v3 |
| --- | --- | --- | --- |
| single-source-of-truth / duplication | ~12 | 1 | **16** |
| negation | 2 | 0 | **3** |
| cut identity | 1 | 5 | 5 |
| demand | 0 | 8 | 4 |
| one trigger per branch | 4 | 4 | 7 |

The recovered categories are exactly the targeted ones. Demand gave back
half its yield — consistent with the finding-budget substitution hypothesis
recorded in the forensics — and the net is +15.

## What this is not

- **A claim against current upstream content — checked, not assumed.** The
  incumbent snapshot (frozen 2026-08-05) includes upstream's 2026-07-23
  rename/restructure and its last content change (2026-07-28); the only
  local delta is one added sentence, the time-relative no-op amendment,
  which makes the baseline strictly harder. An earlier draft of this bullet
  called the snapshot stale, from a research-agent claim of a 2026-07-31
  restructure; upstream's commit log disproved it
  (`gh api repos/mattpocock/skills/commits?path=...`), and this correction
  replaces it.
- **Not a per-rule claim.** The doctrine as a whole out-found its ancestor
  once, on one metric (adversarially-confirmed defects at max_findings=5,
  three skeptics). No individual rule is thereby validated.
- **Not end-task evidence.** The probe measures defect-finding when the
  doctrine is applied, not whether documents edited under it make agents
  better at tasks. That axis belongs to skill-creator's benchmark and is out
  of scope by design (README, "What this does not measure").

## Totals

- 180 calls (15 probe + 165 verify), **$8.2975**, 15/15 targets, no budget
  halt, overflow: 3 findings past the per-document cap, unverified
- One leg, not two: the incumbent baseline re-used after `verify` confirmed
  every shared target unchanged; `--exclude design-drift` carried over
- Cumulative across the doctrine investigation: swapgate3 $14.81 +
  swapgate4 $8.07 + swapgate5 $7.25 + swapgate6 $8.30 = **$38.43**

## Swap decision

R13 as literally worded — equal-or-better on the same pipeline — is
satisfied for the first time: 42 ≥ 29 on raw counts *and* the interval
excludes zero. v3 ships as the bundled doctrine on this branch. The dotfiles
fork at `claude/skills-local/writing-for-agents/` is the incumbent in live
use; replacing it with v3 is a separate decision in that repo, per the
swapgate5 convention.
