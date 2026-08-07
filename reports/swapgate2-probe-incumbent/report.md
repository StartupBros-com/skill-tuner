# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 6 trial(s), $1.4974 spent
- verify: 63 trial(s), $1.4594 spent

## Marginal-value probe verdict

**findings_confirmed: 9**

- doctrine: /home/will/dotfiles/claude/skills-local/writing-for-agents/SKILL.md
- targets: 6
- probe calls: 6
- verify calls: 63 (3 skeptic(s) per finding)
- refuted: 12

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 1 | 4 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 2 | 3 |

### Confirmed findings

- **Context pointers — one trigger per branch ("Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.")**: "browser may not be secure" is not a distinct branch — it is the literal warning text produced by bot detection, as the document itself confirms in the Problem section ("Google OAuth consent -> \"This browser or app may not be secure\""). Listing it alongside "bot detection" writes the same branch twice under different wording, adding always-loaded tokens to the description without covering a genuinely new case.
  - quote: "bot detection, "browser may not be secure", 2FA, CAPTCHA, or OAuth consent screens"
  - proposed fix: Drop the quoted error message and keep the general term: "bot detection, 2FA, CAPTCHA, or OAuth consent screens."
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Context pointers — one trigger per branch: synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches.**: The description's trigger list gives three items for what is really one branch ("has many independent units"). "N-independent-units work" is a verbatim restatement of the umbrella clause "has many independent units" that immediately precedes it, and "whole-codebase campaigns" / "broad multi-file sweeps" are near-synonyms of the same idea. Since this description is always-loaded context on every turn, the redundant branch wording pays load without adding a distinct trigger.
  - quote: "whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work"
  - proposed fix: Collapse to one branch, e.g. "large multi-file or whole-codebase work (refactor / audit / migration / dead-code sweep)", and drop "N-independent-units work" entirely since it duplicates the earlier umbrella clause.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Pruning — relevance: a line loses relevance by never bearing on the task (mere exposition); prune sediment rather than let it settle.**: This HTML comment is a changelog/history note about why the skill was created — it never bears on what the agent does when running the skill, yet it is loaded into context along with the rest of the file whenever the skill fires. It is pure exposition, the exact case the doctrine flags as relevance-losing.
  - quote: "<!-- New skill (not a jsm fork), 2026-07-04. Replaces the trashed jsm swarm mechanism
     (ntm + agent-mail + beads) with the operator's native primitives. Skills that need
     campaign-scale parallelism reference this instead of re-deriving swarm coordination. -->"
  - proposed fix: Delete the comment from the skill body; if the provenance is worth preserving, put it in the commit message or a CHANGELOG rather than SKILL.md.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Negation is the failure mode beside leading words — a prohibition earns its place only as a hard guardrail that cannot be phrased positively, and even then must pair with the positive target; otherwise it duplicates a meaning already stated (single source of truth / pruning).**: Every bullet here is a negated restatement of a rule already given positively elsewhere in the same document: trivial-task sizing is already in "Pick the lightest engine that fits"; worktree-on-mutation is already in "Isolation is the coordination"; model pinning is already in both the engine-pick bullet and "Cost routing"; pipeline-over-barrier is already its own bullet under "The patterns worth knowing"; the Codex-batch rule is already "Never silently absorb a delegatable batch into the session model"; and message-bus/task-pool replacement is already the primitive-map table. None of these is a guardrail that could not be phrased positively — they already are, elsewhere — so the section is pure duplication that inflates these six meanings' prominence past their real rank and costs tokens on every load.
  - quote: "## Anti-patterns

