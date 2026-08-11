# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 7 trial(s), $1.6857 spent
- verify: 69 trial(s), $1.2445 spent

## Run manifest

- run: `batch4-probe-final` (2026-08-11T01:36:37Z → 2026-08-11T02:00:29Z)
- claude CLI: `2.1.224` | skill-tuner: `0.7.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ 8e13f2598a93 |
| target | `/home/will/dotfiles/claude/skills-local/goal-brief/SKILL.md` | `11aa9868aa74` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/google-safe-browsing/SKILL.md` | `57f498564398` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/harness-vet/SKILL.md` | `9aee214765b9` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/measure/SKILL.md` | `6905fc7b413b` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/youtube-transcript/SKILL.md` | `60de363d7df2` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/simplify-and-refactor-code-isomorphically-local/SKILL.md` | `ed582c934d9c` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | `c242a24c47df` | worktree @ cf3033257c8f |

## Marginal-value probe verdict

**findings_confirmed: 11**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- targets: 7
- probe calls: 7
- verify calls: 69 (3 skeptic(s) per finding)
- refuted: 12
- overflow (beyond max_findings cap, not verified): 2

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/goal-brief/SKILL.md` | 0 | 3 |
| `/home/will/dotfiles/claude/skills-local/google-safe-browsing/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/harness-vet/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/measure/SKILL.md` | 1 | 0 |
| `/home/will/dotfiles/claude/skills-local/youtube-transcript/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/simplify-and-refactor-code-isomorphically-local/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | 2 | 1 |

### Confirmed findings

- **Context load**: This HTML comment sits inside the skill file and loads into the agent's context on every invocation, but it documents maintainer rationale (provenance, why the skill was kept model-invocable, a grep-verified coverage-gap claim) rather than anything the agent needs to prevent or fix a Safe Browsing flag. It spends permanent context budget on material that serves a human auditor, not the task.
  - quote: "This operator runs multiple public sites (prbot.ai, startupbros.com) and
  the harness had ZERO prior coverage of this risk category (verified via
  grep 2026-08-10) — worth surfacing unprompted."
  - proposed fix: Move the design-rationale and provenance notes to UPSTREAM.md or a commit message; keep only the minimal license attribution (if legally required) in the file, separate from task instructions.
  - target: /home/will/dotfiles/claude/skills-local/google-safe-browsing/SKILL.md
- **Pruning and drift — Single source of truth**: The opening HTML comment states that the [measured] tags refer to the mined harness runs and that receipts live in EVIDENCE.md. The body immediately restates both facts almost verbatim ("Two evidence tags appear below: ... [measured] (observed on the harness this skill was mined from)" and "EVIDENCE.md holds the receipts for both"). Same meaning stated in two places costs tokens/maintenance for no added routing or execution value.
  - quote: "Receipts and
     external citations: EVIDENCE.md. -->"
  - proposed fix: Trim the comment to pure provenance metadata (date range, harness name, count of evaluations) and drop the clause defining what [measured] means and where receipts live — leave that definition solely to the body's "Two evidence tags appear below" paragraph.
  - target: /home/will/dotfiles/claude/skills-local/harness-vet/SKILL.md
- **Leading words**: "Sweep readers" is a coined term used nowhere else in the document and never defined — unlike "readers," which Phase 3 explicitly defines ("One reader per candidate category ... each carrying the digest"). It's unclear whether sweep readers are the same subagent primitive as Phase-3 readers, a lighter-weight variant, or something else, leaving the two-stage vet for list-type candidates underspecified.
  - quote: "sweep readers score every entry against the digest"
  - proposed fix: Either reuse the already-defined "reader" term (e.g., "readers do a lightweight pass scoring every entry against the digest") or define "sweep reader" explicitly the first time it's used, stating how it differs from a Phase-3 reader.
  - target: /home/will/dotfiles/claude/skills-local/harness-vet/SKILL.md
