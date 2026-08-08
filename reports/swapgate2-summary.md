# Swap-gate re-run (R13, UNIT U8)

> **SUPERSEDED by [`swapgate3-summary.md`](swapgate3-summary.md), which
> records the gate as WORSE — do not swap.** The WON below was noise. At
> n=16 with inputs pinned to `origin/main`, the candidate confirms 19
> findings against the incumbent's 30, mean difference −0.688/document with a
> 95% CI of [−1.19, −0.18], losing 8 documents and winning 1. Re-measured,
> the three documents that carried this run's +2 margin (3, 3, 4) came back
> 1, 1, 1 — this run caught a good draw, not a better doctrine. The caveat
> below about the margin resting on magnitude rather than consistency was
> pointing at exactly this. Kept unedited as the original record.

Gate: skill-tuner replaces the incumbent `writing-for-agents` fork only if it
scores equal-or-better than the incumbent on both legs below, on the same
pipeline. Model pin: `claude-sonnet-5`. Auth mode: api-key, budget-capped per
run. Supersedes `swapgate-summary.md`, which recorded LOST.

## Verdict: **WON**

Both legs pass. Leg (a) probe: the candidate doctrine confirmed **11**
findings against the incumbent's **9**, across six shared target documents.
Leg (b) routing: full parity, 16/16 both conditions, verdict `land`.

Per the gate rule, WON requires both legs; both hold. Recorded as measured —
no prompt, config, or target was changed after seeing a result.

---

## Why the first gate run is superseded

The original run (`swapgate-summary.md`) recorded leg (a) as FAIL on
candidate 0 vs. incumbent 2, on **one** target document. Two defects in the
harness made that number wrong, and a third made it unreviewable:

1. **The quote-existence guard was markdown-blind.** `verify_finding`
   downgraded any CONFIRMED verdict whose quoted text was not a raw substring
   of the target. Markdown repeats `> ` and list markers on every wrapped
   line; a correct quote reproduces the prose and drops them. The candidate's
   one verifier-CONFIRMED finding quoted a blockquote continuation in
   `browser-console-setup/SKILL.md` and was silently downgraded. Its true
   score on that run was 1, not 0. Since every document this probe targets is
   markdown, the false negative was systematic, not a one-off.

2. **n=1 target decided a count-based launch gate.** The original summary
   flagged this ("a thin sample for a count-based gate"). The wider run
   reverses the sign of the result, which settles the question: the first
   verdict was noise.

3. **Refuted findings were counted, never reported.** `report.md` showed
   `refuted: 2` and nothing else, so a code-level downgrade for a fabricated
   quote and a verifier's judgment that a rule did not apply read
   identically. Finding defect 1 required hand-parsing `trials.jsonl` and
   re-running the substring test outside the harness.

Fixed in U8, test-first: `quote_present()` compares prose rather than layout,
refuted findings carry their `refutation_mode`, `verify_trials` judges each
finding with an odd panel of independent skeptics on a strict majority, and
`target_files` runs one gate across many documents. Two further defects
surfaced while running this gate and are fixed in the same unit: the
`--budget-usd` cap was advisory on the probe path (checked pre-flight, never
enforced during the run), and trial rows were buffered in memory until after
the final target instead of persisting as they completed.

---

## Leg (a): Probe comparison

Six target documents, identical for both conditions, fixed before the run.
`max_findings: 5`, `verify_trials: 3`. Neither run halted on budget;
`overflow: 0` on both, so no finding was truncated by the cap.

| Target | incumbent confirmed | candidate confirmed |
| --- | --- | --- |
| `browser-console-setup` | 1 | 0 |
| `agent-swarm` | 3 | 1 |
| `design-drift` | 1 | 0 |
| `cli-doctor-mode` | 1 | **3** |
| `branch-harmonization` | 1 | **3** |
| `curl-bash-installer` | 2 | **4** |
| **Total** | **9** | **11** |

Gate rule: candidate passes if `findings_confirmed(candidate) >=
findings_confirmed(incumbent)`. 11 >= 9. **Leg (a): PASS.**

