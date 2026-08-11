# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 5 trial(s), $1.3467 spent
- verify: 81 trial(s), $1.4825 spent

## Run manifest

- run: `external-fixed-001` (2026-08-11T06:20:57Z → 2026-08-11T06:44:23Z)
- claude CLI: `2.1.224` | skill-tuner: `0.8.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `107b31c2034d` | worktree @ 9a91f44d4a9f |
| target | `/home/will/.claude/jobs/2c802246/tmp/extfix/goal-loop/SKILL.md` | `e642ae53f860` | worktree |
| target | `/home/will/.claude/jobs/2c802246/tmp/extfix/cmux/SKILL.md` | `5d04f2816cea` | worktree |
| target | `/home/will/.claude/jobs/2c802246/tmp/extfix/pptx/SKILL.md` | `18a4c75ce562` | worktree |
| target | `/home/will/.claude/jobs/2c802246/tmp/extfix/algorithmic-art/SKILL.md` | `2f50d2d477ad` | worktree |
| target | `/home/will/.claude/jobs/2c802246/tmp/extfix/canvas-design/SKILL.md` | `bb24a68ddfb1` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 9**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- targets: 5
- probe calls: 5
- verify calls: 81 (3 skeptic(s) per finding)
- refuted: 18

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/.claude/jobs/2c802246/tmp/extfix/goal-loop/SKILL.md` | 1 | 3 |
| `/home/will/.claude/jobs/2c802246/tmp/extfix/cmux/SKILL.md` | 2 | 4 |
| `/home/will/.claude/jobs/2c802246/tmp/extfix/pptx/SKILL.md` | 1 | 4 |
| `/home/will/.claude/jobs/2c802246/tmp/extfix/algorithmic-art/SKILL.md` | 3 | 4 |
| `/home/will/.claude/jobs/2c802246/tmp/extfix/canvas-design/SKILL.md` | 2 | 3 |

### Confirmed findings

- **Pruning and drift — Single source of truth / Duplication [craft]**: This restates the same meaning already given at the top of the document ("**Not:** a budget command, a safety boundary, "run forever", or a replacement for `/plan`. It's a contract enforcer with a verification loop."). The doctrine treats this as duplication — the same meaning in two places costs tokens and creates a two-place edit if the framing ever changes.
  - quote: "`/goal` is a **contract enforcer with a verification loop**, not a "run forever" button."
  - proposed fix: Keep the definition in one place. Either drop the "Not:" framing from "What `/goal` is" and let the Mental model section be the single canonical statement, or drop the Mental model restatement and instead reference the earlier definition.
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/goal-loop/SKILL.md
- **Cut identity the body already states / Single source of truth**: The description already states "macOS only (14.0+)" as part of the always-loaded pointer. Restating it in Common Pitfalls is the same fact in two places — a maintenance/token cost with no added routing signal, since Common Pitfalls isn't reached via this fact.
  - quote: "- **macOS only.** No Linux/Windows port."
  - proposed fix: Keep the platform constraint in the description only (where it does routing work); drop the Common Pitfalls bullet or replace it with something that isn't already said elsewhere.
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/cmux/SKILL.md
- **Progressive disclosure**: This and the surrounding "Hard-won lessons" / pane-reuse / swap-ordering content is deep, narrow reference material specific to one sub-workflow (markdown viewer pane management), yet it's inlined in the always-loaded skill body rather than disclosed behind a pointer — unlike the Socket API section a few headings later, which the same document correctly discloses to `references/socket-api.md`. Every cmux invocation pays for this markdown-viewer minutiae even when the task never touches the markdown viewer.
  - quote: "**Surface refs are global, not per-workspace.** A ref like `surface:126` from an earlier `markdown open` may live in a different window/workspace."
  - proposed fix: Move the Markdown Viewer troubleshooting/hard-won-lessons detail into a `references/markdown-viewer.md`, and leave a one-line pointer in the body naming the branch ("markdown pane swap/reuse quirks") the way the Socket API section already does.
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/cmux/SKILL.md
- **Progressive disclosure / the two loads**: The description explicitly names a read/extract-only branch, yet the body inlines ~120 lines of Create-only reference (the pptxgenjs gotchas section and the entire Design Ideas section: palettes, typography, spacing, avoid-list) with no pointer separating them. Every invocation, including a pure text-extraction request, pays the context cost of generation and design material it will never use.
  - quote: "reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email or summary)"
  - proposed fix: Split 'Creating with pptxgenjs — gotchas' and 'Design Ideas' into a separate disclosed file (e.g. reference/design.md), reached only from the Create/template-fill rows of the top routing table, leaving Read invocations to load only the markitdown/thumbnail guidance.
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/pptx/SKILL.md
- **Single source of truth / Duplication [craft]**: The fixed seed-navigation UI spec (display, prev/next, random, jump-to-seed) is stated in full here, again nearly verbatim under 'WHAT'S FIXED VS VARIABLE > FIXED' ('Seed section in sidebar: Seed display / Previous/Next buttons / Random button / Jump to seed input + Go button'), and a third time under 'Implementation Details > BUILD THE SIDEBAR > 1. Seed (FIXED)' ('Seed display / Prev/Next/Random/Jump buttons'). The same is true for the Actions/Regenerate/Reset spec, restated in both of those same two sections. This is one meaning (the fixed sidebar contents) written three times, costing tokens and creating drift risk if one copy is edited without the others.
  - quote: "**2. Seed Navigation**