- **Relevance and sediment**: This is provenance/process trivia about how the document was assembled (issue number, licensing history, a memory-file pointer) rather than material bearing on how to execute the measurement procedure. It never mattered to the task of measuring something, and it will go stale the moment issue #304 or the referenced memory ages out of relevance — exactly the sediment pattern the doctrine warns accretes when 'adding feels safe and removing feels risky.' It belongs in a commit message or PR description, not in the skill body the agent reads.
  - quote: "<!-- Clean-room extraction (issue #304): method from Douglas Hubbard, "How to
     Measure Anything"; scaffold elements proven valuable in the 2026-08-10
     A/B vet (memory: nurijanian-measurement-skills-vet-2026-08). No candidate
     text vendored — the pasted upstream was unlicensed. -->"
  - proposed fix: Delete the comment entirely. If provenance must be preserved, put it in the commit message or issue #304 itself, not in the skill file.
  - target: /home/will/dotfiles/claude/skills-local/measure/SKILL.md
- **Relevance and sediment**: This is model-invocation trigger language left over from the upstream skill, but the frontmatter sets `disable-model-invocation: true` — a decision the adjacent HTML comment explicitly justifies ("invoke explicitly with /youtube-transcript instead"). With autonomous routing disabled, a list of phrases meant to fire that routing no longer bears on what the document does; it's sediment from before the invocation mode changed.
  - quote: "Triggers on "get the transcript", "transcript of this video", "pull the captions", "download subtitles"."
  - proposed fix: Drop the "Triggers on ..." sentence from the description, or replace it with plain identification text suited to a user-invoked skill (e.g. what the slash command does), since it no longer serves a routing function.
  - target: /home/will/dotfiles/claude/skills-local/youtube-transcript/SKILL.md
- **Completion criteria**: "short" is not checkable — the agent cannot tell without judgment whether a transcript qualifies, so completion of this step is impressionistic rather than verifiable.
  - quote: "Report the saved path; print the text if short."
  - proposed fix: Give a concrete threshold, e.g. "print the text if under ~500 words, otherwise just report the saved path."
  - target: /home/will/dotfiles/claude/skills-local/youtube-transcript/SKILL.md
- **Single source of truth**: The same save-location rule is stated in full in the "Save location" prose ("Otherwise (no dir given, or cwd makes no sense) → save to ~/Downloads") and then restated in the code comment. This is duplication of one meaning in two places rather than co-location, costing tokens and creating two spots to keep in sync if the rule changes.
  - quote: "OUT="$(pwd)"            # or ~/Downloads if cwd makes no sense"
  - proposed fix: Trim the code comment to a short pointer back to the rule, e.g. "# see Save location above", instead of re-stating the condition.
  - target: /home/will/dotfiles/claude/skills-local/youtube-transcript/SKILL.md
- **Single source of truth / splitting earns its cut**: This restates Loop step 0 ("0. SCOPE → for a whole-codebase campaign, parallelize via /agent-swarm (subagents / Workflow / Codex, worktree-isolated); for a single module, run solo.") in expanded form, and the same /agent-swarm pointer appears a third time in the Reference Index's Orchestration row. The same meaning lives in three always-loaded places, so changing parallelism guidance is no longer a one-place edit.
  - quote: "**Parallelism.** For campaign-scale work, fan out via [/agent-swarm](../agent-swarm/SKILL.md) — worktree-isolated subagents or Codex for parallel edits, the Workflow tool for fan-out→verify→synthesize. No file-reservation protocol needed."
  - proposed fix: Delete the standalone Parallelism section and the duplicate Orchestration Reference Index row; keep the guidance only at Loop step 0, the point in the flow where it needs to fire.
  - target: /home/will/dotfiles/claude/skills-local/simplify-and-refactor-code-isomorphically-local/SKILL.md
- **Duplication wearing polarity**: This Anti-Patterns row restates, verbatim down to the citation, the Pre-Flight checklist bullet "No file deletion without permission — per AGENTS.md Rule Number 1." It is the same rule given positively in one place and negated in another, risking drift between the two on a future edit.
  - quote: "NEVER — ask first (Rule Number 1 in AGENTS.md)."
  - proposed fix: Remove the Anti-Patterns row and let the Pre-Flight checklist bullet stand as the single statement of the rule.
  - target: /home/will/dotfiles/claude/skills-local/simplify-and-refactor-code-isomorphically-local/SKILL.md
