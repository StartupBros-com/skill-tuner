# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 6 trial(s), $1.4031 spent
- verify: 66 trial(s), $1.2811 spent

## Marginal-value probe verdict

**findings_confirmed: 11**

- doctrine: /home/will/SITES/skill-tuner/skills/skill-tuner/SKILL.md
- targets: 6
- probe calls: 6
- verify calls: 66 (3 skeptic(s) per finding)
- refuted: 11

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 0 | 3 |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | 0 | 4 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 4 | 0 |

### Confirmed findings

- **Single source of truth [craft] — keep each meaning in one authoritative place**: This HTML comment duplicates two things already stated elsewhere: the old→native mapping is already the entire content of the "Primitive map" table, and "skills that need campaign-scale parallelism reference this" duplicates the frontmatter description's "The shared swarm/delegation layer other skills route through for scale." It's a third restatement of information the description and the table already own.
  - quote: "Replaces the trashed jsm swarm mechanism (ntm + agent-mail + beads) with the operator's native primitives. Skills that need campaign-scale parallelism reference this instead of re-deriving swarm coordination."
  - proposed fix: Remove the HTML comment (or trim it to a one-line changelog note, e.g. "New skill, 2026-07-04, not a jsm fork") and let the description and primitive-map table remain the sole sources for what replaced what and who routes through this skill.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Negation [research] — state the target behaviour instead of the ban; keep prohibition only as a hard guardrail paired with its positive target.**: The sentence leads with the forbidden op ("NO DeletePath") before stating what the enum actually contains, dragging the banned behaviour into context first instead of naming the positive target (the 7 canonical ops) up front.
  - quote: "**The Op enum has NO `DeletePath`.** The 7 canonical ops: `WriteFile`, `AppendFile`, `Rename`, `Chmod`,
