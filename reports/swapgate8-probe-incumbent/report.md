# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $0.8147 spent
- verify: 186 trial(s), $2.2582 spent

## Run manifest

- run: `swapgate8-probe-incumbent` (2026-10-29T09:38:57Z → 2026-10-29T10:07:12Z)
- claude CLI: `2.1.312` | skill-tuner: `0.10.0`
- model pin: `claude-sonnet-5-5` → answered by: `claude-sonnet-5-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/doctrine-gate-68-69/configs/../experiments/doctrine-gate-2026-10-29/candidates/desc-only.SKILL.md` | `13414f9453ad` | worktree @ 49a4ddacfae9 |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0de8b88822ac` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `ecf98ca2b554` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `ccd612736f52` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `5d44a3ae63b7` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `4c9e0d44c9ad` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `acfdd72cf108` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `81a324fa1a17` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `0a247b43b2d1` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `042557dd3a8d` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `e3eb80072a3c` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `d1d441cdbb18` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `58291952bd2a` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `3cc23114e029` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `b8a9c77f0103` | worktree @ 46f806da768b |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `b0da3320d5e6` | worktree @ 46f806da768b |

## Marginal-value probe verdict

**findings_confirmed: 34**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/doctrine-gate-68-69/configs/../experiments/doctrine-gate-2026-10-29/candidates/desc-only.SKILL.md
- targets: 15
- probe calls: 15
- verify calls: 186 (3 skeptic(s) per finding)
- refuted: 28
- overflow (beyond max_findings cap, not verified): 5

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 0 | 5 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 4 | 1 |

### Confirmed findings

- **Relevance and sediment**: This is history about a retired component. It does not change what a worker brief should contain, so it is a stale layer that costs tokens on every load.
  - quote: "the dispatcher's child prompt used this schema (dotfiles#1202) until the dispatcher's retirement in #1873."
  - proposed fix: Delete the sentence. Keep the PR #1167 incident only if it is needed as the reason for pinning the shape.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Relevance and sediment / Cut identity the body already states**: The whole 'primitive map' and the 'core shift' callout explain a retired system (ntm, beads, agent-mail, bv). An agent doing the task today gains nothing from the old-to-new mapping. The engine section already states the current rules.
  - quote: "| Old jsm swarm | Native replacement |"
  - proposed fix: Drop the old-to-new table and the 'old swarm' framing, or reduce them to a one-line note. Keep only the cross-model panel row, which is live guidance.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Completion criteria: two bounds that contradict (a general ceiling in one place, a specific range crossing it in another) leave the agent unable to tell whether a value between them complies**: This general ceiling is stated flatly, but the duration table directly above gives modals and drawers 200–500ms. A 400ms drawer complies with one bound and violates the other. Only the Never Ship row, far away, carves out the exception, so the Duration section contradicts itself.
  - quote: "**UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
  - proposed fix: Co-locate the exception with the ceiling: "**UI animations stay under 300ms, except modals/drawers (up to 500ms) and marketing/onboarding.**"
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Single source of truth / Duplication in disguise (polarity): an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice**: The Never Ship table restates, negated, nearly every rule already given positively in steps 1-7: scale(0), ease-in, duration, transform-origin, keyframes on rapid triggers, properties, Motion shorthands, hover gating, reduced motion, and stagger. The same meaning sits in two places, which costs tokens, inflates those rules' weight, and invites drift between the copies.
  - quote: "| `transition: all` | Name the exact properties |
| `transform: scale(0)` entrance | `scale(0.95)` + `opacity: 0` |
| `ease-in` on a UI element | `ease-out` or a strong custom curve |"
  - proposed fix: Delete the Never Ship table and replace it with a one-line completion check: "Before finishing, re-read steps 1-7 and confirm each applies to the code you wrote." If a table stays, keep only rules that appear nowhere else, such as the `transition: all` ban.
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Cut identity the body already states: the pointer's job is when to reach, not what it is**: The description recites the body's seven-step build sequence and says what the skill does, which the body's opening and Build Sequence already state. This adds permanent context load for no routing signal. The routing signals are in the "Use when" clause and the sibling-skill redirects.
  - quote: "Build an animation from scratch, making the decisions in the order that determines whether it feels right — should it animate at all, what purpose, which tool, which properties, which curve and duration, how it interrupts, how it exits. Writes the implementation."
  - proposed fix: Lead with the trigger: "Use when asked to animate something, add motion, make a component feel alive, or build a transition. For critiquing existing motion use review-animations; for auditing a whole codebase use improve-animations."
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Single source of truth [craft] (duplication)**: The Quick Reference table restates rules already given in full in §§1–15 (feedback on pointer-down, rubber-banding, the projection formula, mirrored easing, and so on). Each meaning now lives in two places, which inflates its rank and doubles maintenance. It also contains a rule found nowhere else in the body ('Use velocity sign, not position'), so the cheat sheet and the body can drift apart.
  - quote: "| Feedback | On pointer-down, continuous | never only at the end |"
  - proposed fix: Delete the Quick Reference table, or reduce it to pointers to the sections. Move the velocity-sign rule into §3 or §5 so it has one authoritative home.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Completion criteria (checkable bounds)**: The prompt's query types include multi-step workflows, high-failure commands and per-cwd repetition. Path B (bash history) has no failure or cwd data and offers only noisy adjacency, so on that path the criterion cannot be met. The agent cannot tell done from not-done and may claim compliance impressionistically.
  - quote: "- [ ] History mined (atuin or bash) for all query types in THE EXACT PROMPT (Step 1)"
  - proposed fix: State the criterion per source. For atuin: 'the Path A queries and Path C cwd query have been run'. For bash: 'the three Path B queries have been run'.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Cache vs environment lookup / Relevance and sediment**: The hard-coded alias count '~40' (repeated later as 'You already keep ~40 aliases') caches a value that one command would return. It goes stale as aliases change, and it adds sediment without helping the agent act.
  - quote: "| **shell aliases** | `~/.bashrc` (~40 aliases) | Existing shortcuts; the gap = frequent-but-unaliased commands |"
  - proposed fix: Drop the count in both places. The grep command already in the document lists the aliases.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Single source of truth (duplication)**: Phase D restates Safety kernel rules 4, 5, 6 and 7: verbatim per-plan recorded authorization, worktrees before branches, `-d` over `-D`, and individual removals. The same meaning sits in two places, which inflates its weight and adds a second edit site that can drift.
  - quote: "2. Get verbatim per-plan authorization; record it to a durable file with a UTC timestamp.
3. `git worktree remove` each non-protected worktree → then `git branch -d` (or `-D` only for
   user-acknowledged unmerged garbage), one at a time, logging each."
  - proposed fix: Keep the rules only in the Safety kernel. Reduce Phase D to a sequence that points at it: 'Present the removal list, then execute per kernel rules 4–7, logging each removal.'
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Single source of truth: duplication wears disguises, and the commonest is polarity: an anti-pattern list that restates, negated, rules the document already gives positively (also Negation: lead with the target behaviour, not the ban)**: Both rows restate, negated, rules already given positively. The Core pattern, The problem, and the When-to-use table already say to use Brave and not Playwright for OAuth consent. The Critical rules already require full URLs with the actual IDs. The table adds a second copy of each meaning and names the banned behaviours.
  - quote: "| Playwright/xvfb for OAuth consent | Bot detection + cannot do 2FA | Real Brave handoff |
| Assume Will knows the IDs | He needs them inline | `project=my-project-123` |"
  - proposed fix: Delete the Anti-patterns section. If the xvfb detail is needed, add it once to the 'Doable headless without detection' row of the When-to-use table.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Single source of truth: the same meaning in more than one place costs maintenance and tokens and inflates a meaning's rank**: Three of the four checklist items re-list the Critical rules (full URLs, exact element text, report-back format), and the identifiers item repeats the full-URL rule. The checklist is the same content written twice.
  - quote: "- [ ] Instructions follow the template's Critical rules (full URLs, exact element text)
- [ ] All identifiers included (project IDs, refs, callback URLs)
- [ ] "Report back" format stated exactly (per Critical rules)"
  - proposed fix: Collapse the checklist to a single line, 'Every Critical rule satisfied and wire-in commands ready', or drop it and keep the Critical rules as the only statement.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Cut identity the body already states; front-load the leading word in the pointer; one trigger per branch**: The always-loaded description opens with a what-it-is sentence that the body already states. The trigger condition only starts in the second sentence. Examples are listed twice ('Google OAuth consent' and 'OAuth consent screens'). Bot detection, 2FA and CAPTCHA are one branch, a step that cannot be scripted, and are written as separate triggers.
  - quote: "Set up cloud consoles that block headless automation (Google OAuth consent, Stripe
  webhooks, GCP credentials) via the local Brave browser, then wire the credentials into
  Supabase/Vault/Vercel/.env. Use when a console step cannot be scripted: bot detection
  (Google's "browser may not be secure"), 2FA, CAPTCHA, or OAuth consent screens."
  - proposed fix: Lead with the trigger and drop the identity sentence: 'Use when a cloud-console step cannot be scripted (bot detection, 2FA, CAPTCHA, OAuth consent, Stripe webhook secrets); hands off to the local Brave browser, then wires credentials into Supabase/Vault/Vercel/.env.' Check the prune at routing parity before landing it.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Relevance and sediment**: This block is dated incident history. It says outright that it is not a current-health guarantee, and it gives the agent nothing to act on. It is stale sediment that adds load on every read. The only live fact, that the wrapper separates retrieval failure from no-candidates, is already stated in the Notes section.
  - quote: "**Historical incidents:** lexical retrieval failed in September 2026 (dotfiles"
  - proposed fix: Delete the block and keep the incident history in the linked issues (dotfiles #1235, cass #494) or the HTML comment.
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Single source of truth (duplication)**: The same lexical-search command appears in the 'When to use which' table and again in the 'Diagnose retrieval without maintenance' code block. Changing the flags would take two edits, and the repeat inflates the command's apparent importance.
  - quote: "CASS_AUTO_REFRESH=0 cass search "query" --robot --no-maintenance --mode lexical --limit 3"
  - proposed fix: Keep the command in one place, e.g. the diagnose section, and have the table row point to it.
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Single source of truth (duplication)**: Loop step 4 already gives the prioritization rule, 'rank by (how often an agent hits it) × (how bad the gap is)'. This second formula adds a third factor, blast_radius, so the two places disagree about how to rank. The 'Cite what you saw' instruction is also stated twice, in the 11 dimensions heading and here.
  - quote: "Optional prioritization heuristic: `priority = frequency × score_gap × blast_radius`."
  - proposed fix: Keep one prioritization statement, in Loop step 4, with a single formula. Drop the 'Optional' heuristic line and the repeated citation instruction.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Context pointers: cut identity the body already states; one trigger per branch**: The description leads with a feature list ('guessable commands, errors that teach, typo inference, parseable deterministic output'). Its trigger sentence then restates the first clause ('Audit and improve a CLI's ergonomics for AI-agent callers') and names a sibling skill, which is identity. This adds permanent context load without adding a routing branch.
  - quote: "Use to make a CLI agent-friendly (sibling of cli-doctor-mode)."
  - proposed fix: Collapse to one trigger per branch, for example: 'Use when auditing or fixing a CLI for AI-agent callers: errors, typo hints, --json/exit-code contract. Defer repair/doctor surfaces to cli-doctor-mode.' Land the change only after a routing-parity check.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Completion criteria (two bounds that contradict are a completion defect)**: The dry-run is specified to run through step 4, which writes a verbatim backup to `<run-dir>/backups/`. The same bullet then promises 'zero disk writes', and the CLI surface says 'execute nothing'. Planning is step 5, so 'up to step 4 then prints the plan' is also out of order. An agent cannot tell whether writing a backup during dry-run complies, whichever bound it follows.
  - quote: "**`--dry-run --fix`** runs the plan through `mutate()` up to step 4 (backup) then prints the plan to"
  - proposed fix: Make the bounds agree. Either run dry-run through step 3 (preconditions) and step 5 (plan) with no backup write, and state 'no writes outside stderr', or allow backups under `.doctor/runs/<run-id>/` and change 'zero disk writes' to 'zero writes to project state'.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Single source of truth (polarity duplication: an anti-pattern list restating, negated, rules already given positively)**: The Anti-patterns section restates, as negations, rules the document already gives positively. Fix-then-detect and the `mutate()` bypass are in The One Rule and the chokepoint section. Verbatim backups are in the safety envelope. No `DeletePath` / rename-to-quarantine is in the Op enum paragraph. Cross-filesystem rename is already in step 6. Each meaning now appears two or three times, which costs tokens and inflates the ranking of those rules. The list also leads with bans, which makes the forbidden behaviours more available.
  - quote: "**Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently."
  - proposed fix: Delete the Anti-patterns section, or reduce it to a one-line pointer to the safety envelope. Keep only items not stated elsewhere, such as random or timestamp finding ids, interactive prompts, and calling home by default, and phrase them positively (content-derived ids, non-interactive, offline by default).
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **One trigger per branch (synonyms that rename a single branch are one branch written twice); Cut identity the body already states**: 'doctor', 'self-healing', 'auto-fix' and 'auto-remediation' all name the same branch, so a run reaching the skill by any of them takes the same path. The property list (idempotent, reversible, backup-aware, machine-readable) restates what the body and the One Rule already say. This is permanent context load with no added routing signal. The only real branches are add and upgrade.
  - quote: "Add or upgrade a CLI doctor/self-healing/auto-fix subcommand: idempotent, reversible, backup-aware repair with machine-readable health output for agent callers. Use for safe CLI auto-remediation; language-agnostic."
  - proposed fix: Prune to one trigger per branch, for example: "Add or upgrade a CLI `doctor --fix` subcommand for agent callers. Use when a CLI needs safe auto-repair." Then check routing parity with a blind battery before landing the change.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Relevance and sediment [craft] / Single source of truth (the environment is a source of truth too)**: This is a snapshot of a transient account state sitting in a procedure. It goes stale as soon as the auth is fixed, and the agent can check auth state itself. It also bears on no step the agent performs. It is sediment.
  - quote: "caam rotation is currently unavailable (its stored Codex profile is unauthorized; the active auth is unmanaged)."
  - proposed fix: Delete the caam sentence. Keep only the durable behaviour: if the quota guard blocks, report the consult as skipped or use /pro-gate.
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Cut identity the body already states / One trigger per branch (context pointers)**: The description spends its leading position on identity, which the title and body already state. The 'Use when' clause then restates the same single branch (writing a curl-pipe-bash installer for a CLI) in different words. That is one trigger written twice, paid for on every turn.
  - quote: "Write a production-grade `curl | bash` installer for a CLI tool."
  - proposed fix: Collapse to one trigger and put the leading words first, e.g. `description: curl-pipe-bash install.sh for a CLI (Rust/TS/Go). Use when writing or editing such an installer.`
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Completion criteria (contradicting bounds)**: Non-negotiable #7 says checksum is skipped only with --no-verify. The `verify_checksum` snippet also skips silently-ish when no SHA256 tool exists (`warn "no SHA256 tool; skipping checksum"; return 0`). The anti-pattern says 'always verify SHA256'. These bounds contradict, so the agent cannot tell whether a missing hash tool complies. `--no-verify` is also absent from the #14 flag list.
  - quote: "skip only on explicit `--no-verify`"
  - proposed fix: Make one bound authoritative: either hard-fail when no SHA256 tool is present unless `--no-verify` is given, or state in #7 that a missing tool soft-skips with a warning. Add `--no-verify` to #14 and align the anti-pattern.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Single source of truth (polarity duplication)**: The Anti-patterns list restates, negated, rules already given positively in the non-negotiables: proxy on every curl (#3), checksum (#7), soft-skip optional tools (#8), flock plus mkdir fallback (#6), musl (#4). The Pre-ship checklist repeats them a third time. This is the same meaning in multiple places, and the bans lead without a positive target.
  - quote: "**Ignoring proxy env** — `PROXY_ARGS` on every curl call."
  - proposed fix: Delete the anti-patterns that mirror numbered rules (proxy, checksum, flock, gnu, optional-feature failure). Keep only gotchas that have no rule elsewhere, such as the `--version` timeout and the PATH check. Trim the checklist to items not already enumerated.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Co-location**: This behavioural rule appears only in the final checklist line. Neither the non-negotiables, the build plan, nor the download or agent-config sections mention it. Applying the existing-install preflight correctly requires having read a different section.
  - quote: "version-already-installed short-circuits download but STILL re-runs agent config (idempotent, not a full no-op)"
  - proposed fix: Move the rule into the Preflight non-negotiable (#5) or the Agent auto-config section, and drop it from the checklist or leave a one-word reference.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Single source of truth (duplication)**: The Parallelism section restates almost word for word the 'Coordination =' block in Quick-Start (whole-repo campaign, /agent-swarm, worktree-isolated subagents or Codex, Workflow tool for fan-out→verify→synthesize). The mode table is also written twice (Quick-Start 'Modes:' line and the Phase Loop 'Mode' table). A change to the behaviour needs edits in several places, and the repetition inflates the meaning's weight.
  - quote: "**Parallelism.** For a whole-repo campaign, fan out via [/agent-swarm](../agent-swarm/SKILL.md) —"
  - proposed fix: Keep the parallelism guidance in the Parallelism section only. Replace the Quick-Start 'Coordination' block with a one-line pointer to it. Drop the Quick-Start 'Modes:' line and keep the Phase Loop mode table as the single copy.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Duplication wears disguises: polarity (anti-pattern list mirroring positive rules); Negation**: The Anti-Patterns table is a negated copy of rules already given positively elsewhere. This row mirrors 'one mechanical move per commit'. 'Drop a re-export' mirrors 'API diff EMPTY' and the façade rules. 'Skip Phase 3' mirrors the baseline requirement. 'Mark a cohesive file must split' mirrors B11. Each row leads with the banned behaviour and names it, which makes it more available, and it repeats the same meaning in a second place.
  - quote: "| Extract + rename + reformat in one commit | Kills `git blame` and reviewability; one mechanical move per commit |"
  - proposed fix: Delete the table, or cut it to the rows that carry a gotcha stated nowhere else (for example the cross-crate inlining loss). Phrase each surviving row as the positive target ('Re-export every existing import path; the API diff stays empty').
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Completion criteria: two bounds that contradict (a general ceiling in one place, a specific range crossing it in another) are a completion defect**: The checklist applies a flat 300ms ceiling and tells the agent to cut to 150-250ms. The body says modals and drawers may run 200-500ms, and its own examples use 400ms toast transitions. An agent reviewing a 400ms drawer cannot tell whether it complies, and the checklist would wrongly flag it.
  - quote: "| Duration > 300ms on UI element             | Reduce to 150-250ms                                              |"
  - proposed fix: Make the checklist row match the rule: 'Duration > 300ms on UI element other than a modal or drawer (those may run to 500ms) | Reduce to 150-250ms'. Also note that toast examples at 400ms are an occasional-use case, or change the examples to fit the bound.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth / Duplication: the same meaning in more than one place**: This restates the 'Use CSS transitions over keyframes for interruptible UI' section, the 'Interruptibility advantage' paragraph, and the checklist row. It adds no new meaning and inflates the rule's rank.
  - quote: "5. **Use transitions, not keyframes, for dynamic UI.** Toasts are added rapidly. Keyframes restart from zero on interruption. Transitions retarget smoothly."
  - proposed fix: Delete principle 5 or replace it with a one-line pointer to the 'Use CSS transitions over keyframes' section.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth / Duplication: the same meaning in more than one place**: The 'How fast should it be?' rule already says 'A 180ms dropdown feels more responsive than a 400ms one. A faster-spinning spinner makes the app feel like it loads faster'. The 'Perceived performance' bullets repeat both claims. The ease-out vs ease-in claim is repeated again from the 'Never use ease-in' paragraph.
  - quote: "- A **fast-spinning spinner** makes loading feel faster (same load time, different perception)
- A **180ms select** animation feels more responsive than a **400ms** one"
  - proposed fix: Fold the one new point (instant subsequent tooltips) into the duration section and delete the 'Perceived performance' subsection.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth / Duplication: the same meaning in more than one place**: The hold-to-delete pattern is written out three times: in the clip-path inset code block, in this prose section, and again in 'Asymmetric enter/exit timing' with its own CSS block. The button `scale(0.97)` press rule is also repeated in several sections. This is the same meaning in several places.
  - quote: "Use `clip-path: inset(0 100% 0 0)` on a colored overlay. On `:active`, transition to `inset(0 0 0 0)` over 2s with linear timing. On release, snap back with 200ms ease-out. Add `scale(0.97)` on the button for press feedback."
  - proposed fix: Keep one authoritative hold-to-delete description, in the clip-path section or the asymmetric-timing section, and reference it from the other.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Completion criteria (two bounds that contradict leave the agent unable to tell whether a value complies)**: This absolute ceiling contradicts the hunt list, which prescribes `height + opacity transition` for accordions and a `clip-path: inset(...)` overlay for hold-to-confirm. An agent cannot tell whether those recipes comply, and obeying either bound breaks the other.
  - quote: "Animate `transform` and `opacity` only;"
  - proposed fix: Make the ceiling a default with named exceptions, for example: "Animate `transform` and `opacity` by default; the accordion height and hold-to-confirm `clip-path` recipes in the hunt list are the only exceptions."
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Single source of truth (duplication of the same meaning in more than one place)**: The same handoff instruction, with the same two targets and the same carry-verbatim condition, is restated in Part 3. A change to the handoff needs two edits, and the repetition inflates its weight.
  - quote: "hand it off: `ce-plan` for a tracked change (carry the exact values from the table into the plan), or `animate` to build it directly when it is small enough not to need a plan."
  - proposed fix: State the handoff once, in Part 3 (or Hard Rule 1), and have the other place point to it or drop it.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Co-location (one concept's rules kept under one heading)**: This rule governs how rows in the Part 1 table are formed, but it sits at the end of Part 3 (Verdict). Applying the Part 1 row format correctly requires reading a different section.
  - quote: "**Prefer a root-cause row over N call-site rows.** If a whole class of call sites is missing the same thing, the finding is the shared component, not the call sites"
  - proposed fix: Move the root-cause-row paragraph under Part 1, next to the table description.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Leading words (a word too weak to beat the model's default is a no-op wearing emphasis)**: This is an uncheckable emphasis directive with no completion condition. The gate's own pass/reject criteria already do the work, so the sentence pays load to say nothing.
  - quote: "Be ruthless."
  - proposed fix: Delete it, or replace it with a checkable bound such as "Done when each candidate has a recorded answer to all four questions and a pass or reject verdict."
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Completion criteria (a bound is checkable when the agent can tell done from not-done without judgment; contradicting or fuzzy bounds are a completion defect)** — verifier: The solo threshold is '< ~5–7' and the Codex threshold is '≥ 5–7'. Both are ranges, not numbers, so a batch of 5 or 6 units can fall under either engine. The agent has to judge which engine applies.
  - quote: "< ~5–7 independent units"
- **Single source of truth / Duplication** — verifier: The 'Cost routing' bullets restate engine and model guidance already given in 'Pick the lightest engine that fits' (pin model, Sonnet/Haiku for mechanical work, Codex for batches). They also overlap the stage tiers below them. Cost routing then points back to the engine section, so the same meaning sits in several places.
  - quote: "**Mechanical** (search sweeps, file collection, log trawls, summarization, bulk edits) → Sonnet, or"
- **Negation** — verifier: The rule leads with a prohibition and gives no positive target. It also names the forbidden behaviour. The preceding bullet's script-file approach is the positive alternative, but this bullet never ties itself to it.
  - quote: "Never prefix `HOME=` or other env vars onto complex commands"
- **Completion criteria: contradictory or ambiguous bounds make compliance uncheckable** — verifier: The easing table prescribes `ease-out` for entering and exiting and for the default, but the following text says "Built-in CSS easings are too weak. Use these," and Never Ship blocks "Built-in `ease-out` on a deliberate animation." The table's `ease-out` could mean the built-in keyword or the custom `--ease-out` token, so an agent following the table literally ships a blocked value.
  - quote: "| Entering or exiting | `ease-out` |"
- **Progressive disclosure [craft] / Sprawl [research]** — verifier: Branch-only reference sits inline beside the motion material: eight general design principles, typography (§15), materials (§12), multimodal feedback (§13) and process (§17). A run on drag/spring physics cannot tell which sections are meant for its path, and the middle of a document this long is measurably harder to use. The doctrine says the cure is the ladder and the split, not line-editing.
  - quote: "## 16. Design foundations — the eight principles"
- **Single source of truth [craft] (duplication)** — verifier: The parenthetical restates the meaning of the bullet it follows ('set `transform-origin` to the trigger') without adding anything. It is sediment that costs tokens and says the same thing twice.
  - quote: "(This is the same origin-awareness point as popovers scaling from their trigger, not their center.)"
- **Single source of truth (duplication)** — verifier: The Loop block restates the Step 5 validation criteria (5 runs, --dry-run, --json, ≥3× faster). The Done When list repeats the ≥3× criterion a third time. Each copy must be edited together when the threshold changes, and the repetition inflates the criterion's weight.
  - quote: "6.  VALIDATE  → 5× run, --dry-run, --json, ≥3× faster"
- **Single source of truth (duplication)** — verifier: THE EXACT PROMPT restates the Step 1 data-source detection, the Path A/B/C queries, the scoring step and the Propose step. The same procedure now sits in two places, which costs tokens and can drift.
  - quote: "Analyze my command history AND my stack's automation surfaces to find opportunities.
1. Detect source (atuin DB if present, else ~/.bash_history). Query: repeated commands,
   multi-step workflows, high-failure commands, per-cwd (per-repo) repetition."
- **Completion criteria / Demand (uncheckable qualifier)** — verifier: 'Top candidates' is undefined. The prompt asks for the top 10 and Step 2 sets a Score ≥ 0.3 cutoff, so the agent has no checkable bound for how many to score.
  - quote: "- [ ] Top candidates scored and ranked"
- **Completion criteria** — verifier: 'Certain' is a judgment call, not a checkable bound. The agent cannot tell done from not-done, so it may stop early while believing it complied, or run every step regardless. The chain has no stated stopping signal per step.
  - quote: "Run this chain per branch, cheapest check first. Stop as soon as a verdict is certain."
- **Progressive disclosure** — verifier: Language-specific regex reference for Python, Go and Rust is left inline among the numbered steps. Each run needs only the language it is on, so the agent cannot tell which material belongs to its path. This is branch-only reference on the steps rung.
  - quote: "- Python: `^\+\s*(async )?def (\w+)` · `^\+\s*class (\w+)` — Go: `^\+func (\w+)` · `^\+type (\w+) (struct|interface)` — Rust: `^\+\s*(pub )?(async )?fn (\w+)`"
- **Single source of truth (duplication)** — verifier: The pipeline diagram and the 'Always run wt-sweep.sh and branch-triage.sh first… start from what they couldn't resolve' paragraph already say that the scripts handle the mechanical dispositions and the skill handles the residue. This sentence says it a third time, and it also conflicts with the diagram's funnel list, which names PROTECTED/MERGED/SYNCED/TREE-SAME/PR-SHIPPED/CHERRY rather than `superseded`.
  - quote: "`branch-triage.sh` already gives you `protected`, `already-merged`, `superseded` (mechanical). Your job is
the rest — and especially routing collisions into **harmonization**."
- **Single source of truth / Duplication (polarity disguise): an anti-pattern list that restates, negated, rules the document already gives positively** — verifier: The Anti-Patterns section restates, negated, rules the document already gives positively. Mechanical Rules are 'the enforceability backbone', Quality Test #5 asks 'Consistent: can it be applied across formats', and the Generic Voice item repeats the 'force specificity' requirement. The same meaning is written twice and the list inflates its rank.
  - quote: "- **The Unenforceable Voice:** all vibes, no mechanical rules. Result: voice drifts within weeks.
- **The Single-Channel Voice:** profile only works for one format (e.g. emails) and breaks on social or long-form. Test across channels."
- **Single source of truth / Duplication** — verifier: The closing 'The Test' repeats the in-template 'Quality Test'. Both cover authenticity, actionability by a second writer, differentiation from anti-aspirations, and mechanical enforceability. Two acceptance checklists for the same artifact drift apart and make the agent guess which one is authoritative.
  - quote: "## The Test

A good Voice Profile produces these results:

1. The user reads it and says "yes, that's it" without hedging
2. A second writer (human or AI) can produce content from it that the user accepts on first draft
3. Anti-aspiration sample phrases feel genuinely wrong, not just stylistically different
4. Mechanical rules are sharp enough to catch violations automatically"
- **Cut identity the body already states / Single source of truth (pointer duplicated in body)** — verifier: The 'When to use' and 'When NOT to use' sections restate the description's triggers and exclusions. The skill body is only read after the skill has fired, so the routing text there adds load and a second place to maintain. The description's triggers 'copy sounds generic' and 'how should this sound? is unclear' also overlap with the body list's generic-copy and inconsistency items.
  - quote: "## When to use this skill

- Starting a new brand, sub-brand, product line, or property
- Defining voice for a new persona (instructor, member spotlight, co-founder, partner author)"
- **Single source of truth / Duplication** — verifier: The 'Two Modes' summary and the later 'Mode 1: Extract' / 'Mode 2: Build' sections each define the same mode twice, once as use-when plus process and again as the full steps. The 'How to choose' block adds a third statement of the same branch conditions. 'Both modes produce the same Voice Profile output format' is also repeated by 'regardless of mode'.
  - quote: "### Mode 1: Extract

**Use when:** the user has existing content they're proud of (website copy, emails, social posts, transcripts) that represents how they want to sound.

**Process:** analyze the content for patterns, then codify what makes it distinctive."
- **Completion criteria: two bounds that contradict are a completion defect** — verifier: The template is declared exact for every profile, yet inside it the Channel and Stage Calibration section says 'If voice doesn't flex by funnel, replace with relevant context dimensions'. The Jargon, Profanity and Tone Spectrum fields also allow adaptation. The agent cannot tell whether altering a section complies with 'exact'.
  - quote: "Use this exact structure for every Voice Profile, regardless of mode."
- **Completion criteria (contradicting bounds) / Negation** — verifier: The description routes broad scans to 'plain cass', but the body opens with 'NEVER run bare `cass`' because it launches a blocking TUI. The two instructions contradict, and the pointer that steers the agent can send it into the thing the body forbids.
  - quote: "for broad scans, plain cass."
- **Cut identity the body already states / Front-load the leading word** — verifier: The description opens with a sentence describing what the tool is, which the body already says. That spends the first, most valuable position of an always-loaded pointer on identity instead of the triggering condition.
  - quote: "Lexical session search with optional semantic reranking. Use INSTEAD of bare `cass search`"
- **Single source of truth (duplication)** — verifier: The HTML comment already records that the original eval used leaked synthetic queries and single-positive labels. This note restates the same meaning, including the same artifact explanation, in a second place.
  - quote: "**Reranking's real-world value is modest.** On the corrected eval, no reranker beat the embedding baseline by much"
- **Single source of truth (duplication, including polarity-disguised anti-pattern lists that mirror rules given positively)** — verifier: This anti-pattern is the negated form of the positive rule 'Ship a **stack** as one coherent commit' and of Loop step 5 ('ship the operator *stacks* above, one coherent commit per stack'). The same meaning is written twice. The 'polite scorecard' anti-pattern likewise restates Loop step 8 ('A scorecard alone is not a deliverable').
  - quote: "Fixing one flag's error in isolation"
- **Completion criteria (contradicting bounds)** — verifier: Recurring fix 1 requires the non-zero exit to be kept when a typo is corrected. The grading ladder and the Intent inference axiom allow 'inferred-and-acted (proceeded with a warning)' and 'succeed-with-warning' for edit-distance-1 typos. The agent cannot tell whether a distance-1 typo should exit non-zero or succeed.
  - quote: "keep the non-zero exit (the hint is additive)"
- **Completion criteria [craft] / Demand [craft]** — verifier: 'Tight' is an uncheckable qualifier. It sits next to a precise 'exactly three parts' list, and it pulls against the requirement to quote Codex's answer verbatim. The agent cannot tell whether a long verbatim quote complies.
  - quote: "Keep the whole thing tight. The value is the disagreement surface between two models, not a wall of duplicated agreement."
- **Completion criteria (checkable bound) / Single source of truth** — verifier: The Build plan also says '4-tier download fallback'. The snippet implements only three URL tiers before the source build, so the count is inconsistent. The agent cannot tell whether a fourth tier is required or what it is.
  - quote: "**Download — 4-tier fallback → source:**"
- **Cut identity the body already states (context pointers)** — verifier: The always-loaded description spends most of its words saying what the skill is and does ('Find monolith files, prove seams empirically, split isomorphically with zero API/perf/compile drift; hand off as GitHub issues'). That is identity the body states in its first lines. Only the 'Use when' clause carries routing signal, so this adds permanent context load on every turn for no routing gain.
  - quote: "Find monolith files, prove seams empirically, split isomorphically with zero"
- **Relevance and sediment** — verifier: The fork-provenance comment narrates what was removed and why (jsm-swarm, beads, ubs, idea-wizard, the un-retired pristine skill). That is change history. The document already points to CHANGELOG.md and UPSTREAM.md for it, so these lines are stale-layer sediment.
  - quote: "Localization: stripped the trashed jsm-swarm/beads/idea-wizard layer — parallelism now routes"
- **Sprawl and Progressive disclosure: inline what every branch needs, disclose what only some branches reach** — verifier: The document is very long and inlines branch-specific reference (clip-path recipes, 3D transforms, gesture/drag, WAAPI, Sonner history, debugging) that most UI review runs never touch. The cost is attention diluted across the middle of the document. Line-editing does not fix this; the structure needs the ladder.
  - quote: "## clip-path for Animation

`clip-path` is not just for shapes. It is one of the most powerful animation tools in CSS."
- **Completion criteria / Demand (a criterion that mixes checkable and uncheckable terms)** — verifier: The rule demands curves from the shared token vocabulary, but the example rows use `transition: 400ms ease` and `ease-out` keywords instead of the named `--ease-*` tokens. The model example therefore violates the criterion it sets, and the agent will copy the example.
  - quote: "Every "Suggested motion" cell carries exact values — the curve, the duration, the properties — pulled from this repo's shared vocabulary"
