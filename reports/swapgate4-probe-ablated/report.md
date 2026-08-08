# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 16 trial(s), $4.4082 spent
- verify: 177 trial(s), $3.6634 spent

## Run manifest

- run: `swapgate4-probe-ablated` (2026-08-08T01:10:20Z → 2026-08-08T02:17:02Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/experiments/ablation-no-apparatus/SKILL.md` | `321c68e718fa` | git:origin/main @ db67f4614d32 |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0dc154c88283` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `7d2290123e00` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `a8d1903218b1` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `2d965c7d2ff9` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `824fdef96119` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `808fcc7103af` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `b6e7cba9bcb5` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `6bcf11e24d2f` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `291233457df4` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `a14d423610c4` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `c6db47a75b83` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `ce83411bd389` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | `d71863fc644d` | git:origin/main @ 33d88ebd138d (differs-from-worktree) |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `e55823e32a45` | git:origin/main @ 33d88ebd138d |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `9ab5c7a6100c` | git:origin/main @ 33d88ebd138d |

## Marginal-value probe verdict

**findings_confirmed: 26**

- doctrine: /home/will/SITES/skill-tuner/experiments/ablation-no-apparatus/SKILL.md
- targets: 16
- probe calls: 16
- verify calls: 177 (3 skeptic(s) per finding)
- refuted: 33
- overflow (beyond max_findings cap, not verified): 2

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 1 | 4 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 0 | 3 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 5 | 0 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 2 | 1 |

### Confirmed findings

- **Single source of truth**: This restates, near-verbatim, a rule already given twice earlier: 'Pin `model` (sonnet/haiku for mechanical sweeps — don't let them inherit the session model)' in 'Pick the lightest engine' and 'Pass `model` explicitly — unpinned subagents silently inherit the session model.' in 'Cost routing'. The same meaning appears in three places, inflating its rank on the ladder past its real importance.
  - quote: "**Unpinned mechanical subagents** — they inherit the expensive session model; pin `sonnet`/`haiku`."
  - proposed fix: State the pin-the-model rule once (e.g., in Cost routing) and drop the restatements in 'Pick the lightest engine' and 'Anti-patterns', or replace the Anti-patterns entry with a one-line cross-reference instead of a full restatement.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Single source of truth**: The duration table allows modals/drawers up to 500ms, but the very next line states "**UI animations stay under 300ms.**" and the Never Ship checklist separately blocks "UI duration over 300ms with no reason" with 150–250ms as the fix. The same meaning (the allowable duration ceiling) is stated in three places with conflicting numbers, leaving the agent no way to know whether a 400ms modal exit is compliant.
  - quote: "| Modals, drawers | 200–500ms |"
  - proposed fix: Reconcile the numbers: either cap modals/drawers at 300ms in the table, or explicitly mark modals/drawers as the named exception to the 300ms rule (e.g. "UI animations stay under 300ms, except modals/drawers which may run to 500ms given their larger footprint") and update the Never Ship row to match.
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Demand [craft]**: Every other technique bullet in the document gives a concrete, checkable value (e.g. '-0.02em' tracking, '~10px' hysteresis, 'decelerationRate ≈ 0.998', 'damping 1.0'). This bullet instead uses uncheckable qualifiers ('higher-contrast', 'slightly heavier', 'small... bump') with no numbers, so an agent implementing it has no criterion for how much is enough — weak demand where the surrounding document's pattern sets an expectation of concrete values.
  - quote: "use higher-contrast, slightly heavier weight, and a small letter-spacing bump"
  - proposed fix: Give a concrete anchor consistent with the rest of the doc, e.g. 'raise contrast to at least 4.5:1, bump weight one step (e.g. regular → medium), and add ~0.01em letter-spacing.'
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Completion criteria — every step ends on a condition telling the agent the work is done; a vague bound invites premature completion**: "all pattern types" is never defined as a term anywhere in the document — the mining section names concrete query targets (repeated commands, multi-step workflows, high-failure commands, per-cwd repetition) but never labels them "pattern types." The checklist item therefore gives the agent an uncheckable bound for the final completion gate, inviting it to mark the box done without a way to verify what "all" refers to.
  - quote: "History mined (atuin or bash) for all pattern types"
  - proposed fix: Replace with the concrete, enumerable set: "History mined (atuin or bash) for repeated commands, multi-step workflows, high-failure commands, and per-cwd repetition."
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and inflates that meaning's rank on the ladder**: Every bullet here restates a meaning already stated once elsewhere: bullet 1 repeats 'The core move' callout at the top ('the job is NOT "pick the right branch"'); bullet 2 repeats Safety kernel rule 2 ('Land on a staging branch, never on canonical'); bullet 3 repeats Safety kernel rule 3 ('git cherry -v ... Trust it over git log ancestry'); bullet 4 repeats Phase A's 'the branch name is a hint, not a verdict... Let the fingerprint override the name every time'; bullet 5 repeats Safety kernel rules 6-7 (verbatim authorization, no mass-delete); bullet 6 repeats the Pipeline section's 'Don't re-implement their funnel here; start from what they couldn't resolve.' This inflates each rule's apparent importance and creates six places to keep in sync instead of one.
  - quote: "## Anti-patterns

