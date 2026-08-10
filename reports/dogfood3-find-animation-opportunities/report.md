# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2720 spent
- verify: 12 trial(s), $0.2506 spent

## Run manifest

- run: `dogfood3-find-animation-opportunities` (2026-08-10T06:53:02Z → 2026-08-10T06:56:29Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/find-animation-opportunities/SKILL.md` | `bdfb8b83dc84` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/find-animation-opportunities/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 3

### Confirmed findings

- **Completion criteria — contradicting bounds (a general ceiling in one place, a specific range crossing it in another)**: The gate states a general ceiling of "under 300ms" for UI, but the table immediately below it gives modals/drawers a range of 200–500ms, which crosses that ceiling. The agent cannot tell whether a 400ms modal transition complies with the gate — it satisfies the table row but violates the stated ceiling, whichever bound it obeys.
  - quote: "The suggestion must work within the standard budgets (UI under 300ms):

| Element | Duration |
| --- | --- |
| Press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing / explanatory | Can be longer |"
  - proposed fix: Remove the blanket "UI under 300ms" framing, or explicitly carve out modals/drawers as an exception the way marketing/explanatory already is, e.g. "UI under 300ms, except modals/drawers (200–500ms) and marketing/explanatory (can be longer)."

### Refuted findings

- **Demand — criteria that mix checkable and uncheckable terms let the agent satisfy the whole thing impressionistically** — verifier: "At most 5–7" is a checkable numeric cap, but "fewer for a single view" is an uncheckable qualifier with no number attached. The agent can claim compliance with any count it likes for a single-view sweep since there is no bound to fail.
  - quote: "At most 5–7 suggestions for a whole app, fewer for a single view."
- **Cut identity the body already states — a pointer restating what the body says about itself adds permanent context load for no routing signal** — verifier: This identity clause in the description is restated almost immediately by the body's opening lines ("A search skill. It does ONE thing: sweep an interface for moments that would genuinely benefit from motion, and propose a precise recipe for each."). The description's job is to signal when to reach the skill, not to restate what it is a second time.
  - quote: "Search a codebase or UI for places that don't animate but should, and reject everything that shouldn't."
- **One trigger per branch — synonyms that rename a single branch are one branch written twice** — verifier: Both phrases route to the exact same branch (find animation opportunities); a run reaching the skill through one phrase would take the identical path as one reaching it through the other. This is a synonym pair paying twice for one route.
  - quote: "Use when the user asks "what could be animated here?" or wants to "make this feel more alive"."
