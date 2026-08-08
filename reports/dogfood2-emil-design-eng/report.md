# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2499 spent
- verify: 12 trial(s), $0.2839 spent

## Run manifest

- run: `dogfood2-emil-design-eng` (2026-08-08T10:40:11Z → 2026-08-08T10:43:34Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/emil-design-eng/SKILL.md` | `0aecd2c248db` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/emil-design-eng/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 2

### Confirmed findings

- **Completion criteria — contradicting bounds (a general ceiling in one place, a specific range crossing it in another)**: This general ceiling directly contradicts the duration table just above it, which lists 'Modals, drawers | 200-500ms' — a range that crosses the 300ms ceiling — and is reinforced by later code examples using 400ms transitions for toasts/@starting-style. The agent has no way to tell whether a 350ms modal transition complies, since one bound says yes and the other says no.
  - quote: "**Rule: UI animations should stay under 300ms.**"
  - proposed fix: Either exempt modals/drawers explicitly from the 300ms rule ('UI animations should stay under 300ms, except modals and drawers which may run up to 500ms') or tighten the table's modal/drawer range to stay within 300ms.
- **Single source of truth / duplication (same meaning repeated in two places)**: The Review Checklist table at the end duplicates rows already given verbatim (same rule, same before/after values) in the Review Format example table earlier ('`ease-in` on dropdown | `ease-out` with custom curve | ...'), as well as the scale(0), transform-origin, and transition:all rows. Each of these rules now lives in two places, so a future edit to one (e.g., changing the recommended duration range) risks drifting from the other.
  - quote: "| `ease-in` on UI element                     | Switch to `ease-out` or custom curve                              |"
  - proposed fix: Keep one canonical table (the Review Format example) and have the Review Checklist reference it by section name instead of re-listing the same before/after pairs, or merge the two tables into one.

### Refuted findings

- **Duplication — polarity (an anti-pattern restatement of a rule the document already gives positively)** — verifier: The prohibition immediately restates, negated, the rule already stated positively in the same sentence, and the document then reinforces it a third time by rendering a full 'Wrong format (never do this)' code block showing the actual banned list layout — dragging the forbidden pattern into context rather than stating only the target behavior.
  - quote: "You MUST use a markdown table with Before/After columns. Do NOT use a list with "Before:" and "After:" on separate lines."
- **Progressive disclosure / Sprawl (inline what every branch needs; disclose what only some branches reach)** — verifier: Deep, branch-specific reference material — spring physics configuration, clip-path techniques (tabs, hold-to-delete, comparison sliders), and drag/gesture momentum math — is inlined at the top level of a skill invoked broadly for any 'UI polish pass.' A review of a static button's hover state pays the context cost of loading spring damping constants, clip-path inset formulas, and pointer-capture drag code that branch never touches.
  - quote: "## Spring Animations"
