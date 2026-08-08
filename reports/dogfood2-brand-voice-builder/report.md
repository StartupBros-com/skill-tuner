# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2720 spent
- verify: 15 trial(s), $0.2610 spent

## Run manifest

- run: `dogfood2-brand-voice-builder` (2026-08-08T10:27:30Z → 2026-08-08T10:31:11Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `993984d44b26` | worktree @ 1ad1a4a67872 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 3**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- probe calls: 1
- verify calls: 15 (3 skeptic(s) per finding)
- refuted: 2

### Confirmed findings

- **Cut identity the body already states [craft]**: This is identity/output information, not a routing trigger, and it costs context on every turn the skill's description is loaded. The body already states the same thing twice: the intro ("The output is a structured Voice Profile that future skills, agents, or humans can read and produce on-brand content from.") and the dedicated "After the Profile: Encoding It as a Skill" section. The pointer's job is when to reach the material, not what it is.
  - quote: "Outputs a structured Voice Profile that can be encoded as a project-specific brand-voice skill afterward."
  - proposed fix: Delete the sentence from the description and let the body (intro + encoding section) be the single place this is stated.
- **One trigger per branch [craft]**: Five nouns stack synonyms for a single branch ("a new named thing needs a voice") — reaching the skill via "sub-brand" vs. "product" vs. "author voice" doesn't change the path taken (the same Build/Extract determination runs regardless). This pays load five times for one route.
  - quote: "Use when starting a new brand, sub-brand, product, persona, or author voice."
  - proposed fix: Collapse to one phrase covering the branch, e.g. "Use when starting any new brand, product, or persona voice."
- **Demand [craft]**: The Quality Test is framed as a single gate ("If any answer is no, the profile needs more specificity. Iterate before locking it in."), but it mixes checkable items ("Mechanically clean: does it pass every Mechanical Rule above?") with an uncheckable one ("does it feel true to who they are or want to be?"). The stray impressionistic qualifier lets the whole gate be satisfied on vibes rather than on the checkable items alone.
  - quote: "**Authentic:** does it feel true to who they are or want to be?"
  - proposed fix: Either rewrite "Authentic" into a checkable form (e.g. "the user can name a specific belief or story this reflects") or pull it out of the pass/fail gate into a separate advisory note.

### Refuted findings

- **Single source of truth / duplication [craft]** — verifier: This restates, negated, a rule the document already gives positively in three places: "The mechanical rules from Q16 become the enforceability backbone," the Mechanical Rules section ("These are bright-line rules. Violations should be auto-corrected"), and Quality Test item 6 ("Mechanically clean: does it pass every Mechanical Rule above?"). Same meaning written a fourth time.
  - quote: "**The Unenforceable Voice:** all vibes, no mechanical rules. Result: voice drifts within weeks."
- **Splitting / Progressive disclosure [craft]** — verifier: Extract and Build are mutually exclusive per invocation, determined right here by a distinct trigger. Yet both full processes (six-lens analysis with sub-bullets, and 17 questions across 5 batches) stay fully inlined in the same always-loaded skill body, so the branch not taken still pays context load every time.
  - quote: "- "Yes, I have content I'm proud of" → Extract mode
- "No, I'm starting fresh" → Build mode"
