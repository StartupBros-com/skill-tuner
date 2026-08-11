# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 8 trial(s), $2.1371 spent
- verify: 120 trial(s), $2.1880 spent

## Run manifest

- run: `external-anthropic-001` (2026-08-11T05:46:30Z → 2026-08-11T06:16:34Z)
- claude CLI: `2.1.224` | skill-tuner: `0.8.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `107b31c2034d` | worktree @ 9a91f44d4a9f |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/skill-creator/SKILL.md` | `dcd4803e61e9` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md` | `a7ff03e2c85b` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md` | `3bc4092c0980` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/doc-coauthoring/SKILL.md` | `2e47d78846fa` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/canvas-design/SKILL.md` | `a1f288079624` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/mcp-builder/SKILL.md` | `0f4592dcb53c` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/xlsx/SKILL.md` | `6712b39718fe` | worktree @ f17010c9bb48 |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/frontend-design/SKILL.md` | `1608ea77fbb6` | worktree @ f17010c9bb48 |

## Marginal-value probe verdict

**findings_confirmed: 20**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- targets: 8
- probe calls: 8
- verify calls: 120 (3 skeptic(s) per finding)
- refuted: 20
- overflow (beyond max_findings cap, not verified): 1

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/skill-creator/SKILL.md` | 0 | 5 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md` | 5 | 3 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md` | 5 | 0 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/doc-coauthoring/SKILL.md` | 1 | 6 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/canvas-design/SKILL.md` | 4 | 2 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/mcp-builder/SKILL.md` | 2 | 2 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/xlsx/SKILL.md` | 2 | 0 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/frontend-design/SKILL.md` | 1 | 2 |

### Confirmed findings

- **Single source of truth**: This restates, almost verbatim, the warning already given in the Scripts table row for thumbnail.py ("Pass `prefix` — it defaults to `thumbnails`, which overwrites the grids of any other deck done in the same directory"). The same meaning lives in two places, so a change to the default or behavior needs a two-place edit.
  - quote: "**Always pass that second argument, named after the deck.** It defaults to `thumbnails`, so two decks thumbnailed in one directory silently overwrite each other's grids — the first deck's are simply gone"
  - proposed fix: State the default-overwrite warning once in the Scripts table, and in the Editing section just point back to it ("see thumbnail.py note above") instead of re-explaining it.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md
- **Single source of truth (duplication via anti-pattern list restating a positive rule)**: This duplicates the rule already stated positively in the Color Palettes section: "Choose colors that match your topic — don't default to generic blue." Same meaning, once positive, once negated in the Avoid list.
  - quote: "**Don't default to blue** — pick colors that reflect the specific topic"
  - proposed fix: Remove the Avoid-list entry; the Color Palettes section's existing sentence already carries the rule.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md
- **Single source of truth (duplication via anti-pattern list restating a positive rule)**: This restates the rule already given positively under "For Each Slide": "Every slide needs a visual element — image, chart, icon, or shape. Text-only slides are forgettable."
  - quote: "**Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets"
  - proposed fix: Drop the Avoid-list entry; the "For Each Slide" statement already establishes the requirement.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md
- **Single source of truth (duplication via anti-pattern list restating a positive rule)**: This duplicates the gotcha already stated in the pptxgenjs section: "Text boxes have built-in internal padding — set `margin: 0` whenever text must align with a shape, line, or icon at the same x."
  - quote: "**Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding"
  - proposed fix: Remove the Avoid-list entry, or replace it with a short pointer back to the pptxgenjs gotcha instead of re-stating the fix.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md
- **Single source of truth (duplication via anti-pattern list restating a positive rule)**: This duplicates the instruction already given in the Editing section: "vary the layouts — don't put every section on the same title-and-bullets slide."
  - quote: "**Don't repeat the same layout** — vary columns, cards, and callouts across slides"
  - proposed fix: Keep the instruction in only one place — either the Editing section or the Avoid list, not both.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/pptx/SKILL.md
- **One trigger per branch [craft]**: This always-loaded description pointer lists five phrases ("creating art using code", "generative art", "algorithmic art", "flow fields", "particle systems") for what is a single branch — every one of them routes to the same two-step philosophy-then-p5.js process, with no different path taken depending on which phrase triggered it. Per the doctrine, synonyms that rename one branch are one branch written twice, and each extra trigger phrase costs on every turn the description is scanned.
  - quote: "Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems."
  - proposed fix: Collapse to one trigger phrase covering the single branch, e.g. "Use this when users request generative or algorithmic art (flow fields, particle systems, etc.)", or only keep separate triggers if they genuinely lead to different handling.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md
- **Pruning and drift — duplication via polarity [craft]**: The "Avoid" (❌) list and the "Follow these practices" (✅) list are the same four rules stated twice, once negated and once positive — exactly the polarity-disguised duplication the doctrine flags: an anti-pattern list that restates, negated, rules the document already gives positively.
  - quote: "**Avoid:**
- ❌ Creating HTML from scratch
- ❌ Inventing custom styling or color schemes
- ❌ Using system fonts or dark themes
- ❌ Changing the sidebar structure

**Follow these practices:**
- ✅ Copy the template's exact HTML structure
- ✅ Keep Anthropic branding (Poppins/Lora fonts, light colors, gradient backdrop)
- ✅ Maintain the sidebar layout (Seed → Parameters → Colors? → Actions)
- ✅ Replace only the p5.js algorithm and parameter controls"
  - proposed fix: Delete the ❌ Avoid list; the ✅ Follow-these-practices list already states every rule positively and completely.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md
- **Single source of truth [craft]**: This is the third full restatement of the same "keep FIXED / replace VARIABLE" rule, after STEP 0 ("Keep all FIXED sections exactly as shown ... Replace only the VARIABLE sections") and the dedicated "CRITICAL: WHAT'S FIXED VS VARIABLE" section which itemizes the same lists in more detail. Each restatement means a future edit to what's fixed vs. variable has to be made in three places, and the excess pads an already long document.
  - quote: "- **templates/viewer.html**: REQUIRED STARTING POINT for all HTML artifacts.
  - This is the foundation - contains the exact structure and Anthropic branding
  - **Keep unchanged**: Layout structure, sidebar organization, Anthropic colors/fonts, seed controls, action buttons
  - **Replace**: The p5.js algorithm, parameter definitions, and UI controls in Parameters section"
  - proposed fix: Keep the detailed breakdown only in the "CRITICAL: WHAT'S FIXED VS VARIABLE" section; replace the STEP 0 and RESOURCES restatements with a short pointer back to it (e.g. "see WHAT'S FIXED VS VARIABLE above").
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md
- **Completion criteria — contradicting bounds [craft]**: Earlier, under "CRITICAL: WHAT'S FIXED VS VARIABLE", the FIXED Actions section is defined as only "Regenerate button" and "Reset button" — no Download PNG button. This later list adds a third FIXED action item not present in the first. The agent can't tell whether a Download PNG button is part of the required FIXED template output or not, whichever list it follows.
  - quote: "**4. Actions (FIXED)** - Always include exactly as shown:
- Regenerate button
- Reset button
- Download PNG button"
  - proposed fix: State the Actions button set once and keep it identical everywhere it's referenced — decide whether Download PNG is FIXED and include it (or omit it) consistently in both the WHAT'S FIXED VS VARIABLE list and the Implementation Details list.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md
- **Single source of truth [craft]**: This ESSENTIAL PRINCIPLES bullet restates, almost word-for-word, the CRITICAL GUIDELINES bullet earlier in the same phase ("Emphasize craftsmanship REPEATEDLY: The philosophy MUST stress multiple times that the final algorithm should appear as though it took countless hours to develop... comes from someone at the absolute top of their field... repeat phrases like 'meticulously crafted algorithm'..."). Both instruct the same behavior — stress craftsmanship repeatedly in the philosophy text — in two separate sections of the same step.
  - quote: "**EXPERT CRAFTSMANSHIP**: Repeatedly emphasize the final algorithm must feel meticulously crafted, refined through countless iterations, the product of deep expertise by someone at the absolute top of their field in computational aesthetics"
  - proposed fix: Keep the craftsmanship-repetition instruction in one place (the CRITICAL GUIDELINES bullet, which is more specific) and drop the duplicate ESSENTIAL PRINCIPLES bullet, or replace it with a one-line cross-reference.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/algorithmic-art/SKILL.md
- **Leading words [craft]**: "Reader Claude" is a coined term first used here with no defining sentence — it is never explicitly introduced as the name for the fresh sub-agent instance, so the agent must infer the referent from context rather than anchoring on a defined term.
  - quote: "Summarize what Reader Claude got right/wrong for each question."
  - proposed fix: Add a defining clause at first use, e.g. "invoke a sub-agent with just the document content and the question — call this instance Reader Claude," then use the term consistently afterward.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/doc-coauthoring/SKILL.md
- **Pruning and drift — Single source of truth / Duplication**: This restates, almost verbatim, the instruction already given under CRITICAL GUIDELINES ('Emphasize craftsmanship REPEATEDLY... repeat phrases like "meticulously crafted," "the product of deep expertise"...'), and the same meaning is stated a third time later under CANVAS CREATION ('To achieve human-crafted quality... someone at the absolute top of their field labored over every detail with painstaking care'). Three restatements of one meaning cost tokens and maintenance three times while routing/behavior once, inflating the rule's rank on the ladder past its real importance.
  - quote: "**EXPERT CRAFTSMANSHIP**: Repeatedly emphasize the final work must look meticulously crafted, labored over with care, the product of countless hours by someone at the top of their field"
  - proposed fix: State the craftsmanship requirement once (e.g., under CRITICAL GUIDELINES) and delete the restatements in ESSENTIAL PRINCIPLES and CANVAS CREATION, or replace them with a short pointer back to the single authoritative statement.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/canvas-design/SKILL.md
- **Pruning and drift — Single source of truth / Duplication**: Three consecutive sentences restate the same checkable requirement (elements must not overlap and must stay within the canvas with margins) without adding new depth, which is the exact anti-pattern the doctrine's redundancy rule warns against.
  - quote: "Regardless of text scale, nothing falls off the page and nothing overlaps. Every element must be contained within the canvas boundaries with proper margins. Check carefully that all text, graphics, and visual elements have breathing room and clear separation."
  - proposed fix: Collapse into one sentence, e.g., 'Every element must stay fully within the canvas boundaries with clear margins, breathing room, and no overlaps.'
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/canvas-design/SKILL.md
- **Pruning and drift — Single source of truth / Duplication**: This repeats a length requirement already given twice earlier ('Articulate the philosophy (4-6 paragraphs - concise but complete)' and 'The actual design philosophy should be 4-6 substantial paragraphs'). The same bound is stated three times with no new information, which is duplication rather than a leading-word repetition.
  - quote: "**The design philosophy should be 4-6 paragraphs long.**"
  - proposed fix: State the 4-6 paragraph requirement once, in the 'Articulate the philosophy' bullet, and remove the later restatements.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/canvas-design/SKILL.md
- **Pruning and drift — Duplication (polarity disguise)**: The sentence already states the rule positively earlier in the same passage ('the approach should still be sophisticated'), then restates it negated, naming 'cartoony' and 'amateur' explicitly. This is the polarity-disguised duplication the doctrine calls out — the same meaning given twice, once positive and once negated, with the negated form needlessly activating the concepts it's trying to suppress.
  - quote: "Never lose sight of the idea that this should be art, not something that's cartoony or amateur."
  - proposed fix: Keep only the positive framing: 'The approach should always be sophisticated, never cartoonish or amateurish in feel' — or simply drop the second sentence since the positive instruction already covers it.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/canvas-design/SKILL.md
- **Cut identity the body already states [craft]**: This always-loaded description sentence restates identity information the body's Overview already gives almost verbatim ("Create MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools."). The pointer's job is to state when to reach the material, not to re-describe what it is; this costs permanent context load on every turn for zero routing signal.
  - quote: "Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools."
  - proposed fix: Trim the description to the trigger condition only, e.g. "Use when building MCP servers to integrate external APIs or services, in Python (FastMCP) or TypeScript (MCP SDK)." and drop the restated identity clause, leaving the Overview as the sole place that defines what the server/skill is.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/mcp-builder/SKILL.md
- **Single source of truth / duplication [craft]**: The same pointer (fetch instruction plus URL) already appears verbatim earlier under Phase 1.3 ("**TypeScript SDK**: Use WebFetch to load `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`"). The same pattern repeats for the Python SDK link, the sitemap link, mcp_best_practices.md, node_mcp_server.md, python_mcp_server.md, and evaluation.md — each stated once inline in its phase and again in the closing Reference Files section. This is the same meaning (where to find X) written two or three times, so a changed URL or filename now needs multi-place edits, and the whole closing section is duplicated always-loaded content rather than a single authoritative index.
  - quote: "**TypeScript SDK**: Fetch from `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`"
  - proposed fix: Keep exactly one mention per link — either only the inline mention at the phase where it's needed, or only the Reference Files index — and delete the redundant copy rather than maintaining both.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/mcp-builder/SKILL.md
- **Pruning and drift — Single source of truth [craft]**: This restates the same meaning already given in the top blockquote ("`openpyxl`, `pandas`, and `markitdown` are preinstalled — do not run `pip install` first; write the script and import directly. Only if an import fails (or the `markitdown` command is missing): `pip install` the missing package."). Both instances tell the agent the same rule — packages are preinstalled, only pip-install on import failure — in slightly different wording. Per the doctrine, this is duplication: the same meaning in two places, costing tokens and creating a second place that could drift out of sync if the policy changes.
  - quote: "`openpyxl`, `pandas`, `markitdown` (pip, preinstalled — install only if an import fails or the command is missing) · LibreOffice (`soffice`, auto-configured for sandboxed environments via `scripts/office/soffice.py`)"
  - proposed fix: Drop the parenthetical pip-install rule from the Dependencies line and let the top blockquote remain the sole authority, e.g. reduce to: "`openpyxl`, `pandas`, `markitdown` (see note above) · LibreOffice (`soffice`, auto-configured for sandboxed environments via `scripts/office/soffice.py`)."
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/xlsx/SKILL.md
- **One trigger per branch [craft]**: This branch is already covered by the earlier clause "open, read, edit, or fix an existing ... file (e.g., ... cleaning messy data)" — both describe the same routing outcome (invoke this skill to clean/restructure messy tabular data). A run reaching the skill through 'cleaning messy data' and a run reaching it through 'malformed rows, misplaced headers, junk data' take the identical path, so this is one branch stated twice, paying context-load cost on every turn for no added routing signal.
  - quote: "Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets."
  - proposed fix: Delete the standalone "Also trigger for cleaning or restructuring..." sentence and fold its distinguishing detail into the existing parenthetical, e.g. "...cleaning messy data (malformed rows, misplaced headers, junk data)", so the branch is written once.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/xlsx/SKILL.md
- **Front-load the leading word [craft]**: The description opens with throat-clearing ('Guidance for') instead of the trigger concept itself. This is the exact pattern the doctrine calls out: 'A pointer that opens with throat-clearing ("This skill provides guidance on...") spends its most valuable position on nothing.' The position the agent reads first is spent on a filler phrase rather than the concept that should do the triggering work.
  - quote: "Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one."
  - proposed fix: Lead with the concept: "Distinctive, intentional visual design for building new UI or reshaping an existing one."
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-anthropic/skills/frontend-design/SKILL.md

### Refuted findings

- **Context pointers — one trigger per branch [craft]** — verifier: The description states each branch twice: 'create new skills' / 'create a skill from scratch', 'modify and improve existing skills' / 'edit ... an existing skill', and 'measure skill performance' is then re-expanded as both 'run evals to test a skill' and 'benchmark skill performance with variance analysis'. None of these paired phrasings route to a different path — they're the same branch written two or three times, which pays context-load cost on every turn for no added routing signal, and the 'optimize an existing skill' phrase further blurs into the separate description-optimization branch named later in the same sentence.
  - quote: "Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy."
- **Progressive disclosure [craft] / Domain organization** — verifier: The Claude.ai-specific and Cowork-specific instructions are each only relevant to a single runtime branch (which product the agent is running in), yet both full sections are inlined permanently in SKILL.md rather than disclosed behind a pointer, exactly the pattern the document itself warns against under 'Domain organization' ('organize by variant ... Claude reads only the relevant reference file'). Every session pays the context cost of reading both platform sections even though at most one applies.
  - quote: "## Claude.ai-specific instructions"
- **Demand [craft] — mixing checkable and uncheckable terms** — verifier: The first two conditions are checkable (explicit user statement, empty feedback file); the third, 'you're not making meaningful progress,' is a judgment call with no observable signal. Mixed into an otherwise precise list, it lets the agent stop the iteration loop impressionistically whenever it prefers, while appearing to satisfy a checkable-looking bullet list.
  - quote: "Keep going until:
- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress"
- **Completion criteria — contradicting bounds [craft]** — verifier: This sets a ceiling/target of 20, but the breakdown immediately after specifies 'should-trigger queries (8-10)' and 'should-not-trigger queries (8-10)', which sums to a range of 16-20. An agent that produces 8+8=16 queries complies with both per-category ranges while contradicting the stated total of 20, and the document gives no way to tell which bound governs.
  - quote: "Create 20 eval queries — a mix of should-trigger and should-not-trigger."
- **Single source of truth / duplication [craft]** — verifier: This reproduces the same core-loop meaning already stated near the top of the document ('At a high level, the process of creating a skill goes like this: ...'), as two separately maintained bullet lists describing overlapping but slightly divergent steps. Any future edit to the loop now requires updating two places, and the duplication inflates the loop's prominence on the ladder beyond a single restatement's worth.
  - quote: "Repeating one more time the core loop here for emphasis:"
- **One trigger per branch** — verifier: Each clause stacks synonyms for a single branch: "creating slide decks, pitch decks, or presentations" is one create branch written three times, "reading, parsing, or extracting text" is one read branch written three times, and "editing, modifying, or updating" is one edit branch written three times. None of these synonyms send the model down a different path than its neighbor, so they pay context load on every turn the description is scanned without adding routing signal.
  - quote: "This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates (.potx), layouts, speaker notes, or comments."
- **One trigger per branch** — verifier: This closing sentence restates the branch already declared in the opening sentence ("Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both"), just adding further synonyms ("opened," "created," "touched") for a branch the description already fully covers. It's permanent context load with no new routing signal.
  - quote: "If a .pptx or .potx file needs to be opened, created, or touched, use this skill."
- **Front-load the leading word** — verifier: The pointer opens with the imperative frame "Use this skill any time" before reaching the token that actually does the triggering work (.pptx/.potx), spending the highest-value read position on framing rather than the trigger.
  - quote: "Use this skill any time a .pptx or .potx file is involved in any way"
- **One trigger per branch [craft]** — verifier: This restates the same branch already covered earlier in the same description ("Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content"). A run reaching the skill via "drafting specs" takes the same path as one reaching it via "technical specs" — it's one branch paid for twice in an always-loaded pointer.
  - quote: "Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks."
- **Front-load the leading word [craft]** — verifier: The pointer's most valuable position (the words the agent reads first) is spent on generic framing ("Guide users through a structured workflow for") rather than the branch-triggering content ("co-authoring documentation"), which is functionally the same problem as opening with "This skill provides guidance on...".
  - quote: "Guide users through a structured workflow for co-authoring documentation."
- **Cut identity the body already states [craft]** — verifier: This is identity/self-description, and the body already states the same thing ("Act as an active guide, walking users through three stages: Context Gathering, Refinement & Structure, and Reader Testing"). It costs permanent context load without adding routing signal.
  - quote: "This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers."
- **Single source of truth [craft]** — verifier: This duplicates the rule already given in Step 6 ("If using artifacts: Provide link to artifact after each edit"), and the neighboring "Use `str_replace` for all edits" bullet likewise duplicates Step 6's "Use `str_replace` to make edits". Restating the same meaning in a closing tips block inflates its rank on the ladder and creates two places to update if the rule changes.
  - quote: "Provide artifact link after every change"
- **Completion criteria [craft]** — verifier: "Questions show understanding" and "edge cases and trade-offs can be asked about" require the agent's own subjective judgment to evaluate — there's no way to tell done from not-done without judgment, so the exit condition is checkable only in the reader's head, not in the agent's.
  - quote: "Sufficient context has been gathered when questions show understanding - when edge cases and trade-offs can be asked about without needing basics explained."
- **Demand [craft]** — verifier: The precise, checkable count ("3 consecutive iterations") is undermined by the uncheckable qualifier "no substantial changes", letting the agent satisfy the whole criterion impressionistically rather than on the count alone.
  - quote: "After 3 consecutive iterations with no substantial changes, ask if anything can be removed without losing important information."
- **Context pointers — One trigger per branch** — verifier: Poster, piece of art, design, and 'other static piece' are synonyms for a single branch (a request for static visual art) — the skill routes and executes identically regardless of which word is used. Per the doctrine, three (here four) phrases for one branch pay three times in always-loaded context and route once.
  - quote: "You should use this skill when the user asks to create a poster, piece of art, design, or other static piece."
- **Leading words — Negation** — verifier: "Human-crafted quality" already states the positive target completely; the parenthetical '(not AI-generated)' is not a hard guardrail that resists positive phrasing, so it needlessly names the forbidden concept and drags it into context, per the doctrine's negation rule.
  - quote: "To achieve human-crafted quality (not AI-generated), create work that looks like it took countless hours."
- **Demand [craft]** — verifier: This list also contains checkable items ("Read-only: Only non-destructive operations required", "Verifiable: Single, clear answer that can be verified by string comparison"), but "Realistic" requires a subjective judgment call about what humans would care about, with no way to tell done from not-done. Per the doctrine, one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole list impressionistically.
  - quote: "- **Realistic**: Based on real use cases humans would care about"
- **Demand [craft]** — verifier: "Full type coverage" is checkable against a type-checker's output, but "Consistent error handling" and "Clear tool descriptions" have no stated check and require subjective judgment, mixing checkable and uncheckable terms in the same review list so the agent can claim the whole review is done without a verifiable basis.
  - quote: "- Consistent error handling
- Full type coverage
- Clear tool descriptions"
- **One trigger per branch [craft]** — verifier: 'Aesthetic direction' and 'making choices that don't read as templated defaults' restate the same branch already named in the preceding sentence ('distinctive, intentional visual design'). A query reaching this skill through either phrase takes the identical path through the identical document — they are one branch written twice (three times, counting the first sentence), paying token cost on every turn without adding routing signal.
  - quote: "Helps with aesthetic direction, typography, and making choices that don't read as templated defaults."
- **Completion criteria [craft]** — verifier: 'Higher confidence it'll delight them' is not checkable — the agent cannot tell done from not-done without judgment, matching the doctrine's uncheckable example ('Verify the config') rather than its checkable one (re-reading and confirming a written value).
  - quote: "only show ideas to the user when you have higher confidence it'll delight them"
