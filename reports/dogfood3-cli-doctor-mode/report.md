# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1816 spent
- verify: 6 trial(s), $0.2084 spent

## Run manifest

- run: `dogfood3-cli-doctor-mode` (2026-08-10T06:40:24Z → 2026-08-10T06:43:14Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/cli-doctor-mode/SKILL.md` | `b3d49f5611e9` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/cli-doctor-mode/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Completion criteria — "a bound is checkable when the agent can tell done from not-done without judgment."**: "the project's floor" is never defined anywhere in the document — no numeric threshold, score cutoff, or reference is given for the 10 dimensions. The agent cannot tell, without judgment, whether a given score for a dimension clears the undefined floor, so this iteration-ending condition is not checkable.
  - quote: "repeat until every FM clears the project's floor on each, then re-mine failure modes on the next material code change (no doctor is ever "done")"
  - proposed fix: Define the floor explicitly, e.g. 'repeat until every FM scores at least N/10 on each dimension (see DOCTOR-SPEC.md for the scoring rubric)', or point to a concrete threshold defined in DOCTOR-SPEC.md.

### Refuted findings

- **Pruning and drift — Duplication (polarity disguise): "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: Every bullet here is a negated restatement of a rule the body already states positively: 'Fix-then-detect' duplicates 'Detect-then-fix, never fix-then-detect' (The One Rule) and the mutate()-chokepoint definition; 'Backups that reformat' duplicates 'Backups are verbatim. No reformatting...' in the safety envelope; 'DeletePath/rm -rf/...' duplicates 'The Op enum has NO DeletePath' and 'Never rm -rf, git reset --hard, or DROP TABLE'; 'ad-hoc exit codes' duplicates 'a documented, additive-only dictionary — never ad-hoc'; and the cross-filesystem-rename bullet is nearly verbatim identical to the mutate() step-6 note 'Cross-FS rename is NOT atomic — the temp file must be on the same filesystem as the target.' This is the same meaning written twice (or more), costing tokens and maintenance and inflating these rules' apparent importance beyond a single authoritative statement.
  - quote: "## Anti-patterns

- **Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it.
- **Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently.
- **`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead.
- **Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract.
- **Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
