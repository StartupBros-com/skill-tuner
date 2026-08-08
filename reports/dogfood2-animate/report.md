# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2711 spent
- verify: 6 trial(s), $0.1899 spent

## Run manifest

- run: `dogfood2-animate` (2026-08-08T10:46:04Z → 2026-08-08T10:49:17Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/animate/SKILL.md` | `a7960e3c584c` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 0**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/animate/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 2

### Refuted findings

- **Completion criteria [craft] — "Two bounds that contradict — a general ceiling in one place, a specific range crossing it in another — are a completion defect... the agent cannot tell whether a value between them complies, whichever bound it obeys."** — verifier: The duration table gives modals/drawers a range up to 500ms, and the very next line states a blanket ceiling of 300ms for "UI animations" with no qualifier. Within this section there is nothing telling the agent that modals/drawers (and marketing) are exempt from the 300ms ceiling — that exemption only appears later, in the separate Never Ship table ("UI duration over 300ms outside modals/drawers or marketing"). An agent reading only the Duration section cannot tell whether a 400ms modal transition complies.
  - quote: "| Modals, drawers | 200–500ms |
| Marketing / explanatory | Can be longer |

**UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
- **Single source of truth / Duplication [craft] — "Duplication wears disguises, and the commonest is polarity: an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: The "Never Ship" table restates, in negated/paired form, rules the document already gives positively elsewhere: this row mirrors "**Never `ease-in` on UI.** It starts slow, delaying the exact moment the user is watching" in the Easing section. The same pattern repeats across most of the table — "transform: scale(0) entrance" mirrors the section 4 scale(0) rule, "Animation on a keyboard shortcut or 100+/day action" mirrors the step-1 frequency table, "Ungated :hover motion" mirrors step 7, "Missing prefers-reduced-motion" mirrors step 7, "Keyframes on toasts..." mirrors step 6, "Animating width/height/margin/padding/top/left" and "Motion x/y/scale props under load" mirror section 4. Each meaning now lives in two places, so a future change to one of these rules (e.g. loosening the scale-entrance floor from 0.9–0.97, which the table already independently states as a single value 0.95) requires editing both and risks the two drifting apart.
  - quote: "| `ease-in` on a UI element | `ease-out` or a strong custom curve |"