- **Picking a winner among colliding branches.** That's the failure this skill exists to prevent — you lose
  the real work in every branch you didn't pick. Harmonize.
- **Landing recovered work directly on canonical.** Always the `branch-rationalization-<date>` staging branch.
- **Trusting `git log` ancestry over `git cherry -v`.** Squash/rebase-landed content looks novel to `log`.
- **Classifying by branch name.** The fingerprint is the evidence; the name is a prior.
- **Batch-deleting after one "yes".** Per-plan verbatim authorization, individual removals, backups first.
- **Re-implementing wt-sweep.sh / branch-triage.sh here.** Let them do the mechanical pass; start from RESIDUE."
  - proposed fix: Delete the Anti-patterns section. If a quick-reference recap is wanted, replace each bullet with a one-line pointer back to its source (e.g. 'See Safety kernel #2/#3/#6-7, Phase A branch-name rule, Pipeline section') instead of restating the rule text.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Context pointer — one trigger per branch (collapse synonyms that rename a single branch)**: This second 'Use when' clause restates a trigger already given earlier in the same description ('Use when starting a new brand, sub-brand, product, persona, or author voice.'). 'A new persona needs voice definition' just renames the 'persona' branch already listed, so the description carries two token-forms of one trigger instead of collapsing them.
  - quote: "Use when copy sounds generic, when a new persona needs voice definition, or when the answer to "how should this sound?" is unclear."
  - proposed fix: Merge into a single trigger list, e.g.: 'Use when starting a new brand, sub-brand, product, or persona, or when existing copy sounds generic and voice was never defined.'
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Single source of truth**: The 'don't use Playwright, use real Brave' meaning is stated three times: in the Core pattern blockquote, again in prose in 'The problem' section (the ASCII comparison plus 'The fix is a human-in-the-loop handoff to a real browser'), and a third time as a row in the Anti-patterns table ('Playwright/xvfb for OAuth consent | Bot detection + cannot do 2FA | Real Brave handoff'). Duplication inflates this single meaning's rank on the ladder and creates three places to update if the rationale changes.
  - quote: "do not fight
