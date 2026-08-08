# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $4.2015 spent
- verify: 153 trial(s), $3.0469 spent

## Run manifest

- run: `swapgate5-probe-doctrine-v2` (2026-08-08T03:13:41Z → 2026-08-08T04:15:37Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/skills/skill-tuner/SKILL.md` | `b81b22f9884f` | git:origin/main @ b7e2cc2244b2 |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0dc154c88283` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `7d2290123e00` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `a8d1903218b1` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `2d965c7d2ff9` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `824fdef96119` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `808fcc7103af` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `b6e7cba9bcb5` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `6bcf11e24d2f` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `291233457df4` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `a14d423610c4` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `c6db47a75b83` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `ce83411bd389` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `e55823e32a45` | git:origin/main @ e46a8ca22461 |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `9ab5c7a6100c` | git:origin/main @ e46a8ca22461 |

## Marginal-value probe verdict

**findings_confirmed: 27**

- doctrine: /home/will/SITES/skill-tuner/skills/skill-tuner/SKILL.md
- targets: 15
- probe calls: 15
- verify calls: 153 (3 skeptic(s) per finding)
- refuted: 24

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 0 | 1 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 4 | 0 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 1 | 4 |

### Confirmed findings

- **Cut identity the body already states [craft]**: This sentence states what the skill *is* (a shared layer other skills route through) rather than *when* to reach it, and duplicates the identity claim already made in the file's own scope note ("Skills that need campaign-scale parallelism reference this instead of re-deriving swarm coordination") and the H1/core-shift framing. It adds permanent context load with no branch/trigger signal.
  - quote: "The shared swarm/delegation layer other skills route through for scale."
  - proposed fix: Remove the sentence from the description; if cross-skill discoverability is the goal, state it once in the body (it already is, in the intro comment) rather than in the always-loaded pointer.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Demand**: This Never Ship row is otherwise a precise, checkable list (named properties, named keyframe cases, named thresholds), but 'with no reason' is an uncheckable qualifier — the agent can satisfy the whole row impressionistically by inventing any justification for a long duration, defeating the self-check the table exists to provide.
  - quote: "UI duration over 300ms with no reason"
  - proposed fix: Drop the qualifier and state the real exception explicitly, e.g. 'UI duration over 300ms outside modals/drawers' or just 'UI duration over 300ms' and let the Duration table's modal/drawer row stand as the sanctioned exception.
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Demand [craft] — criteria that mix checkable and uncheckable terms let the agent satisfy the whole thing impressionistically; watch for a stray uncheckable qualifier inside an otherwise precise list.**: This item sits in a list explicitly labeled 'the feel checklist' alongside concrete, measurable items (~10px hysteresis threshold, ~10px hit padding), but 'confidently' and 'once intent is clear' are impressionistic qualifiers with no checkable bound, letting the whole item be satisfied by judgment rather than a verifiable condition.
  - quote: "then confidently cancel the losers once intent is clear"
  - proposed fix: Tie cancellation to the same measurable threshold already used elsewhere: "then cancel the losers once movement crosses the ~10px direction threshold defined above."
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **One trigger per branch**: The description lists two trigger phrases at the end, but both route to the exact same path through the document (mine history → cluster → score → propose → build). 'Analyzing command patterns' and 'finding automation opportunities' don't diverge into different handling anywhere in the body; they're one branch described twice, paying context-load cost twice for a single routing decision.
  - quote: "analyzing command patterns or finding automation opportunities."
  - proposed fix: Collapse to a single trigger phrase, e.g. 'Use when hunting for automation opportunities in your command history.' and drop the redundant 'analyzing command patterns' synonym.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Completion criteria / Demand**: This checklist item sits among otherwise checkable bounds (5x run, --dry-run produces no side effects, --json parses, ≥3x faster) but 'verify graceful behavior' requires judgment to evaluate — there's no stated condition distinguishing 'graceful' from 'not graceful.' One uncheckable qualifier inside an otherwise precise checklist lets the whole validation step be satisfied impressionistically.
  - quote: "Force failure → verify graceful behavior"
  - proposed fix: Replace with a checkable bound, e.g. 'Force failure → confirm the process exits non-zero, prints a one-line error to stderr, and leaves no partial output files.'
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Progressive disclosure**: The upstream-sync/cherry-pick procedure is relevant only to the rare maintenance branch of updating this fork from jsm — it's never needed on the ordinary mine/cluster/score/build path this skill exists for. It's inlined at the very top of the file instead of behind a pointer, so every invocation pays its context-load cost even though only a fork-maintenance task reaches it.
  - quote: "Upstream sync is NOT automatic."
  - proposed fix: Trim the header comment to a one-line fork marker ('LOCAL FORK — not managed by jsm') and move the cherry-pick/sync procedure to a disclosed reference (e.g. references/UPSTREAM-SYNC.md) reached only when a sync task is underway.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Relevance and sediment**: This HTML comment is plain text loaded into the agent's context on every invocation (comments aren't stripped from a file read as text). It records the skill's distillation lineage — a fact about the document's history, not something that bears on performing the harmonization task. It pays permanent context load for zero task-relevant signal, the textbook definition of sediment.
  - quote: "Distilled 2026-07-04 from the retired 130-file `git-worktree-branch-rationalization`
     skill: kept the archaeology + harmonization + safety kernel; dropped the multi-agent
     swarm tiers, wizard-style adjudication, fuzzing/conformance testing, per-language
     deep-dives, the Bayesian machinery, and the 30 subagents."
  - proposed fix: Delete the comment from the skill body, or move the lineage note to a git commit message / CHANGELOG outside the always-loaded file.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **One trigger per branch**: This closing sentence renames the same branch already stated in the description's opening clause ("forgotten branches/worktrees left by parallel agents"). A run reaching the skill via "parallel-agent branch cleanup" takes the identical path as one reaching it via "forgotten branches/worktrees left by parallel agents" — it's one branch billed twice in an always-loaded field.
  - quote: "Use for parallel-agent branch cleanup."
  - proposed fix: Drop the trailing sentence, or replace it with a genuinely distinct trigger the opening clause doesn't already cover (e.g. naming the RESIDUE hand-off point explicitly: "Use after wt-sweep.sh/branch-triage.sh leave un-disposed RESIDUE").
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Cut identity the body already states [craft]**: This restates the Voice Profile's own structure, which the body already documents exhaustively under '## The Voice Profile (Output Format)' (Tone Spectrum, Vocabulary, Mechanical Rules, On-Brand/Off-Brand Example Phrases, Aspiration Models, Anti-Aspiration, Quality Test headings). It describes what the skill produces, not when to reach it, so it adds permanent context load with no routing signal.
  - quote: "Outputs a complete Voice Profile with tone spectrum, vocabulary, mechanical rules, on-brand and off-brand example phrases, aspiration and anti-aspiration models, and a quality test."
  - proposed fix: Remove this sentence from the description and let the body's Output Format section be the single place that states the profile's structure.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Completion criteria / Demand [craft]**: This criterion sits in a list otherwise anchored by checkable items like "Mechanically clean: does it pass every Mechanical Rule above?" but itself requires judgment ("feel true") with no observable bound. Since the Quality Test gates whether to lock in the profile ("If any answer is no ... Iterate before locking it in"), this stray uncheckable qualifier lets the whole gate be satisfied impressionistically.
  - quote: "**Authentic:** does it feel true to who they are or want to be?"
  - proposed fix: Replace with a checkable version, e.g. "Authentic: does every trait trace back to a specific answer from Q1-Q4 (Extract: an observed pattern) rather than an aspirational or generic label?"
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Cut identity the body already states [craft]**: This clause restates the body's "Core pattern" blockquote almost verbatim ("Open the exact URL in Will's real Windows Brave, hand him precise paste-ready clicks, get the resulting IDs/secrets back, then wire them in programmatically"). It's identity the body already states in full, so it adds permanent context load on every turn with no added routing signal — the description's job here should be limited to naming the trigger conditions.
  - quote: "by opening the exact URL in the local Windows Brave browser and handing paste-ready click steps, then wiring the reported credentials into Supabase/Vault/Vercel/.env"
  - proposed fix: Trim the description to the routing conditions and drop the mechanism restatement, e.g. "Set up cloud consoles that block headless automation (Google OAuth consent, Stripe webhooks, GCP credentials). Use when a console step cannot be scripted: bot detection, 'browser may not be secure', 2FA, or CAPTCHA." and let the body's Core pattern blockquote be the sole statement of the mechanism.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **One trigger per branch [craft]**: The always-loaded description states the same branch condition (use cass-rerank for a single best result vs. plain cass for a broad scan) twice in different wording — 'most relevant past session first' / 'INSTEAD of bare cass search' duplicates 'top-1/top-few results' / 'fall back to plain cass for broad scans' — plus stacks three synonymous examples ('past fixes, decisions, "how did I do X"') for that one branch. Per the doctrine, synonyms renaming a single branch pay their context-load cost multiple times while routing only once.
  - quote: "Use INSTEAD of bare `cass search` when you want the most relevant past session first (past fixes, decisions, "how did I do X"). Prefer this for top-1/top-few results; fall back to plain cass for broad scans."
  - proposed fix: Collapse to a single statement of the branch, e.g.: 'Use INSTEAD of bare `cass search` for top-1/top-few results (e.g. finding the one session that fixed X); fall back to plain cass for broad scans.' Drop the redundant second sentence and the extra example synonyms.
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Demand [craft] — watch for criteria that mix checkable and uncheckable terms; one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.**: The numeric thresholds (≥5, ≥3) are checkable, but "substantive" is not — nothing in the document defines what makes a change substantive, so the agent can decide for itself that trivial edits qualify and satisfy the whole gate impressionistically.
  - quote: "ship ≥5 substantive changes across ≥3 dimensions before calling it done"
  - proposed fix: Replace the qualifier with a checkable proxy, e.g. "ship ≥5 changes, each traceable to a named operator or Recurring Fixes item, across ≥3 dimensions."
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Completion criteria [craft] — a bound is checkable when the agent can tell done from not-done without judgment.**: "Confirm uplift" has no defined measure to check against: the doctrine's own scoring machinery ("per-pass 0-1000 scoring") was explicitly dropped from this distilled skill, and the 11-dimension section gives no scale, so there is no way to tell "uplift confirmed" from "not confirmed" without judgment.
  - quote: "re-run the affected surfaces; confirm uplift; run the project's lint/typecheck/tests"
  - proposed fix: Give the check a concrete bound, e.g. "re-run the 11-dimension score sheet and confirm no targeted dimension regresses and each targeted dimension moves from fail to pass."
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Leading words [craft] — coining your own symbol works only if you define it clearly; a made-up anchor that maps to more than one meaning stops functioning as an anchor.**: The 🚫 icon is used as the leading symbol for two distinct kernel axioms ("Never silent-fail" and "No TUI on bare invocation"). A single coined icon standing for two unrelated concepts can't do reliable anchoring work — later mentions of 🚫 (e.g. in the grading ladder) are ambiguous between the two definitions.
  - quote: "🚫 No TUI on bare invocation."
  - proposed fix: Give the TUI axiom its own distinct icon instead of reusing 🚫, e.g. reserve 🚫 for "never silent-fail" only.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Relevance and sediment [craft] — every line must still bear on what the document does; a line that never matters to the task is sediment kept because removing feels risky.**: This always-loaded HTML comment enumerates features removed from a retired 192-file predecessor skill. None of it bears on executing the current skill — it's a history of what isn't there, paid for on every turn.
  - quote: "per-pass 0-1000 scoring machinery, agent-profile reweighting, 27 subagents, and 47 scripts."
  - proposed fix: Delete the list of dropped features from the comment; keep only a one-line pointer to references/ERGONOMICS-SPEC.md if that isn't already stated in the body (it is, in the Named operators section).
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Completion criteria — sharpen a vague bound before relying on judgment**: "Until clean" gives no way to tell done from not-done without judgment — it's the same shape as the doctrine's "verify the config" counter-example. Paired with "no doctor is ever done," the step has no checkable exit condition at all, inviting the agent to stop whenever it feels satisfied.
  - quote: "**Iterate** — a fresh-eyes/adversarial re-read until clean; re-mine as the project evolves (no doctor is ever "done")."
  - proposed fix: State a checkable exit condition, e.g. "re-read adversarially until no dimension in the 10-dim rubric scores below N for any implemented FM; re-run this step whenever a new FM is added."
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Context pointers — a pointer must name the out-of-context material and the condition for reaching it**: "The cookbook" is never introduced or pointed to anywhere in the instructional body. The only place its location (`references/DOCTOR-SPEC.md`) is stated is the HTML distillation comment at the top of the file, which is editorial metadata, not an agent-facing pointer. An agent executing the build loop has no stated way to reach the material this step tells it to consult.
  - quote: "match against the cookbook pattern"
  - proposed fix: Add an explicit pointer where "cookbook" is first used, e.g. "match against the failure-mode cookbook in [DOCTOR-SPEC.md](references/DOCTOR-SPEC.md#cookbook)", and drop the reliance on the dev comment to carry that routing information.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Relevance and sediment — every line must bear on what the document does**: This editorial history of what was kept/dropped from a retired 166-file skill never bears on performing the doctor-mode task itself; it is provenance for a future human editor, not routing or execution guidance, yet it is inlined in the body and loaded on every use of the skill.
  - quote: "Distilled 2026-07-04 from the retired 166-file `world-class-doctor-mode-for-cli-tools` skill:
     kept the One Rule + core axioms, the CLI surface, the mutate() chokepoint / safety envelope,
     the (detector,fixer,fixture,test) tuple, the 10-dim rubric, and the portable cookbook. Dropped
     the multi-model swarm tiers, session-mining, external issue-tracker plumbing, the per-run 0-1000
     scoring machinery, 18 subagents, and 39 scripts."
  - proposed fix: Move the distillation rationale to a CHANGELOG or the repo's PR description, keeping only the still-needed routing fact (JSON shapes, rubric, and cookbook live in references/DOCTOR-SPEC.md) as a proper in-body pointer.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **One trigger per branch**: The three phrasings — "install.sh", "curl-pipe-bash installer", "one-liner install for a Rust/TS/Go CLI" — all name the same single branch (writing this kind of installer). A run reaching the document through any one of them takes the identical path through the body; they don't split into distinct handling. This is one branch written three times, paying triple context cost to route once.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer, or a one-liner install for a Rust/TS/Go CLI."
  - proposed fix: Collapse to one trigger, e.g. "Use when writing a curl|bash install.sh one-liner for a Rust/TS/Go CLI."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Cut identity the body already states**: This restates, in the always-loaded description, the exact fact already recorded in the body's HTML comment ("This version is self-contained: real snippets inline, no external line-refs"). It carries no routing signal — it doesn't help decide whether to reach the document, only describes an attribute of the document itself — so it's paying permanent context load for nothing.
  - quote: "Self-contained (real bash inline)."
  - proposed fix: Drop the sentence from the description; leave the self-contained/real-snippets fact only in the body's introductory comment, where it's read once rather than loaded every turn.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Progressive disclosure**: Non-negotiable #12 (final summary box) and #13 (uninstall instructions) are required on every run of every installer this skill produces — not just the AI-agent-integration branch. Bundling draw_box and the uninstall snippet behind the same pointer as the genuinely branch-specific agent-hook-config material means universal-need code rides on a pointer meant for branch-only reference, so a run that never touches AI-agent detection still has to remember to open PATTERNS.md for material every run needs.
  - quote: "the `draw_box` implementation, and the uninstall/service snippets are in
