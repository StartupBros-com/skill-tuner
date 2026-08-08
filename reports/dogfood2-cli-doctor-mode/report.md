# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2594 spent
- verify: 9 trial(s), $0.1928 spent

## Run manifest

- run: `dogfood2-cli-doctor-mode` (2026-08-08T10:31:11Z → 2026-08-08T10:34:30Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/cli-doctor-mode/SKILL.md` | `eb3c65796050` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/cli-doctor-mode/SKILL.md
- probe calls: 1
- verify calls: 9 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Completion criteria — "a bound is checkable when the agent can tell done from not-done without judgment."**: "the project's floor" is never defined anywhere in the document or in the DOCTOR-SPEC.md pointer (which is cited only for the 10 dimensions' descriptions, not for a threshold value). The loop's own exit condition is therefore unjudgeable — the agent cannot tell whether a given score clears the floor without inventing a number.
  - quote: "repeat until every FM clears the project's floor on each, then re-mine failure modes on the next material code change (no doctor is ever "done")"
  - proposed fix: Either state a concrete floor (e.g. "score ≥ 7/10 on every dimension") or explicitly point to where the floor is set (e.g. "the floor recorded in `.doctor/floor.json`, or 7/10 if none is set").
- **Relevance and sediment — "every line must still bear on what the document does... without a pruning discipline the default fate is sediment."**: This is a changelog about the document's own editing history (what was kept/dropped from a predecessor skill). It costs context load on every load of the file but does not bear on the task of adding or upgrading a doctor subcommand — it tells the agent nothing about how to do the work.
  - quote: "Distilled 2026-07-04 from the retired 166-file `world-class-doctor-mode-for-cli-tools` skill:
     kept the One Rule + core axioms, the CLI surface, the mutate() chokepoint / safety envelope,
     the (detector,fixer,fixture,test) tuple, the 10-dim rubric, and the portable cookbook. Dropped
     the multi-model swarm tiers, session-mining, external issue-tracker plumbing, the per-run 0-1000
     scoring machinery, 18 subagents, and 39 scripts."
  - proposed fix: Move this provenance note to the commit message or a CHANGELOG, keeping only the still-live pointer ("JSON shapes + rubric + cookbook: references/DOCTOR-SPEC.md") in the file.

### Refuted findings

- **Single source of truth / duplication (Pruning and drift) — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: These Anti-patterns bullets are the negated restatement of rules the document already states positively elsewhere: "Detect-then-fix, never fix-then-detect" and "Detectors READ; fixers MUTATE only by calling `mutate()`" (already given twice), "Backups are verbatim. No reformatting, no 'clean up while I'm here'" (safety envelope), and the content-derived-id / documented-exit-code-dictionary / `--online` opt-in rules stated earlier in their own sections. This is the exact disguised-duplication pattern the doctrine calls out — same meaning in more than one place, costing maintenance (a rule change now requires editing two places) and inflating the anti-pattern list's apparent importance.
  - quote: "- **Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it.
- **Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently.
- **Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract."
