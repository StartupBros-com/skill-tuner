# Swap-gate evaluation (R13, UNIT U7)

> **SUPERSEDED by [`swapgate2-summary.md`](swapgate2-summary.md), which records
> the gate as WON.** Two defects invalidate the leg (a) result below. The
> quote-existence guard compared a model-reproduced quote to the target with a
> raw substring test, so it downgraded the candidate's one verifier-CONFIRMED
> finding for dropping a markdown blockquote marker — the candidate's true
> score on this run is 1, not 0. And a single target document decided a
> count-based launch gate, which this file already flagged as too thin. The
> six-target re-run reverses the sign: candidate 11, incumbent 9. Kept
> unedited below as the original record.

Gate: skill-tuner replaces the incumbent `writing-for-agents` fork only if it
scores equal-or-better than the incumbent on both legs below, on the same
pipeline. Model pin: `claude-sonnet-5`. Auth mode: api-key (budget-capped at
`--budget-usd 5` per run).

## Verdict: **LOST**

Leg (a) probe comparison failed: the candidate doctrine confirmed fewer
findings than the incumbent on the same target document. Per the gate rule,
WON requires both legs to pass; one failing leg is sufficient to block the
swap. This is recorded as measured, not adjusted — no prompts or configs were
changed to force a different outcome.

---

## Leg (a): Probe comparison

Same target document (`browser-console-setup/SKILL.md`, previously
unprocessed by either doctrine), same model, doctrine swapped between runs.

| Run-id | Doctrine | findings_confirmed | refuted | probe calls | verify calls | cost (USD) |
| --- | --- | --- | --- | --- | --- | --- |
| `swapgate-probe-incumbent` | `/home/will/dotfiles/claude/skills-local/writing-for-agents/SKILL.md` | **2** | 1 | 1 | 3 | $0.2918 |
| `swapgate-probe-candidate` | `/home/will/SITES/skill-tuner/skills/skill-tuner/SKILL.md` | **0** | 2 | 1 | 2 | $0.2852 |

Gate rule: candidate passes if `findings_confirmed(candidate) >= findings_confirmed(incumbent)`.
0 >= 2 is false. **Leg (a): FAIL.**

Incumbent's 2 confirmed findings on `browser-console-setup/SKILL.md`:
1. Single-source-of-truth duplication between the "Critical rules" bullets and
   two rows of the "Anti-patterns" table (query-params rule, exact-click-text
   rule stated twice).
2. A vague completion criterion on workflow step 6 ("Verify (re-read the
   config via API)") that doesn't state what "verified" means.

Candidate's probe call raised 2 candidate findings on the same document; both
were refuted by the skeptical verifier (0 confirmed).

## Leg (b): Routing comparison

Run-id `swapgate-routing-001`. Single target = the doctrine skill itself:
`original` description = incumbent's frontmatter description (read from
`writing-for-agents/SKILL.md`), `pruned` description = skill-tuner's
frontmatter description. 5 distractors (de-slopify, repo-junk-triage,
cli-doctor-mode, branch-harmonization, cass-rerank-local), 8-prompt
hand-authored battery (4 should-fire, 2 near-miss, 2 none-of-the-above),
2 trials per condition = 16 router calls per condition, 32 total.

| Condition (skill description) | Accuracy | Near-miss rejection |
| --- | --- | --- |
| `original` (incumbent: "Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.") | 16/16 (100.0%) | 8/8 (100.0%) |
| `pruned` (candidate: "Evidence-tagged rules for writing documents agents consume. Use when creating or editing skills, AGENTS.md, or CLAUDE.md.") | 16/16 (100.0%) | 8/8 (100.0%) |

Verdict (`routing_parity.determine_verdict`): **land**. failing_case_ids: none.

Gate rule: candidate passes if pruned accuracy >= original accuracy (and it
does on both overall and near-miss). **Leg (b): PASS.**

---

## Totals

- Total live `claude -p` calls: 4 (probe-incumbent) + 3 (probe-candidate) + 32 (routing) = **39**
- Total cost: $0.2918 + $0.2852 + $0.2736 = **$0.8506**
- Run-ids: `swapgate-probe-incumbent`, `swapgate-probe-candidate`, `swapgate-routing-001`
- Configs: `configs/swapgate-probe-incumbent.json`, `configs/swapgate-probe-candidate.json`,
  `configs/swapgate-routing-001.json`, `configs/swapgate-routing-battery.json`
- Reports: `reports/swapgate-probe-incumbent/`, `reports/swapgate-probe-candidate/`,
  `reports/swapgate-routing-001/`

## Disposition

Gate LOST blocks the swap per plan. skill-tuner does not replace
`writing-for-agents` as the incumbent doctrine on this measurement. The
routing leg shows the pruned description routes at full parity, so the
description-pruning work itself is sound; the shortfall is specifically in
probe-leg defect-finding yield on this one target document. Candidates for a
re-run: a different/larger target sample (n=1 target is a thin sample for a
count-based gate), or inspecting why the candidate doctrine's two raised
findings were refuted (worth a manual read of `reports/swapgate-probe-candidate/trials.jsonl`)
before concluding the doctrine itself under-finds.
