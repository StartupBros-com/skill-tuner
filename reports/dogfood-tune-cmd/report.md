# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1737 spent
- verify: 6 trial(s), $0.1405 spent

## Run manifest

- run: `dogfood-tune-cmd` (2026-08-08T07:48:05Z → 2026-08-08T07:51:06Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/commands/tune.md` | `e8c70a8306f1` | worktree @ 5d080cf37eb6 |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/commands/tune.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Negation [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available; pair a prohibition with its positive target, and don't lead a rule with the ban alone.**: This bullet leads with two bans back-to-back and never states the positive target (what to do with refuted findings instead — e.g. treat them as closed and move on). Unlike the negations elsewhere in this document (e.g. "Fix the defect, not the sentence containing it" and the 'What you may not claim' section, both of which state the positive instruction first), this one has no positive counterpart anywhere nearby, matching the doctrine's tell for a genuine negation defect.
  - quote: "Do not act on those, and do not re-litigate them."
  - proposed fix: Replace with a positive framing, e.g.: "Treat refuted findings as closed — leave them out of your fix list and your report's 'refuted' section is the only place they belong."
- **Cut identity the body already states [craft] — a pointer restating what the body says about itself adds permanent context load for no routing signal; the pointer's job is when to reach, not what it is.**: This clause in the always-loaded frontmatter description states a property of the tool (how it verifies findings) rather than a trigger for when to reach it, and that same identity is restated in full in the body: "Every finding it reports has already survived three independent skeptics in fresh contexts, plus a code-level check that the quoted text genuinely appears in the document." The description pays permanent load to say what the body already explains at the point it matters.
  - quote: "Adversarially verified — every defect is confirmed by independent skeptics before you act on it."
  - proposed fix: Trim the description to the routing-relevant clause only, e.g. "Find and fix real defects in a skill, AGENTS.md, or CLAUDE.md, then prove the description still routes." and let step 2 of the body carry the adversarial-verification detail alone.
