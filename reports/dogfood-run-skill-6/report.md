# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.4322 spent
- verify: 3 trial(s), $0.1403 spent

## Run manifest

- run: `dogfood-run-skill-6` (2026-08-08T08:11:04Z → 2026-08-08T08:15:25Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ 5d080cf37eb6 (dirty) |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `59bbdc4f0d6e` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 1
- verify calls: 3 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Co-location [craft] — keep a concept's definition, rules, and caveats under one heading, so reading one part brings its neighbours. Spot it by asking whether applying a rule correctly requires having read a different section.**: This is the canonical usage example for `verify`, but the fact that a normal DRIFTED result exits 1 — and that a wrapper must treat 'produced a verdict' as success — is stated only later, in the Gotchas section. An agent that copies this example into a script (e.g. under `set -e`, or checking `$?` / `&&`) would treat a healthy DRIFTED verdict as a crash, which is exactly the misinterpretation the Gotchas bullet warns against. Correctly using the command shown here requires having already read a different, non-adjacent section.
  - quote: "Judge two banked runs, or re-check one for drift — both free:

```bash
python3 skills/skill-tuner/scripts/tune.py compare \
  --baseline swapgate3-probe-incumbent \
  --candidate swapgate5-probe-doctrine-v2 --exclude design-drift

python3 skills/skill-tuner/scripts/tune.py verify swapgate5-probe-doctrine-v2
```"
  - proposed fix: Add the exit-code caveat right at the point of use, e.g. append '`verify` exits 1 on DRIFTED — that is a verdict, not a failure; treat any verdict as success' immediately after the verify example in Direct invocation, instead of leaving it only in Gotchas.