[references/PATTERNS.md](references/PATTERNS.md)"
  - proposed fix: Inline the draw_box and uninstall-instructions snippets in the main body next to non-negotiables #12/#13, and keep only the agent-detection/JSON-merge pattern and the optional systemd/launchd service snippet disclosed in references/PATTERNS.md.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Demand**: "works" is an uncheckable qualifier tacked onto two otherwise precise, checkable clauses in the same checklist line. The agent can satisfy "dual tool" and "soft-skip/hard-fail" concretely, but there is no bound for what "works" means for the source-build fallback, letting that half of the item be ticked off impressionistically.
  - quote: "SHA256 (dual tool) + Sigstore (soft-skip / hard-fail); build-from-source fallback works"
  - proposed fix: Replace with a checkable bound, e.g. "build-from-source fallback: --force --from-source on a clean checkout produces a runnable binary at $DEST."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Demand [craft]**: Mixes a checkable count ("4–5 rounds") with an uncheckable qualifier — "the same standard as the plan itself" is never operationalized anywhere in the document — letting the agent satisfy the whole bound impressionistically by hitting the round count without a way to verify the polish quality itself.
  - quote: "Polish 4–5 rounds against the same standard as the plan itself"
  - proposed fix: Replace the qualifier with a checkable bound, e.g. "Polish 4–5 rounds; each round confirms every field carried from phase8_decomposition_plan.md (winner, runners-up, migration mechanics) is still present verbatim in the issue body."
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Demand [craft]**: This sentence is part of the Review Format's required-output specification, which is otherwise fully checkable (table with named columns, one row per issue). 'Briefly explains the reasoning' is an uncheckable qualifier smuggled into that precise list, letting the agent satisfy the Why column impressionistically rather than against a fixed bound.
  - quote: "The "Why" column briefly explains the reasoning."
  - proposed fix: Replace with a checkable bound, e.g. 'The Why column states the specific rule violated, in one sentence.'
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth [craft]**: This exact rule (never `scale(0)`, use `scale(0.95)` + `opacity: 0`) is stated three separate times: the Review Format example table, the dedicated '### Never animate from scale(0)' section, and this Review Checklist row. The same triplication pattern recurs for the ease-in rule and the transform-origin/popover rule. Each value now has three places to edit if it changes, and the checklist inflates rules already fully covered in-body.
  - quote: "| `scale(0)` entry animation                 | Start from `scale(0.95)` with `opacity: 0`                       |"
  - proposed fix: Keep the full rule only in its dedicated section; have the checklist and Review Format example link back to that section by name (e.g. 'scale(0) entry — see Never animate from scale(0)') instead of restating the fix value.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Cut identity the body already states [craft]**: This identity claim in the pointer is restated by the body twice more: the intro ('...or write the implementation itself') and Hard Rule 1 ('This skill reports; it does not implement.'). The pointer's job is when to reach the skill, not what it is — this clause adds permanent load with no routing signal since the same fact is authoritative in the body.
  - quote: "Read-only; it proposes motion with exact values, it does not implement it."
  - proposed fix: Drop the sentence from the description and let the body's intro paragraph and Hard Rule 1 carry the read-only/no-implementation fact.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **One trigger per branch [craft]** — verifier: "has many independent units" and "N-independent-units work" name the same branch twice with different phrasing. A run reaching the skill through one phrase takes the same path as one reaching it through the other, so the second instance pays permanent context load on every turn without adding routing signal.
  - quote: "Use when a task is too big for one context or has many independent units: whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work, or when you need multiple independent perspectives (adversarial verification)."
