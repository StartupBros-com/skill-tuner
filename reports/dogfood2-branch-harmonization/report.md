# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3156 spent
- verify: 3 trial(s), $0.0846 spent

## Run manifest

- run: `dogfood2-branch-harmonization` (2026-08-08T10:05:54Z → 2026-08-08T10:09:24Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/branch-harmonization/SKILL.md` | `2d40bfb2ed8b` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/branch-harmonization/SKILL.md
- probe calls: 1
- verify calls: 3 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Demand [craft] — "Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically."**: This numeric threshold gates a real decision (auto-classify a branch's verdict vs. escalate to the user) but "confidence" is never defined anywhere in the document. Every sibling metric that appears alongside it is given an explicit, checkable formula — fingerprint_coverage is defined as "found-with-same-signature ÷ total," file_existence_coverage is likewise computed, and the same-signature sampling rule spells out "≥30% of sampled signatures diverge ⇒ flip away from superseded." "Confidence" gets no such definition, yet it's also listed as a variant-matrix column in Phase C ("columns for signatures, hunk intent, tests, proposed synthesis, confidence, risks") as if it were an equally well-specified score. The precise-looking "< 0.7" threshold is therefore uncheckable in practice — the agent has no way to tell done (confident enough to auto-classify) from not-done, and can satisfy the gate impressionistically.
  - quote: "Confidence < 0.7 ⇒ don't auto-classify; surface to the user."
  - proposed fix: Define confidence explicitly as a function of the metrics already established in Phase A — e.g. "confidence = 1 minus the fraction of ambiguous signals: empty vs. non-empty fingerprint, apply-probe clean/reject, and whether ≥3 signatures could be sampled" — or replace the vague gate with an enumerated, checkable rule such as "surface to the user if fewer than 3 symbols could be sampled for signature comparison, or if apply-probe and same-signature sampling disagree on direction."
