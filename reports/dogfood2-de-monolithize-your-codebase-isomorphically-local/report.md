# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3009 spent
- verify: 9 trial(s), $0.3691 spent

## Run manifest

- run: `dogfood2-de-monolithize-your-codebase-isomorphically-local` (2026-08-08T10:16:58Z → 2026-08-08T10:21:18Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `7737730892f3` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- probe calls: 1
- verify calls: 9 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **One trigger per branch [craft]**: The description lists four triggers but they collapse onto only two distinct branches the document actually handles (whole-repo vs. single-file, per the Recipe Selector table). "de-monolithize" and "modularize repo" both route to the same repo-wide Standard-mode branch, and "split giant file" and "file too big" both route to the same single-file Quick-mode branch. Per the doctrine's test — 'does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it?' — these pairs don't, so they should collapse. Paying the always-loaded description budget four times to route to two paths is the exact 'three phrases for one branch' waste the rule warns against.
  - quote: "Use when de-monolithize, split giant file, modularize repo, or file too big."
  - proposed fix: Collapse to one phrase per branch, e.g. "Use when de-monolithizing a repo or splitting a single giant file."
- **Single source of truth (Pruning and drift) [craft]**: The exact same convergence rule (≥10 rounds, <3 new findings for two consecutive rounds, zero unresolved hypotheses with the same 'Deferred reviewed: yes' marker) is independently restated earlier in the Quick-Start block: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings AND every hypothesis resolved (SEAM_CONFIRMED / SEAM_REFUTED /...". Two independently-worded copies of the same numeric threshold mean changing the round floor or finding ceiling requires editing two places, risking silent drift between them.
  - quote: "Converged = two consecutive quiet rounds AND ≥10 total rounds AND zero unresolved hypotheses (DEFERRED requires written rationale plus `Deferred reviewed: yes`)."
  - proposed fix: State the convergence rule once (in the dedicated Convergence section) and replace the Quick-Start copy with a short pointer, e.g. "Convergence: see the Convergence section for the exact gate."

### Refuted findings

- **Duplication (Pruning and drift — polarity) [craft]** — verifier: This anti-pattern row restates, negated, a rule the document already states positively in The One Rule callout: "Seams are discovered *empirically* (graphs, churn, probes), never aesthetically." Per the doctrine, 'an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice.' Several other Anti-Patterns rows have the same problem (e.g. the wc -l row duplicates the taxonomy's 'never line count alone' weighting rule; the re-export row duplicates the Isomorphism Contract's 'API diff must stay empty'), inflating this meaning's rank on the ladder and creating a two-place edit surface.
  - quote: "Split along visual sections ("types here, helpers there")"