`DbExec`, `DbMigrate`, `SymlinkAtomic`."
  - proposed fix: Lead with the positive: "The 7 canonical ops are `WriteFile`, `AppendFile`, `Rename`, `Chmod`, `DbExec`, `DbMigrate`, `SymlinkAtomic` — there is no delete op." then continue with the quarantine-rename guidance.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Completion criteria [craft] — every step ends on a condition telling the agent the work is done; a vague bound invites premature completion.**: "Until clean" is an unbound, uncheckable qualifier with no defined criterion anywhere else in the document — nothing tells the agent what "clean" means or how to verify it, unlike the doc's other bounds (idempotence, reversibility) which are explicitly defined.
  - quote: "a fresh-eyes/adversarial re-read until clean"
  - proposed fix: Replace with a checkable bound, e.g. "re-read against the 10-dimension rubric until every FM scores at or above its target and the round-trip test in step 8 passes with zero new findings."
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and inflates that meaning's rank on the ladder.**: The ban on `rm -rf`, `git reset --hard`, and `DROP TABLE` is already stated in the Safety envelope's "Bounded blast radius" bullet ("Never `rm -rf`, `git reset --hard`, or `DROP TABLE`"). Restating it here duplicates the same meaning in a second authoritative-sounding location.
  - quote: "**`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead."
  - proposed fix: State the destructive-op ban once in the Safety envelope and have the Anti-patterns entry reference it rather than repeat the list, e.g. "Destructive ops under `--fix` — see Bounded blast radius; rename-to-quarantine instead."
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Completion criteria / Demand [craft] — a criterion's wording must actually force the rigor it appears to demand; a bound that only looks sharpened invites the same premature judgment as a vague one.**: This reads as a precise, numeric completion bound replacing the vague 'stop as soon as a verdict is certain' language earlier in Phase A, but 'confidence' is never defined anywhere in the document — no formula, no scoring method, and no tie to the metrics the document does define (fingerprint_coverage, file_existence_coverage, signature-divergence %). An agent has no way to compute whether it is above or below 0.7, so the bound is exactly as fuzzy as the thing it was meant to sharpen, just dressed up with a number.
  - quote: "Confidence < 0.7 ⇒ don't auto-classify; surface"
  - proposed fix: Either define the computation explicitly (e.g. 'confidence = fingerprint_coverage, discounted if any sampled signature diverges') or drop the numeric threshold and gate the surface-to-user decision on the already-defined checkable signals (fingerprint_coverage, apply-probe result, % of sampled signatures diverging).
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Demand [craft] — wording sets how much a criterion requires; a criterion mixing checkable and unchecked terms lets the agent satisfy it impressionistically.**: Every other term in this criterion is operationalized elsewhere in the document — 'apply-clean' by the apply-probe in Phase A step 3, 'absent-on-canonical' by fingerprint_coverage, 'defensive/test' by the intent taxonomy in Phase C. 'Focused' is not in that taxonomy and has no test anywhere in the document, so it's a stray uncheckable qualifier sitting inside an otherwise precisely defined list, leaving the agent to judge it by feel.
  - quote: "new, absent-on-canonical, apply-clean, focused/defensive/test"
  - proposed fix: Drop 'focused' or replace it with a checkable proxy (e.g. 'touches ≤3 files' or 'single intent tag'), matching the rigor of the other terms in the same cell.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Context pointer [craft] — keep one trigger per branch; collapse synonyms that rename a single branch, and cut identity already stated.**: This trailing sentence restates the trigger already established by the opening clause ('forgotten branches/worktrees left by parallel agents') in different words. It adds pointer-load without adding a new distinguishing condition for when to route here.
  - quote: "Use for parallel-agent branch cleanup."
  - proposed fix: Delete the trailing sentence; the opening clause already carries the trigger.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Context pointer [craft] — keep one trigger per branch (collapse synonyms that rename a single branch)**: "install.sh", "curl-pipe-bash installer", and "one-liner install" all name the same single trigger (writing this kind of installer) rather than three distinct branches. Stacking synonyms here pays extra description tokens without adding routing information, contrary to the rule that a pointer should collapse synonyms that rename one branch.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer, or a one-liner install for a Rust/TS/Go CLI."
  - proposed fix: Collapse to a single phrasing, e.g. "Use when creating a curl | bash install.sh one-liner for a Rust/TS/Go CLI."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Context pointer [craft] — cut identity the body already states**: The body's own header comment already states this fact verbatim ("This version is self-contained: real snippets inline, no external line-refs"), so the description restates identity information the body covers, adding permanent context load for no new routing signal.
  - quote: "Self-contained (real bash inline)."
  - proposed fix: Drop "Self-contained (real bash inline)." from the description and leave the self-containment claim to the body comment where it's already made.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Progressive disclosure [craft] — inline what every branch needs, disclose what only some branches reach**: The paragraph is framed entirely by a conditional ("If the CLI plugs into AI agents..."), but it bundles the agent-hook logic — a branch-only concern — together with `draw_box` and the uninstall snippet, both of which back non-negotiables #12 ("Final summary") and #13 ("Uninstall instructions") that every installer build needs. An agent whose CLI doesn't touch AI agents has no signal to open this reference for the always-needed draw_box/uninstall material, making retrieval of that material a coin-flip.
  - quote: "load-bearing reusable piece), the `draw_box` implementation, and the uninstall/service snippets are in"
  - proposed fix: Split the disclosure: keep the AI-agent-hook detection/merge pattern behind its own conditional pointer, and either inline the draw_box/uninstall snippets (since every branch needs them) or give them their own unconditionally-worded pointer separate from the AI-agent sentence.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Negation [research] — state the target behaviour instead; keep prohibition only as a hard guardrail, paired with its positive target**: This core-principle clause states the requirement purely as a prohibition with no adjacent positive rephrasing of what the installer should do instead (e.g. preserve/back up the existing install atomically), unlike the neighboring "leave the machine either fully installed or untouched — never half" which states the positive target before the guardrail.
  - quote: "never corrupt an existing install"
  - proposed fix: Rephrase positively and keep the guardrail as reinforcement, e.g. "preserve the existing install until the new one is verified and installed atomically — never leave it corrupted."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md

### Refuted findings

- **Negation [research]** — verifier: The document's lead framing statement is negation-led: it opens by naming the forbidden behaviour (fighting bot detection with Playwright) before stating the target behaviour. Per the doctrine, prohibition should be reserved for hard guardrails paired with a positive target, not used as the primary explanatory device for a skill's core pattern — leading with the negation drags 'Playwright' into context as the salient anchor rather than the intended handoff behaviour.
  - quote: "When a cloud console blocks headless automation, do not fight"
- **Completion criteria [craft]** — verifier: This workflow step names an action (re-read the config) but not a completion condition — it doesn't say what re-reading should confirm (e.g. that the stored value matches what Will reported). A vague bound like this invites the agent to consider the step done once the API call returns, regardless of whether the value is actually correct.
  - quote: "6. Verify (re-read the config via API)"