- **Single source of truth** — verifier: The curve value cubic-bezier(0.23, 1, 0.32, 1) is hardcoded here identically to its definition in the `--ease-out` token block above. If the token's value is ever tuned, this literal copy in the Never Ship table has no mechanical link to it and can silently drift out of sync — exactly the fork Hard Rule 3 ('extend the codebase's tokens, don't fork them') warns against, applied to the document's own content.
  - quote: "| Built-in `ease-out` on a deliberate animation | `cubic-bezier(0.23, 1, 0.32, 1)` |"
- **Single source of truth** — verifier: This blanket statement directly contradicts the Duration table's own 'Modals, drawers | 200–500ms' row immediately above it, which explicitly sanctions durations up to 500ms for UI elements (modals/drawers are UI, per the Build Sequence's own tier table). An agent applying the '300ms' rule to a modal can't tell done from not-done without judgment, since two authoritative-looking statements disagree.
  - quote: "**UI animations stay under 300ms.**"
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context; prohibition should be paired with its positive target, not lead a rule that never says what to do instead.** — verifier: This bullet is pure prohibition with no positive target anywhere in the section — it never states what the agent should do instead (e.g. keep pointer/touch listeners live). The surrounding bullets address interrupt-from-value and library choice, not input lockout, so nothing else in the section fills the gap.
  - quote: "Never lock out input during a transition."
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context; prohibition should be paired with its positive target, not lead a rule that never says what to do instead.** — verifier: This bullet leads with a ban and gives only the failure mode (legibility collapses), never the positive alternative (what to put beneath a light translucent surface instead). No other bullet in the Materials & depth section supplies that alternative.
  - quote: "Never stack a light translucent surface on another — legibility collapses."
