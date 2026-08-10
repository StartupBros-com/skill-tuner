# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $3.3105 spent
- verify: 132 trial(s), $3.2818 spent

## Run manifest

- run: `rebank-sys-incumbent` (2026-08-10T20:53:33Z → 2026-08-10T21:47:40Z)
- claude CLI: `2.1.224` | skill-tuner: `0.5.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../doctrines/writing-for-agents-8b36d4f.md` | `a61475f4549b` | worktree @ 174bcdf5ce95 (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `2f83bb7c6e55` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `ecf98ca2b554` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `ccd612736f52` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `5d44a3ae63b7` | worktree @ 0eff27fb00ae (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `2d40bfb2ed8b` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `0c38fb28b8c5` | worktree @ 0eff27fb00ae (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `65a8c2e84c7c` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `44ea330fdca2` | worktree @ 0eff27fb00ae (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `b026438e5b18` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `b3d49f5611e9` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `7a2145fdbdee` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `7737730892f3` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `289d2526bc05` | worktree @ 0eff27fb00ae |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `bdfb8b83dc84` | worktree @ 0eff27fb00ae |

## Marginal-value probe verdict

**findings_confirmed: 27**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../doctrines/writing-for-agents-8b36d4f.md
- targets: 15
- probe calls: 15
- verify calls: 132 (3 skeptic(s) per finding)
- refuted: 17

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 2 | 0 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 1 | 0 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 2 | 0 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 1 | 0 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 3 | 2 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 1 | 2 |

### Confirmed findings

- **Pruning no-ops — an instruction the model already obeys by default pays load to say nothing; when a sentence fails this test, delete the whole sentence.**: This sentence immediately follows "Orchestration overhead isn't worth it; a single Sonnet subagent or inline work is cheaper," which already fully conveys the guidance. The negated restatement adds no new behavior-changing information — it's the same meaning spoken twice in one bullet.
  - quote: "Don't build a swarm for a small job."
  - proposed fix: Delete the sentence; the preceding positive statement already establishes the rule.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Context pointers — the pointer must list the branches that should trigger reaching the material it names ("A pointer does two jobs — state what the material is, and list the branches that should trigger reaching it")**: The body explicitly disambiguates this skill from three siblings ("It does not audit a codebase (that's `improve-animations`), critique a diff (that's `review-animations`), or hunt for places that could animate (that's `find-animation-opportunities`)"), but the always-loaded description only routes around two of them. A request to find animation opportunities in a codebase has no disambiguating branch in the pointer and could be misrouted to this construction skill.
  - quote: "Use when asked to animate something, add motion, make a component feel alive, or build a transition. For critiquing existing motion use review-animations; for auditing a whole codebase use improve-animations."
  - proposed fix: Add the missing branch to the description, e.g. "...for auditing a whole codebase use improve-animations; for finding places that could animate use find-animation-opportunities."
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Pruning — single source of truth / duplication ("the same meaning in more than one place... costs maintenance and tokens" and risks drift)**: This row is the compressed self-check version of the rule in the Properties section, but it drops the explicit carve-out stated there: "`height` is tolerated only for accordions, where there's no transform equivalent." Since Never Ship is described as "an automatic block in `review-animations`", an agent relying on this table for its final check would flag a legitimate accordion height animation as a violation.
  - quote: "Animating `width`/`height`/`margin`/`padding`/`top`/`left` | `transform` / `opacity`"
  - proposed fix: Carry the exception into the row, e.g. "Animating width/height/margin/padding/top/left (height on accordions excepted) | transform / opacity".
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Context pointers — "A pointer does two jobs — state what the material is, and list the branches that should trigger reaching it."**: The parenthetical examples don't match what's actually under the body's "Design foundations" heading (§16), which covers Purpose, Agency, Responsibility, Familiarity, Flexibility, Simplicity, Craft, Delight — none of which is "feedback" or "spatial consistency." Those two topics are actually separate sections (§1 Response and §7 Spatial consistency), unrelated to §16. The pointer misdescribes its own target, which will mislead an agent reaching for "design foundations" content.
  - quote: "or the design foundations (feedback, spatial consistency) behind Apple-style interfaces"
  - proposed fix: Either change the parenthetical to match §16's actual principles (e.g. "(agency, familiarity, simplicity)") or reword to "design foundations, feedback, and spatial consistency" so the three are read as separate items rather than examples of one branch.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Co-location — "Keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours with it."**: This rule — that the sign of velocity at release, not the element's position, determines whether a gesture reverses or commits — appears only in the Quick Reference table. No numbered section (§3 Interruptibility, §5 Velocity handoff, or §6 Momentum projection) defines or explains it, so the concept has no home and an agent following a link to "reverse vs. commit" logic has nowhere to read the reasoning behind it.
  - quote: "| Decide reverse vs. commit | Use velocity **sign**, not position | at release |"
  - proposed fix: Add the sign-of-velocity rule to §3 (Interruptibility) where reversal is discussed, then keep the Quick Reference row as a pointer back to it.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Pruning — single source of truth: 'Keep each meaning in a single source of truth... Duplication — the same meaning in more than one place — costs maintenance and tokens.'**: This pointer duplicates the identical inline pointer given earlier in Step 1 ('**Full cookbook (10 queries + export):** [ATUIN-QUERIES.md](references/ATUIN-QUERIES.md)'). The same pattern repeats for SHELL-HISTORY.md, SYSTEMD.md, SCAFFOLD.md, and PATTERN-DETECTION.md — every reference doc is pointed to twice, once inline and once in the Reference Index, doubling context load for the same meaning with no added information.
  - quote: "| Atuin query cookbook (10 queries) | [ATUIN-QUERIES.md](references/ATUIN-QUERIES.md) |"
  - proposed fix: Keep only the inline pointers at point of use and drop the redundant Reference Index table, or vice versa — pick one authoritative location for each pointer.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Pruning — cache: 'Cache what the agent cannot find by looking... Leave the one-file, one-command lookups to the environment, where they cannot go stale.' Combined with duplication: 'the same meaning in more than one place.'**: The exact alias count is restated a second time later in the doc ('You already keep ~40 aliases; find commands you type a lot but haven't shortcut'). Beyond the duplication, this is a cached count of a one-command lookup (`grep -c '^alias' ~/.bashrc`) that the doc itself instructs the agent to run — it will drift out of sync with the user's actual `.bashrc` and provides no information the environment doesn't already supply on demand.
  - quote: "`~/.bashrc` (~40 aliases)"
  - proposed fix: Drop the specific count from both locations; just say 'you keep aliases in ~/.bashrc' and let the grep command in the doc surface the live number.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Leading words — negation: 'steering by prohibition drags the forbidden behaviour into context... Prompt the positive... A prohibition earns its place only as a hard guardrail you cannot phrase positively; even then, pair it with the positive target.'**: This is a pure prohibition with no positive framing paired to it in the same instruction — it is trivially phraseable as a positive rule ('Always complete Steps 1-3 first') but instead is stated only as what not to do, which the doctrine flags as the weaker, riskier framing.
  - quote: "**Never skip 1-3.**"
  - proposed fix: Rephrase as a positive completion criterion, e.g. 'Always complete Steps 1-3 before proposing — data beats intuition about what's repetitive.'
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Pruning — single source of truth / duplication: 'Keep each meaning in a single source of truth... Duplication — the same meaning in more than one place — costs maintenance and tokens.'**: This restates the same fact already established two paragraphs earlier in the Safety Kernel ('`git cherry -v <canonical> <branch>` is the authoritative "already landed" check ... Trust it over `git log` ancestry.'): that cherry -v beats git log ancestry for detecting landed content. The caveat is stated twice within the same short document, in adjacent sections, meaning a future edit to this nuance requires updating two places.
  - quote: "**Already landed?** `git cherry -v <canonical> <branch>` — all `-` lines ⇒ patch-id-equivalent content is already on canonical (even if `git log` shows no ancestry). Verdict `already-merged`; skip."
  - proposed fix: In Phase A step 1, reference the established rule instead of restating it: "Already landed? Per Safety Kernel #3, `git cherry -v <canonical> <branch>` — all `-` lines ⇒ verdict `already-merged`; skip."
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Leading words — negation: 'A prohibition earns its place only as a hard guardrail you cannot phrase positively... Prompt the positive.'**: This is workflow guidance, not an irreversible or destructive action — it doesn't meet the doctrine's bar for when a prohibition is warranted ('hard guardrail you cannot phrase positively'). It can be stated purely positively without loss.
  - quote: "Don't re-implement their funnel here; start from what they couldn't
resolve."
  - proposed fix: Rephrase as: "Start from the RESIDUE they hand you — treat their funnel's dispositions as already resolved."
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Leading words — negation: 'A prohibition earns its place only as a hard guardrail you cannot phrase positively... Prompt the positive.'**: Non-destructive analytical guidance framed as a prohibition rather than a positive instruction; doesn't meet the doctrine's exception for negation (a hard, irreversible guardrail).
  - quote: "Same-signature sampling (don't be fooled by supersession)."
  - proposed fix: Rephrase as: "Same-signature sampling (confirms genuine supersession, not just symbol-name overlap)."
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Pruning — single source of truth / duplication ("Keep each meaning in a single source of truth: one authoritative place... Duplication — the same meaning in more than one place — costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.")**: This sentence restates, at the same level of compression, exactly what the frontmatter description already states: "Define a brand voice from scratch (Build mode) OR extract one from existing content (Extract mode)." It adds no new information beyond what the pointer already carries, and the immediately following "## Two Modes" section already re-derives the same distinction with added detail (Use when / Process for each). The sentence is a pure restatement sitting between the compressed pointer and the detailed body, so removing it changes nothing — a no-op that also creates a two-place edit burden if the mode definitions ever change.
  - quote: "This skill defines that voice. Either by extracting it from existing content the user is proud of, or building it strategically from scratch."
  - proposed fix: Delete the sentence. Let the frontmatter description handle the compressed identity statement and let "## Two Modes" supply the detail; the preceding "reader feels like they're hearing from a PERSON" sentence already carries the paragraph's genuinely new content.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Context pointers — one trigger per branch ("Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.")**: The frontmatter description already names "Google OAuth consent" earlier in the same sentence ("...(Google OAuth consent, Stripe webhooks, GCP credentials) by opening..."). "OAuth consent screens" at the end of the description is the same branch restated a second time within one always-loaded pointer, paying context-load cost twice for one trigger instead of listing it once.
  - quote: "Use when a console step cannot be scripted: bot detection (Google's "browser may not be secure"), 2FA, CAPTCHA, or OAuth consent screens."
  - proposed fix: Drop the redundant second mention, e.g. end the sentence with "...bot detection (Google's "browser may not be secure"), 2FA, or CAPTCHA." since OAuth consent is already covered by the earlier parenthetical.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Pruning — relevance: "A line loses relevance by never bearing on the task (mere exposition...)"**: This is historical trivia about a retired routing path. It doesn't inform any action the agent takes when using the skill (the agent only needs to know to call `cass-rerank`/`cass --robot`), so it costs context load on every skill invocation without bearing on the task — mere exposition rather than an actionable reason behind a choice.
  - quote: "The old wm -> ai-gateway:18000 -> mac-studio tunnel chain is retired."
  - proposed fix: Delete the sentence about the retired tunnel chain; keep only the still-relevant architecture note ("routes through ai-gateway's local-rerank lane over the tailnet with a scoped virtual key") if it's needed for debugging the health-check command below.
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Information hierarchy / progressive disclosure — "Branching is the cleanest disclosure test: inline what every branch needs, and push behind a pointer what only some branches reach... Push too little down and the top bloats."**: The entire index-repair flow (status-check command, explanation of the `cass index --full` failure mode, the multi-line `setsid env ...` repair command with seven tuning env-vars, timing/memory figures, and a dated verification note) is a rare branch — only reached when the lexical index is corrupted — yet it's inlined in full and makes up roughly a third of the document's body. This buries the primary steps ("Use it", the routing table) under reference material most invocations never need.
  - quote: "That usually means the **lexical index is broken**, not that nothing matched. Check first:"
  - proposed fix: Move the repair walkthrough (status check through "Verified 2026-07-29...") to a sibling reference file (e.g. `REPAIR.md`) and replace it in the main skill with a one-line pointer: "If results are empty for everything, the lexical index is likely broken — see REPAIR.md for the diagnostic and fix."
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Pruning — keep each meaning in a single source of truth; duplication (the same meaning restated in two places) costs maintenance and creates ambiguity about which version is authoritative.**: This three-factor formula is restated in 'The loop' step 4 as only two factors — 'rank by (how often an agent hits it) × (how bad the gap is)' — silently dropping blast_radius. The same concept ('priority') now has two inconsistent definitions that must be kept in sync by hand, exactly the maintenance risk the doctrine flags under duplication.
  - quote: "priority = frequency × score_gap × blast_radius"
  - proposed fix: State the formula once (in the dimensions section) and have step 4 reference it explicitly, e.g. 'Prioritize — rank by priority = frequency × score_gap × blast_radius (see dimensions section above); pick the top-leverage batch,' instead of restating a different formula.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning — single source of truth; the same concept restated in two places should not diverge, since divergence forces the agent to guess which version governs.**: The 'crown jewel' error template immediately below defines four components — the what/where line, a one-line WHY, one or more REMEDIATIONS, and a 'see:' pointer line — not three. An agent following the axiom literally could satisfy 'three parts' while omitting the WHY and 'see:' lines the template treats as required, since the two definitions of 'a good error' don't match.
  - quote: "Every error has three parts: (a) what failed, (b) where (`file:line` if applicable), (c) the *exact copy-pasteable command* the agent should have used."
  - proposed fix: Make the axiom's count match the template exactly (e.g. rewrite to 'four parts: what/where, why, remediation(s), and a see: pointer') or explicitly mark WHY/see: as optional in both places, so there is one authoritative definition of what an error must contain.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning — single source of truth: "Keep each meaning in a single source of truth: one authoritative place... Duplication — the same meaning in more than one place — costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank."**: Every bullet here just re-states, in negative form, a rule already given positively earlier in the same document: bullet 1 restates the One Rule callout ('Detect-then-fix, never fix-then-detect') and the mutate() chokepoint description; bullet 2 restates the Safety envelope's 'Backups are verbatim. No reformatting...'; bullet 3 restates both the Safety envelope's 'Never rm -rf, git reset --hard, or DROP TABLE' and the mutate() section's 'The Op enum has NO DeletePath'; bullet 4 restates the content-derived-id rule, the additive-only exit-code dictionary rule, and the 'no TTY, no human to ask' / '--online opt-in' rules from earlier sections; bullet 5 restates the mutate() step-6 footnote on cross-FS rename verbatim. None of these add a new checkable criterion — they duplicate the same meaning a second time, inflating their prominence and creating five places that must be kept in sync if any one rule changes, which is exactly the maintenance and token cost the doctrine warns duplication causes.
  - quote: "## Anti-patterns

- **Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it.
- **Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently.
- **`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead.
- **Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract.
- **Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
  - proposed fix: Cut the Anti-patterns section down to a bare index that points back at the single authoritative statement of each rule instead of re-explaining it, e.g. 'Re-check before shipping: mutate()-bypass (see chokepoint), non-verbatim backup (see safety envelope), DeletePath/destructive ops (see Op enum), random/timestamp ids (see failure-mode ids), cross-FS rename (see mutate step 6).' This keeps the review-checklist function (step 10 references it) without restating each rule's content a second time.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Steps and completion criteria — Clarity: can the agent tell done from not-done?**: Step 2 pipes the assembled prompt from this specific file path, but Step 1 ('Assemble a self-contained prompt') never instructs the agent to write the assembled prompt to $CLAUDE_JOB_DIR/tmp/codex-consult.md. The completion criterion for step 1 is therefore not checkable against what step 2 actually needs — an agent could 'assemble' the prompt in-context and have nothing on disk at the required path, silently breaking the pipeline.
  - quote: "< "$CLAUDE_JOB_DIR/tmp/codex-consult.md""
  - proposed fix: Add an explicit instruction at the end of step 1, e.g. 'Write the assembled prompt to $CLAUDE_JOB_DIR/tmp/codex-consult.md.'
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Pruning — single source of truth / duplication: "Keep each meaning in a single source of truth... Duplication — the same meaning in more than one place — costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank."**: This restates non-negotiable #4 ("prefer `musl` on Linux for static portability") and the code caption ("Prefer `musl` on Linux — static, no glibc skew") as a third, separate assertion of the identical rule. If the target-triple guidance ever changes, it now requires edits in three places instead of one.
  - quote: "**`gnu` target on Linux** — not portable; use `musl` (static)."
  - proposed fix: Delete this Anti-patterns bullet; fold its one new piece of information (that `gnu` specifically is the wrong default) into non-negotiable #4, e.g. "prefer `musl` over `gnu` on Linux for static portability."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Leading words — negation: "Prompt the positive... A prohibition earns its place only as a hard guardrail you cannot phrase positively; even then, pair it with the positive target so attention lands on what to do."**: The bullet already resolves into a positive instruction ("check `:$PATH:`, offer to fix") but then re-appends the negation "don't assume," pulling attention back onto the banned behavior right after it was replaced with a positive one.
  - quote: "**Assuming `~/.local/bin` is on PATH** — check `:$PATH:`, offer to fix, don't assume."
  - proposed fix: End on the positive: "check `:$PATH:`, offer to fix." — drop the trailing "don't assume."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Context pointers: "A pointer does two jobs — state what the material is, and list the branches that should trigger reaching it."**: The pointer names the material ("optional... snippet") but not the branch condition that should trigger reaching it. The actual trigger ("if daemon") lives only in the Build plan's step 15, scattered away from the pointer that would otherwise let an agent decide on the spot whether to open the file.
  - quote: "and the optional systemd/launchd `uninstall_service` snippet, are in [references/PATTERNS.md](references/PATTERNS.md)"
  - proposed fix: State the trigger inline at the pointer, e.g. "...and the optional systemd/launchd `uninstall_service` snippet (only needed if the CLI installs a background service) are in references/PATTERNS.md."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Context pointers — the pointer's wording, not its target, decides when the agent reaches the material; pointers must accurately name reachable material.**: The TOC lists 'Rubric' as a distinct section, but no header of that name exists — the rubric content lives inside '## Decomposition Design (Phase 8)'. Conversely, the TOC omits '## Self-Test', a real terminal section of the document. As an always-loaded navigation pointer, the TOC should name reachable targets exactly; a stale/incomplete index makes the agent's lookup unreliable.
  - quote: "<!-- TOC: One Rule | First-30-Seconds | Quick-Start | Confirmations | Bootstrap | Phases | Parallelism | Convergence | Operators | Taxonomy | Contract | Rubric | GitHub Issues | Anti-Patterns | Checklist | Reference Index -->"
  - proposed fix: Rename the TOC entry to match the real header (e.g. 'Decomposition' instead of 'Rubric', or add an explicit '### Rubric' anchor inside that section) and append 'Self-Test' to the TOC list.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Context pointers must name material that is actually reachable; a pointer with no linked target rides entirely on cognitive load with no way to resolve it.**: 'DEAD-CODE-SAFETY discipline' is named as if it were a defined procedure or document, but no such file or section appears anywhere in the document or the Reference Index, unlike comparable references (e.g. 'AGENTS.md Rule #1' in the ABORT IF list, or '◐ CLUSTER evidence' elsewhere in the Anti-Patterns table, which points to a real operator). The agent has no way to reach the named material.
  - quote: "Silently delete dead code found en route | Record it; route through DEAD-CODE-SAFETY discipline; never delete without permission"
  - proposed fix: Either add a 'DEAD-CODE-SAFETY' entry to the Reference Index pointing to the file/section that defines it, or replace the phrase with a concrete pointer to an existing doc (e.g. AGENTS.md) or inline the actual rule.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Pruning — single source of truth: duplication (the same meaning stated in more than one place) costs maintenance and inflates a meaning's prominence past its real rank.**: The scale(0) rule is fully explained with rationale and code in the "Never animate from scale(0)" section, then restated with the exact fix in the Review Format example table (`transform: scale(0)` → `transform: scale(0.95); opacity: 0`), and restated a third time here in the Review Checklist. Two other checklist rows (ease-in, transform-origin) avoid this by pointing back to their source section ("See ... above"), showing the doc already knows the correct pattern but applies it inconsistently.
  - quote: "| `scale(0)` entry animation                 | Start from `scale(0.95)` with `opacity: 0`                       |"
  - proposed fix: Change this checklist row's fix to a pointer, e.g. "See 'Never animate from scale(0)' above", matching the pattern already used for the ease-in and transform-origin rows.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Pruning — single source of truth: duplication costs maintenance and inflates prominence past its real rank.**: This exact rule (with the same fix and near-identical wording) already appears as the first row of the Review Format example table ("`transition: all 300ms` | `transition: transform 200ms ease-out` | Specify exact properties; avoid `all`"). Neither location is the canonical source and there is no cross-reference between them, so a future change to the recommended duration or property list requires editing two places.
  - quote: "| `transition: all`                          | Specify exact properties: `transition: transform 200ms ease-out` |"
  - proposed fix: Keep the fix in one place — either fold it into the Performance Rules "Only animate transform and opacity" section as the canonical explanation and have both tables point back to it, or delete the duplicate row from one of the two tables.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Pruning — single source of truth / duplication**: This restates the same handoff logic already given in full in Hard Rule 1 ("hand it off: `ce-plan` for a tracked change (carry the exact values from the table into the plan), or `animate` to build it directly when it is small enough not to need a plan"). The same meaning lives in two places with slightly different wording, so a future change to the handoff rule (e.g. adding a third destination) requires editing both and risks drift.
  - quote: "Close by pointing at the handoff: hand the chosen row to `ce-plan` as the origin document (carrying its exact curve, duration and properties verbatim) for a tracked change, or to `animate` to build it now if it is a one-component fix."
  - proposed fix: State the handoff rule once in Hard Rule 1 and have Part 3 reference it briefly, e.g. "Close by pointing at the handoff from Hard Rule 1 for the top row."
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Leading words — coining your own works only if you define it clearly; a made-up word recruits no priors so you pay in definition tokens what a pretrained word gives free.** — verifier: "doghouse tripped" is a coined term for some circuit-breaker/lockout state on Codex, used as if already known, with no definition and no pointer to where it's defined. The agent has no way to recognize this condition when it actually occurs.
  - quote: "If Codex is unavailable (doghouse tripped, auth outage), fall back to a Sonnet-class subagent"
- **Single source of truth — duplication of the same meaning in more than one place, especially when the copies disagree, costs maintenance and confuses which version governs.** — verifier: This directly conflicts with the adversarial-verification pattern stated earlier in the same document — "spawn *independent skeptics* per finding (prompted to refute; kill on majority-refute)" — which describes exactly the N-identical-refuters shape (each skeptic runs the same refute prompt, decided by majority). The document gives two contradictory prescriptions for the same verification step with no reconciliation.
  - quote: "prefer *diverse-lens* verification (correctness / security / does-it-reproduce) over N identical refuters"
- **Context pointers — "One trigger per branch. Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches."** — verifier: "drag/swipe/sheet interactions" is a specific instance of "gesture-driven UI" rather than a distinct branch, and "momentum and interruptible transitions" is the same branch as "spring animations" restated at finer grain (the doc's own Core Idea says springs are the tool for momentum/interruptibility). This inflates the always-loaded description with synonym restatement instead of genuinely distinct triggers.
  - quote: "Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency) behind Apple-style interfaces."
- **Leading words — "Repeated as a token, never as a sentence, it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens."** — verifier: "Response" is already used as the name of an entire top-level principle ("## 1. Response — kill latency", about input/feedback latency) and is then redefined here as a specific spring-timing parameter. The same token now anchors two unrelated concepts in the same document, diluting the leading-word mechanism rather than sharpening it — later references to "response" (e.g. in the Quick Reference table) are ambiguous between the two meanings without re-reading context.
  - quote: "**Response** — how quickly the value reaches the target, in seconds."
- **Pruning — "Keep each meaning in a single source of truth: one authoritative place, so changing the behaviour is a one-place edit... Duplication... costs maintenance and tokens."** — verifier: This restates the concrete damping/response values already given in §4's table (Move/reposition: 1.0/0.4; Drawer tap-triggered: 1.0/0.3). The same numeric defaults now live in two places, so a change to the shipped values requires editing both the §4 table and the Quick Reference row to stay consistent.
  - quote: "| Default UI spring | Critically damped, no overshoot | `damping 1.0`, `response 0.3–0.4` |"
- **Pruning — duplication / cache: 'a document that restates [the environment] is a cache... Without a pruning discipline the default fate is sediment: stale layers that settle because adding feels safe and removing feels risky.'** — verifier: This TOC comment restates the document's own header structure, which the agent already sees directly in the body — pure identity the body already carries, spent for no navigational gain. It has also already gone stale: it omits the 'Done When' section that exists in the current document, demonstrating exactly the drift risk the doctrine warns caches accrue over time.
  - quote: "<!-- TOC: Core Insight | The Loop | Mine & Cluster | Score | Propose | Build | Validate | Anti-Patterns | References -->"
- **Pruning — single source of truth ("Duplication — the same meaning in more than one place — costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.")** — verifier: Every line in this checklist restates a rule already stated verbatim elsewhere in the document: item 1 restates the "Critical rules" list, item 2 restates the "Assume Will knows the IDs" anti-pattern, item 3 restates the "Say precisely WHAT to report back" critical rule, and item 4 restates Workflow step 5 ("wires the values into configs programmatically (Supabase/Vault/Vercel/.env)"). This is the same meaning kept in two places with no single authoritative source, so a future edit to one copy risks leaving the other stale.
  - quote: "- [ ] Instructions follow the template's Critical rules (full URLs, exact element text)
- [ ] All identifiers included (project IDs, refs, callback URLs)
- [ ] Clear "report back" format
- [ ] Programmatic wire-in commands ready (Supabase/Vault/Vercel)"
- **Leading words / negation — a prohibition earns its place only when it cannot be phrased positively, and even then must be paired with (and anchored by) the positive target rather than a repeated negative token.** — verifier: This axiom's leading-word label is negation-framed even though the behavior is trivially phrasable positively (e.g. 'always fail loud'). The doctrine's own test — 'earns its place only as a hard guardrail you cannot phrase positively' — isn't met here. Worse, the negative token '🚫 never-silent-fail' is reused verbatim later as a compact tag in the Intent-Recovery Triad and in the grading ladder ('🚫 silent-fail'), so the repeated leading word anchors the forbidden behavior rather than the desired one, which is exactly the failure mode the doctrine warns against ('the elephant is all there is').
  - quote: "🚫 Never silent-fail."
- **Leading words / negation — prompt the positive; a prohibition should be phrased as the target behavior, not the forbidden one, whenever a positive phrasing exists.** — verifier: The desired behavior ('bare invocation shows help/triage and exits, or is routed to an explicit `tui` subcommand') is directly phrasable in positive form, yet the axiom is named after the prohibited case. This label is the token the agent repeatedly encounters as a leading word, so it anchors on the forbidden behavior instead of the target one.
  - quote: "🚫 No TUI on bare invocation."
- **Pruning — single source of truth: keep each meaning in one authoritative place** — verifier: This restates three of the same categories already enumerated in 'When this is worth the round-trip' (architecture decisions, security review of auth/crypto/user-input/shell-exec, non-trivial algorithms/concurrency reasoning) as a second, independently-worded list. The same meaning now lives in two places that must be kept in sync by hand, risking drift if one list is edited and not the other.
  - quote: "Bump to **`xhigh`** for architecture, security
   audits, or hard algorithm/concurrency questions."
- **Pruning — single source of truth / duplication** — verifier: Duplicates non-negotiable #3 ("passed to every curl call") and the proxy-array code caption ("so every curl call stays unconditional") without adding new information — the same behavioral requirement is stated a third time.
  - quote: "**Ignoring proxy env** — `PROXY_ARGS` on every curl call."
- **Pruning — single source of truth / duplication** — verifier: Restates non-negotiable #6 ("flock-first with mkdir spinlock fallback (macOS has no flock)") verbatim in meaning, with no new caveat, making the rule's authoritative location ambiguous between two sections.
  - quote: "**`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback."
- **Pruning — single source of truth; duplication of the same meaning in multiple places costs maintenance/tokens and inflates the meaning's prominence past its real rank.** — verifier: The exact convergence rule (≥10 rounds, 2 consecutive quiet rounds, all hypotheses resolved, DEFERRED+'Deferred reviewed: yes') is stated in full three separate times: in the Quick-Start block (quoted here), again as an ABORT IF bullet ('You think the ≥10-round convergence floor is optional...'), and a third time nearly verbatim under '## Convergence (non-negotiable)'. Each restatement risks drifting from the others on future edits, and there is no single authoritative definition.
  - quote: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings
              AND every hypothesis resolved (SEAM_CONFIRMED / SEAM_REFUTED /
              DEFERRED+rationale with `Deferred reviewed: yes`)."
- **Pruning — single source of truth / co-location: a concept's definition and rules should live under one heading rather than scattered across the document.** — verifier: This restates the exact guidance already given in full, with rationale and code, under "Make popovers origin-aware" ("Popovers should scale in from their trigger, not from center... The default `transform-origin: center` is wrong for almost every popover"), and is also present as a row in the Review Format table. The same meaning is now scattered across three sections instead of grouped under one, and the Checklist row for this topic already correctly points back to "Make popovers origin-aware" rather than restating it.
  - quote: "Every element has an anchor point from which transforms execute. The default is center. Set it to match where the trigger lives for origin-aware interactions."
- **Negation is a failure mode: steering by prohibition drags the forbidden behavior into context, making it more available rather than less. Prompt the positive; a spelled-out negative example should only be included as a hard guardrail, and even then should not duplicate a positive instruction that already fully specifies the target.** — verifier: The required format is already fully specified positively just above ("you MUST use a markdown table with Before/After columns... Always output an actual markdown table like this:" followed by a complete correct example). This block adds a fully-rendered example of the banned list-style format on top of that, which per the doctrine's negation guidance makes the forbidden pattern more salient in context rather than less, without adding information the positive example didn't already convey.
  - quote: "Wrong format (never do this):

```
Before: transition: all 300ms
After: transition: transform 200ms ease-out
────────────────────────────
Before: scale(0)
After: scale(0)
```"
- **Context pointers — one trigger per branch (synonyms that rename a single branch are one branch written twice; collapse them)** — verifier: Both quoted phrasings trigger the exact same branch — running this search skill to surface opportunities. They aren't distinct cases the skill handles differently; they're two vocabularies for one trigger. Since the description is always-loaded for routing, the extra phrasing pays context cost without adding a genuinely new branch.
  - quote: "Use when the user asks "what could be animated here?" or wants to "make this feel more alive"."
- **Pruning — environment as source of truth; cache what can't be found by looking, not one-file lookups that can go stale** — verifier: This skill is repo-agnostic (per the Recon step's instruction to identify 'existing easing/duration tokens' from whatever codebase is being swept), yet the output format states specific hardcoded token names and cubic-bezier values as if they are '`this repo's` shared vocabulary' — a fact only true for one particular codebase. Presented without qualification as an example, this contradicts the earlier discovery step and risks being applied verbatim to repos that use different token names.
  - quote: "pulled from this repo's shared vocabulary (`--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)`, `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)`), never approximated"
