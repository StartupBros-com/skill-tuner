# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 48 trial(s), $0.2849 spent
- pruned: 48 trial(s), $0.2802 spent

## Run manifest

- run: `swapgate8-routing-desc` (2026-10-29T09:28:04Z → 2026-10-29T09:35:36Z)
- claude CLI: `2.1.312` | skill-tuner: `0.10.0`
- model pin: `claude-sonnet-5-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/doctrine-gate-68-69/configs/../skills/skill-tuner/SKILL.md` | `8b5cc479b9bd` | worktree @ f03f30515d2a |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `4012476af8a4` | worktree |
| distractor | `/home/will/.claude/skills/readme-writing/SKILL.md` | `3099296a8c7f` | worktree |
| distractor | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `339fe7f6d2aa` | worktree @ 46f806da768b |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `e3eb80072a3c` | worktree @ 46f806da768b |
| distractor | `/home/will/.claude/skills/tdd/SKILL.md` | `5505d25bbaa8` | worktree |
| battery | `/home/will/SITES/skill-tuner/.claude/worktrees/doctrine-gate-68-69/configs/swapgate8-routing-battery.json` | `1c72256a53aa` | worktree @ f03f30515d2a |

## Routing-parity verdict

**Verdict: land**

- original: accuracy 48/48 (100.0%), near-miss rejection 28/28 (100.0%)
- pruned: accuracy 48/48 (100.0%), near-miss rejection 28/28 (100.0%)
