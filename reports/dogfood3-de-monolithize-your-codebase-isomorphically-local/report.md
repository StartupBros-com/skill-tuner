# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3885 spent
- verify: 12 trial(s), $0.6001 spent

## Run manifest

- run: `dogfood3-de-monolithize-your-codebase-isomorphically-local` (2026-08-10T06:43:14Z → 2026-08-10T06:49:34Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `f9b2e20ec909` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 2

### Confirmed findings

- **Relevance and sediment [craft] (Pruning and drift) — a line loses relevance by going stale as the document changes; the cure is a pruning discipline, not letting sediment pile up.**: The TOC has gone stale relative to the actual headers: it lists "Rubric" as a section, but no header by that name exists (the actual section is "Decomposition Design (Phase 8)", which merely mentions a rubric in its body text), and it omits the "Self-Test" header that closes the document. A reader using the TOC as a navigation pointer is misled on both counts.
  - quote: "<!-- TOC: One Rule | First-30-Seconds | Quick-Start | Confirmations | Bootstrap | Phases | Parallelism | Convergence | Operators | Taxonomy | Contract | Rubric | GitHub Issues | Anti-Patterns | Checklist | Reference Index -->"
  - proposed fix: Replace "Rubric" with "Decomposition Design" (matching the actual header) and append "Self-Test" to the TOC list.
- **Demand [craft] (Steps, completion, and demand) — "watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically."**: "preserve every feature" is checkable (diffable against the plan's feature list), but "the plan's full level of detail" is a judgment call with no way to tell done from not-done, letting the whole polish bound be satisfied impressionistically.
  - quote: "Polish 4–5 rounds against the same standard as the plan itself — preserve every feature and the plan's full level of detail in each pass."
  - proposed fix: Replace "the plan's full level of detail" with a checkable proxy, e.g. "the same section count and per-issue field list (migration mechanics, proof-gate dependency, docs dependency) as the plan."

### Refuted findings

- **Duplication [craft] (Pruning and drift) — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: This anti-pattern row (and several neighbors, e.g. "Split along visual sections" vs. the One Rule's "never aesthetically," and "Drop a re-export..." vs. the façade requirement) is the negated restatement of a rule the document already states positively — "one mechanical move per commit" appears verbatim in the Phase Loop table and again in Decomposition Design. The anti-pattern table pays the same meaning a third time.
  - quote: "| Extract + rename + reformat in one commit | Kills `git blame` and reviewability; one mechanical move per commit |"
- **Single source of truth / Duplication [craft] (Pruning and drift) — keep each meaning in one authoritative place so changing the behaviour is a one-place edit; duplication inflates a meaning's rank on the ladder past its real importance.** — verifier: The full convergence definition (≥10 rounds, <3 new findings, DEFERRED+rationale, 2 consecutive quiet rounds) is restated near-verbatim in four places: the Quick-Start block, this Convergence section, the ABORT IF list, and the Pre-Flight & End Checklist. Any future change to the numeric floor requires editing all four in lockstep or the copies drift out of sync.
  - quote: "A round is **quiet** when every registry entry has verdict ≠ OPEN/NEEDS_REFINEMENT and the round's
genuinely-new-findings count is <3. Converged = two consecutive quiet rounds AND ≥10 total rounds
AND zero unresolved hypotheses (DEFERRED requires written rationale plus `Deferred reviewed: yes`)."
