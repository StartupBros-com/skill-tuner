# skill-tuner eval report

Conditions compared: **original** vs **pruned**.

- original: 52 trial(s), $0.2921 spent
- pruned: 52 trial(s), $0.2890 spent

## Run manifest

- run: `trigger-improving-routing` (2026-10-29T17:51:26Z → 2026-10-29T17:58:05Z)
- claude CLI: `2.1.312` | skill-tuner: `0.10.0`
- model pin: `claude-sonnet-5-5` → answered by: `unrecorded`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/trigger-improving/configs/../skills/skill-tuner/SKILL.md` | `62f3338b8914` | worktree @ 6b001fb97404 |
| distractor | `/home/will/.claude/skills/de-slopify/SKILL.md` | `4012476af8a4` | worktree |
| distractor | `/home/will/.claude/skills/readme-writing/SKILL.md` | `3099296a8c7f` | worktree |
| distractor | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `339fe7f6d2aa` | worktree @ 46f806da768b |
| distractor | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `e3eb80072a3c` | worktree @ 46f806da768b |
| distractor | `/home/will/.claude/skills/tdd/SKILL.md` | `5505d25bbaa8` | worktree |
| distractor | `/home/will/.claude/plugins/cache/claude-plugins-official/skill-creator/f8c5e7a1dcb7/skills/skill-creator/SKILL.md` | `dcd4803e61e9` | worktree |
| battery | `/home/will/SITES/skill-tuner/.claude/worktrees/trigger-improving/configs/trigger-improving-routing-battery.json` | `8f379de06688` | worktree @ 6b001fb97404 |

## Routing-parity verdict

**Verdict: land**

- original: accuracy 49/52 (94.2%), near-miss rejection 32/32 (100.0%)
- pruned: accuracy 52/52 (100.0%), near-miss rejection 32/32 (100.0%)
- discordant trials: pruned lost 0, gained 3; exact two-sided p=0.250 — a refuse with p near 1 is indistinguishable from routing noise at this trial count
