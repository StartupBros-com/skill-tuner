# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2949 spent
- verify: 12 trial(s), $0.3020 spent

## Run manifest

- run: `dogfood3-cli-agent-ergonomics` (2026-08-10T06:35:45Z → 2026-08-10T06:40:24Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/cli-agent-ergonomics/SKILL.md` | `b026438e5b18` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/cli-agent-ergonomics/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 3

### Confirmed findings

- **Demand [craft] — "Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically."**: The numeric thresholds (≥5, ≥3) are checkable, but "substantive" is not — nothing in the document defines what makes a change substantive versus cosmetic, so an agent can round up trivial edits to hit the count and satisfy the gate impressionistically.
  - quote: "ship ≥5 substantive changes across ≥3 dimensions before calling it done"
  - proposed fix: Replace "substantive" with a checkable proxy, e.g. "ship ≥5 changes, each moving at least one of the 11 dimensions' score, across ≥3 dimensions before calling it done", or drop the adjective and let the count/dimension-spread alone define the bar.

### Refuted findings

- **Completion criteria [craft] — "Two bounds that contradict — a general ceiling in one place, a specific range crossing it in another — are a completion defect in the same family: the agent cannot tell whether a value between them complies, whichever bound it obeys."** — verifier: The grading ladder reserves 'inferred-and-acted' (proceed with a warning) for exactly edit-distance-1, non-destructive corrections — which is precisely what a flag typo like `--jsno`→`--json` is. But Recurring fixes item 1 ("Levenshtein-1 typo correction on flags — ... suggest only at distance 1, keep the non-zero exit") mandates hint-only behavior with a non-zero exit for that identical case, never acting. The document's own worked example (`--jsno` → exit 1, hint only) confirms it follows the second rule, not the first. An agent implementing the feature cannot tell whether edit-distance-1 flag typos should auto-correct-and-proceed or only hint-and-exit-nonzero.
  - quote: "**Ship for "useful hint" minimum**; reserve inferred-and-acted for edit-distance-1, *non-destructive* corrections only — **destructive flags are NEVER auto-corrected; the agent must type the canonical form.**"
- **Duplication / Single source of truth [craft] — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: This is a negated restatement of two rules already given positively elsewhere: the default mode described in "When to use" ("audit + apply + re-score + test") and the "Ambition gate" in The loop ("ship ≥5 substantive changes... A scorecard alone is not a deliverable"). It's the same meaning written a third time.
  - quote: "**A polite scorecard with no applied fixes** (when improvement was asked for). Ship changes, not a report."
- **Duplication / Single source of truth [craft] — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: This restates, negated, the rule already given positively in Named operators: "Ship a **stack** as one coherent commit." Same meaning in two places means the stacking rule can be edited in one place and silently drift out of sync with its anti-pattern mirror.
  - quote: "**Fixing one flag's error in isolation** — apply the operator stack so the whole surface class improves together."
