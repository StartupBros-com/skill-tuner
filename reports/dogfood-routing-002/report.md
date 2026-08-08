# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 20 trial(s), $0.1651 spent
- pruned: 20 trial(s), $0.2132 spent

## Run manifest

- run: `dogfood-routing-002` (2026-08-08T08:16:10Z → 2026-08-08T08:17:36Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/SITES/skill-tuner/.claude/skills/run-skill-tuner/SKILL.md` | `970bcba28e0d` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/commands/tune.md` | `e8c70a8306f1` | worktree @ 5d080cf37eb6 |
| distractor | `/home/will/.claude/skills/writing-for-agents/SKILL.md` | `a61475f4549b` | worktree |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `a14d423610c4` | worktree @ 77e155f9b4ff |
| distractor | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `277645e3ec2e` | worktree @ 77e155f9b4ff |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `291233457df4` | worktree @ 77e155f9b4ff |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `3cac571ed3cc` | worktree |

## Routing-parity verdict

**Verdict: land**

- original: accuracy 20/20 (100.0%), near-miss rejection 8/8 (100.0%)
- pruned: accuracy 20/20 (100.0%), near-miss rejection 8/8 (100.0%)
