# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 2 trial(s), $0.6099 spent
- verify: 3 trial(s), $0.0386 spent

## Run manifest

- run: `dogfood-run-skill-7` (2026-08-08T08:16:08Z → 2026-08-08T08:21:46Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ 5d080cf37eb6 (dirty) |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `a6a6fef7604a` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 2
- verify calls: 3 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Single source of truth [craft]**: The same meaning (run the unit suite from skills/skill-tuner/scripts because tests import sibling modules by bare name) is restated almost verbatim in the Troubleshooting table row for ModuleNotFoundError ('Run `cd skills/skill-tuner/scripts` first; the tests import sibling modules by bare name.'). The doctrine requires each meaning live in one authoritative place so a behavior change is a one-place edit; the document itself demonstrates the correct alternative elsewhere ('The unit suite runs from `skills/skill-tuner/scripts` as shown under "Direct invocation"' in the Test section), showing the duplication here was avoidable.
  - quote: "Run **from that directory** — the tests import sibling modules by bare name."
  - proposed fix: Replace the Troubleshooting row's explanation with a cross-reference, e.g. 'Run from `skills/skill-tuner/scripts` — see "Direct invocation" above.' instead of restating the sibling-import rationale.
