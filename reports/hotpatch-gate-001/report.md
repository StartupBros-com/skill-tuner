# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $3.9490 spent
- verify: 135 trial(s), $3.0755 spent

## Run manifest

- run: `hotpatch-gate-001` (2026-08-10T22:05:27Z → 2026-08-10T23:02:29Z)
- claude CLI: `2.1.224` | skill-tuner: `0.5.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/.claude/skills/writing-for-agents/SKILL.md` | `ed9b37ec5fc1` | worktree |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `7796547e22c8` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `ecf98ca2b554` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `ccd612736f52` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `5d44a3ae63b7` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `4c9e0d44c9ad` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `0c38fb28b8c5` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `b2391637231c` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `44ea330fdca2` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `042557dd3a8d` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `2365c3c980db` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `58291952bd2a` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `ce0f88ce495c` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `3ca7a75bbacb` | worktree @ 0758c6d4d13e |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `b0da3320d5e6` | worktree @ 0758c6d4d13e |

## Sequential gate verdict

**Sequential: undecided** after 15/15 targets (delta=1, alpha=0.05, sigma0=2)

- fixed-n verdict of record on the 15 collected pairs: **inconclusive** (95% CI [-1.18, -0.02])

| n | target | diff | mean | lambda_margin | lambda_zero | stop |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | agent-swarm | -2 | -2.000 | 0.75 | 0.91 |  |
| 2 | animate | +0 | -1.000 | 0.58 | 0.68 |  |
| 3 | apple-design | -1 | -1.000 | 0.50 | 0.66 |  |
| 4 | automating-your-automations-local | -3 | -1.500 | 0.49 | 1.10 |  |
| 5 | branch-harmonization | +0 | -1.200 | 0.42 | 0.86 |  |
| 6 | brand-voice-builder | -1 | -1.167 | 0.38 | 0.91 |  |
| 7 | browser-console-setup | -1 | -1.143 | 0.36 | 0.96 |  |
| 8 | cass-rerank-local | -1 | -1.125 | 0.34 | 1.03 |  |
| 9 | cli-agent-ergonomics | +0 | -1.000 | 0.32 | 0.87 |  |
| 10 | cli-doctor-mode | -1 | -1.000 | 0.30 | 0.94 |  |
| 11 | codex-consult | -1 | -1.000 | 0.29 | 1.02 |  |
| 12 | curl-bash-installer | +1 | -0.833 | 0.29 | 0.73 |  |
| 13 | de-monolithize-your-codebase-isomorphically-local | +0 | -0.769 | 0.29 | 0.65 |  |
| 14 | emil-design-eng | +1 | -0.643 | 0.32 | 0.51 |  |
| 15 | find-animation-opportunities | +0 | -0.600 | 0.33 | 0.47 |  |
