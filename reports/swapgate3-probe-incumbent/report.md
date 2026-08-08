# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 16 trial(s), $3.8413 spent
- verify: 177 trial(s), $3.6257 spent

## Run manifest

- run: `swapgate3-probe-incumbent` (2026-08-07T23:51:31Z → 2026-08-08T00:49:10Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/dotfiles/claude/skills-local/writing-for-agents/SKILL.md` | `a61475f4549b` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0dc154c88283` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `7d2290123e00` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `a8d1903218b1` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `2d965c7d2ff9` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `824fdef96119` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `808fcc7103af` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `b6e7cba9bcb5` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `6bcf11e24d2f` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `291233457df4` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `a14d423610c4` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `c6db47a75b83` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `ce83411bd389` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | `d71863fc644d` | git:origin/main @ 57d885c18ad0 (differs-from-worktree) |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `e55823e32a45` | git:origin/main @ 57d885c18ad0 |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `9ab5c7a6100c` | git:origin/main @ 57d885c18ad0 |

## Marginal-value probe verdict

**findings_confirmed: 30**

- doctrine: /home/will/dotfiles/claude/skills-local/writing-for-agents/SKILL.md
- targets: 16
- probe calls: 16
- verify calls: 177 (3 skeptic(s) per finding)
- refuted: 29

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 3 | 2 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 2 | 3 |

### Confirmed findings

- **Context pointers — one trigger per branch; collapse synonyms that rename a single branch**: 'whole-codebase campaigns', 'broad multi-file sweeps', and 'N-independent-units work' are three different phrasings of the same underlying branch (a large task decomposable into independent units), not genuinely distinct branches. Only 'multiple independent perspectives (adversarial verification)' is a truly separate branch.
  - quote: "whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work, or when you need multiple independent perspectives (adversarial verification)"
  - proposed fix: Collapse to one phrasing, e.g. 'whole-codebase campaigns and other N-independent-units work (refactor / audit / migration / dead-code sweep), or when you need multiple independent perspectives (adversarial verification).'
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Pruning — relevance (a line loses relevance by never bearing on the task; mere exposition becomes sediment)**: This is creation-date/changelog metadata about the skill's history, not material the agent needs to execute the skill. It sits in the body (loaded on every invocation) and never bears on what the agent does when running a swarm.
  - quote: "<!-- New skill (not a jsm fork), 2026-07-04. Replaces the trashed jsm swarm mechanism
     (ntm + agent-mail + beads) with the operator's native primitives. Skills that need
     campaign-scale parallelism reference this instead of re-deriving swarm coordination. -->"
  - proposed fix: Delete the comment; keep this history in the commit message or a changelog, not the skill body.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Pruning — single source of truth / duplication; Negation is the failure mode (steering by prohibition should pair with, not merely restate, the positive already given)**: Every bullet here is a negated restatement of a rule already given positively earlier in the same document (solo/inline threshold under 'Pick the lightest engine', worktree isolation under 'Isolation is the coordination', model pinning under both 'Pick the lightest engine' and 'Cost routing', pipeline-vs-barrier under 'The patterns worth knowing', Codex absorption under 'Cost routing', and the message-bus/bead-pool point under the core-shift callout). This duplicates the same meaning across multiple places (inflating its prominence and creating a maintenance burden) and uses negation to restate rules that were already stated as positives, rather than adding new guardrails.
  - quote: "## Anti-patterns

- **Orchestrating a trivial task** — solo/inline beats a swarm below ~5–7 units.
- **Parallel mutation without worktree isolation** — the one way to actually get conflicts back.
- **Unpinned mechanical subagents** — they inherit the expensive session model; pin `sonnet`/`haiku`.
- **Barrier where pipeline would do** — wastes the fast items' idle time waiting on the slowest.
- **Silently doing a Codex-sized batch in the session model** — that's the delegation the routing exists for.
- **Re-implementing a message bus / task pool** — you have the Workflow tool; don't rebuild beads."
  - proposed fix: Delete the section, or cut it down to only genuinely new caveats not already stated; if a scannable checklist is wanted, cross-reference the earlier bullets by name instead of re-deriving each rule as a negation.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Context pointers — cut identity the body already carries**: This spells out the entire seven-step Build Sequence (its own section headers: "Should this animate at all?", "What is the purpose?", "Pick the tool", "Pick the properties", "Easing and duration", "Interruption and exit") inside the always-loaded description. The pointer only needs to state what the material is and when to reach it, not replicate the body's structure at cost on every turn.
  - quote: "making the decisions in the order that determines whether it feels right — should it animate at all, what purpose, which tool, which properties, which curve and duration, how it interrupts, how it exits"
  - proposed fix: Trim to identity plus trigger, e.g. "Build an animation from scratch, gating on whether it should animate before writing the implementation."
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Steps and completion criteria — clarity: a vague or contradictory bound leaves the agent unable to tell done from not-done**: This flat rule sits directly beneath the Duration table's own "Modals, drawers | 200–500ms" row, which explicitly sanctions durations up to 500ms — nearly double the stated 300ms ceiling. The completion criterion for picking a duration is contradictory: the agent cannot tell whether a 400ms modal transition satisfies or violates the rule.
  - quote: "**UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
  - proposed fix: Scope the ceiling, e.g. "Non-modal UI animations stay under 300ms; modals/drawers may run to 500ms per the table above."
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Context pointers — 'A pointer does two jobs — state what the material is, and list the branches that should trigger reaching it.'**: The pointer attributes 'spatial consistency' and 'restraint' to the 'design foundations' branch, but §16 ('Design foundations — the eight principles') is Purpose/Agency/Responsibility/Familiarity/Flexibility/Simplicity/Craft/Delight — it contains neither term. 'Spatial consistency' is actually the title of the unrelated §7 (symmetric paths, anchored origins, a motion rule), and 'restraint' names no section or concept anywhere in the body. An agent using the pointer to decide whether/where this skill answers a spatial-consistency or restraint question is misled about the document's actual structure.
  - quote: "the design foundations (feedback, spatial consistency, restraint) behind Apple-style interfaces"
  - proposed fix: Either rename the parenthetical to match §16's real content (e.g. 'design foundations (purpose, agency, craft)') or move 'spatial consistency' out to sit alongside the motion/gesture branches where §7 actually lives, and drop 'restraint' unless a concept by that name is added to the body.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Keep each meaning in a single source of truth: one authoritative place, so changing the behaviour is a one-place edit. Duplication — the same meaning in more than one place — costs maintenance and tokens.**: The weight of each scoring factor (40/30/20/10%) is already stated in the table immediately above ('Frequency 40%', 'Time saved 30%', etc.). Restating the identical weights as formula coefficients means a future weight change requires editing two places instead of one.
  - quote: "Score = freq_norm×0.4 + time_norm×0.3 + fail_norm×0.2 + simplicity_norm×0.1"
  - proposed fix: Drop the % column from the table and let the formula be the single source of truth for weights (or drop the formula and keep only the table, with prose describing how to combine the normalized scores).
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Keep each meaning in a single source of truth: one authoritative place, so changing the behaviour is a one-place edit. Duplication — the same meaning in more than one place — costs maintenance and tokens.**: This decision tree re-encodes the same mapping already stated in the top-of-document Principle table ('Complex/stateful → Python; glue → bash; one-liner → alias'). The two independently-editable statements of the same routing rule mean a change to the implementation-choice logic must be made twice.
  - quote: "Stateful? (remembers across runs, parses data, needs SQLite/JSON)
├─ YES → Python CLI (uv/pipx), argparse/click, --json output
│  ├─ Scheduled? → systemd timer
│  └─ Interactive? → subcommands + --json
└─ NO
   ├─ >3 steps of glue? → bash script → ~/.local/bin/
   ├─ Retry/guard?      → bash wrapper + set -euo pipefail
   └─ Single command?   → shell alias/function → ~/.bash_aliases"
  - proposed fix: Remove the mapping row from the Principle table (keep only the frequency×pain principle there) and let the Step 3 flowchart be the single, authoritative statement of the implementation-choice rule, since the flowchart carries more detail anyway.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Pruning — relevance (mere exposition doesn't bear on the task)**: This is historical exposition about the skill's own provenance — it never bears on what the agent does when running the skill, yet sits in the in-file body that is fully loaded on every invocation. Git commit history is already the authoritative source for what was distilled and when.
  - quote: "<!-- Distilled 2026-07-04 from the retired 130-file `git-worktree-branch-rationalization`
     skill: kept the archaeology + harmonization + safety kernel; dropped the multi-agent
     swarm tiers, wizard-style adjudication, fuzzing/conformance testing, per-language
     deep-dives, the Bayesian machinery, and the 30 subagents. See references/HARMONIZATION.md. -->"
  - proposed fix: Move this note out of the skill body into the commit message or a changelog file that isn't loaded at invocation time.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Context pointers — one trigger per branch**: "a new persona needs voice definition" is a synonym restatement of the branch already listed earlier in the same description ("Use when starting a new brand, sub-brand, product, persona, or author voice"). This is one branch written twice rather than a genuinely distinct trigger, inflating the always-loaded description.
  - quote: "Use when copy sounds generic, when a new persona needs voice definition, or when the answer to "how should this sound?" is unclear."
  - proposed fix: Drop the "new persona needs voice definition" clause from the second Use-when list since persona is already covered in the first list.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Pruning — single source of truth / duplication**: The 'Quality Test' embedded in the Voice Profile template already tests this exact meaning ("Actionable: could a writer (human or AI) produce on-brand content using only this profile?"), as does the mechanical-rules and anti-aspiration overlap between the two lists. Two differently-named checklists ('Quality Test' vs 'The Test') restate largely the same criteria, so a change to one criterion requires remembering to update the other.
  - quote: "A second writer (human or AI) can produce content from it that the user accepts on first draft"
  - proposed fix: Merge the two checklists into one. Keep 'Quality Test' inside the Voice Profile template as the single authoritative pass/fail list, and trim 'The Test' at the end of the skill to only the criteria that are genuinely distinct (e.g. 'the profile gets used') rather than repeating actionability, differentiation, and mechanical-cleanliness checks.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Leading words — negation**: The preceding sentence, "Ask in 5 batches," already states the positive target. This negation restates the same instruction by invoking the forbidden behavior (dumping all 17 at once) rather than adding new information, paying load to say nothing beyond what the positive instruction already conveys.
  - quote: "Don't dump all 17 at once."
  - proposed fix: Delete the sentence, or fold its intent into the positive instruction: "Ask in 5 batches, waiting for answers before moving to the next."
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Context pointers — one trigger per branch**: "bot detection", "browser may not be secure", and "OAuth consent screens" are largely restatements of one branch (automation is blocked by anti-bot checks during an OAuth-style flow) rather than genuinely distinct triggers, and OAuth consent is already named in the main clause's parenthetical example list. Listing near-synonyms as separate triggers inflates the always-loaded pointer without adding distinct branches.
  - quote: "Use when a console step cannot be scripted: bot detection, "browser may not be secure", 2FA, CAPTCHA, or OAuth consent screens."
  - proposed fix: Collapse to the genuinely distinct branches, e.g. "Use when a console step is blocked from automation (bot/anti-WebDriver detection, CAPTCHA) or has no API path at all (2FA, one-time secret reveal)."
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Information hierarchy / Progressive disclosure — push behind a pointer what only some branches reach**: Everything under this heading — the diagnostic checkpoint query, the explanation of why `cass index --full` stalls, the 8-variable `setsid`/`nohup` repair command, and the verification criteria — is reference material for one rare failure branch (a broken lexical index). It is inlined in the main skill body rather than disclosed behind a pointer, so it loads every time the skill fires even though the overwhelming majority of invocations (a normal search) never reach this branch, bloating the primary path the doctrine says should stay legible.
  - quote: "## If it returns "no results" for everything"
  - proposed fix: Move this section into a sibling file (e.g. `TROUBLESHOOTING.md`) and replace it in the main body with a short pointer: "If `cass-rerank` returns no results for everything, the lexical index is likely broken — see TROUBLESHOOTING.md for the repair procedure."
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Leading words — a repeated token anchors one concept; reusing it for two concepts breaks the anchor**: The same symbol 🚫 is assigned to two distinct axioms (never-silent-fail and no-TUI-on-bare-invocation). Later the doc leans on the bare symbol to recall a specific axiom (e.g. the Intent-Recovery Triad's '🚫 never-silent-fail'), but since 🚫 now names two different things, the token can't reliably anchor either one — the exact failure mode the leading-word technique is meant to avoid.
  - quote: "- **🚫 Never silent-fail.** A command that fails but exits 0 with empty stdout is the agent's worst
  nightmare — it can't even detect the failure to retry. Every failure → stderr + non-zero exit.
- **🚫 No TUI on bare invocation.** Bare `<tool>` launching a TUI blocks any agent that didn't expect it.
  Either `<tool>` shows useful help/triage and exits, or `<tool> tui` is the explicit interactive entry — never both."
  - proposed fix: Give the TUI axiom its own unique symbol (e.g. 🔓 or 🖥️) so 🚫 uniquely means never-silent-fail throughout the document.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Leading words — consistency of the token across the document**: The axiom is marked with the symbol ① (reads as '1') but the same bullet names it 'Axiom 0'. The symbol and its own stated name disagree, so an agent trying to use the token to recall 'the axiom that wins ties' has no stable anchor between the two labels.
  - quote: "**① First-try inevitability.** The first command an agent guesses must work or be redirected with a
  useful hint. A surface that fails this on its *canonical* task is a P0 finding regardless of other scores. **Axiom 0 wins ties.**"
  - proposed fix: Make the symbol and the name agree — either use ⓪ for the symbol, or rewrite the sentence as 'Axiom ① wins ties.'
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning — relevance (mere exposition costs context load without bearing on the task)**: This is pure history about the skill's own distillation — which prior sections were kept or dropped from a retired skill. It never bears on how an agent should audit or fix a CLI's ergonomics, yet it is loaded into context on every invocation of the skill.
  - quote: "Distilled 2026-07-04 from the retired 192-file `agent-ergonomics-and-intuitiveness-maximization-for-cli-tools`
     skill: kept the kernel axioms, the error-rewriting cookbook, the named operators, the mega-command shapes,
     the 11-dim rubric, and the recurring-fixes checklist. Dropped the multi-agent swarm tiers, session-mining,
     per-pass 0-1000 scoring machinery, agent-profile reweighting, 27 subagents, and 47 scripts."
  - proposed fix: Delete the distillation history from the file; if it must be kept for humans, move it to a CHANGELOG or commit message outside the skill file.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning — single source of truth / duplication**: This restates, almost word-for-word, the fact already given in the mutate() chokepoint section ("Cross-FS rename is NOT atomic — the temp file must be on the same filesystem as the target."). Two authoritative statements of the same fact means an edit to one can silently diverge from the other, and it inflates this fact's prominence past its real rank on the ladder.
  - quote: "**Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
  - proposed fix: Drop the restatement in Anti-patterns and instead cross-reference the chokepoint step, e.g. "Cross-filesystem rename (see mutate() step 6) — not atomic."
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Pruning — relevance**: This is always-loaded content (an inline comment in the main file, not behind a pointer) that recounts the skill's authoring history rather than anything the agent needs to add or upgrade a doctor subcommand. It never bears on the task itself — pure exposition that costs context load on every invocation.
  - quote: "Distilled 2026-07-04 from the retired 166-file `world-class-doctor-mode-for-cli-tools` skill:
     kept the One Rule + core axioms, the CLI surface, the mutate() chokepoint / safety envelope,
     the (detector,fixer,fixture,test) tuple, the 10-dim rubric, and the portable cookbook. Dropped
     the multi-model swarm tiers, session-mining, external issue-tracker plumbing, the per-run 0-1000
     scoring machinery, 18 subagents, and 39 scripts."
  - proposed fix: Move this changelog note to the skill's commit message or a CHANGELOG, keeping only the still-actionable pointer ("JSON shapes + rubric + cookbook: references/DOCTOR-SPEC.md") in the file.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Context pointers — 'Every word of an always-loaded pointer costs on every turn, so it earns even harder pruning than the body' / Pruning — single source of truth (duplication)**: The frontmatter description is always-loaded pointer material and states the same fact twice: 'read-only' already establishes that Codex cannot modify anything, then the second sentence restates it as 'Codex never edits files.' Pointers are singled out for harder pruning than the body precisely because every word costs on every turn — this is a synonym restating one fact, not two distinct pieces of information.
  - quote: "Ask Codex (GPT-5.5) for a read-only second opinion on the current problem, then synthesize agree/disagree against Claude's own view. Advisory only — Codex never edits files."
  - proposed fix: Collapse to one statement, e.g.: "Ask Codex (GPT-5.5) for a read-only second opinion on the current problem, then synthesize agree/disagree against Claude's own view." — drop the redundant 'Advisory only — Codex never edits files' clause, since 'read-only' already carries that meaning.
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Pruning — relevance ("A line loses relevance by never bearing on the task (mere exposition...) or by going stale as the behaviour or world it describes changes.")**: This is historical exposition about the skill's own lineage — it doesn't help the agent write an installer and is already stale-by-construction (describing a retired predecessor). It rides in context on every load for no behavioral payoff.
  - quote: "Distilled 2026-07-04 from the retired 30-file `installer-workmanship` skill, whose method was to
     study-and-emulate two upstream install.sh exemplars that don't exist on this machine."
  - proposed fix: Delete the provenance narrative; keep only the still-load-bearing pointer to pro-gate-lib.sh (already stated in the Core principle box) if it isn't duplicated there.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Pruning — single source of truth ("Duplication — the same meaning in more than one place — costs maintenance and tokens.")**: Both facts here are restated verbatim in the body: the pro-gate-lib.sh reference exemplar is repeated in the "Core principle" callout ("Reference exemplar for real cross-platform locking/OS-detection: `~/SITES/pro-gate/lib/pro-gate-lib.sh`"), and the PATTERNS.md pointer is repeated under the "Agent auto-config, draw_box, uninstall/service" heading. The comment adds no new meaning, only maintenance surface.
  - quote: "Locking + OS-detection re-anchored
     on the operator's own ~/SITES/pro-gate/lib/pro-gate-lib.sh (production flock-first/mkdir-fallback).
     Agent auto-config + draw_box + uninstall: references/PATTERNS.md"
  - proposed fix: Remove these two sentences from the comment and rely on the single in-body statements as the source of truth.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Context pointers ("A pointer does two jobs — state what the material is, and list the branches that should trigger reaching it") / Information hierarchy branching test ("inline what every branch needs, and push behind a pointer what only some branches reach")**: The section's only stated trigger is "If the CLI plugs into AI agents…", but the pointer also gates the `draw_box` implementation and uninstall/service snippets — both required on every run per non-negotiables #12 and #13, not only the AI-agent branch. An agent building a non-agent-integrated CLI could read the conditional framing and skip fetching PATTERNS.md, missing the mandatory final-summary-box and uninstall material.
  - quote: "The full detection + JSON-merge-with-backup pattern (the load-bearing reusable piece), the `draw_box` implementation, and the uninstall/service snippets are in [references/PATTERNS.md](references/PATTERNS.md)."
  - proposed fix: Split the pointer: keep the AI-agent-conditional detection/JSON-merge pattern under its "if the CLI plugs into AI agents" trigger, and state separately, unconditionally, that draw_box and uninstall/service snippets (required every run) are also in references/PATTERNS.md.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Pruning — single source of truth / duplication**: The install-without-approval rule is stated in full twice: once here in 'First actions, in order' step 5, and again in Confirmation item 4 ('offer (a) auto-install all missing, (b) per-tool interactive, (c) skip-and-degrade ... Never install without approval.'). Same meaning in two places means a future change to the approval policy requires editing both, and it inflates the rule's footprint on the ladder beyond its rank.
  - quote: "then get the toolchain install/degrade decision (never auto-install before approval)."
  - proposed fix: In step 5, drop the parenthetical and just point back: 'then get the toolchain install/degrade decision (see Confirmation 4).' Keep the full policy statement only in the Up-Front Confirmations section.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Pruning — single source of truth / duplication**: The convergence definition is fully restated here in Quick-Start and again, in different wording, under 'Convergence (non-negotiable)' ('Converged = two consecutive quiet rounds AND ≥10 total rounds AND zero unresolved hypotheses...'), and gestured at a third time in the ABORT IF bullet about the '≥10-round convergence floor'. This is one meaning spelled out twice (plus a third reminder), so a change to the formula (e.g. adjusting the round floor) risks going stale in one of the copies.
  - quote: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings
              AND every hypothesis resolved (SEAM_CONFIRMED / SEAM_REFUTED /
              DEFERRED+rationale with `Deferred reviewed: yes`)."
  - proposed fix: State the convergence formula once, in the 'Convergence (non-negotiable)' section, and have the Quick-Start block and the ABORT IF bullet just point to it (e.g. 'Convergence: see Convergence section below') rather than restating the AND-clauses.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Context pointers — a must-have target behind a weakly worded pointer is a variance bug**: The document itself treats compile-memory/rustc-exhaustion requests as a distinct, explicitly-supported branch (smell-test row: "'This file is slow to compile' / 'rustc eats 20GB on this crate' → YES (compile-memory monolith track)", and the Self-Test trigger phrase "rustc runs out of memory on this crate — restructure it"), but the always-loaded frontmatter description — the pointer that decides whether this skill is even reached — never mentions compile time, memory, or rustc. A query phrased that way is less likely to route to this skill at all.
  - quote: "Use when de-monolithize, split giant file, modularize repo, or file too big."
  - proposed fix: Add the compile-memory branch to the description, e.g. '...or file too big, or compile times/memory blowing up.'
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Steps and completion criteria — Clarity (a wrong or vague bound invites premature completion)**: The step tells the agent to read 'the four detectors,' but the table immediately below it lists six rows (colour literals, arbitrary values, raw palette utilities, missing scales, near-duplicate colours, unresolved tokens), matching the six ids later listed ('color arbitrary palette scale nearcolor orphan'). An agent anchoring on the stated count of four has a checkable-but-wrong bound and may treat the step as done after the first four rows, silently skipping near-duplicate colours and unresolved tokens.
  - quote: "### 2. Read the four detectors"
  - proposed fix: Change the header to 'Read the six detectors' (or otherwise make the count match the table's six rows).
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Pruning — single source of truth / duplication**: The "Perceived performance" section restates claims already made verbatim earlier in the document: "A faster-spinning spinner makes the app feel like it loads faster, even when the load time is identical" and "A 180ms dropdown feels more responsive than a 400ms one" both appear under "How fast should it be?", and the ease-out/ease-in perception claim repeats the reasoning already given under "Never use ease-in for UI animations." The instant-tooltip point is also re-covered later in "Tooltips: skip delay on subsequent hovers." None of this adds new meaning; it duplicates three other sections under a new heading.
  - quote: "- A **fast-spinning spinner** makes loading feel faster (same load time, different perception)
- A **180ms select** animation feels more responsive than a **400ms** one"
  - proposed fix: Delete the "Perceived performance" section and fold any non-redundant point (if any) into the "How fast should it be?" and easing sections where the claims already live.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Pruning — single source of truth / duplication**: This restates the exact handoff logic already given in Hard Rule 1 ("If asked to build a suggestion, hand it off: `ce-plan` for a tracked change (carry the exact values from the table into the plan), or `animate` to build it directly when it is small enough not to need a plan."). Same meaning, two locations — a future change to the handoff rule (e.g. a new target skill) now requires editing both spots and risks drift.
  - quote: "Close by pointing at the handoff: hand the chosen row to `ce-plan` as the origin document (carrying its exact curve, duration and properties verbatim) for a tracked change, or to `animate` to build it now if it is a one-component fix."
  - proposed fix: Keep the full handoff rule only in Hard Rule 1. In the Verdict section, just point back to it: "Close by pointing at the handoff — send the top row to `ce-plan` or `animate` per the handoff rule above."
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Pruning — relevance**: Pure exposition that never bears on what the agent does — it restates the framing already established in Operating Posture ("this skill is a filter as much as a finder") without adding any new instruction or criterion.
  - quote: "This section is what separates this skill from an animation wishlist."
  - proposed fix: Delete the sentence; the Rejected Candidates section's purpose is already clear from its content and requirement (2–5 entries with gate reasons).
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Context pointers — front-load the leading word (the pointer is where it does its triggering work)** — verifier: The skill description is a context pointer, and its triggering condition ('Use when...') is buried behind a full sentence of identity/mechanism description instead of leading. The pointer's wording decides when the agent reaches the skill, so delaying the trigger weakens the moment where it does its triggering work.
  - quote: "Run a large or parallelizable task across many agents using the native stack —
  parallel Claude Code subagents, the Workflow tool, Codex delegation, and worktree
  isolation — instead of a coordination protocol. Use when a task is too big for one
  context or has many independent units:"
- **Context pointers — one trigger per branch: synonyms that rename a single branch are one branch written twice; collapse them** — verifier: The four listed triggers — "animate something", "add motion", "make a component feel alive", "build a transition" — are near-synonyms for a single branch (a request to build an animation), not genuinely distinct cases. This is a single trigger written four times in an always-loaded pointer.
  - quote: "Use when asked to animate something, add motion, make a component feel alive, or build a transition."
- **Pruning — single source of truth: duplication of the same meaning in more than one place costs maintenance and inflates prominence** — verifier: This restates the rule already given in full in "Pick the properties" ("**Never `scale(0)`.** Start from `scale(0.9–0.97)` + `opacity: 0`."), and the restatement has already drifted from the source — "scale(0.95)" is a single value where the canonical rule gives a range — the exact maintenance-cost risk the doctrine warns duplication creates.
  - quote: "| `transform: scale(0)` entrance | `scale(0.95)` + `opacity: 0` |"
- **Information hierarchy / Sprawl — 'Branching is the cleanest disclosure test: inline what every branch needs, and push behind a pointer what only some branches reach.'** — verifier: The pointer's own branch list shows these are genuinely disjoint use cases (a typography task needs none of the spring/gesture/momentum material; a translucency task needs none of the typography or eight-principles material), yet the document inlines all 17 sections plus a Quick Reference into one file that loads in full on every invocation. Per the disclosure test, only material every branch needs (e.g. 'The Core Idea') belongs at the top; the rest should be split behind pointers by branch (motion/gesture, materials & depth, typography, design foundations) so a given task loads only its own path.
  - quote: "Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency, restraint) behind Apple-style interfaces."
- **Pruning — single source of truth / duplication: 'Keep each meaning in a single source of truth... Duplication... costs maintenance and tokens.'** — verifier: This restates, in a second notation, the exact projection formula and deceleration constant already given as executable code in §6 (`function project(initialVelocity, decelerationRate = 0.998) { return (initialVelocity / 1000) * decelerationRate / (1 - decelerationRate); }`). The Quick Reference table repeats this pattern for nearly every row (default spring damping, velocity-handoff formula, rubber-banding, etc.), each already stated in its own section — the same facts now live in two places that must be kept in sync.
  - quote: "| Flick landing point | Project momentum | `current + (v/1000)·d/(1−d)`, `d ≈ 0.998` |"
- **Branching is the cleanest disclosure test: inline what every branch needs, and push behind a pointer what only some branches reach.** — verifier: 'Detect the data source first' establishes atuin-present vs. no-atuin as mutually exclusive branches — only one applies per run. Yet both Path A (full SQL queries) and Path B (full awk/sort recipes) are fully inlined in the main file even though a 'Full cookbook' / 'More parsing recipes' pointer to references/ATUIN-QUERIES.md and references/SHELL-HISTORY.md already exists for overflow detail. Every run pays the context load of the branch it did NOT take.
  - quote: "### Path A — atuin present (rich queries)

Open read-only: `sqlite3 -readonly "$ATUIN_DB"`. Atuin stores `timestamp`/`duration` in **nanoseconds**; exit 0 = success."
- **Keep each meaning in a single source of truth: one authoritative place, so changing the behaviour is a one-place edit. Duplication — the same meaning in more than one place — costs maintenance and tokens.** — verifier: This guardrail duplicates the meaning already captured in the Anti-Patterns table row 'Automate before measuring | Mine history first'. Both state the same rule (don't build before measuring) in two separately maintained places.
  - quote: "**Never skip 1-3.** Intuition about what's repetitive is unreliable; data wins."
- **Context pointers — one trigger per branch / cut identity the body already carries** — verifier: This trailing sentence in the always-loaded description restates the same trigger already given in the first sentence ('forgotten branches/worktrees left by parallel agents'). It is a synonym renaming one branch, not a distinct branch, so it spends context-load tokens on every turn without adding new triggering information.
  - quote: "Use for parallel-agent branch cleanup."
- **Pruning — single source of truth / duplication** — verifier: Every item restates a rule already stated verbatim elsewhere in the document with no new execution detail: 'picking a winner' vs. the opening callout ('the job is NOT "pick the right branch"'), 'landing on canonical' vs. Safety kernel #2, 'trusting git log' vs. Phase A step 1, 'classifying by branch name' vs. the 'Let the fingerprint override the name' line, 'batch-deleting' vs. Safety kernel #6/#7, and 're-implementing the scripts' vs. the Pipeline section's 'Don't re-implement their funnel here.' This duplicates the same meaning in six places, so a future edit to any one rule requires updating two places to stay consistent.
  - quote: "## Anti-patterns

- **Picking a winner among colliding branches.** That's the failure this skill exists to prevent — you lose
  the real work in every branch you didn't pick. Harmonize.
- **Landing recovered work directly on canonical.** Always the `branch-rationalization-<date>` staging branch.
- **Trusting `git log` ancestry over `git cherry -v`.** Squash/rebase-landed content looks novel to `log`.
- **Classifying by branch name.** The fingerprint is the evidence; the name is a prior.
- **Batch-deleting after one "yes".** Per-plan verbatim authorization, individual removals, backups first.
- **Re-implementing wt-sweep.sh / branch-triage.sh here.** Let them do the mechanical pass; start from RESIDUE."
- **Context pointers — cut identity the body already carries** — verifier: This always-loaded frontmatter description restates the full structure of the output, which the body already documents exhaustively under '## The Voice Profile (Output Format)'. The pointer's job is to state what the material is and list trigger branches, not carry the body's identity — this sentence spends context load on every turn without helping the routing decision.
  - quote: "Outputs a complete Voice Profile with tone spectrum, vocabulary, mechanical rules, on-brand and off-brand example phrases, aspiration and anti-aspiration models, and a quality test."
- **Information hierarchy — progressive disclosure (branching test)** — verifier: Any single run of this skill takes either Extract mode or Build mode, never both — yet the full six-lens analysis process (Extract-only) and the full 17-question process (Build-only) are both inlined in the main file. Per the branching disclosure test, material only some branches reach should sit behind a pointer, not be carried by every run's context.
  - quote: "### The 17 Strategic Questions"
- **Pruning — single source of truth / duplication** — quote_not_found: These three checklist items restate the exact same three rules already stated verbatim in "Critical rules" ("Include FULL URLs with query params...", "Use EXACT element text...", "Say precisely WHAT to report back and the format...") and again in the Anti-patterns table ("Vague \"click the button\"", "Skip query params"). The same meaning is stated in three separate places, inflating its prominence past its real rank and creating three spots to update if the rule changes.
  - quote: "- [ ] URLs verified (correct page loads in Brave)
- [ ] Element names match the current UI exactly
- [ ] Clear "report back" format"
- **Pruning — single source of truth / duplication** — verifier: This callout restates the same sequence as the numbered "Workflow" section immediately below it (open URL in Brave -> paste-ready instructions -> get IDs/secrets back -> wire in programmatically). The workflow's meaning now lives in two places, so a change to the process requires editing both.
  - quote: "> **Core pattern:** When a cloud console blocks headless automation, do not fight
> it with Playwright. Open the exact URL in Will's real Windows Brave, hand him
> precise paste-ready clicks, get the resulting IDs/secrets back, then wire them
> in programmatically."
- **Context pointers — cut identity the body already carries** — verifier: The frontmatter description (an always-loaded context pointer) spells out the exact same target list that Workflow step 5 already states ("Agent wires the values into configs programmatically (Supabase/Vault/Vercel/.env)"). Per the doctrine, a pointer should state what triggers reaching the material, not restate identity the body already carries — this costs tokens on every turn for detail the body will supply anyway.
  - quote: "then wiring the reported credentials into Supabase/Vault/Vercel/.env."
- **Pruning — Duplication: keep each meaning in a single source of truth** — verifier: This restates, almost verbatim ("leaked queries and single-positive labels"), the same eval-artifact fact already given in the header comment ("the original 'granite-r2 is best' result came from an eval with leaked synthetic queries and single-positive labels... The 2026-07 rebuild (pi-evals #891) reversed it"). The same meaning lives in two places, so a future correction to the eval story requires editing both, and the comment even admits its own irrelevance ("which sidesteps that choice entirely"), meaning the duplicated material has no separate function beyond restating what Notes already says.
  - quote: "**Reranking's real-world value is modest.** On the corrected eval, no reranker beat the embedding baseline by much once labels credited all genuinely-relevant sessions; the big lifts in the original eval were an artifact of leaked queries and single-positive labels."
- **Pruning — single source of truth / duplication** — verifier: The heading itself instructs 'compose; don't re-derive,' pointing at cli-doctor-mode as the owner of the output contract, but the clause immediately re-derives that exact contract (stdout/stderr split, exit-code dictionary, --json schema, capabilities, determinism, env vars) in full. This contradicts its own instruction and duplicates meaning that the doc says should live in a single place.
  - quote: "**Shared-with-doctor axioms (compose; don't re-derive):** stdout is data / stderr is diagnostics (mixing
breaks every downstream `| jq`); exit codes are a documented dictionary (0=success, ≥1=categorized), not
vibes; every read verb has `--json` with a schema pinned by a regression test; `capabilities --json` +
`robot-docs guide` let the agent read the contract in-tool; output is deterministic (same input → same
bytes, honors `SOURCE_DATE_EPOCH`); honors `NO_COLOR`/`CI`/`TERM=dumb`/non-TTY."
- **Pruning — single source of truth / duplication** — verifier: This is the same enumeration already given verbatim in the safety envelope ("Never `rm -rf`, `git reset --hard`, or `DROP TABLE`.") plus the Op-enum section ("The Op enum has NO `DeletePath`."). Restating the identical list a third time is duplication of one meaning across multiple places rather than a single authoritative statement.
  - quote: "**`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead."
- **Context pointers — pointer must name material and encode how to reach it** — verifier: "The cookbook" is invoked as if it's a known, reachable concept, but no pointer in the visible body says where it lives. Other disclosed material in this document (the 10-dim rubric, the JSON shapes) gets an explicit `[DOCTOR-SPEC.md](references/DOCTOR-SPEC.md)` link; the cookbook does not, even though the frontmatter comment implies it was kept in that same file. The agent has no way to reach it when this step fires.
  - quote: "git-log grep, CHANGELOG, issue tracker, `--help` walk; match against the cookbook pattern."
- **Context pointers — one trigger per branch** — verifier: These seven names are synonyms for a single branch — "an existing self-repair-flavored subcommand under any name" — since the document treats all of them identically afterward (pin the same CLI spec, wire the same mutate() chokepoint). Spelling out seven near-synonymous triggers for one branch is one branch written seven times rather than the genuinely distinct add-vs-upgrade split.
  - quote: "upgrade an existing `doctor`/`health`/`verify`/`repair`/`check`/`diagnose`/`fix`"
- **Pruning — single source of truth / duplication; Leading words — 'a triad spelled out at three sites... is a passage begging to collapse into a single token'** — quote_not_found: This restates, almost verbatim, three of the five categories already enumerated in the 'When this is worth the round-trip' list ('Architecture decisions...', 'Security review of auth / crypto...', 'Non-trivial algorithms or concurrency reasoning'). The same triad is spelled out at two sites rather than named once and referenced, inflating its prominence and creating a two-place edit if the category list ever changes.
  - quote: "Bump to `xhigh` for architecture, security audits, or hard algorithm/concurrency questions."
- **Context pointers — "One trigger per branch. Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches."** — verifier: The frontmatter description is a context pointer, and this clause lists three phrasings — "install.sh", "curl-pipe-bash installer", "one-liner install" — that are synonyms for the same trigger (writing this kind of installer), not genuinely distinct branches. It pays context load on every turn to say the same thing three times.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer, or a one-liner install for a Rust/TS/Go CLI."
- **Context pointers — one trigger per branch** — verifier: "de-monolithize" and "modularize repo" both name the same whole-repo branch (mode: Standard, per the Recipe-selector table), and "split giant file" and "file too big" both name the same single-file branch (mode: Quick). These are synonyms renaming one branch as two rather than genuinely distinct branches, which the doctrine calls out to collapse.
  - quote: "Use when de-monolithize, split giant file, modularize repo, or file too big."
- **Context pointers — One trigger per branch (synonyms that rename a single branch should be collapsed)** — verifier: Both clauses describe the same underlying branch — the optional 'propose' step in the body that emits a DESIGN.md plus DTCG token files (section 4) — restated with different wording. Combined with the earlier clause in the same description, 'then optionally PROPOSE a DESIGN.md + DTCG token files by clustering those measurements,' this one branch is spelled out three times in a single always-loaded pointer instead of once.
  - quote: "author a DESIGN.md from an existing messy codebase, or turn design-drift findings into a token architecture"
- **Pruning — single source of truth (duplication inflates a meaning's prominence and costs maintenance)** — verifier: This instruction (verify the cited code before reporting it) is stated in Hard Rule 2 and then restated with different wording in Workflow step 3 ('Vet, then rank by blast radius... Re-read the cited code before reporting anything'). The same behavioral requirement lives in two places, so a future edit to the verification rule risks updating only one of the two.
  - quote: "Confirm at the `file:line` before citing it."
- **Pruning — single source of truth / duplication ("the same meaning in more than one place... costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank")** — verifier: The Review Checklist table at the end restates, row for row, rules that are already stated twice earlier: once as prose in their own sections ("Never animate from scale(0)", "Never use ease-in for UI animations", "Make popovers origin-aware", etc.) and again as example rows in the Review Format table near the top. Nearly every row of the checklist (scale(0), ease-in, transform-origin, keyboard animation, >300ms duration, missing hover media query, keyframes vs. transitions, Framer Motion x/y, asymmetric timing, stagger) has a full-section counterpart elsewhere, so the same rule exists in two or three places with no single authoritative source — a change to one guideline requires editing multiple locations.
  - quote: "| `scale(0)` entry animation                 | Start from `scale(0.95)` with `opacity: 0`                       |
| `ease-in` on UI element                    | Switch to `ease-out` or custom curve                             |
| `transform-origin: center` on popover      | Set to trigger location or use Base UI's `var(--transform-origin)` (modals are exempt — keep centered) |"
- **Negation as failure mode ("steering by prohibition drags the forbidden behaviour into context... A prohibition earns its place only as a hard guardrail you cannot phrase positively; even then, pair it with the positive target")** — verifier: The positive requirement is already fully specified ("You MUST use a markdown table with Before/After columns" plus a complete worked example table). This block then reproduces the forbidden list-style output verbatim in a fenced code block, dragging the exact pattern to avoid into context in reproducible form, on top of the already-stated "Do NOT use a list..." prohibition — a guardrail that was phraseable (and was phrased) positively, so the negative example is unnecessary reinforcement of the wrong pattern rather than the target one.
  - quote: "Wrong format (never do this):

```
Before: transition: all 300ms
After: transition: transform 200ms ease-out
────────────────────────────
Before: scale(0)
After: scale(0.95)
```"
- **Pruning — single source of truth / duplication** — verifier: This duplicates Hard Rule 2's "Every suggestion must pass the full Gate below. No exceptions for 'it would look cool.'" — the same rejection criterion is stated once as a general rule and again inside the Gate itself, inflating its prominence past its real rank and creating two places to keep in sync.
  - quote: ""It looks cool" is not on this list. If you can't name the purpose in one of these words, reject the candidate."
- **Steps and completion criteria — clarity** — verifier: Unlike step 2, which has an explicit checkable bound ("Done when every seam class has either yielded candidates with file:line evidence or been explicitly cleared"), this step ends with no completion criterion at all — there is no condition telling the agent recon is finished, inviting premature completion into the Sweep step.
  - quote: "1. **Recon.** Identify the stack, motion libraries, existing easing/duration tokens (suggestions must extend these, not invent parallel ones), and the product's personality — a crisp dashboard earns fewer and subtler suggestions than a playful consumer app. Build a rough frequency map of the surfaces you'll judge."
- **Co-location** — verifier: This is a rule about how to write rows in the Part 1 Opportunities table, but it sits scattered after Part 3 (Verdict) instead of beside Part 1 where the table format is defined — reading Part 1 does not bring this caveat along with it.
  - quote: "**Prefer a root-cause row over N call-site rows.** If a whole class of call sites is missing the same thing, the finding is the shared component, not the call sites — one row against the design-system `Button` beats 600 rows against its consumers. Say the blast radius in the row."