- **Negation** — verifier: This bullet leads with the ban ('Never skip') rather than stating the required behaviour directly, and the sentence itself never restates the positive target — it only gestures at it via 'data wins.' Per the doctrine, prohibition should be reserved for hard guardrails paired explicitly with their positive target, not used as the lead phrasing of a rule.
  - quote: "**Never skip 1-3.**"
- **Cut identity the body already states** — verifier: The body's opening blockquote ("The core move... the job is NOT 'pick the right branch'... That synthesis is harmonization") already states this identity at length. Repeating it in the always-loaded description adds permanent context cost with no additional routing signal — the pointer's job is to say when to reach the skill, not to re-explain what harmonization is.
  - quote: "the judgment layer over wt-sweep.sh/branch-triage.sh that harmonizes competing variants rather than picking one winner"
- **Completion criteria** — verifier: This reads as a checkable numeric bound, but "Confidence" is never defined or computed anywhere in the document — unlike fingerprint_coverage, file_existence_coverage, and the ≥30% signature-divergence threshold, which are all explicitly derived. Without a stated formula, the agent cannot tell done (confident) from not-done (not confident) without judgment, so the 0.7 threshold is precision theater over an impressionistic call.
  - quote: "Confidence < 0.7 ⇒ don't auto-classify; surface to the user."
