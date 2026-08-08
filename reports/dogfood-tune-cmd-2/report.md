# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2193 spent
- verify: 3 trial(s), $0.0704 spent

## Run manifest

- run: `dogfood-tune-cmd-2` (2026-08-08T07:57:43Z → 2026-08-08T08:00:07Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/commands/tune.md` | `8b47d78dcf8e` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 0**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/commands/tune.md
- probe calls: 1
- verify calls: 3 (3 skeptic(s) per finding)
- refuted: 1

### Refuted findings

- **Single source of truth [craft]** — verifier: Step 1 already directs the agent to read the full doctrine at SKILL.md, so by Step 3 the doctrine's rule names are already in context. Restating a subset of them here creates a second place that must be kept in sync if the doctrine renames or adds rules (e.g. this list would silently omit 'co-location' or 'demand' after an update). The doctrine's own caching rule says restating a lookup 'earns its load only when the lookup is expensive' — here the lookup was already paid for one step earlier, so the restatement earns nothing.
  - quote: "The doctrine's rules are the target shape — positive phrasing over prohibition, one trigger per branch, checkable completion bounds, one meaning in one place."
