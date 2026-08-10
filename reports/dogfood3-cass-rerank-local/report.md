# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1667 spent
- verify: 9 trial(s), $0.1456 spent

## Run manifest

- run: `dogfood3-cass-rerank-local` (2026-08-10T06:33:15Z → 2026-08-10T06:35:45Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `443f9d904aa4` | worktree @ 0eff27fb00ae (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- probe calls: 1
- verify calls: 9 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Duplication / single source of truth [craft]**: The routing decision (top-1/few → cass-rerank, broad scan → plain cass) is stated in the always-loaded description and then restated in the body's 'When to use which' table ('"Find the ONE session where I solved X" (top-1 matters)' → cass-rerank; 'Broad keyword scan, many hits' → plain cass). Same meaning lives in two places, so an edit to one (e.g. changing the threshold for when to fall back) can drift from the other.
  - quote: "Use INSTEAD of bare `cass search` for top-1/top-few
  relevant-session results (past fixes, decisions, "how did I do X"); fall
  back to plain cass for broad scans."
  - proposed fix: Keep the routing decision only in the table (body reference) and shorten the description to name what the skill is and the single condition to reach it, e.g. 'Use for finding a specific past session (top-1 relevance); see table below for other cass tools.'
- **Progressive disclosure [craft]**: This section (status-check command, phase-stall diagnosis, the full env-var repair invocation, timing/RSS figures) is reference material for a narrow, rare failure branch (a stalled/interrupted index rebuild), yet it sits inline in the main skill body alongside the everyday 'Use it' steps. It is loaded on every invocation of the skill regardless of whether the failure occurs, and its length and density (specific env vars, magic numbers like `planned_shards≈317`, RSS thresholds) make it exactly the kind of branch-only detail the doctrine says to disclose rather than inline.
  - quote: "## If it returns "no results" for everything

That usually means the **lexical index is broken**, not that nothing matched. Check first:"
  - proposed fix: Move the index-repair procedure to a separate reference file (e.g. `cass-index-repair.md`) and leave a short in-file pointer: 'If cass-rerank returns no results for everything, the lexical index may be broken — see cass-index-repair.md for the fix.'

### Refuted findings

- **One trigger per branch [craft]** — verifier: Three parenthetical phrases are offered for a single branch (top-1/top-few relevant-session lookup). A query phrased as a 'past fix', a 'decision', or 'how did I do X' all route to the exact same behavior — per the doctrine's test, none of these phrases sends the agent down a different path than the one beside it, so they are one branch written three times, paying context-load three times for one routing decision.
  - quote: "(past fixes, decisions, "how did I do X")"