- **One trigger per branch [craft]** — verifier: "persona" appears as a trigger in the first 'Use when' list, then reappears as "a new persona needs voice definition" in the second 'Use when' list. A run reaching the skill via 'persona' and one reaching it via 'a new persona needs voice definition' take the same path -- it's one branch written twice, paying context load twice for one route.
  - quote: "Use when starting a new brand, sub-brand, product, persona, or author voice. Outputs a complete Voice Profile with tone spectrum, vocabulary, mechanical rules, on-brand and off-brand example phrases, aspiration and anti-aspiration models, and a quality test. The profile is structured so it can be encoded as a project-specific brand-voice skill afterward. Use when copy sounds generic, when a new persona needs voice definition, or when the answer to "how should this sound?" is unclear."
- **Negation [research]** — verifier: This closing admonition leads with the ban ("Don't skip the encoding step") and follows it with a consequence, not a restated positive instruction in the same breath -- the tell the doctrine flags. It drags "skip the encoding step" into context as the most available frame instead of reinforcing the concrete action.
  - quote: "Don't skip the encoding step: a profile that isn't wired into a skill gets ignored."
- **One trigger per branch [craft]** — verifier: "Google OAuth consent" in the parenthetical example list and "OAuth consent screens" in the trigger list name the same branch twice with different wording. A run reaching the doc via either phrase routes to the same content (the Google OAuth playbook), so the second mention pays context load without adding a distinct routing path.
  - quote: "Set up cloud consoles that block headless automation (Google OAuth consent, Stripe webhooks, GCP credentials) by opening the exact URL in the local Windows Brave browser and handing paste-ready click steps, then wiring the reported credentials into Supabase/Vault/Vercel/.env. Use when a console step cannot be scripted: bot detection, "browser may not be secure", 2FA, CAPTCHA, or OAuth consent screens."