- **Orchestrating a trivial task** — solo/inline beats a swarm below ~5–7 units.
- **Parallel mutation without worktree isolation** — the one way to actually get conflicts back.
- **Unpinned mechanical subagents** — they inherit the expensive session model; pin `sonnet`/`haiku`.
- **Barrier where pipeline would do** — wastes the fast items' idle time waiting on the slowest.
- **Silently doing a Codex-sized batch in the session model** — that's the delegation the routing exists for.
- **Re-implementing a message bus / task pool** — you have the Workflow tool; don't rebuild beads."
  - proposed fix: Delete the Anti-patterns section; if a compact recap is wanted, keep only genuinely new guardrails not covered elsewhere, phrased positively per the doctrine's guidance.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Context pointers — "One trigger per branch. Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches."**: These are two separately-worded triggers for the exact same branch: the workflow's own step 4 header treats them as one thing ("When the ask is to *author* a DESIGN.md / token architecture from the mess — not just list it — run the proposer"). Listing them as distinct 'Use when' clauses in the always-loaded description pays context load twice for one branch.
  - quote: "author a DESIGN.md from an existing messy codebase, or turn design-drift findings into a token architecture"
  - proposed fix: Collapse to a single clause, e.g. "...or author a DESIGN.md / token architecture from an existing messy codebase."
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Pruning — single source of truth / duplication.**: This re-states 'Detect-then-fix, never fix-then-detect' from the One Rule box at the top of the document — the same meaning given a second time.
  - quote: "**Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it."
  - proposed fix: Trim the Anti-patterns bullet to the actionable part only, e.g. 'Any disk write that bypasses `mutate()` — grep the doctor module for writes not routed through it,' relying on The One Rule for the detect/fix ordering.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Pruning — relevance ("A line loses relevance by never bearing on the task (mere exposition...)")**: This is provenance/editorial history about a retired skill — it never bears on what the agent does when executing this skill, yet it sits in the always-loaded in-file body, costing context on every invocation for pure exposition.
  - quote: "<!-- Distilled 2026-07-04 from the retired 130-file `git-worktree-branch-rationalization`
     skill: kept the archaeology + harmonization + safety kernel; dropped the multi-agent
     swarm tiers, wizard-style adjudication, fuzzing/conformance testing, per-language
     deep-dives, the Bayesian machinery, and the 30 subagents. See references/HARMONIZATION.md. -->"
  - proposed fix: Move this note to the git history/PR description for the skill's distillation rather than the skill body; drop it from the file entirely.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Context pointers — "A pointer does two jobs — state what the material is, and list the branches that should trigger reaching it."**: This single pointer bundles material with different trigger conditions: the agent-hook detection/merge pattern is genuinely conditional ("if the CLI plugs into AI agents"), while draw_box and uninstall/service are unconditional per non-negotiables #12/#13 (required every run). Lumping a conditional branch and mandatory always-needed material behind one sentence obscures when each piece must actually be reached.
  - quote: "The full detection + JSON-merge-with-backup pattern (the load-bearing reusable piece), the `draw_box` implementation, and the uninstall/service snippets are in [references/PATTERNS.md](references/PATTERNS.md)."
  - proposed fix: Split into two pointers: one gated on the AI-agent branch ("if the CLI plugs into AI agents, see references/PATTERNS.md for the detection+merge pattern"), and a separate, unconditionally-worded pointer for draw_box and uninstall/service ("every run needs draw_box and uninstall output — see references/PATTERNS.md").
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Pruning — "Keep each meaning in a single source of truth: one authoritative place, so changing the behaviour is a one-place edit. Duplication ... costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank."**: The musl-over-gnu rule is already the authoritative statement in non-negotiable #4 ("prefer `musl` on Linux for static portability") and restated again in the code-snippet comment ("Prefer `musl` on Linux — static, no glibc skew"). This anti-pattern bullet is a third restatement of the identical rule, so changing the guidance later requires editing three places instead of one.
  - quote: "**`gnu` target on Linux** — not portable; use `musl` (static)."
  - proposed fix: State the musl rule once in the 14 non-negotiables; have the snippet comment and anti-pattern entry reference it ("see #4") instead of restating it.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md

### Refuted findings

- **Pruning — single source of truth ("Keep each meaning in a single source of truth: one authoritative place... Duplication — the same meaning in more than one place — costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.")** — verifier: This same rule (and the other two Critical rules bullets) is restated a second time almost verbatim in the Pre-flight checklist ("URLs verified (correct page loads in Brave)", "Element names match the current UI exactly", "Clear \"report back\" format"), and again in the Anti-patterns table's "Do instead" column ("Full URL, opened in Brave", `Click "Create credentials"`). The same three meanings are now authored in three places, so a change to any one rule requires editing three sections in sync.
  - quote: "Include FULL URLs with query params (`?project=xyz`) and open them in Brave."
- **Negation is the failure mode — prompt the positive; a negation that adds nothing beyond an already-stated positive is a no-op.** — verifier: This sentence immediately follows "Orchestration overhead isn't worth it; a single Sonnet subagent or inline work is cheaper," which already states the same rule positively. The negated restatement adds no new information and is the exact no-op/negation pattern the doctrine warns against (steering by prohibition after the positive is already spoken).
  - quote: "Don't build a swarm for a small job."
- **Pruning — "Keep each meaning in a single source of truth... Duplication — the same meaning in more than one place — costs maintenance and tokens."** — verifier: This restates Hard Rule 2 ("Every hit is a lead, not a verdict. Confirm at the file:line before citing it.") verbatim in meaning. The same instruction to verify findings before reporting them now lives in two places, so a future change to that policy requires editing both.
  - quote: "Re-read the cited code before reporting anything."