it with Playwright."
  - proposed fix: Keep the Playwright/bot-detection rationale in one place (the Core pattern box or 'The problem' section) and drop the redundant Anti-patterns row, or replace that row with a distinct anti-pattern not already covered.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Completion criteria**: This workflow step gives no condition for what 'verified' means (e.g., matches the value Will reported, no error response) — a vague bound that invites the agent to consider the step done once it re-reads anything, rather than actually confirming correctness.
  - quote: "6. Verify (re-read the config via API)"
  - proposed fix: State the check explicitly, e.g. '6. Verify: re-read the config via API and confirm the stored value matches what Will reported.'
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Progressive disclosure**: The full diagnosis-and-repair procedure (status probe, seven env vars, timing/RSS figures, a verified-date footnote) is branch-only material reached only when the lexical index breaks — a rare event ('13-day outage'). It's inlined in the main skill file at the same rung as the everyday 'Use it' steps, so it's paid as context load on every invocation and competes for attention with the primary path, exactly the coin-flip the doctrine warns against.
  - quote: "What does work is the **inline repair via a non-robot search**, which engages the staged shard-build path (`planned_shards≈317`), memory-bounded so it survives alongside running agent sessions:"
  - proposed fix: Push the repair procedure to a separate reference file (e.g. cass-rerank-repair.md) and leave a one-line pointer under the 'no results' heading: 'index likely broken — see cass-rerank-repair.md for the repair procedure.'
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Leading words [craft]**: The same symbol 🚫 is used as the leading token for two distinct kernel axioms — 'Never silent-fail' and 'No TUI on bare invocation.' A leading word/operator is supposed to anchor one concept the agent can think with wherever it recurs; reusing 🚫 for two different rules means the token no longer picks out a single branch, so later references to 🚫 (e.g. in the Intent-Recovery Triad's '🚫 never-silent-fail') are ambiguous against the kernel list.
  - quote: "**🚫 No TUI on bare invocation.**"
  - proposed fix: Give 'No TUI on bare invocation' its own distinct symbol (e.g. 🖥 or 🚪) so 🚫 stays uniquely bound to 'never silent-fail' everywhere it appears in the document.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Completion criteria [craft]**: 'Substantive' is an uncheckable qualifier gating the loop's completion criterion. The numeric threshold (≥5, ≥3) is concrete, but what counts as a qualifying change is not, so an agent under pressure to hit the count can rationalize trivial edits as 'substantive' and claim the gate is satisfied — exactly the vague-bound-invites-premature-completion failure mode the doctrine warns about.
  - quote: "ship ≥5 substantive changes across ≥3 dimensions before calling it done"
  - proposed fix: Define 'substantive' concretely, e.g. 'a change that moves at least one of the 11 dimension scores, verified by re-running that dimension's check' rather than leaving it to judgment.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and inflates that meaning's rank on the ladder past its real importance.**: Nearly every bullet in this section restates a meaning already stated once earlier under its own heading: the fix-then-detect bullet duplicates The One Rule callout, the fixture bullet duplicates 'No fixture = no fixer' in the Build unit section, the backups bullet duplicates 'Backups are verbatim. No reformatting...' in the Safety envelope, the DeletePath bullet duplicates both 'The Op enum has NO DeletePath' and 'Never rm -rf, git reset --hard, or DROP TABLE', the capabilities bullet duplicates 'generated from the live registry...never hand-maintained' in the CLI surface, and the cross-FS bullet duplicates the footnote in the mutate() chokepoint steps. This scatters each meaning across two places rather than keeping it in one authoritative spot.
  - quote: "- **Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it.
- **A fixer without a fixture** — you can't distinguish fixed from regressed-back next pass.
- **Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently.
- **`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead.
- **Hand-maintained `capabilities`** — generate it from the live detector/fixer registry so it can't lie.
- **Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract.
- **Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
  - proposed fix: Cut the Anti-patterns section to only entries that introduce a new meaning not stated elsewhere, or replace it with a bare cross-reference list ('see: The One Rule, Fixture bullet, Safety envelope, mutate() step 6') rather than restating each rule's content.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Context pointer [craft]**: This trailing clause restates identity information the body already states in its own header comment ("This version is self-contained: real snippets inline, no external line-refs"). The doctrine says a pointer's wording should cut identity the body already states — this fragment doesn't help decide when to reach the skill, it just duplicates a body-level property at permanent context-load cost.
  - quote: "Self-contained (real bash inline)."
  - proposed fix: Drop the clause from the description; leave the self-contained/inline-snippets claim to the body comment where it already lives.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Completion criteria [craft]**: Every other item in the pre-ship checklist gives a concrete, checkable bound (e.g. "WSL warned not blocked", "re-run = no dup hooks", "--offline <tarball> (no network)"), but this item's bound is the vague "works" — no observable condition (which platform, which failure mode, what output) tells the agent the check is satisfied, inviting premature ticking of the box.
  - quote: "build-from-source fallback works"
  - proposed fix: Replace with a concrete bound, e.g. "build-from-source fallback installs successfully when no prebuilt tarball matches (tested by forcing all 3 download URLs to fail)".
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Single source of truth — keep each meaning in one authoritative place; duplication costs maintenance and inflates rank**: The full convergence formula (≥10 rounds, <3 new findings for 2 consecutive rounds, zero unresolved hypotheses with the same DEFERRED-rationale wording) is restated nearly verbatim in the dedicated '## Convergence (non-negotiable)' section below, and referenced a third time in the ABORT IF list. One meaning is scattered across three places instead of living in one authoritative spot, so a future edit to the threshold risks going stale in the copies.
  - quote: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings
              AND every hypothesis resolved (SEAM_CONFIRMED / SEAM_REFUTED /
              DEFERRED+rationale with `Deferred reviewed: yes`)."
  - proposed fix: State the formula once under '## Convergence (non-negotiable)' and replace the Quick-Start box's full restatement with a one-line pointer, e.g. "Convergence: see Convergence (non-negotiable) below."
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; two places stating incompatible facts about the same capability is the failure this rule prevents.**: This flatly states the skill never writes tokens, but Step 4 documents exactly that: 'Write DESIGN.md + tokens/{color,typography,spacing}.json' via propose.mjs --out=<dir>. The intro's capability claim contradicts the workflow it precedes.
  - quote: "It does not restyle components, pick a palette, or write the tokens for you."
  - proposed fix: Qualify the intro claim, e.g. 'It does not restyle components or pick a palette on its own — the optional propose step (§4) can emit token files, but only from values the codebase already ships.'
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Relevance and sediment [craft] — a line loses relevance by going stale as the behaviour it describes changes; without pruning discipline, stale counts pile up.**: The table under this heading lists six detectors (colour literals, arbitrary values, raw palette utilities, missing scales, near-duplicate colours, unresolved tokens), matching the six detector ids listed just above in the Scan section ('color arbitrary palette scale nearcolor orphan'). The heading's count wasn't updated when detectors were added.
  - quote: "### 2. Read the four detectors"
  - proposed fix: Change the heading to '### 2. Read the six detectors' (or drop the number entirely).
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Context pointer [craft] — keep one trigger per branch; collapse synonyms that rename a single branch.**: These are two phrasings of the same branch: Step 4 treats 'propose a DESIGN.md' and 'emit DTCG token files' as one combined, optional action ('PROPOSE a DESIGN.md + DTCG token files by clustering those measurements'), not two separate asks. Listing both as distinct 'Use when' triggers pays extra description tokens without adding a real branch.
  - quote: "author a DESIGN.md from an existing messy codebase, or turn design-drift findings into a token architecture"
  - proposed fix: Collapse to a single trigger, e.g. 'or author a DESIGN.md + token architecture from an existing messy codebase.'
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Progressive disclosure [craft] — inline what every branch needs, disclose what only some branches reach; branch-only reference left in-file among steps turns attending to it into a coin-flip.**: This section, along with the adjoining Monorepo caveat, lint-CLI-quirks, and Method sources paragraphs, is reference material relevant only to the optional Step 4 propose branch. Because the skill is user-invoked (disable-model-invocation: true) and this content sits inline in the main SKILL.md, every invocation — including plain audit-only requests that never touch propose.mjs — pays the context load for it.
  - quote: "**Evidence comes in two tiers, and the DESIGN.md names each role's tier.**"
  - proposed fix: Move the propose-specific reference block (evidence tiers, monorepo caveat, lint-result quirks, method sources) to a separate doc (e.g. propose-notes.md) reached by a pointer from Step 4, leaving the main file with just the propose commands and hand-off steps.
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available, not less; keep prohibition only as a hard guardrail, paired with its positive target.**: The document doesn't just prohibit the wrong format, it reproduces a full worked example of it. Per the doctrine's own research citation, showing the forbidden pattern in detail makes that pattern more available to the model, not less — the opposite of the intended effect.
  - quote: "Wrong format (never do this):

```
Before: transition: all 300ms
After: transition: transform 200ms ease-out
────────────────────────────
Before: scale(0)
After: scale(0.95)
```"
  - proposed fix: Delete the 'Wrong format' block entirely. State the requirement once, positively: 'Always output a single markdown table with | Before | After | Why | columns, one row per issue' — the correct example already shown earlier is sufficient.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and inflates that meaning's rank on the ladder past its real importance.**: This Review Checklist row restates, almost verbatim, rows already given in the earlier Review Format example table (transition: all, scale(0) entry, ease-in, transform-origin on popover). The same before/after guidance is now maintained in two places that can drift out of sync.
  - quote: "| `transition: all`                          | Specify exact properties: `transition: transform 200ms ease-out` |"
  - proposed fix: Keep one table. Either drop the duplicated rows from the Review Checklist and keep only issues not already covered by the Review Format example table, or delete the Review Format table's example rows and point to the Review Checklist as the single reference.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth [craft] — duplication (the same meaning in more than one place) costs maintenance and inflates that meaning's rank on the ladder.**: This Sonner Principle restates, nearly word for word, the 'Use CSS transitions over keyframes for interruptible UI' section under Component Building Principles ('CSS transitions can be interrupted and retargeted mid-animation. Keyframes restart from zero.'). The 'keyframes restart from zero' fact also reappears a third time under Spring Animations' Interruptibility advantage.
  - quote: "**Use transitions, not keyframes, for dynamic UI.** Toasts are added rapidly. Keyframes restart from zero on interruption. Transitions retarget smoothly."
  - proposed fix: State the keyframes-vs-transitions rule once under Component Building Principles, and in the Sonner Principles list replace the restatement with a short reference back to it (e.g. 'see Use CSS transitions over keyframes above — Sonner is the reference implementation').
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place instead of restating it under a second heading.**: This 'transform-origin' entry under CSS Transform Mastery restates the same guidance already given in full, with the modal exception, under 'Make popovers origin-aware' in Component Building Principles ('Popovers should scale in from their trigger, not from center... Exception: modals'). The rule now lives in two places that could diverge (e.g. the modal exception is stated only in one of them).
  - quote: "Every element has an anchor point from which transforms execute. The default is center. Set it to match where the trigger lives for origin-aware interactions."
  - proposed fix: Co-locate: keep the full origin-aware rule (including the modal exception) only under 'Make popovers origin-aware', and shrink the CSS Transform Mastery entry to the mechanical fact only ('transform-origin sets the anchor point for transforms; default is center') without re-deriving the popover guidance.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Completion criteria [craft] — every bound should be sharpened rather than left as a vague qualifier that invites inconsistent application (cf. the uncheckable-qualifier defect the doctrine's own probe example flags).**: "When appropriate" gives no condition for deciding when to trade discoverability for memorability, so it can be invoked to justify either choice after the fact rather than guiding the decision beforehand.
  - quote: "Sacrifice discoverability for memorability when appropriate."
  - proposed fix: Replace with a concrete condition, e.g. 'Sacrifice discoverability for memorability for consumer-facing, brand-driven products; keep literal, searchable names for internal or infrastructure libraries.'
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth [craft]**: This inline restatement of the budget table gives a single blanket number (300ms) that the very table beneath it contradicts: 'Modals, drawers | 200–500ms' exceeds 300ms. The doctrine warns that a document restating a lookup is a cache, and a cache that drifts from its source costs exactly the maintenance problem duplication creates — here the drift is already visible within the same section, leaving the agent unable to tell which number is authoritative for modals/drawers.
  - quote: "The suggestion must work within the standard budgets (UI under 300ms):"
  - proposed fix: Drop the '(UI under 300ms)' parenthetical and let the table alone be the authoritative budget source, or if a blanket ceiling is wanted, raise it to cover the table's actual range (e.g. 'UI under 500ms, most well under 300ms').
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Pointers & descriptions — Context pointer [craft]**: This identity content in the frontmatter description is restated almost verbatim two lines into the body: 'It does not review existing animations (that's `review-animations`), audit and plan fixes for them (that's `improve-animations`), or write the implementation itself.' The doctrine directs pointers to 'cut identity the body already states' — this clause spends pointer tokens on something the reader gets again immediately upon opening the file.
  - quote: "Read-only; it proposes motion with exact values, it does not implement it."
  - proposed fix: Trim the description to the trigger condition and disambiguation only, e.g. 'Search a codebase or UI for places that don't animate but should. Use when the user asks "what could be animated here?" or wants to "make this feel more alive." For fixing existing animations, use improve-animations or review-animations instead.' and let the body's opening paragraph carry the read-only/no-implementation identity.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Context pointer** — verifier: The rule calls for one trigger per branch, collapsing synonyms that rename a single branch. 'too big for one context', 'many independent units', 'whole-codebase campaigns', 'broad multi-file sweeps', and 'N-independent-units work' are five restatements of the same 'large/many-unit task' trigger stacked into the description, inflating it without adding a distinct branch (only the trailing 'adversarial verification' clause is genuinely different).
  - quote: "Use when a task is too big for one context or has many independent units: whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work, or when you need multiple independent perspectives (adversarial verification)."
- **Context pointer** — verifier: This sentence states the skill's identity rather than a triggering condition; per the rule, a pointer should cut identity the body already states rather than spend description tokens restating what the skill is.
  - quote: "The shared swarm/delegation layer other skills route through for scale."
- **Single source of truth** — verifier: Duplicates the meaning of the earlier 'Never silently absorb a delegatable batch into the session model.' bullet in Cost routing; the same rule is stated authoritatively twice.
  - quote: "**Silently doing a Codex-sized batch in the session model** — that's the delegation the routing exists for."
- **Leading words** — verifier: 'doghouse' is a coined term used with no definition anywhere in the document; the rule requires a made-up word to be defined clearly since it recruits no priors from pretraining.
  - quote: "If Codex is unavailable (doghouse tripped, auth outage), fall back to a Sonnet-class subagent — not the session model."
- **Completion criteria** — verifier: This row is part of the Never Ship self-check ("Self-check before you finish. Each of these is an automatic block in review-animations") but "with no reason" is an uncheckable qualifier — it doesn't say what counts as a valid reason, so the agent can wave through any duration by asserting one exists. A vague bound in a completion check invites the exact premature-completion failure the doctrine warns about.
  - quote: "UI duration over 300ms with no reason"
- **Demand** — verifier: This is one of four criteria for reaching for a spring instead of a curve. The other three ("drag with momentum," "a gesture the user can interrupt or reverse," "decorative mouse-tracking") are concrete and checkable; this one gives no operational test, so it doesn't bind the tool-selection decision the way the rest of the list does — it lets "feels alive" justify a spring for anything.
  - quote: "an element that should feel alive"
- **Negation [research]** — verifier: This is a bare negation-led bullet with no positive-target framing or explanation — unlike every other prohibition in the document (e.g. 'Avoid CSS transitions... — Springs animate from the current value by default'), it states only the forbidden behaviour and pairs it with nothing. Per the doctrine's Negation rule, prohibition should be paired with its positive target so the banned behaviour isn't the only thing said.
  - quote: "**Never lock out input during a transition.**"
- **Negation [research]** — verifier: A bare 'Never X' clause appended after the Wayfinding questions, restating what 'How do I get out?' already implies, without itself naming the positive target behaviour (a guaranteed exit). This is the exact negation-led-bullet pattern the doctrine flags as a defect the probe catches even after a heavier audit passes it.
  - quote: "Never trap the user."
- **Context pointer — keep one trigger per branch (collapse synonyms that rename a single branch)** — verifier: The description states two trigger phrases — "analyzing command patterns" and "finding automation opportunities" — for what is a single underlying invocation condition (this skill fires whenever someone wants to mine history to find automatable work). The doctrine requires collapsing synonyms that rename one branch rather than stacking near-duplicate phrasings, which just inflates the always-loaded pointer without adding routing coverage.
  - quote: "Use when analyzing command patterns or finding automation opportunities."
- **Progressive disclosure — inline what every branch needs, disclose what only some branches reach** — verifier: This fork-provenance and upstream-sync procedure is only relevant to the rare branch of doing a jsm sync/cherry-pick — it is dead weight for the actual mining/scoring/building task the skill performs on every other invocation. Because it sits inline at the top of the file rather than behind a pointer, it pays full context load on every load of the skill instead of only when someone is doing sync maintenance.
  - quote: "<!--
  LOCAL FORK — not managed by jsm; do not expect `jsm install-all` to preserve it.
  Origin: forked from jsm upstream skill `automating-your-automations` v2 (jeffreys-skills.md).
  Localized to this stack: de-Rust'd (build targets are bash / Python via uv|pipx, not Rust CLIs),
  de-zsh'd (bash: ~/.bashrc, ~/.bash_aliases), data source is runtime-detected (atuin DB if present,
  else ~/.bash_history), and foreign skill links (/rust-cli-with-sqlite, /cass, /br) removed.
  The `-local` suffix stops `jsm install-all` from overwriting this fork; it WILL re-add pristine
  `automating-your-automations` as a separate skill — uninstall that if it reappears.
  Upstream sync is NOT automatic. Cherry-pick: `jsm install automating-your-automations` into a
  scratch dir, diff, port worthwhile changes, discard the scratch copy.
-->"
- **Single source of truth — keep each meaning in one authoritative place** — verifier: The Score ≥ 0.3 threshold is already stated authoritatively in Step 2 ("Only automate if Score ≥ 0.3"). Restating the same numeric cutoff in the Anti-Patterns table duplicates that meaning in a second place, so a future change to the threshold requires updating two locations and risks the two drifting apart.
  - quote: "Automate rare commands (Score < 0.3) | Skip — maintenance > benefit"
- **Negation [research] — steer by stating the target behaviour, keeping prohibition only as a hard guardrail paired with its positive target** — verifier: This is a judgment heuristic, not a destructive-action hard guardrail (unlike the Safety kernel's negations, which are exempted), so it should be phrased as the target behaviour rather than a prohibition. Both the heading and the first sentence are negation-led ('don't be fooled', 'isn't proof') before the positive procedure (signature sampling) appears three sentences later — the doctrine's own probe example flags exactly this pattern (a negation-led bullet) as a defect that survives ordinary review.
  - quote: "**Same-signature sampling (don't be fooled by supersession).** A symbol *existing* on canonical isn't proof it's superseded."
- **Context pointer — cut identity the body already states** — verifier: This clause enumerates the exact section headers of the '## The Voice Profile (Output Format)' template in the body (Tone Spectrum, Vocabulary, Mechanical Rules, On-Brand/Off-Brand Example Phrases, Aspiration/Anti-Aspiration Models, Quality Test). The pointer's job is to get the agent to the material, not pre-restate its full contents.
  - quote: "Outputs a complete Voice Profile with tone spectrum, vocabulary, mechanical rules, on-brand and off-brand example phrases, aspiration and anti-aspiration models, and a quality test."
- **Negation — state the target behaviour instead of the prohibition** — verifier: The instruction is negation-led with no positive framing at the point of the actual directive (the preceding sentences are role descriptions, not an alternative action). Per the doctrine, this drags 'skip the encoding step' into context rather than stating what to do.
  - quote: "Don't skip the encoding step: a profile that isn't wired into a skill gets ignored."
- **Completion criteria — a vague bound invites inconsistent behaviour** — verifier: "Strong reactions" is an uncheckable qualifier with no stated bound (what utterance or behavior counts as 'strong'?), leaving the mode-selection branch to the agent's unguided judgment call.
  - quote: "If they have strong reactions, switch to Build."
- **Single source of truth** — verifier: This same rule is restated as an Anti-patterns row ('Skip query params | Wrong page loads | Full URL, opened in Brave') and again as a Pre-flight checklist item ('URLs verified (correct page loads in Brave)'). All three express the identical meaning about full URLs/query params, which the doctrine flags as a maintenance cost rather than a co-located elaboration.
  - quote: "Include FULL URLs with query params (`?project=xyz`) and open them in Brave."
- **Negation** — verifier: The Anti-patterns table structures every row negation-first (Playwright/xvfb, vague clicking, assuming Will knows IDs, skipping query params), leading with the forbidden behavior as the primary column before any positive framing. Per the doctrine's research finding, this drags each forbidden action into context repeatedly rather than stating the target behavior directly; the doctrine reserves prohibition for hard guardrails, not a routine four-row reference table that mostly restates rules already given positively elsewhere in the document.
  - quote: "| Don't | Why | Do instead |"
- **Relevance and sediment** — verifier: This comment block (architecture history plus the granite-r2 eval saga) is loaded as context every time the skill fires, but it documents a retired path and a model choice the doc itself says the gateway 'sidesteps... entirely.' A line that only describes what used to be true, by the doctrine's own admission, never bears on what the document does now — it's sediment kept because removing it felt risky, not because it's load-bearing.
  - quote: "wm -> ai-gateway:18000 -> mac-studio tunnel chain is retired."
- **Context pointer** — verifier: The description restates the same routing guidance the body's 'When to use which' table already gives in full ('Broad keyword scan, many hits | plain `cass search "..." --robot`'). The pointer's job is to decide whether the agent reaches the material, not to duplicate the body's reference content — this is exactly the identity/guidance the body already states.
  - quote: "fall back to plain cass for broad scans."
- **Single source of truth [craft]** — verifier: The 'bare invocation must not launch a TUI' rule is stated in full three separate times with the same meaning: the kernel axiom ('🚫 No TUI on bare invocation... Either `<tool>` shows useful help/triage and exits, or `<tool> tui` is the explicit interactive entry — never both'), recurring-fix #8 ('Bare invocation launches a TUI — near-universal P0; move interactive mode behind an explicit `tui` subcommand'), and this anti-patterns bullet. This is duplication of one meaning across multiple places, not co-location, and inflates the rule's apparent weight while creating three places to keep in sync.
  - quote: "**Bare `<tool>` opening a TUI**; **exit 1 meaning "no results"**; **prompting for confirmation** in a non-TTY."
- **Negation [research]** — verifier: This anti-pattern bullet is phrased purely as a prohibition with no paired positive target in the same bullet, unlike its neighbors in the same list (e.g. 'Ship changes, not a report,' 'introspect it,' 'apply the operator stack'). Per the doctrine's negation rule, steering by prohibition alone makes the forbidden behavior more available rather than less; prohibition should be paired locally with its positive target.
  - quote: "**ANSI/emoji or stack traces in errors, or errors on stdout** — all break non-TTY agents and `| jq`."
- **Negation [research] — state the target behaviour instead of the ban; keep prohibition only as a hard guardrail, paired with its positive target.** — verifier: This bullet lists four banned behaviors with no positive target stated in the same breath, unlike neighboring Anti-patterns bullets that pair the ban with its fix (e.g. the DeletePath bullet says 'rename-to-quarantine instead'). Per the doctrine, unpaired prohibition drags the forbidden behavior into context without displacing it with the wanted one.
  - quote: "**Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract."
- **Completion criteria [craft] — every step ends on a condition telling the agent the work is done; a vague bound invites premature completion.** — verifier: 'Until clean' is an uncheckable bound — nothing in the document defines what 'clean' means (zero rubric gaps? zero anti-pattern hits? a fixed number of passes?), so the agent has no way to know when this step is satisfied and can plausibly stop after one pass believing it's done.
  - quote: "10. **Iterate** — a fresh-eyes/adversarial re-read until clean; re-mine as the project evolves (no doctor is ever "done")."
- **Relevance and sediment [craft] — a line loses relevance by never mattering to the task; without a pruning discipline the default fate is sediment.** — verifier: This inventory of features cut from a retired predecessor skill never bears on how an agent adds or upgrades a doctor subcommand today — it's provenance trivia carried forward because removing it felt riskier than keeping it, exactly the sediment pattern the doctrine warns about.
  - quote: "Dropped
     the multi-model swarm tiers, session-mining, external issue-tracker plumbing, the per-run 0-1000
     scoring machinery, 18 subagents, and 39 scripts."
- **Completion criteria** — verifier: Step 1 never tells the agent where to put the assembled prompt, yet step 2's command reads it from a specific path (`$CLAUDE_JOB_DIR/tmp/codex-consult.md`). The step's bound is not just vague — it omits the deliverable entirely, so the agent has no stated condition for 'done' that would make step 2 actually work.
  - quote: "1. **Assemble a self-contained prompt.** Codex runs read-only and may lack your
   conversation context, so embed the essentials: the question, the relevant code
   (paste the actual snippets/diffs), constraints, and what you've already tried."
- **Negation** — verifier: This bullet leads with the prohibition and fully spells out the excluded categories before any positive framing, dragging the discouraged behavior into context first rather than stating the target behavior. It isn't a hard guardrail (nothing enforces it), so per the doctrine it should be phrased positively instead of negation-led.
  - quote: "**Not worth it:** naming debates, "what does this code do", style nitpicks."
- **Completion criteria / Demand** — verifier: This is an uncheckable qualifier — 'tight' gives the agent no verifiable bound, unlike the concrete 'Return exactly three parts' criterion given just above it. A vague closing directive like this invites the agent to judge conciseness however it likes rather than against a stated standard.
  - quote: "Keep the whole thing tight."
- **Negation [research]** — verifier: The entire Anti-patterns section is built from prohibition-led bullets: each bolded lead names the forbidden behaviour ("Skipping checksum verification", "Hard-failing on optional features", "Ignoring proxy env", "flock as your only lock", "Raw unstyled output", etc.) before any positive instruction appears. Per the doctrine, this drags the forbidden behaviour into context and makes it more available, not less — the positive target should be named first, with prohibition reserved for a hard guardrail paired with it, not used as the section's organizing device.
  - quote: "- **Skipping checksum verification** — supply-chain risk; always verify SHA256."
- **Context pointer [craft]** — verifier: This clause lists three phrasings — "install.sh", "curl-pipe-bash installer", "one-liner install for a Rust/TS/Go CLI" — that all rename the same single branch (writing this kind of installer script). The doctrine requires collapsing synonyms that rename one branch into a single trigger, since each restated synonym pays permanent context load in the always-loaded description without adding a distinct routing condition.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer, or a one-liner install for a Rust/TS/Go CLI."
- **Context pointer — front-load the leading word, keep one trigger per branch (collapse synonyms that rename a single branch)** — verifier: These four phrases are not distinct branches — they're synonym-stacked restatements of the same trigger (a file/repo has grown too big and needs splitting). The doctrine's own routing-parity evidence shows cutting synonym-stacked language costs no recall; leaving all four in the always-loaded description pays context load for zero added routing power.
  - quote: "Use when de-monolithize, split giant file, modularize repo, or file too big."
- **Subagent-dispatch escape hatch has a cost ceiling [measured] — every data-driven fan-out must be hard-capped** — verifier: This and the sibling rows ('1 RECON ... × top-level dirs', '5 EXPERIMENTS ... × open EXP', '11 SOAK ... × campaigns') define fan-out width as a direct function of repo-discovered data (file count, experiment count) with no stated ceiling anywhere in the document. Per the measured cost-ceiling finding, uncapped data-driven fan-out is exactly the pattern that turns the legwork-hiding subagent-dispatch escape hatch into runaway spend.
  - quote: "2 STATIC | seam-analyst + intra-file-grapher + coverage-mapper × monolith file | `phase2_findings_<file-slug>.md`"
- **Negation [research] — state the target behaviour instead of the ban; keep prohibition only as a hard guardrail paired with its positive target.** — verifier: This is a negation-led bullet with no paired positive target immediately after it (the next sentences discuss evidence tiers, not what the proposer does instead) and no hard-guardrail justification — it drags 'invent a brand,' 'pick fonts,' and 'migrate call sites' into context rather than stating what the proposer actually produces.
  - quote: "**What it will not do.** It does not invent a brand, pick fonts, or migrate call sites."
- **Completion criteria [craft]** — verifier: Unlike step 2, which explicitly states 'Done when every seam class has either yielded candidates with `file:line` evidence or been explicitly cleared,' step 1 ends on an action ('Build a rough frequency map') with no condition telling the agent recon is complete. A vague, absent bound on the first step invites premature completion — moving to Sweep before the stack/tokens/personality picture is actually settled.
  - quote: "1. **Recon.** Identify the stack, motion libraries, existing easing/duration tokens (suggestions must extend these, not invent parallel ones), and the product's personality — a crisp dashboard earns fewer and subtler suggestions than a playful consumer app. Build a rough frequency map of the surfaces you'll judge."
