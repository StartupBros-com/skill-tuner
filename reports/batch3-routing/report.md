# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 38 trial(s), $0.3464 spent
- pruned: 38 trial(s), $0.2590 spent

## Run manifest

- run: `batch3-routing` (2026-08-11T00:52:09Z → 2026-08-11T00:58:39Z)
- claude CLI: `2.1.224` | skill-tuner: `0.7.0`
- model pin: `claude-sonnet-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/dotfiles/claude/skills-local/kill-ai-slop/SKILL.md` | `0979bb273dbe` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/memory-mine/SKILL.md` | `836b0a2e55ce` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/review-animations/SKILL.md` | `61cf8ac0c4c8` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/ssh-local/SKILL.md` | `5af00e3203d8` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/verify-review/SKILL.md` | `f17a0d10cfe6` | worktree @ cf3033257c8f (dirty) |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `2365c3c980db` | worktree @ cf3033257c8f |
| distractor | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `58291952bd2a` | worktree @ cf3033257c8f |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `3cac571ed3cc` | worktree |
| distractor | `/home/will/.claude/skills/tdd/SKILL.md` | `5e6b9c16b547` | worktree |
| distractor | `/home/will/.claude/skills/ui-polish/SKILL.md` | `60debbc2299a` | worktree |

## Routing-parity verdict

**Verdict: land**

- original: accuracy 38/38 (100.0%), near-miss rejection 8/8 (100.0%)
- pruned: accuracy 38/38 (100.0%), near-miss rejection 8/8 (100.0%)