- **Pruning — single source of truth / duplication: 'the same meaning in more than one place — costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.'** — verifier: This restates the exact same rule already given twice earlier: as step 4 of the mutate() chokepoint ('Write a verbatim backup ... assert cmp -s against the live file') and again verbatim in the Safety envelope ('Backups are verbatim. No reformatting, no "clean up while I'm here"...'). The same meaning now lives in three places, so a future change to the backup rule requires editing three sites and risks drifting out of sync.
  - quote: "**Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently."
- **Pruning — single source of truth / duplication.** — verifier: This duplicates the Safety envelope's 'Never `rm -rf`, `git reset --hard`, or `DROP TABLE`.' — the same prohibition, same three operations, stated twice in the document.
  - quote: "**`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead."
- **Steps and completion criteria — clarity: 'A vague bound ("understanding reached") invites premature completion.'** — verifier: Every other step in the build loop and the rest of the document ties completion to a checkable artifact (exit code, hash match, fixture pass). This final step's bound is 'until clean,' which is undefined anywhere in the doc, and the parenthetical explicitly disclaims any completion state — inviting the agent to stop at whatever level of re-read feels sufficient.
  - quote: "**Iterate** — a fresh-eyes/adversarial re-read until clean; re-mine as the project evolves (no doctor is ever "done")."
- **Pruning — relevance: 'A line loses relevance by never bearing on the task (mere exposition...).'** — verifier: This comment records the skill's editorial history (what was kept/dropped from a prior 166-file version). It doesn't bear on adding or upgrading a doctor subcommand — it's exposition for whoever maintains the skill, not material the agent needs to execute the task, yet it loads with the rest of the body whenever the skill fires.
  - quote: "<!-- Distilled 2026-07-04 from the retired 166-file `world-class-doctor-mode-for-cli-tools` skill:"
- **Context pointers — one trigger per branch ("Synonyms that rename a single branch are one branch written twice; collapse them")** — verifier: The description's opening clause already states the triggering condition ("forgotten branches/worktrees left by parallel agents"). This trailing sentence is a synonym of the same branch, not a distinct one, and since the description is always-loaded, it spends pointer tokens saying nothing new.
  - quote: "Use for parallel-agent branch cleanup."
- **Pruning — single source of truth / duplication ("Duplication — the same meaning in more than one place — costs maintenance and tokens")** — verifier: Every bullet here restates, with the same meaning, a rule already stated once elsewhere: bullet 1 duplicates the opening "core move" callout; bullet 2 duplicates Safety kernel #2; bullet 3 duplicates Safety kernel #3 and Phase A step 1; bullet 4 duplicates Phase A's "the branch name is a hint, not a verdict"; bullet 5 duplicates Safety kernel #6/#7 and Phase D; bullet 6 duplicates the Pipeline section's "Don't re-implement their funnel here." This inflates each rule's apparent prominence and creates multiple places to edit if any rule changes.
  - quote: "## Anti-patterns

- **Picking a winner among colliding branches.** That's the failure this skill exists to prevent — you lose
  the real work in every branch you didn't pick. Harmonize.
- **Landing recovered work directly on canonical.** Always the `branch-rationalization-<date>` staging branch.
- **Trusting `git log` ancestry over `git cherry -v`.** Squash/rebase-landed content looks novel to `log`.
- **Classifying by branch name.** The fingerprint is the evidence; the name is a prior.
- **Batch-deleting after one "yes".** Per-plan verbatim authorization, individual removals, backups first.
- **Re-implementing wt-sweep.sh / branch-triage.sh here.** Let them do the mechanical pass; start from RESIDUE."
- **Context pointers — "Cut identity the body already carries."** — verifier: The description spends tokens restating that the skill is self-contained, but the body's own opening HTML comment already says this explicitly ("This version is self-contained: real snippets inline, no external line-refs"). This is identity the body already carries, and every word of an always-loaded description costs on every turn.
  - quote: "Self-contained (real bash inline)."
- **Context pointers — "One trigger per branch. Synonyms that rename a single branch are one branch written twice; collapse them and keep only genuinely distinct branches."** — verifier: "install.sh", "a curl-pipe-bash installer", and "a one-liner install" are three phrasings of the same trigger condition (the agent is being asked to write this kind of installer), not three distinct branches. Spelling out synonyms bloats the always-loaded description without adding a genuinely new case.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer, or a one-liner install for a Rust/TS/Go CLI."
- **Pruning — "Keep each meaning in a single source of truth ... Duplication ... costs maintenance and tokens."** — verifier: The flock-first/mkdir-fallback/stale-PID-heal rule is already stated as the authoritative rule in non-negotiable #6 and again in the "Atomic lock" snippet's lead-in prose, and is checked again in the pre-ship checklist. This anti-pattern bullet is a fourth restatement of the same meaning, inflating its prominence and creating four places to keep in sync.
  - quote: "**`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback."
