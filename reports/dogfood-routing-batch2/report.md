# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 68 trial(s), $0.7328 spent
- pruned: 68 trial(s), $0.7361 spent

## Run manifest

- run: `dogfood-routing-batch2` (2026-08-08T09:57:15Z → 2026-08-08T10:03:00Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0dc154c88283` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `a8d1903218b1` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `824fdef96119` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `993984d44b26` | worktree @ a0487393147b (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `b6e7cba9bcb5` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `39f309dee303` | worktree @ a0487393147b (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `c6db47a75b83` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `ce83411bd389` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `e55823e32a45` | worktree @ a0487393147b |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `9ab5c7a6100c` | worktree @ a0487393147b |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `a14d423610c4` | worktree @ a0487393147b |
| distractor | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `277645e3ec2e` | worktree @ a0487393147b |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `3cac571ed3cc` | worktree |
| distractor | `/home/will/.claude/skills/tdd/SKILL.md` | `5e6b9c16b547` | worktree |
| distractor | `/home/will/.claude/skills/ui-polish/SKILL.md` | `60debbc2299a` | worktree |

## Routing-parity verdict

**Verdict: refuse**

- original: accuracy 57/68 (83.8%), near-miss rejection 8/8 (100.0%)
- pruned: accuracy 56/68 (82.4%), near-miss rejection 8/8 (100.0%)

Failing case ids: agent-swarm__paraphrase__1, cass-rerank-local__obvious__2, de-monolithize-your-codebase-isomorphically-local__paraphrase__1, emil-design-eng__obvious__1, emil-design-eng__obvious__2, emil-design-eng__paraphrase__1
