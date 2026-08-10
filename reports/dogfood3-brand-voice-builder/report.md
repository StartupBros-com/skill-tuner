# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2907 spent
- verify: 18 trial(s), $0.4111 spent

## Run manifest

- run: `dogfood3-brand-voice-builder` (2026-08-10T06:26:20Z → 2026-08-10T06:30:27Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `f86cf23af688` | worktree @ 0eff27fb00ae (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 3**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- probe calls: 1
- verify calls: 18 (3 skeptic(s) per finding)
- refuted: 3

### Confirmed findings

- **Cut identity the body already states [craft]**: The always-loaded description restates what the body already says about itself ('The output is a structured Voice Profile that future skills, agents, or humans can read and produce on-brand content from.', plus the whole 'After the Profile: Encoding It as a Skill' section). This is identity, not a routing trigger, so it spends permanent context load with no help deciding when to reach the skill.
  - quote: "Outputs a structured Voice Profile that can be encoded as a project-specific brand-voice skill afterward."
  - proposed fix: Drop the output-description clause from the description field; keep only the trigger conditions (Build/Extract, generic-copy signal, does-not-apply-existing-voices) and let the body state what it produces.
- **One trigger per branch [craft]**: Brand, sub-brand, product, persona, and author voice do not route to different processing paths inside this document -- every one of them lands on the same Build-vs-Extract decision. These are five synonyms for a single branch ('something new needs a voice') written out in full on every turn the description is loaded.
  - quote: "Use when starting a new brand, sub-brand, product, persona, or author voice."
  - proposed fix: Collapse to one phrase covering the branch, e.g. 'Use when a brand, product, or persona needs a voice defined,' and let the body's 'When to use this skill' list carry the enumerated examples.
- **Progressive disclosure [craft] / Splitting [craft]**: This is a genuine invocation-level branch -- a run only ever needs one mode's material. Yet the full six-lens Extract analysis and the full 17-question, 5-batch Build sequence are both inlined in the same always-loaded SKILL.md, so every invocation carries the other mode's steps as dead weight the agent must read past to find its own path.
  - quote: "Ask the user: "Do you have existing content that represents how you want to sound?"

- "Yes, I have content I'm proud of" → Extract mode
- "No, I'm starting fresh" → Build mode"
  - proposed fix: Split Mode 1 and Mode 2 into separate disclosed files (e.g. EXTRACT.md, BUILD.md) referenced by pointer from 'How to choose,' loading only the chosen mode's steps.

### Refuted findings

- **Duplication / polarity restatement (Pruning and drift) [craft]** — verifier: This anti-pattern is the negated restatement of a rule the document already gives positively: 'These are bright-line rules. Violations should be auto-corrected.' and 'The mechanical rules from Q16 become the enforceability backbone.' It is the same meaning written twice under a different name.
  - quote: "**The Unenforceable Voice:** all vibes, no mechanical rules. Result: voice drifts within weeks."
- **Duplication / polarity restatement (Pruning and drift) [craft]** — verifier: This restates, negated, the Quality Test's already-stated positive rule: '**Consistent:** can it be applied across formats (social, email, long-form, ad)?' Same meaning duplicated across two lists under different names.
  - quote: "**The Single-Channel Voice:** profile only works for one format (e.g. emails) and breaks on social or long-form. Test across channels."
- **Completion criteria [craft]** — verifier: This states an unconditional bound ('exact structure ... regardless of mode'), but the template itself later permits deviation: '(If voice doesn't flex by funnel, replace with relevant context dimensions: long-form vs short-form, public vs member-only, etc.)' The agent cannot tell whether replacing that table complies with the 'exact structure' instruction or violates it.
  - quote: "Use this exact structure for every Voice Profile, regardless of mode."
