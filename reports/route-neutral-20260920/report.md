# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 26 trial(s), $0.2029 spent
- pruned: 26 trial(s), $0.1657 spent

## Run manifest

- run: `route-neutral-20260920` (2026-09-20T21:23:44Z → 2026-09-20T21:25:58Z)
- claude CLI: `2.1.278` | skill-tuner: `0.9.0`
- model pin: `claude-sonnet-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/dotfiles/claude/skills-local/stash-mining/SKILL.md` | `9d877fc45769` | worktree @ ff0a5f8808f2 |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `81a324fa1a17` | worktree @ ff0a5f8808f2 |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `ca9e6832a361` | worktree @ ff0a5f8808f2 |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `4012476af8a4` | worktree |
| distractor | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `339fe7f6d2aa` | worktree @ ff0a5f8808f2 |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `2365c3c980db` | worktree @ ff0a5f8808f2 |
| distractor | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `4c9e0d44c9ad` | worktree @ ff0a5f8808f2 |
| distractor | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `009876ab5045` | worktree @ ff0a5f8808f2 |

## Routing-parity verdict

**Verdict: refuse**

- original: accuracy 26/26 (100.0%), near-miss rejection 8/8 (100.0%)
- pruned: accuracy 23/26 (88.5%), near-miss rejection 8/8 (100.0%)
- discordant trials: pruned lost 3, gained 0; exact two-sided p=0.250 — a refuse with p near 1 is indistinguishable from routing noise at this trial count

Failing case ids: agent-swarm__obvious__1, agent-swarm__obvious__2
