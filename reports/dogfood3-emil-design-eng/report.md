# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3083 spent
- verify: 6 trial(s), $0.1816 spent

## Run manifest

- run: `dogfood3-emil-design-eng` (2026-08-10T06:49:34Z → 2026-08-10T06:53:02Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/emil-design-eng/SKILL.md` | `289d2526bc05` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/emil-design-eng/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Completion criteria [craft] — 'Two bounds that contradict — a general ceiling in one place, a specific range crossing it in another — are a completion defect in the same family: the agent cannot tell whether a value between them complies, whichever bound it obeys.'**: This blanket 300ms ceiling directly contradicts the duration table two paragraphs above it, which lists 'Modals, drawers | 200-500ms' as the recommended range, and the same contradiction is then codified in the Review Checklist ('Duration > 300ms on UI element | Reduce to 150-250ms'). An agent reviewing a 400ms modal transition (compliant with the modals/drawers row) cannot tell whether it satisfies the doctrine's own rule or violates it — whichever bound it obeys, it appears to break the other.
  - quote: "**Rule: UI animations should stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
  - proposed fix: Scope the ceiling explicitly, e.g. 'Rule: UI animations should stay under 300ms, except modals/drawers which may run up to 500ms and marketing/explanatory animations which have no cap' — or lower the modals/drawers table range to fit under 300ms and drop the exception.

### Refuted findings

- **Single source of truth / duplication [craft] — 'an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror.'** — verifier: This Review Checklist row restates, in Issue/Fix form, the exact same meaning already given positively in the '### Never animate from scale(0)' section ('Start from scale(0.9) or higher, combined with opacity') and again in the Review Format example table ('`transform: scale(0)` | `transform: scale(0.95); opacity: 0`'). The same pattern repeats for `transition: all`, `ease-in`, `transform-origin: center` on popovers, keyboard-action animation, and the transitions-vs-keyframes rule — each stated once as body guidance, once in the Review Format example, and once again in the Review Checklist, tripling maintenance cost and inflating each rule's apparent rank without adding routing or execution value.
  - quote: "| `scale(0)` entry animation                 | Start from `scale(0.95)` with `opacity: 0`                       |"
