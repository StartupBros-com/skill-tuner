# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $0.7862 spent
- verify: 168 trial(s), $1.9658 spent

## Run manifest

- run: `swapgate8-gate-combined` (2026-10-29T10:07:39Z → 2026-10-29T10:32:52Z)
- claude CLI: `2.1.312` | skill-tuner: `0.10.0`
- model pin: `claude-sonnet-5-5` → answered by: `claude-sonnet-5-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/doctrine-gate-68-69/configs/../experiments/doctrine-gate-2026-10-29/candidates/combined.SKILL.md` | `62f3338b8914` | worktree @ c948837d09ed |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0de8b88822ac` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `ecf98ca2b554` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `ccd612736f52` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `5d44a3ae63b7` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `4c9e0d44c9ad` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `acfdd72cf108` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `81a324fa1a17` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `0a247b43b2d1` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `042557dd3a8d` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `e3eb80072a3c` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `d1d441cdbb18` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `58291952bd2a` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `3cc23114e029` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `b8a9c77f0103` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `b0da3320d5e6` | worktree @ 46f806da768b |

## Sequential gate verdict

**Sequential: undecided** after 15/15 targets (delta=1, alpha=0.05, sigma0=2)

- fixed-n verdict of record on the 15 collected pairs: **not_worse** (95% CI [-0.56, +1.09])

| n | target | diff | mean | lambda_margin | lambda_zero | stop |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | agent-swarm | +1 | +1.000 | 0.91 | 0.75 |  |
| 2 | animate | -1 | +0.000 | 0.68 | 0.58 |  |
| 3 | apple-design | +2 | +0.667 | 1.09 | 0.57 |  |
| 4 | automating-your-automations-local | +0 | +0.500 | 1.10 | 0.49 |  |
| 5 | branch-harmonization | -1 | +0.200 | 0.86 | 0.42 |  |
| 6 | brand-voice-builder | +2 | +0.500 | 1.61 | 0.44 |  |
| 7 | browser-console-setup | -2 | +0.143 | 0.96 | 0.36 |  |
| 8 | cass-rerank-local | +3 | +0.500 | 2.46 | 0.42 |  |
| 9 | cli-agent-ergonomics | +1 | +0.556 | 3.66 | 0.43 |  |
| 10 | cli-doctor-mode | +0 | +0.500 | 3.89 | 0.40 |  |
| 11 | codex-consult | +0 | +0.455 | 4.15 | 0.37 |  |
| 12 | curl-bash-installer | -1 | +0.333 | 3.25 | 0.32 |  |
| 13 | de-monolithize-your-codebase-isomorphically-local | +1 | +0.385 | 4.82 | 0.33 |  |
| 14 | emil-design-eng | +1 | +0.429 | 7.24 | 0.35 |  |
| 15 | find-animation-opportunities | -2 | +0.267 | 4.20 | 0.28 |  |
