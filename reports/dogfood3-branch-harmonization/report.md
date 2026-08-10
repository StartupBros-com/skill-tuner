# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3062 spent
- verify: 9 trial(s), $0.2116 spent

## Run manifest

- run: `dogfood3-branch-harmonization` (2026-08-10T06:21:26Z → 2026-08-10T06:26:20Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/branch-harmonization/SKILL.md` | `2d40bfb2ed8b` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/branch-harmonization/SKILL.md
- probe calls: 1
- verify calls: 9 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Single source of truth [craft] (Pruning and drift)**: The Pipeline section defines RESIDUE as branches the mechanical funnel (branch-triage.sh's PROTECTED/MERGED/SYNCED/TREE-SAME/PR-SHIPPED/CHERRY categories) couldn't resolve, and explicitly says not to re-implement that funnel. But Phase A step 1 ("Already landed? `git cherry -v <canonical> <branch>` ... Verdict `already-merged`; skip.") re-runs exactly the CHERRY check the funnel already performs, and Phase B's verdict table repeats `already-merged` again. This is the same meaning (already-landed detection via `git cherry -v`) computed in two places, contradicting the document's own instruction and the definition of RESIDUE.
  - quote: "Don't re-implement their funnel here; start from what they couldn't resolve."
  - proposed fix: Drop the already-landed re-check from Phase A step 1 and the `already-merged` row from Phase B, since branch-triage.sh's CHERRY funnel already disposes of these before handing off RESIDUE. If a defensive re-check is genuinely wanted (e.g., in case triage was skipped or is stale), say so explicitly rather than presenting it as step 1 of the normal per-branch chain.
- **Completion criteria / Demand [craft] (mixing checkable and uncheckable terms)**: The numeric threshold (0.7) makes this look checkable, but "confidence" is never operationalized anywhere in the document — unlike `fingerprint_coverage` (explicitly defined as found-with-same-signature ÷ total) or `file_existence_coverage`. The agent must impressionistically self-assess a confidence score to compare against the bound, which is exactly the doctrine's warning about a stray uncheckable qualifier inside an otherwise precise-looking rule.
  - quote: "Confidence < 0.7 ⇒ don't auto-classify; surface to the user."
  - proposed fix: Define confidence as a function of the already-defined metrics, e.g., "confidence = min(fingerprint_coverage agreement, file_existence_coverage) — below 0.7, surface to the user instead of auto-classifying," or otherwise specify how the score is computed.

### Refuted findings

- **Completion criteria [craft] (Steps, completion, and demand)** — verifier: "a verdict is certain" gives the agent no checkable bound for when to stop running checks — it requires the same kind of judgment call the doctrine flags with "Verify the config" as an example of an uncheckable criterion. Nothing in the chain ties "certain" to a specific, inspectable condition (e.g., which table row matched).
  - quote: "Run this chain per branch, cheapest check first. Stop as soon as a verdict is certain."