- **Single source of truth / duplication (Pruning and drift)**: The document declares detector ids twice and the two lists have drifted apart. The canonical list under Step 1 is `color arbitrary palette scale nearcolor orphan` (six ids), but the suppression-comment list here only has four (`color arbitrary scale nearcolor`), silently dropping `palette` and `orphan`. This is the sediment pattern the doctrine warns about: the same enumeration exists in two places and one copy went stale, leaving no way to tell whether `palette`/`orphan` are genuinely unsuppressible or the list was just never updated.
  - quote: "optionally followed by detector ids
(`color arbitrary scale nearcolor`). With no ids it suppresses every detector."
  - proposed fix: Either state explicitly why `palette` and `orphan` are excluded from inline suppression (e.g. "palette and orphan are whole-file/whole-tree findings and cannot be suppressed per-line"), or reconcile the two lists to match. Better still, define the detector-id set once and have the suppression section point back to it ("any detector id from the Step 1 list except orphan/palette, see above") instead of re-enumerating.
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Single source of truth / duplication (Pruning and drift)**: This restates, almost verbatim, the explanation already given under Step 4's 'Reading the lint result': 'Expect 0 errors. `orphaned-tokens` warnings are inherent... an EMPTY frontmatter lints 0-findings — the proposer's own guard refuses to emit that, and lint-clean alone proves nothing.' The same fact (0 errors expected, orphaned-tokens warnings are normal, empty-frontmatter lints clean but proves nothing, the proposer's guard is what actually protects against that) is stated in full twice, in two different places that would each need editing if the CLI's behavior changes.
  - quote: "**Valid.** `npx -y -p @google/design.md@0.4.0 designmd lint` → 0 errors
(orphaned-tokens warnings are expected; empty frontmatter lints clean, so
lint alone proves nothing — the proposer's own guard covers that)."
  - proposed fix: Have the posture-check row point back to the earlier explanation instead of repeating it, e.g. "Valid. `npx ... lint` → 0 errors (see 'Reading the lint result' in Step 4 for caveats)."
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md

### Refuted findings

- **Single source of truth / duplication (Pruning and drift)** — verifier: The comment itself says attribution already lives in LICENSE + UPSTREAM.md, then re-narrates that same provenance story (fabricated upstream claims, lifecycle states, pause/resume, create_goal, subscription auth) inline in the skill body anyway. This is always-loaded sediment: none of it bears on the task of drafting a contract body from $ARGUMENTS, and it duplicates a meaning the doc names its own authoritative source for.
  - quote: "<!-- Template adapted from davidondrej/skills goal-loop (template only; every
     product/feature claim in that source -- lifecycle states, pause/resume,
     create_goal, subscription auth -- is fabricated and discarded; LICENSE +
     UPSTREAM.md in this directory carry attribution). Our real `/goal <text>`
     is a Claude Code built-in: it installs a session-scoped Stop hook that
     blocks stopping until the condition holds and auto-clears on success
     (see memory: goal-command-sets-session-scoped-stop-hook). -->"
- **Negation (Leading words)** — verifier: Two stacked prohibitions in the Constraints field with no paired positive target, which per the doctrine drags the banned behaviours ('refactor unrelated code', 'add dependencies') into context as the more available concept rather than suppressing them.
  - quote: "Do not refactor unrelated code. Do not add dependencies."
- **Negation (Leading words)** — verifier: Four stacked negations in the anti-reward-hacking clause with no positive framing paired anywhere in the sentence or the field -- exactly the tell the doctrine flags: a rule that leads with the ban and never says what to do instead.
  - quote: "Do not delete, skip, weaken, or narrow tests to make the goal pass."
- **One trigger per branch** — verifier: Five of these six phrases ("dangerous site", "deceptive site", "site blocked", "phishing flag", "red warning screen") all rename the single branch already stated earlier in the same description — "any site shows a red 'Dangerous site' / 'Deceptive site' warning in Chrome, Brave, Safari, Firefox, or Edge." A run reaching the skill via any of these synonyms takes the identical path (Diagnosis/Recovery), so per the doctrine they should collapse to one trigger instead of paying always-loaded context cost six times over.
  - quote: "Triggers on "dangerous site", "deceptive site", "site blocked", "safe browsing", "phishing flag", "red warning screen"."
- **Single source of truth** — verifier: The specific fact that startupbros.com and prbot.ai are already covered by the service account is already stated in full in the 'Our stack' section above, and is meant to be derived live via `gsc sites --json` in both places. Restating the domain names here duplicates that fact and creates two places to update if the service account's grants ever change — exactly the caching-what-should-be-looked-up anti-pattern the doctrine warns against.
  - quote: "Confirm coverage: `gsc sites --json` — already listed (true today for `startupbros.com` and `prbot.ai`) → skip to step 3."
- **Structure and disclosure — Co-location** — verifier: This instruction lives in Phase 1 (Intake) and tells the agent to score entries against "the digest," but the harness digest isn't built until Phase 2 (Digest). Applying this Phase-1 step correctly requires content the document hasn't introduced yet, which is exactly the co-location failure the doctrine names: reading one part (Phase 1) doesn't bring the neighbour (Phase 2) it depends on.
  - quote: "sweep readers score every entry against the digest, then at most 3 entries per run get the full phases 3-6."
- **Context pointers — Cut identity the body already states** — verifier: The frontmatter description already enumerates the candidate types ("Vet a skill, plugin, MCP server, rules file, repo, or paper"). The body's opening sentence restates the identical list. This is the pointer-and-body restating the same identity information, adding no new routing or execution signal while creating two places to keep in sync if candidate types change.
  - quote: "You are vetting a **candidate** — a skill, plugin, MCP server, rules file, repo,"
- **Negation** — verifier: This is a pure prohibition with no positive target stated alongside it, so attention lands on the banned behavior (downloading audio for Whisper) rather than on what to do instead. The doctrine requires even justified hard guardrails to be paired with their positive target.
  - quote: "Never fall back to downloading audio for Whisper unless the user explicitly asks."
- **One trigger per branch (context pointers)** — verifier: "reduce duplication" and "DRY" are two description triggers for the same branch. The skill's own Quick Triggers table confirms this by collapsing "remove duplication" / "DRY it up" into a single row with one first move — so a run reaching the document through either phrase takes the same path. Paying always-loaded description tokens twice for one branch is exactly the case the rule warns against.
  - quote: "duplication, remove lines, extract helper, reuse component, DRY, collapse, better abstraction"
- **Single source of truth (cache vs. duplication)** — verifier: The Rule, Loop, score formula, clone taxonomy, and commit gates are already written out in full in this same SKILL.md body (The One Rule callout, The Loop, Opportunity Matrix, Duplication Taxonomy, Checklist). QUICK-REFERENCE.md isn't caching an expensive external lookup — the source is the very document the pointer sits in — so it's a second authoritative copy of the same meanings rather than a justified cache.
  - quote: "one-screen card with the rule, loop, score formula, clone taxonomy, and every commit gate"
- **Duplication wearing polarity** — verifier: "One lever per commit" is already stated positively in Loop step 5, the Pre-Flight checklist ("One lever per commit"), and the final Checklist ("One lever only"). This row, and the neighboring "Introduce a new abstraction while removing duplication" row, restate the same constraint negated instead of pointing back to the existing rule.
  - quote: "Rename during refactor | Two levers per commit; reviewers can't tell what changed"
- **Cut identity the body already states (Context pointers)** — verifier: The description restates, in near-identical wording, the identity claim the body already makes for itself in its opening line: 'A detection skill. It does ONE thing: find where a codebase has drifted away from a design system — or never had one.' The pointer's job is to state when to reach the document, not to re-describe what it fundamentally is once the reader is already in it.
  - quote: "Find where a codebase reinvents its own design system — raw colour literals,
one-off Tailwind arbitrary values, palette utilities, unresolved tokens, and
clusters that reveal a scale nobody defined"
