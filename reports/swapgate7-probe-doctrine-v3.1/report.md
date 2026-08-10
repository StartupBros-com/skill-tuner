# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $4.1472 spent
- verify: 153 trial(s), $3.6970 spent

## Run manifest

- run: `swapgate7-probe-doctrine-v3.1` (2026-08-10T06:07:48Z → 2026-08-10T07:09:49Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `2f83bb7c6e55` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `ecf98ca2b554` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `ccd612736f52` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `d3c2e90ee9c1` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `2d40bfb2ed8b` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `993984d44b26` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `65a8c2e84c7c` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `39f309dee303` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `b026438e5b18` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `b3d49f5611e9` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `7a2145fdbdee` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `7737730892f3` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `289d2526bc05` | worktree @ 0492e1e9e5f2 |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `bdfb8b83dc84` | worktree @ 0492e1e9e5f2 |

## Marginal-value probe verdict

**findings_confirmed: 24**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../skills/skill-tuner/SKILL.md
- targets: 15
- probe calls: 15
- verify calls: 153 (3 skeptic(s) per finding)
- refuted: 27
- overflow (beyond max_findings cap, not verified): 3

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 0 | 2 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 0 | 3 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 1 | 4 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 2 | 0 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 2 | 1 |

### Confirmed findings

- **One trigger per branch [craft] / Progressive disclosure [craft]**: The description lists eight distinct branches, but the body is one monolithic, undisclosed file with no per-topic sub-files or headings behind their own pointers. A run reaching the document via 'typography' loads the exact same content as one reaching it via 'translucent materials and depth' or 'momentum and interruptible transitions' — all 17 sections, every time. Per the doctrine's own test ('does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it? If not, collapse them'), these triggers all resolve to the identical path, so either the branches should collapse into fewer trigger phrases or the body should actually be split so each branch discloses only its own material.
  - quote: "Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency) behind Apple-style interfaces."
  - proposed fix: Either split the skill into disclosed sub-files (e.g. motion-physics.md, materials.md, typography.md, accessibility.md) each reached by its own branch, or collapse the description to a single trigger phrase (e.g. 'Apple-style interface motion, materials, and typography for the web') since the whole body loads regardless of which phrase matches.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Relevance and sediment [craft]**: This comment names a trigger ("before running `jsm install-all`") and a reference file that never appear anywhere else in the document; the skill's body never discusses `jsm install-all` or fork-syncing. It doesn't bear on what this document does — it reads as leftover boilerplate from a template rather than live material, i.e. sediment.
  - quote: "<!-- Local fork — see references/FORK-SYNC.md before running `jsm install-all`. -->"
  - proposed fix: Delete the comment if fork-sync is not actually relevant to this skill, or, if it is, integrate it into a real step explaining what `jsm install-all` does and when an agent using this skill would run it.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Single source of truth / duplication (Pruning and drift) — 'Don't re-implement their funnel here; start from what they couldn't resolve.'**: The pipeline diagram states branch-triage.sh's mechanical funnel already includes a CHERRY check and disposes of already-merged branches zero-loss before handing off RESIDUE, and the document explicitly instructs 'Don't re-implement their funnel here; start from what they couldn't resolve.' Phase A step 1 then re-implements exactly that already-merged/cherry check as the first archaeology step, contradicting its own stated policy and duplicating a check the mechanical script is said to already perform.
  - quote: "1. **Already landed?** `git cherry -v <canonical> <branch>` — all `-` lines ⇒ patch-id-equivalent content is already on canonical (even if `git log` shows no ancestry). Verdict `already-merged`; skip."
  - proposed fix: Remove the already-merged cherry-v check from Phase A (or note it only as a defensive re-verification for branches where branch-triage.sh was skipped/DRY_RUN), and state that RESIDUE branches are assumed already-merged-filtered so Phase A begins at fingerprinting.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Demand [craft] — 'Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.'**: Every other threshold in Phase A is precisely defined with a formula (fingerprint_coverage = found-with-same-signature ÷ total, file_existence_coverage, ≥30% of sampled signatures diverge, same-signature ≥ 0.7), but 'Confidence' is never defined or given a computation anywhere in the document. This lets the agent satisfy the 0.7 gate impressionistically rather than by a checkable calculation, undermining the otherwise precise classification chain.
  - quote: "**Confidence < 0.7 ⇒ don't auto-classify; surface to the user.**"
  - proposed fix: Define 'confidence' explicitly as a function of the already-computed metrics (e.g., confidence = min(fingerprint_coverage certainty, signature-sample agreement) or an explicit weighted formula), or replace the term with one of the existing named metrics.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Cut identity the body already states [craft]**: This is identity information (what the skill produces), not a routing trigger, and it duplicates the body's opening statement: "The output is a structured Voice Profile that future skills, agents, or humans can read and produce on-brand content from." It adds permanent context load with no triggering work.
  - quote: "Outputs a structured Voice Profile that can be encoded as a project-specific brand-voice skill afterward."
  - proposed fix: Remove this sentence from the description and keep only trigger conditions there; let the body's opening paragraph be the single place that states what the skill outputs.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Demand [craft] — mixing checkable and uncheckable terms in one criterion list**: This sits inside the numbered "Quality Test" list alongside checkable items like "Mechanically clean: does it pass every Mechanical Rule above?" and "Consistent: can it be applied across formats...?" The uncheckable, feelings-based "Authentic" item lets the agent satisfy the whole six-item test impressionistically rather than against a verifiable bound.
  - quote: "**Authentic:** does it feel true to who they are or want to be?"
  - proposed fix: Replace with a checkable proxy, e.g. "Authentic: does at least one Core Personality Trait trace directly to an answer given in Batch 1 (Identity)?"
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Completion criteria ("a bound is checkable when the agent can tell done from not-done without judgment. 'Verify the config' is not [checkable]")**: "Verify" alone is not a checkable bound — it matches the doctrine's own example of an unchecked criterion almost verbatim. Re-reading the config via API doesn't say what makes verification succeed, so the agent can consider the step done without actually confirming the written values match what Will reported.
  - quote: "6. Verify (re-read the config via API)"
  - proposed fix: Replace with a checkable bound, e.g. "Re-read the config via the API and confirm each field equals the value Will reported back."
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Progressive disclosure**: This section (diagnosis command, explanation of why `cass index --full` stalls, and a dense multi-env-var repair command) is branch-only reference — it only matters when the index is already broken — but it is inlined in the main body alongside the always-relevant usage steps. Per the doctrine, branch-only reference left in-file among steps 'turns attending to it into a coin flip: the agent cannot tell material meant for its path from material meant for a path it isn't on,' and it pays context load on every normal, non-broken-index invocation of the skill.
  - quote: "## If it returns "no results" for everything"
  - proposed fix: Move the repair procedure (diagnosis command through the `setsid`/env-var block and the 'Verified 2026-07-29' note) into a separate disclosed file, e.g. `REPAIR.md`, and replace it inline with a one-line pointer: 'If cass-rerank returns no results for everything, the lexical index is likely broken, not empty — see REPAIR.md.'
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Single source of truth**: This routing rule (use cass-rerank for top-1/top-few results, fall back to plain cass for broad scans) is already stated in the always-loaded `description`: 'Use INSTEAD of bare `cass search` for top-1/top-few relevant-session results ... fall back to plain cass for broad scans.' The same meaning is now kept in two places (description and table), so changing the routing logic requires editing both, and the description pays permanent context load for a distinction the body restates in full.
  - quote: "| "Find the ONE session where I solved X" (top-1 matters) | `cass-rerank` |"
  - proposed fix: Trim the description to name only the trigger for reaching the skill (e.g. 'reranked search over prior agent sessions; use for top-1/top-few results') and let the 'When to use which' table be the single authoritative place for the full three-way routing logic (cass-rerank vs plain cass vs cass pack).
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Pruning and drift — duplication wears disguises: an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice.**: This anti-pattern bullet restates, in negated form, the same meaning already stated positively in the Ambition gate step ("ship ≥5 substantive changes across ≥3 dimensions before calling it done. A scorecard alone is not a deliverable"). It is the same rule written twice, costing tokens and creating two places to update if the rule changes.
  - quote: "**A polite scorecard with no applied fixes** (when improvement was asked for). Ship changes, not a report."
  - proposed fix: Delete this Anti-patterns bullet; the Ambition gate already carries this meaning as the single source of truth.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Demand [craft] — watch for criteria that mix checkable and uncheckable terms; one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.**: The numeric thresholds (≥5, ≥3) are checkable, but "substantive" is not — an agent can count 5 trivial edits and label them substantive by its own judgment, satisfying the letter of the gate without the intended bar.
  - quote: "ship ≥5 substantive changes across ≥3 dimensions before calling it done"
  - proposed fix: Replace "substantive" with a checkable proxy, e.g. "ship ≥5 changes, each closing a Recurring-fixes item or kernel-axiom gap, across ≥3 of the 11 dimensions."
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning and drift — Duplication (polarity): "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."**: Every bullet here is the same meaning as a rule already stated positively earlier: 'Fix-then-detect' restates 'Detect-then-fix, never fix-then-detect' (The One Rule); 'Backups that reformat' restates 'Backups are verbatim. No reformatting, no "clean up while I'm here"' (Safety envelope); 'DeletePath / rm -rf / git reset --hard / DROP TABLE' restates 'The Op enum has NO DeletePath' and 'Never rm -rf, git reset --hard, or DROP TABLE' (Safety envelope); 'Random/timestamp finding ids, ad-hoc exit codes' restates 'Give each failure mode a content-derived id... never a random or wall-clock id' and 'Exit codes are... never ad-hoc' (Build unit / CLI surface); 'Cross-filesystem rename' restates the italicized aside in mutate() step 6 almost verbatim. This is the polarity disguise the doctrine calls out: the same meaning written twice, doubling maintenance and token cost with no new routing or execution signal.
  - quote: "## Anti-patterns

- **Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it.
- **Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently.
- **`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead.
- **Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract.
- **Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
  - proposed fix: Delete the Anti-patterns section, or collapse it to a single line pointing back at the rules it mirrors (e.g. 'Violations of any positive rule above — mutate() chokepoint, safety envelope, exit-code table — are the anti-patterns; grep for their inverse').
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Completion criteria — "Two bounds that contradict... are a completion defect in the same family: the agent cannot tell whether a value between them complies, whichever bound it obeys."**: Step 4 of the mutate() chokepoint is explicitly 'Write a verbatim backup to <run-dir>/backups/<rel-path>' — a disk write. Saying dry-run runs 'up to step 4 (backup)' and then claims 'zero disk writes' contradicts itself: either the backup step is executed (a disk write happens) or it isn't (in which case 'up to step 4' is wrong). The CLI surface table doubles down with 'execute nothing.' An agent cannot tell whether `.doctor/runs/.../backups/` gets populated during a dry run.
  - quote: "**`--dry-run --fix`** runs the plan through `mutate()` up to step 4 (backup) then prints the plan to
  **stderr** instead of executing step 6 — zero disk writes."
  - proposed fix: Pick one and state it precisely, e.g.: 'runs mutate() through step 3 (preconditions only, no backup written) then prints the plan to stderr — zero disk writes' — or, if the backup is intentionally taken, change 'zero disk writes' to 'zero writes to the target file; only the run directory is touched.'
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Completion criteria — "a bound is checkable when the agent can tell done from not-done without judgment."**: "The project's floor" is never defined anywhere in the document — no numeric threshold, no per-dimension minimum, no pointer to where it's set. The agent has no way to tell whether a given score 'clears' the floor without an undefined judgment call, which is exactly the vague-bound pattern the doctrine flags.
  - quote: "repeat until every FM clears the project's floor on each, then re-mine failure modes on the next material code change (no doctor is ever "done")."
  - proposed fix: Either define the floor explicitly (e.g., 'repeat until every FM scores ≥ 8/10 on each of the 10 dimensions') or point to where a project sets it (e.g., a `floor` field in `capabilities --json` or a project config value).
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Single source of truth (Pruning and drift)**: This restates the same meaning already given in the frontmatter description ('Ask Codex (GPT-5.5) for a read-only second opinion on the current problem, then synthesize agree/disagree against Claude's own view'). The 'synthesize, don't forward' instruction is then stated a third time in step 3 ('Synthesize — never just forward'). Per the doctrine, keeping one meaning in one authoritative place avoids the maintenance and token cost of duplication; here the same rule is written three times across the document.
  - quote: "Get an independent read from **Codex / GPT-5.5** on `$ARGUMENTS`, then return a
synthesis — not a raw forward."
  - proposed fix: Drop the restatement from the body's opening paragraph and let it lead straight into the mechanics ('This is the lightweight, stateless counterpart to...'), relying on the frontmatter description for identity and step 3 alone for the synthesize-not-forward requirement.
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Cut identity the body already states [craft] — a pointer restating what the body says about itself adds permanent context load for no routing signal.**: This clause describes what the skill's output *is* (identity), not when to reach for it. The body already states this identity verbatim in the heading "## Core snippets (real, self-contained)", so the description pays context load on every turn to restate a fact the body already owns.
  - quote: "Self-contained (real bash inline)."
  - proposed fix: Remove the clause from the description; leave the self-contained/real-bash claim to the body's "Core snippets" heading.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Progressive disclosure [craft] — inline what every branch needs; disclose/mark what only some branches reach, or the agent can't tell material meant for its path from material meant for a path it isn't on.**: Step 15 is explicitly marked conditional ('if daemon'), but steps 16-17 (AI-agent detection and hook config) are listed as plain, unconditional steps in the ordered build sequence — even though the dedicated section below states this material is branch-specific: "If the CLI plugs into AI agents ... the installer should detect which are present." An agent following the numbered build plan has no signal that 16-17 only apply when the target CLI integrates with agents, unlike 15 which is clearly flagged.
  - quote: "Integrate  13. completions (XDG)   14. PATH check (--easy-mode appends rc)   15. service (systemd/launchd) if daemon
           16. detect installed AI agents   17. configure hooks/skills idempotently (JSON-merge + timestamped backup)"
  - proposed fix: Add the same conditional marker used on step 15, e.g. "16. detect installed AI agents (if CLI integrates with agents)  17. configure hooks/skills idempotently (same)".
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Pruning and drift — duplication (polarity disguise), same clause as above.**: "one mechanical move per commit" is already stated positively in Decomposition Design ("one mechanical move per commit (`git mv`-friendly, blame-preserving)") and in the ⊕ EXTRACT operator card ("`git mv`-friendly; one move per commit"). This anti-pattern row is the same rule negated a third time, not a distinct piece of guidance.
  - quote: "Extract + rename + reformat in one commit | Kills `git blame` and reviewability; one mechanical move per commit"
  - proposed fix: Remove this row; keep the single positive statement in Decomposition Design (or the operator card) as the one authoritative place for the rule.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Front-load the leading word [craft] / Cut identity the body already states [craft]**: The description opens with throat-clearing identity content ('This skill encodes...philosophy...') that the body already states in full under 'Core Philosophy' and the 'You are a design engineer...' paragraph, before finally reaching the actual trigger information ('Invoke by name during UI polish passes') at the very end. The pointer's job is to say when to reach the material, not restate what it is, and the triggering phrase should occupy the position read first.
  - quote: "This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great. Invoke by name during UI polish passes (pairs with /ui-polish and /kill-ai-slop)."
  - proposed fix: Lead with the trigger: e.g. 'Invoke during UI polish passes (pairs with /ui-polish and /kill-ai-slop) for Emil Kowalski's design-engineering review process.' Drop the philosophy restatement — it belongs only in the body.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Completion criteria [craft] — contradictory bounds**: This general ceiling directly contradicts the duration table's row 'Modals, drawers | 200-500ms' and the Review Checklist row 'Duration > 300ms on UI element | Reduce to 150-250ms.' A 400ms modal transition satisfies the table's explicit allowance but violates the stated 300ms rule and the checklist's own remediation range (150-250ms), so the agent cannot tell whether a value like 400ms complies, whichever bound it follows.
  - quote: "**Rule: UI animations should stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
  - proposed fix: Reconcile the numbers: either exempt modals/drawers explicitly from the 300ms rule ('UI animations should stay under 300ms, except modals/drawers which may run 200-500ms') or cap the modal/drawer row at 300ms and update the checklist's reduce-to range to include modal-appropriate durations.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth / Duplication [craft]**: The fact that 'keyframes restart from zero' on interruption is stated here, again almost verbatim under 'Interruptibility advantage' ('CSS animations and keyframes restart from zero'), and a third time under Sonner Principle 5 ('Keyframes restart from zero on interruption. Transitions retarget smoothly.'). The same meaning is repeated in three separate places, costing tokens and maintenance without adding routing or execution value.
  - quote: "CSS transitions can be interrupted and retargeted mid-animation. Keyframes restart from zero. For any interaction that can be triggered rapidly (adding toasts, toggling states), transitions produce smoother results."
  - proposed fix: State the 'keyframes restart from zero, transitions retarget smoothly' fact once (e.g. under Component Building Principles) and have the other two sections reference it instead of restating it.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth / Duplication [craft]**: This exact hold-to-delete recipe (2s linear press, 200ms ease-out release, scale(0.97) button feedback) is already given as the code example under 'The inset shape' a few lines earlier, and is restated a third time under 'Asymmetric enter/exit timing' ('hold-to-delete: 2s linear...release...200ms ease-out') with its own near-identical code block. The same meaning is written three times instead of once.
  - quote: "Use `clip-path: inset(0 100% 0 0)` on a colored overlay. On `:active`, transition to `inset(0 0 0 0)` over 2s with linear timing. On release, snap back with 200ms ease-out. Add `scale(0.97)` on the button for press feedback."
  - proposed fix: Define the hold-to-delete pattern once under clip-path, and have 'Asymmetric enter/exit timing' link back to it rather than repeating the values and code.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Completion criteria [craft] — two bounds that contradict (a general ceiling in one place, a specific range crossing it in another) are a completion defect: the agent cannot tell whether a value between them complies.**: The gate states a hard ceiling of 300ms for UI animation, but the very next table lists 'Modals, drawers | 200–500ms' — a range that crosses the stated ceiling by up to 200ms. An agent proposing a 400ms modal transition can't tell whether it complies (it's inside the table's row) or fails (it exceeds the stated 300ms budget). The document's own worked example in Part 1 even uses 'transition: 400ms ease' for a toast, instantiating the contradiction.
  - quote: "The suggestion must work within the standard budgets (UI under 300ms):"
  - proposed fix: Either raise the stated ceiling to cover the modal/drawer row (e.g. 'UI under 500ms, tighter for frequent elements') or cap the modals/drawers row at 300ms so no row in the table exceeds the stated general bound.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; the same rule restated in two places with drifted wording risks contradiction and costs maintenance.**: The ce-plan/animate handoff rule is stated twice: once in Hard Rules #1 ('hand it off: ce-plan for a tracked change... or animate to build it directly when it is small enough not to need a plan') and again in Part 3 Verdict ('hand the chosen row to ce-plan... or to animate to build it now if it is a one-component fix'). The two statements use different conditions for the animate branch ('small enough not to need a plan' vs 'a one-component fix'), so an edit to one criterion won't propagate to the other, and the agent has two non-identical tests for the same decision.
  - quote: "or `animate` to build it directly when it is small enough not to need a plan"
  - proposed fix: State the ce-plan/animate handoff rule once (in Hard Rules #1) and have Part 3 simply reference it ('hand off per the rule above') rather than restating the condition in different words.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Cut identity the body already states [craft]** — verifier: The description opens by restating the skill's identity (the native-stack primitives) rather than only the conditions for reaching it. That same identity — 'parallel Claude Code subagents, the Workflow tool, Codex delegation, and worktree isolation ... instead of a coordination protocol' — is already stated in the body's title ('parallelize with the native stack, not a protocol'), its callout box ('The core shift...'), and the primitive-map table. Restating it in the always-loaded description adds permanent context load with no added routing signal; the pointer's job is when to reach, not what it is.
  - quote: "Run a large or parallelizable task across many agents using the native stack —"
- **One trigger per branch [craft]** — verifier: 'Broad multi-file sweeps' and 'N-independent-units work' rename the same branch — a task with many independent units routed through the 'Pick the lightest engine that fits' section — rather than naming two distinct paths through the document. A run reaching the skill through either phrase takes the identical path, so per the doctrine's test ('does a run reaching the document through this phrase take a different path than the one beside it?') these should collapse into one trigger.
  - quote: "broad multi-file sweeps, N-independent-units work"
- **Duplication (polarity) — Pruning and drift: "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror"** — verifier: This Never Ship row restates, in negated form, the same rule already given positively in section 4: "Never `scale(0)`. Start from `scale(0.9–0.97)` + `opacity: 0`." The same pattern recurs through most of the table — `ease-in` on UI, built-in `ease-out` vs. the custom curve, `transform-origin: center`, keyframes on toasts, animating width/height, Motion x/y/scale props, ungated `:hover`, and missing `prefers-reduced-motion` all mirror rules the document already states positively in the Build Sequence. That's the same meaning written twice per row, paid for in tokens and maintenance (a future edit to one of these rules now has two places to update).
  - quote: "| `transform: scale(0)` entrance | `scale(0.95)` + `opacity: 0` |"
- **Completion criteria — Steps, completion, and demand: "a general ceiling in one place, a specific range crossing it in another... the agent cannot tell whether a value between them complies, whichever bound it obeys"** — verifier: This ceiling directly follows the duration table's "Modals, drawers | 200–500ms" row, a range that exceeds 300ms by up to 200ms. The exemption for modals/drawers is only spelled out later, in the Never Ship table ("UI duration over 300ms outside modals/drawers or marketing/onboarding"), not co-located with this sentence. At the point this ceiling appears, an agent that just read the 500ms modal figure cannot tell whether that value complies or violates "stays under 300ms."
  - quote: "**UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
- **Demand — Steps, completion, and demand: "Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically"** — verifier: Three of the four listed triggers are checkable (drag with momentum, an interruptible/reversible gesture, decorative mouse-tracking), but "an element that should feel alive" is a judgment call with no way to tell compliance from non-compliance. Sitting inside an otherwise precise list, it lets the agent justify reaching for a spring on essentially anything by appeal to that one impressionistic phrase.
  - quote: "**Reach for a spring instead** when the motion is drag with momentum, an element that should feel alive, a gesture the user can interrupt or reverse, or decorative mouse-tracking"
- **Co-location [craft]** — verifier: This Quick Reference row introduces a rule — deciding whether a gesture reverses or commits using the sign of velocity at release — that is not explained, defined, or even mentioned anywhere in the numbered sections above. Every other row in the table summarizes a rule stated earlier in the body (§1–§15), but this one exists only in the summary table, so applying it correctly requires information the document never actually provides.
  - quote: "| Decide reverse vs. commit | Use velocity **sign**, not position | at release |"
- **Completion criteria / Demand [craft]** — verifier: This bullet sits in a list whose other items are checkable ("Animate only compositor-friendly properties — transform and opacity", "hint with will-change"), but 'perception threshold' names no number and no test, so the agent cannot tell a compliant per-frame delta from a non-compliant one without judgment. This is exactly the mixed checkable/uncheckable list pattern the doctrine warns lets an agent satisfy the whole list impressionistically.
  - quote: "Keep the per-frame positional change below the perception threshold to avoid strobing."
- **Context pointers — One trigger per branch [craft]** — verifier: "analyzing command patterns" and "finding automation opportunities" are two phrasings of the same single branch — the document has no path that only analyzes patterns without proceeding toward automation (The Loop always runs Mine→Cluster→Score→Propose→Build→Install). Per the doctrine's test, a run reaching the doc through either phrase takes the identical path, so this is one trigger paid for twice on every load.
  - quote: "Use when analyzing command patterns or finding automation opportunities."
- **Negation [research]** — verifier: The mandatory-loop rule is phrased as a prohibition rather than the target behavior, which the doctrine says drags the forbidden behavior (skipping) into context rather than reinforcing the wanted one. It is directly analogous to the doctrine's own example ("don't write long comments" vs. "write one-line comments") and has an obvious positive phrasing available.
  - quote: "**Never skip 1-3.**"
- **Pruning and drift — Single source of truth / Duplication [craft]** — verifier: This restates the exact heading structure that already exists as live `##` headers further down. It's the same meaning (document structure) written twice — one authoritative (the headers) and one duplicate (the comment) that must be kept in sync by hand and pays permanent context load for zero routing signal, since it's an invisible HTML comment with no navigational function for a human reader either.
  - quote: "<!-- TOC: Core Insight | The Loop | Mine & Cluster | Score | Propose | Build | Validate | Anti-Patterns | References -->"
- **Pruning and drift — Single source of truth (environment as source of truth) [craft]** — verifier: The alias count is a one-command lookup (`grep -c '^alias' ~/.bashrc`) that the environment can always answer accurately. Hardcoding "~40" caches a fact that will silently drift as aliases are added or removed, exactly the kind of stale-prone number the doctrine says to leave to the environment rather than restate.
  - quote: "`~/.bashrc` (~40 aliases)"
- **One trigger per branch [craft]** — verifier: This lists five near-synonymous triggers ("new brand", "sub-brand", "product", "persona", "author voice") that all route to the identical downstream process (choose Build or Extract, then produce a Voice Profile) — no branch behaves differently depending on which noun fired it. It is one branch written five times, paying five times in context load to route once.
  - quote: "Use when starting a new brand, sub-brand, product, persona, or author voice."
- **Pruning and drift — duplication via polarity [craft]** — verifier: This anti-pattern restates, negated, a rule the document already gives positively: the template's "These are bright-line rules. Violations should be auto-corrected" and the Build-mode synthesis instruction "The mechanical rules from Q16 become the enforceability backbone." It is the same meaning (mechanical rules prevent drift) written a third time.
  - quote: "**The Unenforceable Voice:** all vibes, no mechanical rules. Result: voice drifts within weeks."
- **Pruning and drift — duplication via polarity [craft]** — verifier: This restates, negated, the "Consistent" criterion already given positively in the Quality Test ("can it be applied across formats (social, email, long-form, ad)?") and covered again by the dedicated Channel and Stage Calibration section — the same meaning stated a third time instead of once.
  - quote: "**The Single-Channel Voice:** profile only works for one format (e.g. emails) and breaks on social or long-form. Test across channels."
- **Single source of truth / duplication ("an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror")** — verifier: This anti-pattern row is a negated restatement of the rule the Core pattern callout already gives positively ("do not fight it with Playwright... Open the exact URL in Will's real Windows Brave"). It's the same meaning written twice — once as the document's stated method, once again as a negated table row — which is exactly the polarity disguise the doctrine calls out.
  - quote: "| Playwright/xvfb for OAuth consent | Bot detection + cannot do 2FA | Real Brave handoff |"
- **Single source of truth / duplication ("an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice")** — verifier: This row duplicates the Critical rules bullet "Include FULL URLs with query params (`?project=xyz`) and open them in Brave" — the same instruction (put real IDs inline) is stated once positively in Critical rules and again here as a negated anti-pattern.
  - quote: "| Assume Will knows the IDs | He needs them inline | `project=my-project-123` |"
- **Relevance and sediment** — verifier: The comment's own closing clause states this reasoning no longer applies to any decision the agent (or the document) can act on — the model choice is fixed upstream by the gateway. A line that 'loses relevance by never mattering to the task' is sediment per the doctrine, yet the full eval-history narrative (leaked synthetic queries, pi-evals #891, granite-r2 reversal) remains, spending always-loaded context on a decision nobody using this skill can make.
  - quote: "The gateway lane exposes `local-rerank` only,
  which sidesteps that choice entirely."
- **Pruning and drift — duplication wears disguises: an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice.** — verifier: This duplicates, negated, the rule already given positively under "Named operators (the moves) + stacks": "Ship a stack as one coherent commit." Same meaning, two locations.
  - quote: "**Fixing one flag's error in isolation** — apply the operator stack so the whole surface class improves together."
- **Negation [research] — a prohibition earns its place only as a hard guardrail you cannot phrase positively, and even then it stands paired with its positive target so attention lands on what to do; the tell is a rule that leads with the ban and never says what to do instead.** — verifier: This is a bare prohibition with no positive target stated beside it, and unlike the neighboring "Never silent-fail" (which is later paired with its own elaborated axiom and positive instruction "Every failure → stderr + non-zero exit"), this phrase never gets a paired positive statement anywhere in the document, so the agent is told only what not to do.
  - quote: "Never punish a reasonable misstep."
- **Leading words — coining requires definition** — verifier: "doghouse guard" is a coined, tool-specific term with no definition anywhere in the document. Per the doctrine, a made-up word recruits no priors and must be defined to earn its place ('you pay in definition tokens what a pretrained word gives free'). As written, the agent has no way to know what this guard is, what triggering it looks like beyond 'blocked', or what 'Respect it' concretely requires.
  - quote: "If the circuit breaker is open, the PreToolUse doghouse guard will block this
   and tell you to fall back or `caam activate codex <profile>`. Respect it."
- **One trigger per branch [craft] — synonyms that rename a single branch are one branch written twice.** — verifier: The description states the same triggering branch twice in different words: "a production-grade curl | bash installer for a CLI tool" and "a curl-pipe-bash install.sh one-liner for a CLI" describe the identical task. A run reaching the skill through either phrase takes the same path, so this is one branch paid for twice on every turn this always-loaded description is in context.
  - quote: "Write a production-grade `curl | bash` installer for a CLI tool. Use when writing a
  curl-pipe-bash install.sh one-liner for a CLI (Rust/TS/Go)."
- **Duplication / Single source of truth [craft] — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: Most bullets restate, negated, a rule the '14 non-negotiables' or code comments already give positively: checksum verification mirrors non-negotiable #7, the musl/gnu bullet mirrors #4 ('prefer musl on Linux for static portability'), the JSON-backup bullet mirrors the Agent auto-config section's 'timestamped backup → jq-or-Python3 merge', the cosign hard-fail bullet mirrors #8's soft-skip/hard-fail rule, the flock bullet mirrors #6, the raw-output bullet mirrors the output-stack code's own NO_COLOR/non-TTY comment, and the proxy bullet mirrors #3 ('passed to every curl call'). Each pair is the same meaning in two places, so a future change to any of these rules requires editing two locations to stay consistent.
  - quote: "## Anti-patterns

- **Skipping checksum verification** — supply-chain risk; always verify SHA256.
- **`gnu` target on Linux** — not portable; use `musl` (static).
- **Editing settings/JSON without a backup**, or with `sed`/`awk` — `cp file file.bak.$(date +%s)` first, merge with `jq`/Python3.
- **Assuming `~/.local/bin` is on PATH** — check `:$PATH:`, offer to fix, don't assume.
- **Hard-failing on optional features** (missing cosign/gum) — warn and continue.
- **`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback.
- **Raw unstyled output** — route through `info/ok/warn/err`; honor `NO_COLOR`/non-TTY so piped/CI output has no ANSI.
- **`<tool> --version` with no timeout** — wrap in `timeout 1` (some CLIs hang).
- **Ignoring proxy env** — `PROXY_ARGS` on every curl call."
- **Pruning and drift — duplication (polarity disguise): "Duplication wears disguises, and the commonest is polarity: an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."** — verifier: The One Rule block already states this positively-and-negatively in one place: "Seams are discovered *empirically* (graphs, churn, probes), never aesthetically." The anti-pattern row is the same meaning written a second time, just negated and expanded, costing tokens without adding routing or execution signal.
  - quote: "Split along visual sections ("types here, helpers there") | Aesthetic seams cut through call graphs and shared state; use ◐ CLUSTER evidence"
- **Pruning and drift — single source of truth: "keep each meaning in one authoritative place, so changing the behavior is a one-place edit."** — verifier: The full convergence formula (round floor, quiet-round count, hypothesis-resolution requirement) is defined in full in the Quick-Start block, again in full in the "Convergence (non-negotiable)" section, and abbreviated again in the Pre-Flight Checklist. Three independent restatements of the same numeric thresholds mean a change to the round floor or the findings threshold requires editing multiple places to stay consistent, risking silent drift between them.
  - quote: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings"
- **Steps, completion, and demand — "The subagent escape hatch has a cost ceiling" [measured]: "fan-out must stay capped — a verify fleet no wider than its producers, every data-driven fan-out hard-capped — or the dispatch meant to buy legwork buys runaway spend instead."** — verifier: This stage (and RECON's "× top-level dirs" and EXPERIMENTS' "× open EXP", re-fanned again in Phase 7's "re-fan 2–6") sizes its subagent fan-out directly off data discovered at runtime (number of monolith files / dirs / open experiments) with no stated cap anywhere in this document. For a large repo this is exactly the runaway-spend pattern the doctrine warns about.
  - quote: "seam-analyst + intra-file-grapher + coverage-mapper × monolith file"
- **Single source of truth / Duplication [craft]** — verifier: These four Review Checklist rows restate the same four before/after facts already given verbatim in the Review Format example table earlier ('transition: all 300ms' → ..., 'transform: scale(0)' → ..., 'ease-in' on dropdown → ..., 'transform-origin: center' on popover → ...). The meaning is duplicated across two tables instead of kept in one authoritative place.
  - quote: "| `transition: all`                          | Specify exact properties: `transition: transform 200ms ease-out` |
| `scale(0)` entry animation                 | Start from `scale(0.95)` with `opacity: 0`                       |
| `ease-in` on UI element                    | See "Never use ease-in for UI animations" above                  |
| `transform-origin: center` on popover      | Set to trigger location (see "Make popovers origin-aware")       |"
- **One trigger per branch [craft] — synonyms that rename a single branch are one branch written twice; if two trigger phrases route to the same path, collapse them.** — verifier: Both quoted phrases lead to the identical workflow (sweep, gate, report) — there is no distinct path for the literal framing versus the emotional framing. Per the doctrine's test, a trigger that doesn't change the run's path should be collapsed into the one beside it; here two phrasings pay context/routing cost for one branch.
  - quote: "Use when the user asks "what could be animated here?" or wants to "make this feel more alive"."