- Display current seed number
- "Previous" and "Next" buttons to cycle through seeds
- "Random" button for random seed
- Input field to jump to specific seed
- Generate 100 variations when requested (seeds 1-100)"
  - proposed fix: State the fixed Seed and Actions UI element list once (e.g. under WHAT'S FIXED VS VARIABLE), and have REQUIRED FEATURES and BUILD THE SIDEBAR each point back to it rather than re-enumerating the same buttons.
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/algorithmic-art/SKILL.md
- **Completion criteria [craft] — checkable bound ('the agent can tell done from not-done without judgment')**: This is offered as the CRITICAL bar for the implementation step, but 'feel like they emerged through countless iterations by a master' and 'ensure every pattern emerges with purpose' give the agent no way to tell done from not-done without subjective judgment — the doctrine's own example of an uncheckable bound ('verify the config').
  - quote: "To achieve mastery, create algorithms that feel like they emerged through countless iterations by a master generative artist. Tune every parameter carefully. Ensure every pattern emerges with purpose."
  - proposed fix: Replace with checkable criteria, e.g. 'every parameter has a min/max/default and visibly changes the output when moved; no two default runs look identical; no unused parameters remain.'
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/algorithmic-art/SKILL.md
- **Demand [craft] — mixing checkable and uncheckable qualifiers in one criteria list lets the agent satisfy it impressionistically**: Reproducibility is checkable (run the same seed twice, compare output), but Balance, Color Harmony, and Composition are impressionistic ('without visual noise', 'thoughtful', 'visual hierarchy'). Bundled into one CRAFTSMANSHIP REQUIREMENTS list, the checkable item lets the agent treat the whole list as satisfied once it passes the one item it can actually verify.
  - quote: "- **Balance**: Complexity without visual noise, order without rigidity
- **Color Harmony**: Thoughtful palettes, not random RGB values
- **Composition**: Even in randomness, maintain visual hierarchy and flow
- **Performance**: Smooth execution, optimized for real-time if animated
- **Reproducibility**: Same seed ALWAYS produces identical output"
  - proposed fix: Separate the list into a verifiable subset (e.g. reproducibility, performance budget) the agent must literally check, and a stated-intent subset (balance, harmony, composition) framed as guidance rather than a requirement to be 'met'.
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/algorithmic-art/SKILL.md
- **Demand — mixing checkable and uncheckable terms**: "within the canvas boundaries" and "no overlaps" are checkable, but "clear margins" and "breathing room" carry no measurable threshold. The stray uncheckable qualifiers let the whole criterion be satisfied impressionistically even where the checkable parts are met.
  - quote: "Every element must stay fully within the canvas boundaries with clear margins, breathing room, and no overlaps, regardless of text scale. This is non-negotiable for professional execution."
  - proposed fix: Quantify the vague terms, e.g. "stay within the canvas boundaries with a minimum N% margin on all sides and no overlaps, regardless of text scale."
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/canvas-design/SKILL.md
- **Demand — mixing checkable and uncheckable terms**: "nothing overlaps" is checkable, but "formatting is flawless" and "every detail perfect" are unbounded superlatives with no way to distinguish done from not-done. Mixed into the same checklist, they let the agent claim compliance on judgment rather than verification.
  - quote: "Double-check that nothing overlaps, formatting is flawless, every detail perfect."
  - proposed fix: Drop the superlatives and keep only checkable items, e.g. "Double-check that nothing overlaps and all text sits fully inside the canvas margins."
  - target: /home/will/.claude/jobs/2c802246/tmp/extfix/canvas-design/SKILL.md

### Refuted findings

- **Leading words — Negation [research]** — verifier: The rule leads with the ban and never states the positive alternative — what the goal prompt should say instead when an ADR-worthy decision comes up. The doctrine requires a prohibition to stand paired with its positive target.
  - quote: "**Never instruct the agent to create new ADRs** — ADRs require the user's explicit approval, so goal prompts must not pre-approve or encourage them."
- **Leading words — Negation [research]** — verifier: Pure prohibition with no positive framing, unlike the reward-hacking bullet immediately above it, which correctly leads with the positive target ("Keep the existing test suite intact; add new tests only to cover new behavior.") before the negation. This is the exact tell the doctrine flags: a rule that leads with the ban and never says what to do instead.
  - quote: "Forbid scope creep explicitly: "Do not refactor unrelated code. Do not add dependencies.""
- **Context pointers — One trigger per branch [craft]** — verifier: "mentions `/goal`", "goal loop", and "Ralph loop" are three names for the same subject rather than distinct branches — a run reached through any of the three takes the same path through the document. Three phrases for one branch pay three times and route once.
  - quote: "Use when the user mentions `/goal`, "goal loop", "Ralph loop", wants to kick off a long-running autonomous agent run, asks how to write a goal prompt, or wants a one-paragraph goal instruction drafted."
- **One trigger per branch** — verifier: "a cmux pane, cmux workspace, cmux surface, or an agent running in cmux" are four rephrasings of one branch — the user naming cmux. None routes to a different path than the others, so per the doctrine's test ("does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it?") they should collapse into one. This is an always-loaded pointer, so the redundant tokens cost on every turn.
  - quote: "Trigger ONLY when the user explicitly says "cmux" — a cmux pane, cmux workspace, cmux surface, or an agent running in cmux."
- **Duplication (polarity) — Pruning and drift** — verifier: This is the negated restatement of the rule immediately preceding it ("Trigger ONLY when the user explicitly says 'cmux'"). "Trigger only when X" already excludes every case where X is false; spelling out four excluded terms and four excluded tools is the same branch-exclusion meaning written twice, just with the polarity flipped, and it bloats an always-loaded pointer.
  - quote: "Do NOT trigger on generic mentions of "workspace", "pane", "the other agent", or "delegate" when cmux is not named — workspaces in tmux, Ghostty, herdr, VS Code, etc. are NOT cmux."
- **Single source of truth (environment as source of truth)** — verifier: The doc already instructs the agent to run `cmux docs settings` to get "paths, schema URL, reload cmd — read BEFORE editing." Restating the exact paths right below is caching a one-command lookup that isn't expensive to obtain and can go stale, contrary to "leave the one-command lookups to the environment, where they cannot go stale."
  - quote: "- cmux settings: `~/.config/cmux/cmux.json` (canonical). Project-local override: `.cmux/cmux.json` or `./cmux.json`."
- **Leading words (undefined coined term) / Co-location** — verifier: "Panel" is used here as if it were a defined concept, but Core Concepts only defines Window, Workspace, Pane, and Surface — never Panel. Coining a term this close in spelling to the already-defined "Pane" without a definition is exactly the failure the doctrine flags: a made-up/undefined word recruits no priors and risks being read as a typo for "pane," and there's no section co-locating what a panel is.
  - quote: "`send-panel` / `send-key-panel` exist ONLY for panels (`--panel`), not surfaces."
- **One trigger per branch [craft]** — verifier: The always-loaded description states the same branch three times (open, middle, and close all say 'any .pptx/.potx involvement triggers this') and stacks synonym triples per branch ('creating slide decks, pitch decks, or presentations'; 'reading, parsing, or extracting text'; 'editing, modifying, or updating'). A run reaching the skill via 'parsing' takes the same path as one reaching it via 'extracting text' — these are one branch written three times, paying context load on every turn with no added routing signal.
  - quote: "Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates (.potx), layouts, speaker notes, or comments. Trigger whenever the user mentions "deck," "slides," "presentation," or references a .pptx or .potx filename, regardless of what they plan to do with the content afterward. If a .pptx or .potx file needs to be opened, created, or touched, use this skill."
- **Duplication / anti-pattern list restating a positive rule [craft]** — verifier: This restates, negated, the exact sizing already given positively in the Typography table ('Slide title | 36-44pt bold', 'Body text | 14-16pt'). It is the same meaning written twice — the doctrine names this exact pattern as the commonest disguise of duplication.
  - quote: "**Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body"
- **Duplication / anti-pattern list restating a positive rule [craft]** — verifier: This restates, negated, the rule already given positively in the Spacing section ('0.3-0.5" between content blocks'). Same meaning in two places with no new information, inflating its rank on the ladder.
  - quote: "**Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently"
- **Negation [research]** — verifier: This is a hard guardrail (unphraseable-positive candidate), but the doctrine requires even hard guardrails to stand paired with their positive target so attention lands on what to do — this rule leads with the ban and never states the positive action.
  - quote: "**Never reorder the children of `<p:presentation>`.** pptxgenjs writes `<p:notesMasterIdLst>` right after `<p:sldIdLst>` and points both masters at one theme part. PowerPoint reads that happily — move the element and the same deck becomes unopenable."
- **Completion criteria [craft] — contradictory bounds ('the agent cannot tell whether a value between them complies, whichever bound it obeys')** — verifier: The frontmatter description instructs 'Create original algorithmic art rather than copying existing artists' work to avoid copyright violations,' but the 'DEDUCING THE CONCEPTUAL SEED' section instructs embedding a 'subtle, niche reference' to another work, explicitly analogized to 'a jazz musician quoting another song.' One instruction bounds the work away from referencing others' work, the other requires quoting another work into it. The agent cannot satisfy both, and whichever it follows, it silently violates the other.
  - quote: "Think like a jazz musician quoting another song through algorithmic harmony - only those who know will catch it, but everyone appreciates the generative beauty."
- **Completion criteria [craft] — contradictory bounds** — verifier: This bullet directly contradicts the guideline immediately above it in the same CRITICAL GUIDELINES list: '**Avoid redundancy**: Each algorithmic aspect should be mentioned once. Avoid repeating concepts about noise theory, particle dynamics, or mathematical principles unless adding new depth.' One rule says mention each aspect once; the adjacent rule mandates repeating specific craftsmanship phrases multiple times. The agent cannot tell which bound governs the philosophy text it writes.
  - quote: "**Emphasize craftsmanship REPEATEDLY**: The philosophy MUST stress multiple times that the final algorithm should appear as though it took countless hours to develop, was refined with care, and comes from someone at the absolute top of their field. This framing is essential - repeat phrases like "meticulously crafted algorithm," "the product of deep computational expertise," "painstaking optimization," "master-level implementation.""
- **Completion criteria [craft] — checkable bound** — verifier: This is the success condition for the 'CRITICAL STEP' of deducing the conceptual seed, but 'feel it intuitively' is unfalsifiable — there is no way for the agent to check whether it has met this bar before moving on.
  - quote: "Someone familiar with the subject should feel it intuitively, while others simply experience a masterful generative composition."
- **One trigger per branch [craft] — synonyms that rename a single branch are one branch written twice** — verifier: 'Generative' and 'algorithmic' name the same single branch (a request for this kind of computational art) rather than two distinct cases the skill handles differently — the body itself uses the terms interchangeably throughout ('algorithmic philosophy', 'generative aesthetic movement', 'PURE GENERATIVE ART'). Per the doctrine, a run reaching the skill via 'generative art' takes the same path as one reaching it via 'algorithmic art', so listing both pays twice for one route.
  - quote: "Use this when users request generative or algorithmic art (flow fields, particle systems, etc.)."
- **Completion criteria / Demand — contradicting bounds** — verifier: This bullet sets a general ceiling ("mentioned once") that directly contradicts the very next bullet, "Emphasize craftsmanship REPEATEDLY: The philosophy MUST stress multiple times... repeat phrases like 'meticulously crafted'...". The agent cannot tell whether repeating the craftsmanship framing violates the redundancy rule or is exempt from it — the doctrine's completion-criteria defect of a general ceiling contradicted by a specific range crossing it.
  - quote: "**Avoid redundancy**: Each design aspect should be mentioned once. Avoid repeating points about color theory, spatial relationships, or typographic principles unless adding new depth."
- **Single source of truth** — verifier: This restates, almost verbatim, the craftsmanship framing already given in CRITICAL GUIDELINES ("stress multiple times that the final work should appear as though it took countless hours to create, was labored over with care, and comes from someone at the absolute top of their field"). Unlike ESSENTIAL PRINCIPLES, which correctly cross-references ("See the craftsmanship framing under CRITICAL GUIDELINES above") instead of repeating, this section duplicates the meaning in full rather than pointing back to it.
  - quote: "Make it appear as though someone at the absolute top of their field labored over every detail with painstaking care."
- **One trigger per branch** — verifier: "poster," "piece of art," "design," and "other static piece" all route to the same single, non-branching flow in the body (design philosophy → canvas expression). They are synonyms for one branch written four times, each paying context load on every turn without adding routing signal.
  - quote: "You should use this skill when the user asks to create a poster, piece of art, design, or other static piece."
