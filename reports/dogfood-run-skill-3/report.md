# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2713 spent
- verify: 6 trial(s), $0.1188 spent

## Run manifest

- run: `dogfood-run-skill-3` (2026-08-08T07:54:23Z → 2026-08-08T07:57:43Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `51e8ae11841d` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Negation [research] — steer toward the target behaviour instead of leading with the ban; keep prohibition paired with its positive target and never as the unexplained lead.**: The bullet leads with the banned action ("Never tail"), which the doctrine flags as making the forbidden behaviour more available rather than less. The positive target ("Grep the whole capture for ^OK$") is buried at the end instead of leading, so the rule reads as a prohibition-first warning rather than a stated target behaviour.
  - quote: "**Never `tail` the test output.** The suite prints cost estimates to stdout
  while unittest writes its verdict to stderr; the last few interleaved lines
  are usually noise. Grep the whole capture for `^OK$`."
  - proposed fix: Reorder to lead with the target: "**Grep the whole capture for `^OK$`.** The suite prints cost estimates to stdout while unittest writes its verdict to stderr, so tailing the output shows interleaved noise instead of the verdict."
- **Single source of truth [craft] — keep each meaning in one authoritative place so it doesn't need reconciling against a contradicting statement elsewhere.**: The document declares this as the governing convention for every path shown afterward, but the "Test" section's commands (`python3 scripts/check_stdlib_only.py`, `python3 scripts/validate_skillcreator_reader.py`) omit the `skills/skill-tuner/` prefix and don't resolve from the repo root — nor do they match the `cd skills/skill-tuner/scripts` convention set up in "Direct invocation" either. An agent following the stated rule literally hits the exact `ModuleNotFoundError` the Troubleshooting table already anticipates for a different case, because the doc gives two irreconcilable statements about where these two commands must be run from.
  - quote: "All paths below are relative to the repo root."
  - proposed fix: Either prefix the Test section's commands with `skills/skill-tuner/` to match the stated repo-root convention, or state explicitly that the Test section assumes `cd skills/skill-tuner` first.