- **Demand [craft]** — verifier: This checklist item sits among otherwise checkable items ("URLs verified", "Element names match the current UI exactly", "All identifiers included") but "Clear" is an uncheckable qualifier — the agent cannot tell a clear format from an unclear one without judgment, letting it check the box impressionistically.
  - quote: "Clear "report back" format"
- **Completion criteria [craft]** — verifier: The step names a mechanism (re-read via API) but not a comparison, so it stops short of a checkable bound — the doctrine's own worked example distinguishes "verify the config" (uncheckable) from "re-read the config via the API and confirm the field equals the value you wrote" (checkable). As written, the agent can satisfy this step by reading the API response without confirming it matches the value it wrote.
  - quote: "Verify (re-read the config via API)"
- **Demand [craft]** — verifier: 'Results look unranked' is a judgment call, not a checkable condition — the agent cannot reliably tell 'looks unranked' from 'looks ranked' without inference. This is the kind of stray uncheckable qualifier the doctrine warns lets a criterion be satisfied impressionistically instead of on a verifiable bound.
  - quote: "check health explicitly if results look unranked"
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context; keep prohibition only as a hard guardrail paired with its positive target. The tell is a rule that leads with the ban and never says what to do instead.** — verifier: Unlike its neighboring bullets in the same Anti-patterns list, which each pair the ban with a positive fix, this bullet stacks three banned behaviors with no accompanying "do X instead" in the same breath.
  - quote: "**Bare `<tool>` opening a TUI**; **exit 1 meaning "no results"**; **prompting for confirmation** in a non-TTY."
