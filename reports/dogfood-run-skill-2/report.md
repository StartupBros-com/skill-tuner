# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1928 spent
- verify: 3 trial(s), $0.0772 spent

## Run manifest

- run: `dogfood-run-skill-2` (2026-08-08T07:52:08Z → 2026-08-08T07:53:59Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `61a5c78fa4aa` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 1
- verify calls: 3 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **One trigger per branch [craft]**: The description encodes the same branch multiple times under different wording. 'Run' and 'drive' both mean 'operate the CLI' and route to the same material (there is no body section that treats 'driving' differently from 'running'). Separately, 'smoke-test' and 'check that the CLI still works after a change' name the identical action — the smoke.sh script literally is the CLI-still-works check described in the 'Run (agent path)' section. Per the doctrine, synonyms that rename a single branch are one branch written twice and pay context-load cost on every turn without adding routing signal.
  - quote: "description: Run, drive, smoke-test and debug skill-tuner. Use when asked to run skill-tuner, probe a document, compare two runs, verify a banked run, or check that the CLI still works after a change."
  - proposed fix: Collapse the duplicate triggers: 'Run, smoke-test, and debug skill-tuner. Use when asked to run skill-tuner, probe a document, compare two runs, or verify a banked run.' This keeps one phrase per distinct branch (generic run, probe, compare, verify, debug) and drops the redundant 'drive' and 'check that the CLI still works after a change'.
