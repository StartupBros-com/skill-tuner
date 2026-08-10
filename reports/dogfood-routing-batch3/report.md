# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 44 trial(s), $0.5042 spent
- pruned: 44 trial(s), $0.4313 spent

## Run manifest

- run: `dogfood-routing-batch3` (2026-08-10T06:15:01Z → 2026-08-10T06:25:40Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/.claude/skills/agent-swarm/SKILL.md` | `2f83bb7c6e55` | worktree |
| target | `/home/will/.claude/skills/brand-voice-builder/SKILL.md` | `f86cf23af688` | worktree @ 0492e1e9e5f2 (dirty) |
| target | `/home/will/.claude/skills/browser-console-setup/SKILL.md` | `ea01d618edcc` | worktree |
| target | `/home/will/.claude/skills/cass-rerank-local/SKILL.md` | `443f9d904aa4` | worktree @ 0492e1e9e5f2 (dirty) |
| target | `/home/will/.claude/skills/curl-bash-installer/SKILL.md` | `a45f84a6944d` | worktree |
| target | `/home/will/.claude/skills/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `543ec33dce28` | worktree |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `b3d49f5611e9` | worktree @ 0492e1e9e5f2 |
| distractor | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `277645e3ec2e` | worktree @ 0492e1e9e5f2 |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `3cac571ed3cc` | worktree |
| distractor | `/home/will/.claude/skills/tdd/SKILL.md` | `5e6b9c16b547` | worktree |
| distractor | `/home/will/.claude/skills/ui-polish/SKILL.md` | `60debbc2299a` | worktree |

## Routing-parity verdict

**Verdict: land**

- original: accuracy 42/44 (95.5%), near-miss rejection 8/8 (100.0%)
- pruned: accuracy 42/44 (95.5%), near-miss rejection 8/8 (100.0%)