- **Context pointer [craft]** — verifier: "bot detection" and "'browser may not be secure'" name the same underlying trigger — the latter is Google's specific error text produced by bot detection, not a separate branch. Stacking both as distinct list items violates the pointer rule to keep one trigger per branch and collapse synonyms that rename a single branch, inflating the description's permanent context-load cost without adding a reachable condition.
  - quote: "bot detection, "browser may not be secure", 2FA, CAPTCHA, or OAuth consent screens"
- **Context pointer [craft] — keep one trigger per branch (collapse synonyms that rename a single branch)** — verifier: "whole-codebase campaigns", "broad multi-file sweeps", and "N-independent-units work" are three renamings of the same underlying trigger (a large task with many independent units), not three distinct branches. This is synonym stacking that inflates the always-loaded description without adding routing signal beyond the one genuinely distinct branch that follows ("multiple independent perspectives").
  - quote: "whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work, or when you need multiple independent perspectives (adversarial verification)"
- **Single source of truth [craft] — keep each meaning in one authoritative place** — quote_not_found: The instruction to pin `model` on mechanical subagents so they don't inherit the session model is stated three times with three different phrasings: in "Pick the lightest engine" ("Pin `model` (sonnet/haiku for mechanical sweeps — don't let them inherit the session model)"), in "Cost routing" ("Pass `model` explicitly — unpinned subagents silently inherit the session model"), and again here in Anti-patterns. Three independently-worded copies of one rule risk drifting out of sync on a future edit (e.g. if the recommended model tier changes).
  - quote: "Unpinned mechanical subagents — they inherit the expensive session model; pin `sonnet`/`haiku`."
- **Single source of truth [craft] — keep each meaning in one authoritative place** — verifier: This restates the rule already given in full under "The patterns worth knowing": "Pipeline, not barrier, by default. Only force a `parallel` barrier when a stage genuinely needs all prior results at once... Otherwise `pipeline` — item A verifies while item B is still being reviewed." The same meaning is authored twice, once as the positive rule and once as its negated restatement, doubling the maintenance surface for one decision rule.
  - quote: "Barrier where pipeline would do — wastes the fast items' idle time waiting on the slowest."
- **Negation [research] — state the target behaviour instead of leading with prohibition; keep negation only as a hard guardrail paired with its positive target.** — verifier: This bullet leads with two banned locations and their justification before ever stating the target behaviour, dragging the forbidden paths into context first. Unlike the document's other prohibitions (e.g. "Never edit source. This skill reports."), the positive instruction here is deferred to the very end of the paragraph instead of leading or immediately pairing.
  - quote: "Not at the repo root and not at `docs/DESIGN.md` — compound-engineering discovers those paths as an *HTML-styling* override for its own plan/brainstorm documents (confirmed CE v3.21.3). Use `design/DESIGN.md` (or similar) so the two never collide."
- **Context pointer [craft] — cut identity the body already states from the pointer's wording.** — verifier: The description restates identity information the body already states more precisely in Hard Rule 1 ("Never edit source. This skill reports."). This is redundant load paid on every appearance of the pointer for information the agent gets again once the material is reached.
  - quote: "Read-only on app source."
- **Context pointer [craft] — keep one trigger per branch, collapsing synonyms that rename a single branch.** — verifier: Both phrases describe the same optional branch — Step 4's propose.mjs, which emits a DESIGN.md plus DTCG token files in one run. Stating it twice with different wording is synonym-stacking for a single trigger rather than naming two distinct branches.
  - quote: "author a DESIGN.md from an existing messy codebase, or turn design-drift findings into a token architecture"
- **Completion criteria [craft] — every step ends on a condition telling the agent the work is done; a vague bound invites premature completion.** — verifier: Unlike the document's other steps, which give concrete, checkable bounds ("Confirm at the file:line before citing it", "carrying exact file:line → target token"), this step never states what a completed review looks like or what to check the highlighted fields for, inviting the agent to treat a glance as done.
  - quote: "Review the proposal — especially `action.primary` and the status colours."
- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and inflates that meaning's rank on the ladder.** — verifier: This restates, near-verbatim, the footnote already given under the mutate() chokepoint ("Cross-FS rename is NOT atomic — the temp file must be on the same filesystem as the target"). The same fact now lives in two places that can drift out of sync on a future edit.
  - quote: "**Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
