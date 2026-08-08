# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.1857 spent
- verify: 6 trial(s), $0.1464 spent

## Run manifest

- run: `dogfood2-find-animation-opportunities` (2026-08-08T10:43:35Z → 2026-08-08T10:46:04Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/find-animation-opportunities/SKILL.md` | `bdfb8b83dc84` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/find-animation-opportunities/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Completion criteria [craft] — two bounds that contradict (a general ceiling in one place, a specific range crossing it in another) are a completion defect: the agent cannot tell whether a value between them complies.**: The gate states a general ceiling of 'UI under 300ms', but the very table meant to operationalize that ceiling lists Modals/drawers at 200–500ms, which crosses the stated ceiling by up to 200ms. An agent evaluating a 400ms modal animation cannot tell whether it passes (per the table) or fails (per the 300ms ceiling) — exactly the contradictory-bounds defect the doctrine describes.
  - quote: "The suggestion must work within the standard budgets (UI under 300ms):

| Element | Duration |
| --- | --- |
| Press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing / explanatory | Can be longer |"
  - proposed fix: Either raise the stated ceiling to cover the table's max (e.g. 'UI under 500ms, tighter for frequent elements') or cap the modal row at 300ms and move anything longer into the 'Marketing / explanatory' exception explicitly.
- **Completion criteria [craft] — contradictory bounds between a general rule and a specific suggested value elsewhere in the document.**: The Speed gate sets a general ceiling of 'UI under 300ms' for standard UI motion, but this recipe in 'Where to Hunt' prescribes a 2000ms (2s) press animation with no carve-out. Nothing in the Speed section exempts hold-to-confirm interactions, so an agent applying the gate literally would have to reject its own hunt-list recipe, or apply the recipe and silently violate the stated budget.
  - quote: "Destructive actions confirmed with a plain click where a hold-to-confirm fill would prevent slips → `clip-path: inset(0 100% 0 0)` overlay, 2s linear on press, 200ms ease-out snap-back on release"
  - proposed fix: Add an explicit exception to the Speed table for intentional hold/press-and-hold interactions (distinct from the general UI budget), or note next to the hold-to-confirm recipe that its long duration is deliberate and exempt from the 300ms ceiling.