- **Demand — watch for criteria that mix checkable and uncheckable terms** — verifier: This is the first item in a 10-dimension scoring list where every other dimension (agent_ergonomics, data_safety, idempotence, reversibility, etc.) is stated as a checkable fact (byte-identical backups, exit codes, stable schema_version). "Can an agent guess the right invocation" is a subjective judgment call with no bound for telling a pass from a fail, so it lets the whole rubric be scored impressionistically once this one stray uncheckable qualifier is present.
  - quote: "**agent_intuitiveness** — can an agent guess the right invocation from `--help` alone?"
- **Demand [craft]** — verifier: This catch-all sits inside an otherwise checkable list (≥2 failed fixes, specific security paths like auth/crypto/user-input/shell-exec). Per the Demand rule, one stray uncheckable qualifier inside an otherwise precise list lets the whole criterion be satisfied impressionistically — 'low-confidence' has no checkable bound, so it licenses invoking Codex for any question at all, undermining the specificity the rest of the list establishes.
  - quote: "Anything you (Claude) are low-confidence on"
- **One trigger per branch [craft]** — verifier: Four trigger phrases route to only two distinct branches: "de-monolithize" and "modularize repo" both land on the whole-repo/Standard path, and "split giant file" and "file too big" both land on the single-file/Quick path (confirmed by the Recipe Selector table, which maps 'Split this ONE file' to Quick and 'De-monolithize the repo (generic)' to Standard). Per the doctrine, synonyms that rename a single branch pay context load on every turn but route only once.
  - quote: "Use when de-monolithize, split giant file, modularize repo, or file too big."
- **Negation [research]** — verifier: This parenthetical leads with two bans and never states the positive target — what a correctly-preserved, non-oversimplified issue looks like — which per the doctrine drags 'oversimplify' and 'lose features' into context as the most available concepts rather than steering toward the desired behavior.
  - quote: "(DO NOT OVERSIMPLIFY; DO NOT LOSE FEATURES)"
- **Front-load the leading word [craft]** — verifier: The description pointer opens with throat-clearing ('This skill encodes...') instead of leading with the trigger word, spending the most-read position on self-identification rather than routing signal — the exact anti-pattern the doctrine names ('This skill provides guidance on...').
  - quote: "This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great."
- **One trigger per branch [craft]** — verifier: The skill does exactly one thing (it says so itself: 'It does ONE thing'), so there is only one branch to route to. These two quoted phrases are synonyms for entering that single branch, not distinct triggers for distinct paths — a run reaching the skill through either phrase executes the identical workflow. Per the doctrine, synonyms that rename a single branch are one branch written twice.
  - quote: "Use when the user asks "what could be animated here?" or wants to "make this feel more alive"."
- **Completion criteria [craft]** — verifier: This is the closing instruction of Step 1 (Recon) but gives no checkable done-condition — 'rough' is inherently a judgment call, and there is no bound analogous to Step 2's explicit 'Done when every seam class has either yielded candidates with file:line evidence or been explicitly cleared.' The agent cannot tell when Recon is finished versus merely started.
  - quote: "Build a rough frequency map of the surfaces you'll judge."
- **Demand [craft]** — quote_not_found: 'Through all four questions' is a checkable criterion (each candidate is scored pass/fail on each). 'Be ruthless' is an uncheckable qualifier tacked onto it, letting the agent satisfy the whole instruction impressionistically — e.g. skipping or softening a question while still feeling it was 'ruthless' — exactly the mixed checkable/uncheckable pattern the doctrine warns about.
  - quote: "Gate every candidate through all four questions. Be ruthless."
- **Completion criteria [craft]** — verifier: This budget directly contradicts the section's own framing, 'The suggestion must work within the standard budgets (UI under 300ms)', stated immediately above the table. A modal/drawer suggestion at 350–500ms is simultaneously inside the table's stated budget and outside the '300ms' ceiling, so the agent cannot tell pass from fail without guessing which number governs.
  - quote: "| Modals, drawers | 200–500ms |"
