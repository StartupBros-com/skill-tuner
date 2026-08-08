# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $3.9809 spent
- verify: 165 trial(s), $4.3166 spent

## Run manifest

- run: `swapgate6-probe-doctrine-v3` (2026-08-08T08:13:04Z → 2026-08-08T09:18:05Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ 5d080cf37eb6 (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | `0dc154c88283` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | `7d2290123e00` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | `a8d1903218b1` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `2d965c7d2ff9` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | `824fdef96119` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | `808fcc7103af` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | `b6e7cba9bcb5` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `6bcf11e24d2f` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | `291233457df4` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | `a14d423610c4` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | `334f34680634` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | `c6db47a75b83` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | `ce83411bd389` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | `e55823e32a45` | worktree @ 77e155f9b4ff |
| target | `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | `9ab5c7a6100c` | worktree @ 77e155f9b4ff |

## Marginal-value probe verdict

**findings_confirmed: 42**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../skills/skill-tuner/SKILL.md
- targets: 15
- probe calls: 15
- verify calls: 165 (3 skeptic(s) per finding)
- refuted: 13
- overflow (beyond max_findings cap, not verified): 3

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 5 | 0 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 4 | 0 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 3 | 2 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 4 | 0 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 0 | 1 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 4 | 0 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 2 | 2 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 2 | 2 |

### Confirmed findings

- **Pruning and drift — duplication wears disguises, the commonest is polarity: an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror.**: Every item in this list is the negated restatement of a rule already given positively elsewhere in the same document: 'trivial task' mirrors the 'Solo / inline — < ~5–7 independent units' bullet; 'worktree isolation' mirrors the 'Parallel agents that MUTATE files → one git worktree per agent' bullet; 'unpinned mechanical subagents' mirrors 'Pin model' and 'Pass model explicitly' elsewhere; 'barrier where pipeline would do' mirrors 'Pipeline, not barrier, by default'; 'silently doing a Codex-sized batch' is near-verbatim of 'Never silently absorb a delegatable batch into the session model'; 'message bus / task pool' mirrors the Workflow-tool description and the 'No file reservations, no message bus, no bead pool' line. Each is the same meaning written twice, inflating six facts' apparent rank and cost with zero new information.
  - quote: "## Anti-patterns

- **Orchestrating a trivial task** — solo/inline beats a swarm below ~5–7 units.
- **Parallel mutation without worktree isolation** — the one way to actually get conflicts back.
- **Unpinned mechanical subagents** — they inherit the expensive session model; pin `sonnet`/`haiku`.
- **Barrier where pipeline would do** — wastes the fast items' idle time waiting on the slowest.
- **Silently doing a Codex-sized batch in the session model** — that's the delegation the routing exists for.
- **Re-implementing a message bus / task pool** — you have the Workflow tool; don't rebuild beads."
  - proposed fix: Delete the Anti-patterns section entirely; each positive rule it mirrors already states the boundary condition on its own (e.g. 'Orchestration overhead isn't worth it' under Solo/inline already covers the trivial-task case).
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place, so changing the behaviour is a one-place edit.**: This restates, in near-identical wording, the rule already given under 'Pick the lightest engine that fits': 'Pin `model` (sonnet/haiku for mechanical sweeps — don't let them inherit the session model).' The same fact then appears a third time, negated, in the Anti-patterns list ('Unpinned mechanical subagents — they inherit the expensive session model; pin sonnet/haiku'). Three copies of one rule mean an edit to the pinning policy requires finding and updating all three.
  - quote: "Pass `model` explicitly — unpinned subagents silently inherit the session model."
  - proposed fix: State the model-pinning rule once (under 'Pick the lightest engine that fits', where it's first needed) and drop it from 'Cost routing' and the anti-patterns list.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **One trigger per branch [craft] — synonyms that rename a single branch are one branch written twice; ask whether a run reaching the document through one trigger phrase takes a different path than one reaching it through the phrase beside it.**: 'whole-codebase campaigns', 'broad multi-file sweeps', and 'N-independent-units work' all describe the same underlying branch — a large task decomposable into many independent units, routed through the same engine-selection logic in the body — rather than three distinct paths. They pay three times in the always-loaded description to route to one place.
  - quote: "broad multi-file sweeps, N-independent-units work"
  - proposed fix: Collapse to a single phrase, e.g. 'whole-codebase campaigns and other N-independent-units work (refactor / audit / migration / dead-code sweep)', and keep 'multiple independent perspectives (adversarial verification)' as the one genuinely distinct second branch.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Demand [craft] — "Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically."**: This row is presented as an automatic block ("Each of these is an automatic block in `review-animations`"), which requires a checkable bound. The numeric 300ms threshold is checkable, but "with no reason" is not — it lets any duration over 300ms be waved through so long as the agent asserts a justification, defeating the automatic-block purpose of the rest of the table and letting the whole criterion be satisfied impressionistically.
  - quote: "UI duration over 300ms with no reason"
  - proposed fix: Drop the qualifier and state the checkable bound alone (e.g. "UI duration over 300ms outside the modal/drawer range"), or replace it with a named, enumerable exception list rather than an open-ended "reason."
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Completion criteria — contradicting bounds**: This states damping ~0.8 is reserved for momentum-carrying gestures (flick/throw/drag-release). But the 'Concrete values Apple ships' table right below assigns damping 0.8 to 'Rotation' and 'Drawer / sheet' unconditionally, with no momentum qualifier — a drawer opened by a tap (no momentum) would still read as damping 0.8 per the table, directly contradicting the general rule. This is the doctrine's named failure: a general ceiling in one place and a specific value crossing it in another, leaving the agent unable to tell which bound governs a non-momentum sheet/rotation.
  - quote: "Add bounce (**damping ~`0.8`**) **only when the gesture itself carried momentum** (a flick, a throw, a drag release)."
  - proposed fix: Qualify the table rows, e.g. 'Drawer / sheet (momentum-driven open/close) | 0.8 | 0.3' and add a separate row or note for non-momentum sheet opens defaulting to damping 1.0, so the two rules agree.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Context pointers — pointer wording must name reachable material**: The pointer promises 'restraint' as one of the design foundations reachable in this skill, but no such concept is named or defined anywhere in the body — section 16's eight principles are Purpose, Agency, Responsibility, Familiarity, Flexibility, Simplicity, Craft, and Delight, and the 'four human needs' are safety/predictability, understanding, achievement, and joy. An agent or human reaching for 'restraint' finds nothing under that name.
  - quote: "the design foundations (feedback, spatial consistency, restraint) behind Apple-style interfaces"
  - proposed fix: Either add a named 'Restraint' concept to §16 (e.g. under Purpose or Simplicity, since both already gesture at it) or drop 'restraint' from the description's parenthetical so the pointer doesn't promise unfulfilled material.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Negation**: This is a standalone prohibition with no paired positive target — it leads with the ban and doesn't state what to do instead, which is the doctrine's explicit tell for a negation defect. It's also easily phrasable positively, so it doesn't qualify for the 'hard guardrail' exception.
  - quote: "Never lock out input during a transition."
  - proposed fix: Rephrase positively: 'Keep the UI responsive to input throughout every transition.'
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Negation**: Leads with the ban and never states the positive alternative (what to place under a light translucent surface instead). This is readily phrasable positively, so it doesn't meet the bar for an unavoidable guardrail exception.
  - quote: "**Never stack a light translucent surface on another** — legibility collapses."
  - proposed fix: Rephrase as: 'Place a light translucent surface only over an opaque or darker layer — stacking two light translucent surfaces collapses legibility.'
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Pruning and drift — duplication wears disguises, and the commonest is polarity: an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice.**: Every row here just negates a rule the document already states positively elsewhere: 'Never skip 1-3' / 'data wins' already covers 'Automate before measuring'; the Principle table ('Complex/stateful → Python; glue → bash') and the Step 3 decision tree already cover the Python-vs-bash row; Step 4's '--dry-run for safe testing' and Step 5's '--dry-run produces no side effects' already cover the dry-run row; Step 4's 'Non-zero exit codes on failure' already covers the exit-code row; and Step 2's 'Only automate if Score ≥ 0.3' already covers the scoring row. Each is the same meaning written twice, inflating maintenance surface (a rule change now needs a second edit here) without adding routing or execution signal.
  - quote: "| Automate before measuring | Mine history first |
| Python CLI for 2-line glue | Bash script or alias |
| Skip `--dry-run` | Always add dry-run mode |
| Ignore exit codes | Non-zero exit + logging |
| Automate rare commands (Score < 0.3) | Skip — maintenance > benefit |"
  - proposed fix: Delete the rows that only negate an existing positive rule (measuring-first, Python-vs-bash, dry-run, exit codes, score threshold). Keep only genuinely new guidance not stated elsewhere, e.g. 'One giant script → Unix philosophy: small composable tools.'
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Completion criteria — a bound must be checkable, and a step the document marks mandatory ('Never skip 1-3') must actually give the agent something to check.**: The Loop lists CLUSTER as step 2 and 'Never skip 1-3' makes it mandatory, but no 'Step: Cluster' section exists anywhere in the body — Step 1 covers only mining, Step 2 (headed 'Score') jumps straight to scoring. There is no query, heuristic, or reference link for doing 'semantic similarity + temporal adjacency' clustering, so the agent cannot tell whether it has complied with the mandatory step versus skipped it.
  - quote: "2. CLUSTER   → semantic similarity + temporal adjacency"
  - proposed fix: Either add a 'Step 2: Cluster' section (or fold explicit clustering guidance into Step 1) with a checkable method, or drop CLUSTER from the numbered loop and from the 'never skip 1-3' mandate if it isn't actually a discrete step the agent performs.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Demand — watch for criteria that mix checkable and uncheckable terms; one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.**: Every other Validate bullet is checkable without judgment ('Run 5×...', '--json output parses as valid JSON', '≥ 3× faster'), but 'verify graceful behavior' gives no bound for what counts as graceful — the exact 'verify the config'-style vagueness the doctrine calls out. The agent can mark this box satisfied on impression alone.
  - quote: "- [ ] Force failure → verify graceful behavior"
  - proposed fix: Replace with a checkable bound, e.g. 'Force failure → exits non-zero, prints an error to stderr, and leaves no partial output files.'
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Demand — a stray uncheckable qualifier inside an otherwise precise checklist lets the agent satisfy the whole list impressionistically.**: The other Done When items are checkable ('At least one automation built and validated', 'Automation installed (PATH, alias, or systemd timer)'), but this bullet gives no method or threshold for what 'measured' means, unlike Step 5's parallel and already-checkable '≥ 3× faster than manual.' It duplicates that criterion in vaguer form.
  - quote: "- [ ] Time savings measured"
  - proposed fix: Either remove this bullet (Step 5's '≥ 3× faster' already covers it) or make it checkable, e.g. 'Measured time saved ≥ [X] and recorded in the automation's --help or README.'
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Progressive disclosure — inline what every branch needs; disclose what only some branches reach.**: This whole comment block (provenance, upstream cherry-pick instructions, jsm install-all collision warning) is only relevant to the maintenance branch — syncing this fork with upstream — never to the mining/scoring/building branch the skill actually exists to run. It's inlined at the top of the always-loaded body, so every invocation of the skill (to mine automations) pays the context cost of upstream-sync instructions it never needs.
  - quote: "LOCAL FORK — not managed by jsm; do not expect `jsm install-all` to preserve it."
  - proposed fix: Move the fork-provenance and sync-cherry-pick instructions to a small reference file (e.g. references/FORK-SYNC.md) and leave only a one-line pointer in the body: 'Local fork — see references/FORK-SYNC.md before running jsm install-all.'
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Duplication / polarity disguise ("Pruning and drift" — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice")**: Every line in this Anti-patterns list is the negated restatement of a rule already given positively elsewhere: 'picking a winner' vs. the core-move callout's 'harmonize, don't pick a winner'; 'landing on canonical' vs. Safety kernel #2 ('Land on a staging branch, never on canonical'); 'trusting git log' vs. Safety kernel #3 ('git cherry -v is the authoritative check ... Trust it over git log ancestry'); 'classifying by branch name' vs. Phase A's 'Let the fingerprint override the name every time'; 'batch-deleting' vs. Safety kernel #6/#7; 're-implementing wt-sweep.sh/branch-triage.sh' vs. the Pipeline section's 'Don't re-implement their funnel here.' Each meaning is now maintained in two places, inflating token cost and creating a maintenance hazard if one copy is edited and the other isn't.
  - quote: "- **Picking a winner among colliding branches.** That's the failure this skill exists to prevent — you lose
  the real work in every branch you didn't pick. Harmonize.
- **Landing recovered work directly on canonical.** Always the `branch-rationalization-<date>` staging branch.
- **Trusting `git log` ancestry over `git cherry -v`.** Squash/rebase-landed content looks novel to `log`.
- **Classifying by branch name.** The fingerprint is the evidence; the name is a prior.
- **Batch-deleting after one "yes".** Per-plan verbatim authorization, individual removals, backups first.
- **Re-implementing wt-sweep.sh / branch-triage.sh here.** Let them do the mechanical pass; start from RESIDUE."
  - proposed fix: Delete the Anti-patterns section entirely; the positive rules it mirrors already exist in the Safety kernel, Pipeline, and Phase A sections. If a compact recap is wanted, replace it with a single line pointing back to the Safety kernel rather than restating each rule negated.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Cut identity the body already states (Context pointers)**: This clause explains what the skill *is* (a judgment layer over two scripts, doing harmonization instead of picking a winner) rather than when to reach it. That identity is already stated in the body's core-move callout and in the Pipeline diagram ('THIS SKILL (the cognitive layer over the RESIDUE)'). The description pays permanent context load to restate it with no added routing signal.
  - quote: "the judgment layer over wt-sweep.sh/branch-triage.sh that harmonizes competing variants rather than picking one winner"
  - proposed fix: Trim the description to the triggering condition only, e.g. 'Salvage and rationalize forgotten branches/worktrees left by parallel-agent development. Use for parallel-agent branch cleanup.' and let the body's opening callout carry the identity/positioning explanation.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **One trigger per branch (Context pointers)**: This trailing sentence restates the same triggering condition already given in the description's opening clause ('forgotten branches/worktrees left by parallel agents'). A run reaching the skill through either phrase takes the same path — it is one branch (parallel-agent branch pileup) paid for twice.
  - quote: "Use for parallel-agent branch cleanup."
  - proposed fix: Drop the trailing 'Use for parallel-agent branch cleanup.' sentence; the opening clause already establishes the trigger.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Relevance and sediment (Pruning and drift)**: This is a permanently-loaded changelog note about the skill's own editorial history (what a prior, retired skill contained and what was cut from it). It never bears on how to actually assess or harmonize branches — it is provenance for a human maintainer, not operational content for the agent — yet it costs context on every load.
  - quote: "<!-- Distilled 2026-07-04 from the retired 130-file `git-worktree-branch-rationalization`
     skill: kept the archaeology + harmonization + safety kernel; dropped the multi-agent
     swarm tiers, wizard-style adjudication, fuzzing/conformance testing, per-language
     deep-dives, the Bayesian machinery, and the 30 subagents. See references/HARMONIZATION.md. -->"
  - proposed fix: Move this distillation note to the commit message or a CHANGELOG, and remove it from the skill body.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **One trigger per branch**: The description's first sentence already lists 'persona' as a branch ('Use when starting a new brand, sub-brand, product, persona, or author voice'). This second clause names the same branch again in different words, paying routing-load twice for one path instead of once.
  - quote: "when a new persona needs voice definition"
  - proposed fix: Drop 'when a new persona needs voice definition' from the second clause since 'persona' is already covered in the first, leaving only the genuinely distinct triggers (generic copy, unclear tone).
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Cut identity the body already states**: This sentence in the always-loaded description enumerates the exact section headers of the Voice Profile template that the body already defines in full under '## The Voice Profile (Output Format)'. It restates identity ('what the output is') rather than routing information ('when to reach it'), paying permanent context load for no triggering signal.
  - quote: "Outputs a complete Voice Profile with tone spectrum, vocabulary, mechanical rules, on-brand and off-brand example phrases, aspiration and anti-aspiration models, and a quality test."
  - proposed fix: Shorten to something like 'Outputs a structured Voice Profile document' and let the body's template headers be the single place the profile's contents are enumerated.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Single source of truth**: This duplicates the description's 'Does NOT apply existing voices -- for that, use the brand-specific voice skill (hov-brand-voice, email-brand-voice, prbot-brand-voice, etc)', down to the same example skill names. The exclusion rule is now maintained in two places.
  - quote: "- The brand voice is already defined and encoded in a project-specific skill: use that skill directly (e.g. hov-brand-voice, prbot-brand-voice)."
  - proposed fix: State the exclusion once, either in the description or the body, and have the other location reference it rather than restate it.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Context pointers — one trigger per branch [craft]**: "bot detection" and "browser may not be secure" are not distinct branches — the latter is the literal error text Google shows *because of* bot detection (confirmed by the doc's own diagram: `Google OAuth consent -> "This browser or app may not be secure"`). A run reaching this skill via either phrase takes the identical path (open Brave, hand off clicks). Per the doctrine's test, these should collapse into one trigger instead of paying twice in the always-loaded description.
  - quote: "bot detection, "browser may not be secure", 2FA, CAPTCHA, or OAuth consent screens"
  - proposed fix: Collapse to a single trigger, e.g. "bot detection (Google's 'browser may not be secure'), 2FA, CAPTCHA, or OAuth consent screens".
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Pruning and drift — duplication via polarity [craft]**: This anti-pattern row is the negated restatement of a rule already given positively: "Include FULL URLs with query params (`?project=xyz`) and open them in Brave." It's the same meaning written twice — the polarity disguise the doctrine calls out explicitly.
  - quote: "Skip query params | Wrong page loads | Full URL, opened in Brave"
  - proposed fix: Drop this row from the Anti-patterns table; the Critical rules bullet already covers it.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Pruning and drift — duplication via polarity [craft]**: This restates, negated, the Critical rules bullet "Use EXACT element text (copy from the current UI)." Same meaning, two places — costs maintenance and tokens without adding routing or execution signal.
  - quote: "Vague "click the button" | Which one? | `Click "Create credentials"`"
  - proposed fix: Drop this row; keep the positive rule in Critical rules only.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Pruning and drift — single source of truth [craft]**: These checklist items are a third restatement of the same two meanings already stated positively in Critical rules ("Include FULL URLs with query params...", "Use EXACT element text...") and negatively in Anti-patterns. Three places carrying one meaning means any future change to the rule requires a three-way edit.
  - quote: "- [ ] URLs verified (correct page loads in Brave)
- [ ] Element names match the current UI exactly"
  - proposed fix: Replace with a single checklist line that points back rather than restates, e.g. "- [ ] Instructions follow the template's Critical rules", removing the re-derived specifics.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **One trigger per branch [craft]**: The description states the same branch (single/best-result search) twice in one sentence: "when you want the most relevant past session first" and "Prefer this for top-1/top-few results" are synonymous triggers for the identical routing decision. Per the doctrine's test — "does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it?" — these do not diverge, so they should collapse into one phrasing rather than paying context load twice on every turn.
  - quote: "this for top-1/top-few results; fall back to plain cass for broad scans."
  - proposed fix: Collapse to a single statement of the branch, e.g. "Use INSTEAD of bare `cass search` for top-1/top-few relevance-ranked results; fall back to plain cass for broad scans."
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Pruning and drift — Duplication / Single source of truth ('an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice')**: Each of these anti-pattern bullets is a negated restatement of a rule the document already gives positively elsewhere: destructive-flag auto-correction is already forbidden in the Grading ladder ('destructive flags are NEVER auto-corrected; the agent must type the canonical form'); ANSI/emoji/stack traces are already banned in the Error anti-patterns list ('no stack traces outside --debug ... no ANSI/emoji in errors ... stderr only'); capabilities drift is already the subject of Recurring fix #4 ('introspected from the real command tree (hand-curated drifts)'); bare-TUI is already stated as axiom 🚫 and Recurring fix #8; exit-1-overload is already Recurring fix #10; confirmation-prompting is already banned in Error anti-patterns ('never prompt for confirmation on a destructive op'). This is duplication wearing the polarity disguise the doctrine calls out — same meaning written twice (in some cases three times), inflating these items' apparent rank and costing tokens without adding routing or execution signal.
  - quote: "- **Auto-correcting a destructive flag** — hint, never act, on anything irreversible.
- **ANSI/emoji or stack traces in errors**, or errors on stdout — all break non-TTY agents and `| jq`.
- **Hand-maintained `capabilities`/`--help`** that drifts from the real command tree — introspect it.
- **Bare `<tool>` opening a TUI**; **exit 1 meaning "no results"**; **prompting for confirmation** in a non-TTY."
  - proposed fix: Cut these four bullets from Anti-patterns since the rules already exist positively elsewhere; keep only anti-pattern items that add information not stated elsewhere (e.g. 'a polite scorecard with no applied fixes' and 'fixing one flag's error in isolation').
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning and drift — Relevance and sediment ('every line must still bear on what the document does')**: This is authoring history about a retired sibling skill — what was kept and dropped during a distillation pass. It never bears on the task of auditing a CLI's agent ergonomics, yet it sits in the always-loaded body of the skill and pays context load on every invocation. This is exactly the sediment pattern the doctrine warns about: a stale layer that felt safe to leave in because removing it felt risky.
  - quote: "Distilled 2026-07-04 from the retired 192-file `agent-ergonomics-and-intuitiveness-maximization-for-cli-tools`
     skill: kept the kernel axioms, the error-rewriting cookbook, the named operators, the mega-command shapes,
     the 11-dim rubric, and the recurring-fixes checklist. Dropped the multi-agent swarm tiers, session-mining,
     per-pass 0-1000 scoring machinery, agent-profile reweighting, 27 subagents, and 47 scripts."
  - proposed fix: Delete the historical distillation note; keep only the still-useful line pointing to references/ERGONOMICS-SPEC.md, or move the changelog content to the commit message / a CHANGELOG file outside the loaded skill body.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Pruning and drift — duplication (polarity disguise): "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."**: This anti-pattern bullet is the negated restatement of the rule already given positively in the Build-unit section: "No fixture = no fixer — pass N+1 can't tell "fixed" from "regressed-back" without it." Same meaning, same wording almost verbatim, written twice — it costs tokens and maintenance without adding routing or execution signal.
  - quote: "**A fixer without a fixture** — you can't distinguish fixed from regressed-back next pass."
  - proposed fix: Delete this bullet from Anti-patterns; the positive rule under the Fixture bullet already covers it. If a quick-reference list is wanted, link back to that bullet instead of restating it.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Pruning and drift — duplication (polarity disguise)**: Duplicates the rule already stated in the CLI surface section: "capabilities --json is generated from the live registry of detectors/fixers — never hand-maintained, so it can't drift from reality." Same meaning in two places is a one-place-edit rule violated twice over.
  - quote: "**Hand-maintained `capabilities`** — generate it from the live detector/fixer registry so it can't lie."
  - proposed fix: Remove this bullet; the CLI surface section is the single authoritative place for this rule.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Steps, completion, and demand — Completion criteria: "a bound is checkable when the agent can tell done from not-done without judgment."**: "until clean" gives no checkable condition for when the re-read is finished — it requires the same kind of judgment call the doctrine flags with "Verify the config" as a non-example. The agent cannot tell done from not-done without guessing at what "clean" means.
  - quote: "**Iterate** — a fresh-eyes/adversarial re-read until clean; re-mine as the project evolves (no doctor is ever "done")."
  - proposed fix: Replace with a checkable bound, e.g. "re-read against the 10-dimension rubric and the anti-pattern list; iterate until no dimension scores below the project's floor, then re-mine failure modes on the next material code change."
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Progressive disclosure [craft] — "inline what every branch needs; disclose what only some branches reach."**: Non-negotiables #12 ("Final summary — one box... ") and #13 ("Uninstall instructions — printed at the end of every run") are explicitly required on every run, not branch-specific — yet their implementations (`draw_box`, uninstall) are bundled behind the same pointer as the genuinely branch-specific agent-hook-config and optional systemd/launchd service snippets. Material every branch needs is being disclosed alongside material only some branches reach, so the agent building a run-of-the-mill installer must still open the external file to get code required on every invocation.
  - quote: "The full detection + JSON-merge-with-backup pattern (the
load-bearing reusable piece), the `draw_box` implementation, and the uninstall/service snippets are in
[references/PATTERNS.md](references/PATTERNS.md)."
  - proposed fix: Inline the `draw_box` and uninstall snippets directly in the skill body next to non-negotiables #12/#13 (they're needed on every run); leave only the agent-detection/JSON-merge pattern and the optional daemon-service snippet — both genuinely branch-specific — behind references/PATTERNS.md.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Single source of truth [craft] — "keep each meaning in one authoritative place, so changing the behaviour is a one-place edit."**: The fact that locking/OS-detection is anchored on `~/SITES/pro-gate/lib/pro-gate-lib.sh` is stated three times: once in the leading HTML comment ("Locking + OS-detection re-anchored on the operator's own ~/SITES/pro-gate/lib/pro-gate-lib.sh..."), once in this Core-principle callout, and once more in the Atomic lock snippet header ("from your own `pro-gate-lib.sh`"). Same meaning, three locations, three places to update if the exemplar path ever changes.
  - quote: "Reference exemplar for real cross-platform locking/OS-detection:
`~/SITES/pro-gate/lib/pro-gate-lib.sh`."
  - proposed fix: State the exemplar path once (the Core-principle callout is the natural place, since it's read first) and drop it from the HTML comment and the Atomic-lock snippet header, replacing the latter with a bare reference like "see Core principle above."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **One trigger per branch [craft] — "synonyms that rename a single branch are one branch written twice."**: "creating install.sh", "a curl-pipe-bash installer", and "a one-liner install for a Rust/TS/Go CLI" all name the same task from the same entry point — none of them routes to a different path through the document. Per the doctrine's own test ("does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it?"), these should collapse into one trigger.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer,
  or a one-liner install for a Rust/TS/Go CLI."
  - proposed fix: Collapse to a single trigger phrase, e.g. "Use when writing a curl-pipe-bash install.sh one-liner for a CLI (Rust/TS/Go)."
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Cut identity the body already states [craft] — "the pointer's job is when to reach, not what it is."**: This clause is a feature inventory that maps almost one-to-one onto the body's "14 non-negotiables" headings (platform detection, version resolution, checksum, signature, build-from-source, completions, uninstall). It restates what the skill *is* rather than *when to reach for it*, and since the description is always-loaded, it pays permanent context cost for identity the body already establishes on invocation.
  - quote: "platform→target-triple detection, version-resolution fallback chain, checksum + Sigstore
  verification, atomic locking, build-from-source fallback, shell completions, AI-agent
  hook auto-config, and uninstall."
  - proposed fix: Trim the description to the trigger condition plus at most one or two distinguishing words (e.g. "production-grade", "self-contained"), and let the body's non-negotiables list be the single place the full feature set is enumerated.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Pruning and drift — duplication via polarity: "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror."**: This anti-pattern row is the negated restatement of a rule already given positively twice elsewhere: Up-Front Confirmations #5 ("Bench baselines + post-split comparisons must run on the same machine — pin one worker or run both locally") and the ABORT IF list ("bench baselines and comparisons MUST share one machine and quiet conditions"). The same meaning now lives in three places, so changing the rule requires a three-way edit instead of one.
  - quote: "Bench before/after on different machines or load | Comparison is void; same machine, quiet, same conditions |"
  - proposed fix: Drop the anti-pattern row (or shrink it to a one-line pointer back to Confirmation #5) and let that be the single authoritative statement of the same-machine requirement.
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Pruning and drift — duplication via polarity, same clause as above.**: This restates, negated, the rule already given positively in the B10 taxonomy row ("exclude or fix the generator; NEVER hand-split") and again in ABORT IF ("generated files are excluded or fixed at the generator, never hand-split"). The same rule now appears in three separate places rather than one authoritative one.
  - quote: "Hand-split a generated file | Regenerated next build; fix the generator or exclude (B10) |"
  - proposed fix: Remove the anti-pattern row; the B10 taxonomy entry is already the authoritative source and ABORT IF already points to it via [references/MONOLITH-TAXONOMY.md §B10].
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **One trigger per branch [craft] — "synonyms that rename a single branch are one branch written twice ... Three phrases for one branch pay three times and route once."**: "split giant file" and "file too big" both name the same single-oversized-file case, and "de-monolithize" and "modularize repo" both name the same whole-codebase case — none of the four takes a different downstream path than its neighbor. This is a description-level synonym stack, paying context-load four times to route the same one or two branches.
  - quote: "Use when de-monolithize, split giant file, modularize repo, or file too big."
  - proposed fix: Collapse to one phrase per distinct case, e.g. "Use when a file or repo has grown into a monolith that needs splitting."
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Negation [research] — "State the target behaviour so the banned one is never named ... even then it stands paired with its positive target so attention lands on what to do. The tell is a rule that leads with the ban and never says what to do instead."**: Two stacked prohibitions naming the exact failure modes (oversimplification, feature loss) with no positive target given for either — the surrounding text only says to match "the same standard as the plan itself," which doesn't specify what to do instead of oversimplifying or dropping features.
  - quote: "DO NOT OVERSIMPLIFY; DO NOT LOSE FEATURES"
  - proposed fix: State the positive target directly, e.g. "preserve every feature and the plan's full level of detail in each polish pass."
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Duplication / Single source of truth**: The Review Checklist re-states, almost verbatim, the rule and modal exception already given in full under "Make popovers origin-aware" (and again under "CSS Transform Mastery > transform-origin"). The same meaning now lives in three places; the checklist restates the same content already given for scale(0) entry animations, ease-in, and keyboard animations elsewhere in the document too. A future change to any of these rules (e.g. adding another exception) requires editing multiple spots to stay consistent.
  - quote: "| `transform-origin: center` on popover      | Set to trigger location or use Base UI's `var(--transform-origin)` (modals are exempt — keep centered) |"
  - proposed fix: Trim the checklist to short labels only (e.g. "transform-origin wrong on popover") without re-deriving the rule/exception text, or drop the checklist and let section headers serve as the review reference.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Front-load the leading word / Cut identity the body already states**: The description opens with throat-clearing identity framing ("This skill encodes...") instead of leading with the condition under which it should be reached, and it restates content the body's "Core Philosophy" section (unseen details, taste, beauty) already establishes about itself — spending the pointer's length on what the skill is rather than when to reach it.
  - quote: "This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great."
  - proposed fix: Lead with the trigger: "During UI polish passes, apply Emil Kowalski's animation and component philosophy (pairs with /ui-polish, /kill-ai-slop)." and drop the identity restatement.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth — duplication (same meaning stated in two places)**: Hard Rule 2 already rejects "it would look cool" as a justification, and the Purpose gate restates the identical judgment a few paragraphs later: "'It looks cool' is not on this list." Both sentences carry the same meaning (this justification is never valid) in two authoritative-sounding places, so a future edit to loosen or tighten this rule risks updating only one of them.
  - quote: "No exceptions for "it would look cool.""
  - proposed fix: State the rule once — keep it in the Purpose gate where the full list of valid purposes already lives — and drop the redundant clause from Hard Rule 2, or replace it there with a cross-reference ("see Purpose gate").
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Cut identity the body already states (context pointers)**: The description restates identity the body already establishes: Hard Rule 1 says "Never modify source code. This skill reports; it does not implement," and the opening paragraph already scopes the skill against implementation and the sibling skills. The description's "it does not implement it" pays permanent context load repeating what the body says about itself rather than adding routing signal beyond what "Search... for places that don't animate but should" already conveys.
  - quote: "Read-only; it proposes motion with exact values, it does not implement it."
  - proposed fix: Trim the description to the routing-relevant parts ("Search a codebase or UI for places that don't animate but should, and reject everything that shouldn't" plus the branch pointers to improve-animations/review-animations) and let Hard Rule 1 in the body be the single authoritative statement of the no-implementation constraint.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Completion criteria [craft] — "Two bounds that contradict — a general ceiling in one place, a specific range crossing it in another — are a completion defect in the same family: the agent cannot tell whether a value between them complies, whichever bound it obeys."** — verifier: This general ceiling directly conflicts with the duration table's own entry "Modals, drawers | 200–500ms", which permits durations up to 500ms — well past the stated 300ms cap. An agent building a 400ms modal animation cannot tell whether it complies: the specific table row says yes, the general rule says no. This is the exact contradiction pattern the doctrine names as a completion defect.
  - quote: "**UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
- **Splitting / Progressive disclosure** — verifier: The description names several genuinely independent branches (motion/gesture physics, translucent materials, typography, reduced-motion accessibility, high-level design foundations/process), but the body inlines all of them in one ~500-line file with no split. Per 'Push too much down and you hide material the agent needs... Split by invocation when a distinct trigger word should fire material on its own,' a run reached only for typography guidance still loads the full drag-physics, spring-math, materials, and audio-haptics content it doesn't need.
  - quote: "Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency, restraint) behind Apple-style interfaces."
- **Single source of truth** — verifier: The 'When to use this skill' list repeats the same triggers already stated in the description ('starting a new brand, sub-brand, product, persona, or author voice'). The same meaning now lives in two places, so changing when this skill applies requires editing both the pointer and the body.
  - quote: "- Starting a new brand, sub-brand, product line, or property"
- **Single source of truth** — verifier: This anti-pattern restates, negated, what the document already establishes positively elsewhere: the template's 'Mechanical Rules (always enforceable)' section says rules are 'gold,' and the Build-mode synthesis step says 'The mechanical rules from Q16 become the enforceability backbone.' It's the same meaning written a third time under a different polarity.
  - quote: "**The Unenforceable Voice:** all vibes, no mechanical rules. Result: voice drifts within weeks."
- **Progressive disclosure [craft]** — verifier: This section (status-check snippet, the explanation of why `cass index --full` stalls, and the full setsid command with seven CASS_TANTIVY_* env vars) is branch-specific reference that only the rare broken-index case needs, yet it is fully inlined in the same file that loads on every normal search invocation. Per the doctrine, material only some branches reach belongs on the disclosed rung of the ladder, not in-file among the primary 'Use it' steps every call pays for.
  - quote: "## If it returns "no results" for everything"
- **Steps, completion, and demand — Demand ('criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically')** — verifier: This is a three-item list in the document's opening statement of intent, and two of the three are checkable (silent-fail is detectable via exit code/stdout; 'safe alternative for any dangerous request' is a presence check) but 'Never punish a reasonable misstep' has no checkable bound — 'reasonable' and 'punish' are left to judgment. An agent can satisfy the whole triad impressionistically by pointing at the uncheckable middle clause.
  - quote: "Never silent-fail. Never punish a reasonable misstep. Always provide a safe alternative for any dangerous request."
- **Pruning and drift — duplication (polarity disguise)** — verifier: This restates, negated, the rule already stated positively in the safety envelope: "Backups are verbatim. No reformatting, no 'clean up while I'm here' — that silent extra edit is the #1 way reversibility breaks." The two say the same thing in two places, inflating this meaning's apparent importance without adding new content.
  - quote: "**Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently."
- **Single source of truth / duplication (polarity) — Pruning and drift** — verifier: The 'no edits' constraint is stated positively ("TEXT-ONLY advisory second opinion") and then immediately restated negated ("Do not modify files, create branches, or open PRs") in the same blockquote — the polarity disguise the doctrine calls out under duplication. The same meaning is already given a third time in the frontmatter description ("Advisory only — Codex never edits files.") and a fourth time via the `-s read-only` flag description in step 2. This is one meaning written in four places instead of one authoritative statement.
  - quote: "You are a senior engineer giving a TEXT-ONLY advisory second opinion. Do not
   > modify files, create branches, or open PRs."
- **Duplication / "Duplication wears disguises... an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice" [craft]** — verifier: Nearly every entry in this anti-pattern list is the negated restatement of a rule already given positively elsewhere: checksum vs. non-negotiable #7, gnu-vs-musl vs. non-negotiable #4, JSON-backup vs. the agent-auto-config paragraph, cosign/gum soft-fail vs. non-negotiable #8, flock-vs-mkdir vs. non-negotiable #6, and proxy vs. non-negotiable #3. This is the same meaning written twice per item, inflating the document without adding routing or execution signal, and creating two places that must be kept in sync if any rule changes.
  - quote: "- **Skipping checksum verification** — supply-chain risk; always verify SHA256.
- **`gnu` target on Linux** — not portable; use `musl` (static).
- **Editing settings/JSON without a backup**, or with `sed`/`awk` — `cp file file.bak.$(date +%s)` first, merge with `jq`/Python3.
- **Assuming `~/.local/bin` is on PATH** — check `:$PATH:`, offer to fix, don't assume.
- **Hard-failing on optional features** (missing cosign/gum) — warn and continue.
- **`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback.
- **Raw unstyled output** — route through `info/ok/warn/err`; honor `NO_COLOR`/non-TTY so piped/CI output has no ANSI.
- **`<tool> --version` with no timeout** — wrap in `timeout 1` (some CLIs hang).
- **Ignoring proxy env** — `PROXY_ARGS` on every curl call."
- **Completion criteria — contradictory bounds** — verifier: This general ceiling directly contradicts the Duration table's own row "Modals, drawers | 200-500ms", which the rule sits right below in the same section. The doctrine names this exact pattern — a general ceiling in one place and a specific range crossing it in another — as a completion defect: the agent cannot tell whether a 350ms or 400ms modal transition complies, whichever bound it tries to obey.
  - quote: "**Rule: UI animations should stay under 300ms.**"
- **Progressive disclosure / Sprawl** — verifier: This section, along with sibling sections like "Spring Animations," "clip-path for Animation," and "Debugging Animations," addresses a narrow branch (drag-based components, spring-driven motion, clip-path reveals) that most UI-polish passes never touch, yet all of it is permanently inlined in one 500+ line file with no disclosed sub-references. This is exactly the sprawl the doctrine warns about — attention thins across live, unique material that only some branches reach — and the fix is splitting into disclosed references, not trimming prose.
  - quote: "## Gesture and Drag Interactions"
- **Completion criteria — contradicting bounds ("a general ceiling in one place, a specific range crossing it in another")** — verifier: The prose states a hard ceiling of 300ms for UI animation, but the very next table row gives "Modals, drawers | 200–500ms", a range that crosses the stated ceiling. An agent proposing a 400ms modal transition cannot tell whether it complies: the ceiling says no, the specific row says yes. This is the exact contradiction the doctrine calls out — a general ceiling in one place, a specific range crossing it in another — and it isn't hypothetical: the worked example in Part 1's output table itself uses `transition: 400ms ease` for a toast, which is inside the table's modal/drawer range but outside the stated 300ms ceiling.
  - quote: "The suggestion must work within the standard budgets (UI under 300ms):"
- **One trigger per branch** — verifier: Both phrases route to the same single behavior (sweep for new opportunities) with no divergent path — there's no branch where "make this feel more alive" is handled differently from "what could be animated here?" Per the doctrine's test (does a run reaching the doc through one phrase take a different path than through the other?), these are one branch stated twice, paying context/description cost twice for one routing outcome.
  - quote: "Use when the user asks "what could be animated here?" or wants to "make this feel more alive"."