| Run-id | Doctrine | confirmed | refuted | probe calls | verify calls | cost |
| --- | --- | --- | --- | --- | --- | --- |
| `swapgate2-probe-incumbent` | `writing-for-agents/SKILL.md` | 9 | 12 | 6 | 63 | $2.9568 |
| `swapgate2-probe-candidate` | `skill-tuner/SKILL.md` | 11 | 11 | 6 | 66 | $2.6842 |

### What the margin does and does not say

The per-target record is **3–3**. The candidate wins three documents by a
clear margin (3v1, 3v1, 4v2) and loses three narrowly (0v1, 1v3, 0v1), so the
aggregate +2 is carried by magnitude on the documents it wins, not by winning
more often. R13's rule is an aggregate count and the aggregate passes, but
this is not a dominant result and should not be cited as one.

Both doctrines raised similar volume — 21 findings (incumbent) vs 22
(candidate). The difference is in confirmation rate: 43% vs 50%.

Qualitatively the two differ in spread. The incumbent's nine confirmations
cluster on two rules (context pointers, pruning/relevance). The candidate's
eleven span six (single source of truth, negation, completion criteria,
demand, progressive disclosure, context pointer). The candidate carries 20
rules to the incumbent's 9, and the wider defect vocabulary is where that
surface pays.

One candidate finding was refuted by the code-level guard for a quote absent
from the target (`refutation_mode: quote_not_found`) — the backstop working
after the markdown false-negative was removed from it.

## Leg (b): Routing comparison

Run-id `swapgate2-routing-001`, re-measured rather than carried forward.
Single target = the doctrine skill itself: `original` = the incumbent's
frontmatter description, `pruned` = skill-tuner's. 5 distractors, 8-prompt
hand-authored battery (4 should-fire, 2 near-miss, 2 none-of-the-above), 2
trials per condition = 16 router calls per condition, 32 total.

| Condition | Accuracy | Near-miss rejection |
| --- | --- | --- |
| `original` (incumbent description) | 16/16 (100.0%) | 8/8 (100.0%) |
| `pruned` (skill-tuner description) | 16/16 (100.0%) | 8/8 (100.0%) |

Verdict (`routing_parity.determine_verdict`): **land**. failing_case_ids: none.
Reproduces the first run's leg (b) exactly. **Leg (b): PASS.**

---

## Totals

- Live `claude -p` calls: 69 (probe-incumbent) + 72 (probe-candidate) + 32 (routing) = **173**
- Total cost: $2.9568 + $2.6842 + $0.3235 = **$5.9645**
- Run-ids: `swapgate2-probe-incumbent`, `swapgate2-probe-candidate`, `swapgate2-routing-001`
- Configs: `configs/swapgate2-probe-incumbent.json`, `configs/swapgate2-probe-candidate.json`,
  `configs/swapgate-routing-001.json`, `configs/swapgate-routing-battery.json`
- Reports: `reports/swapgate2-probe-incumbent/`, `reports/swapgate2-probe-candidate/`,
  `reports/swapgate2-routing-001/`

## Disposition

The gate is won, so R13's block on launch lifts and the plan's stop condition
("never ship a loser") is satisfied. What remains before skill-tuner can be
pinned into the hov marketplace is not measurement:

1. **The dotfiles swap.** R13's promise is that what ships is what the authors
   themselves switched to. The incumbent fork at
   `claude/skills-local/writing-for-agents/` should now be swapped for this
   doctrine in a separate dotfiles PR, per the plan's adjacent-work boundary.
2. **Publication — Will-owned, not automated.** `StartupBros-com/skill-tuner`
   is private with no release tag. hov-marketplace CI has run full
   pinned-source validation unconditionally since 2026-07-14
   (`HOV_SOURCES_PUBLIC` true), so the repo must be public with a resolvable
   `v<version>` tag at the pinned sha before the U7 marketplace PR can go
   green. The public-flip runbook owns this step.
3. **Then U7's marketplace entry**: allowlist case line plus the pinned
   `marketplace.json` row satisfying the validator's six checks, and the F2
   idempotency check after publish.

### Standing caveat for whoever cites these numbers

One run per doctrine. `verify_trials: 3` stabilizes the *verification* of a
finding, but each target's *probe* call is still n=1 — the finding set a
doctrine proposes for a given document is measured once. The 3–3 target split
means a repeat run could plausibly land at parity or narrowly the other way.
Cite this as "won its gate on six documents", never as "finds ~20% more
defects".
