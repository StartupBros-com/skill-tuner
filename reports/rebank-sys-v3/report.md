# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $4.2005 spent
- verify: 156 trial(s), $3.6095 spent

## Run manifest

- run: `rebank-sys-v3` (2026-08-10T20:53:34Z → 2026-08-10T21:59:14Z)
- claude CLI: `2.1.224` | skill-tuner: `0.5.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ 174bcdf5ce95 |
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

**findings_confirmed: 34**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/configs/../skills/skill-tuner/SKILL.md
- targets: 15
- probe calls: 15
- verify calls: 156 (3 skeptic(s) per finding)
- refuted: 18

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 2 | 0 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 4 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 5 | 0 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 1 | 0 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 4 | 1 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 2 | 0 |

### Confirmed findings

- **One trigger per branch (Context pointers)**: "broad multi-file sweeps" and "N-independent-units work" are two more phrasings of the same branch already named by "many independent units" — a run reaching the skill through either phrase takes the identical fan-out path described in the body. This is the synonym-stacking the doctrine flags: three phrases for one branch pay three times in always-loaded description tokens and route once.
  - quote: "has many independent units: whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work, or when you need multiple independent perspectives (adversarial verification)"
  - proposed fix: Collapse to a single phrasing, e.g. "Use when a task is too big for one context or has many independent units (whole-codebase campaigns: refactor / audit / migration / dead-code sweep), or when you need multiple independent perspectives (adversarial verification)." — drop "broad multi-file sweeps" and "N-independent-units work" as they add no distinct branch.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Demand — criteria mixing checkable and uncheckable terms**: The vote counts ("single-vote", "3–5-vote") are checkable, but the finder-pool sizes ("a few finders", "larger finder pool") are not — there's no number or ratio to compare against. An agent can satisfy the whole scaling rule impressionistically by launching any pool it deems "a few" or "larger" while still hitting the precise vote count, which is exactly the impressionistic-compliance failure the doctrine warns against when a vague qualifier rides inside an otherwise precise list.
  - quote: "Scale to the ask: a quick check → a few finders, single-vote verify. "Be comprehensive" → larger finder pool, 3–5-vote adversarial pass, synthesis."
  - proposed fix: Replace with checkable bounds on both axes, e.g. "a quick check → 2–3 finders, single-vote verify. 'Be comprehensive' → 6+ finders, 3–5-vote adversarial pass, synthesis."
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Cut identity the body already states**: This clause enumerates the exact seven-step sequence that the body's "Build Sequence" headers already state in full (1. Should this animate, 2. What is the purpose, 3. Pick the tool, 4. Pick the properties, 5. Easing and duration, 6. Interruption and exit, 7. Reduced motion). It restates identity/structure the body already gives, adding permanent context load on every turn with no routing signal — the pointer's job is when to reach the doc, which the following sentence already covers.
  - quote: "Build an animation from scratch, making the decisions in the order that determines whether it feels right — should it animate at all, what purpose, which tool, which properties, which curve and duration, how it interrupts, how it exits. Writes the implementation."
  - proposed fix: Cut the step enumeration from the description and keep only the routing clause, e.g.: "Build an animation for a component from scratch, from whether it should animate through implementation. Use when asked to animate something, add motion, or build a transition. For critiquing existing motion use review-animations; for auditing a whole codebase use improve-animations."
  - target: /home/will/dotfiles/claude/skills-local/animate/SKILL.md
- **Context pointers — pointer wording must accurately name what the body contains**: The document's actual section titled 'Design foundations' (§16) covers the eight principles — Purpose, Agency, Responsibility, Familiarity, Flexibility, Simplicity, Craft, Delight — not 'feedback' and 'spatial consistency'. Spatial consistency is a wholly separate, dedicated section (§7, 'Spatial consistency — symmetric paths, anchored origins') with no connection to §16. The pointer's parenthetical misrepresents the target's own contents, which can misdirect an agent or human deciding whether this is the right document to reach for a spatial-consistency question.
  - quote: "the design foundations (feedback, spatial consistency) behind Apple-style interfaces"
  - proposed fix: Either drop 'spatial consistency' from the design-foundations parenthetical and list it as its own trigger ('spatial consistency (symmetric paths, anchored origins)'), or reword the parenthetical to match §16's actual content, e.g. 'design foundations (purpose, agency, familiarity, simplicity, craft)'.
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **One trigger per branch**: The skill has a single mine-then-build pipeline with no branch that does pattern-analysis without automation-building or vice versa. "analyzing command patterns" and "finding automation opportunities" are two phrasings of the same trigger paid for twice in the always-loaded description.
  - quote: "Use when analyzing command patterns or finding automation opportunities."
  - proposed fix: Collapse to one trigger, e.g. "Use when the user wants to turn repeated shell commands into a script, CLI, alias, or timer."
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Relevance and sediment**: "jsm install-all" is never explained, defined, or referenced anywhere else in the document, and FORK-SYNC.md is absent from the Reference Index where every other reference is consolidated. It reads as stale residue from an unrelated tooling system rather than material that bears on this document's task (mining history, building automations).
  - quote: "<!-- Local fork — see references/FORK-SYNC.md before running `jsm install-all`. -->"
  - proposed fix: Remove the comment if obsolete, or if still needed, explain what `jsm install-all` does and add FORK-SYNC.md as a row in the Reference Index table.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Single source of truth**: This HTML comment restates the document's own headers verbatim. Because it's a comment, it never renders for the human reader, so it buys no navigation benefit for them, while still costing context load on every load for the agent, which already sees each heading as it reads through the file — the same meaning (document structure) stated twice for a zero-value second copy.
  - quote: "<!-- TOC: Core Insight | The Loop | Mine & Cluster | Score | Propose | Build | Validate | Anti-Patterns | References -->"
  - proposed fix: Delete the TOC comment; the actual `##` headers already provide navigation.
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Single source of truth (environment as source of truth)**: Hardcodes a snapshot count that a cheap one-command lookup (`grep -c '^alias' ~/.bashrc`) can answer at run time. Baking the number into the document means it silently goes stale as the user adds or removes aliases, and it isn't a gotcha or unwritten convention worth caching.
  - quote: "`~/.bashrc` (~40 aliases)"
  - proposed fix: Drop the count: "Existing shortcuts (`grep -c '^alias' ~/.bashrc` for current count); the gap = frequent-but-unaliased commands".
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Single source of truth (environment as source of truth)**: States a specific ranked fact about the user's command frequency as fixed prose, even though Step 1's own mining queries (`SELECT command, COUNT(*) ... ORDER BY cnt DESC`) already exist to discover exactly this. The claim will drift as usage changes and duplicates what the document's own tooling is built to determine fresh each run.
  - quote: "Your top commands are `claude`/`pi`/`codex`; the repeated *work* happens inside sessions."
  - proposed fix: Rephrase generically and let the mining step supply the actual answer, e.g. "If your top mined commands are agent CLIs (claude/codex/etc.), the repeated work happens inside sessions, not the shell."
  - target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- **Completion criteria — a bound is checkable when the agent can tell done from not-done without judgment.**: This bound gates a real decision (auto-classify vs. surface to user) but 'confidence' is never defined anywhere in the document. Every other threshold in Phase A is given an explicit formula (`fingerprint_coverage` = found-with-same-signature ÷ total, same-signature ≥ 0.7, file_existence_coverage ≤ 0.5), but 'confidence' has no computation, no inputs, and no worked example — it also reappears undefined as a bare column header in the Phase C variant matrix ('columns for signatures, hunk intent, tests, proposed synthesis, confidence, risks'). The agent can satisfy this gate impressionistically, defeating its purpose as a safety check on auto-classification.
  - quote: "**Confidence < 0.7 ⇒ don't auto-classify; surface to the user.**"
  - proposed fix: Define 'confidence' the same way the other Phase A metrics are defined, e.g. as a function of the number of chain steps that agreed on a verdict (cherry -v, fingerprint_coverage, apply-probe, signature-sampling) versus steps that conflicted or were inconclusive, and give the same formula for the Phase C matrix column.
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **One trigger per branch**: The description enumerates five near-synonymous nouns (brand, sub-brand, product, persona, author voice) as separate triggers, but none of them route to a different path within the document — every one of them lands on the same Build/Extract decision ("How to choose"). Per one-trigger-per-branch, a trigger list should be tested by whether reaching the doc through one phrase takes a different path than another; since it doesn't here, the enumeration is one branch paid for five times in the always-loaded description.
  - quote: "Use when starting a new brand, sub-brand, product, persona, or author voice, when copy sounds generic, or when "how should this sound?" is unclear."
  - proposed fix: Collapse the list to a single phrase that names the branch once, e.g. "Use when defining a new voice (brand, product, or persona) or when existing copy sounds generic and undefined."
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Progressive disclosure**: The "How to choose" step establishes that Extract mode and Build mode are mutually exclusive branches selected by a single question, yet the full step-by-step process for both modes (six-lens analysis for Extract, 17 questions across five batches for Build) is inlined in the same file. Every invocation loads the entirety of the branch it didn't take, violating "inline what every branch needs; disclose what only some branches reach."
  - quote: "- "Yes, I have content I'm proud of" → Extract mode
- "No, I'm starting fresh" → Build mode"
  - proposed fix: Split Mode 1 and Mode 2 into separate reference files (e.g. extract-mode.md, build-mode.md) disclosed by pointer once the branch is chosen, keeping only the shared Voice Profile template and the choice logic in the main SKILL.md.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Completion criteria**: The Quality Test list mixes a checkable criterion ("Mechanically clean: does it pass every Mechanical Rule above?") with judgment-based, unfalsifiable ones ("Recognizable," "Authentic") in the same flat numbered list with a single completion instruction ("If any answer is no..."). An agent applying this list has no way to check "Recognizable" without external human validation, so it will answer impressionistically — the stray uncheckable items let the whole list be satisfied on vibes.
  - quote: "**Recognizable:** could a member of this audience identify this content as "theirs" without a byline?"
  - proposed fix: Separate the checklist into what the agent can verify directly (e.g. "Mechanically clean") and what requires human sign-off (e.g. "Recognizable," "Authentic"), and mark the latter as requiring the user's confirmation rather than the agent's judgment.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Single source of truth**: This criterion in the closing "The Test" section is a near-verbatim restatement of the "Actionable" criterion in the Voice Profile template's "Quality Test" ("could a writer (human or AI) produce on-brand content using only this profile?"). The two lists overlap further ("Mechanical rules are sharp enough to catch violations automatically" vs. "Mechanically clean: does it pass every Mechanical Rule above?"), meaning the same meaning is maintained in two separate checklists that could drift apart.
  - quote: "A second writer (human or AI) can produce content from it that the user accepts on first draft"
  - proposed fix: Merge the two lists or clearly scope each (Quality Test evaluates a draft against the profile; The Test evaluates the profile document itself) and remove the overlapping writer/actionable criterion from one of them.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Single source of truth**: This callout restates, almost clause for clause, the description's procedural summary ('opening the exact URL in the local Windows Brave browser and handing paste-ready click steps, then wiring the reported credentials into Supabase/Vault/Vercel/.env'). The same meaning is written in two places: the always-loaded description and the body's Core pattern block, doubling maintenance cost and token load for no added routing signal.
  - quote: "Open the exact URL in Will's real Windows Brave, hand him
precise paste-ready clicks, get the resulting IDs/secrets back, then wire them
in programmatically."
  - proposed fix: Trim the description to the routing-relevant clause (what blocks it, when to use it) and let the Core pattern callout be the single authoritative statement of the actual workflow, since the description is paid on every turn while the callout is paid only when the skill fires.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Single source of truth (polarity duplication)**: This anti-pattern row restates, in negated form, the rule already given positively twice: in the Core pattern callout ('do not fight it with Playwright... Open the exact URL in Will's real Windows Brave') and in the Problem section's ASCII diagram (Playwright fails on OAuth consent, real Brave works). It's the same meaning written a third time.
  - quote: "| Playwright/xvfb for OAuth consent | Bot detection + cannot do 2FA | Real Brave handoff |"
  - proposed fix: Delete this row — the Core pattern callout and Problem diagram already establish 'don't use Playwright, use real Brave.' If the anti-patterns table is kept, reserve it for failure modes not already covered elsewhere.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Progressive disclosure**: This is dense, highly specific reference material (stall phases, memory ceilings, a multi-env-var repair invocation) for a rare edge case — a corrupted lexical index — not something every invocation of cass-rerank needs. Inlining it among the normal-use steps means it loads into context on every skill fire even for the common path (a plain successful search), rather than only when the 'no results' branch is actually hit.
  - quote: "**`cass index --full` will not fix it on a large archive** — on a ~17 GB / 22k-conversation DB it stalls in phase `preparing` with the rebuild pipeline never engaging (`is_rebuilding: false`, all queues 0) while RSS climbs to ~12 GB, then dies. Two `stall_detected` events are emitted."
  - proposed fix: Move the entire 'If it returns "no results" for everything' section into a separate disclosed file (e.g. cass-repair.md) and replace it in the body with a one-line pointer keyed to the trigger condition: "If cass-rerank returns no results for everything, see cass-repair.md — likely a broken lexical index, not zero matches."
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Relevance and sediment**: This describes an architecture that the sentence itself says no longer exists. It never bears on the agent's task of running cass-rerank searches, and is stale history left in the always-loaded body — a clear case of sediment accumulating because removing it felt riskier than leaving it.
  - quote: "wm -> ai-gateway:18000 -> mac-studio tunnel chain is retired."
  - proposed fix: Delete the retired-architecture history from the comment. If the pairing/source-location note is still needed for human maintainers, keep only the current facts (wrapper path, that it routes through ai-gateway's local-rerank lane) and drop the retired-chain sentence entirely.
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **One trigger per branch**: These three parenthetical examples all route to the same branch — top-1/top-few retrieval via cass-rerank — and none of them causes a different path than the others. Per the doctrine's test, phrases that don't change the routing outcome should collapse into one; listing three synonymous examples spends extra always-loaded tokens for no added routing signal.
  - quote: "(past fixes, decisions, "how did I do X")"
  - proposed fix: Collapse to a single example, e.g. "(e.g., 'how did I fix X')", removing the redundant 'past fixes' and 'decisions' variants.
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Leading words — a leading word anchors by consistent repetition of the same token; a made-up identifier only works if it stays consistent**: The tie-breaking axiom is labeled `①` ("**① First-try inevitability.**") everywhere else in the kernel, but the tie-breaker sentence calls it "Axiom 0" — a different token for the same referent. This splits the anchor: a reader (or an agent citing 'Axiom 0' back at the doc) can't tell whether it names the same axiom as `①` or a separate, undocumented axiom preceding it.
  - quote: "**Axiom 0 wins ties.**"
  - proposed fix: Use the same identifier consistently, e.g. "① wins ties" or rename the bullet "Axiom 0 — First-try inevitability" so the numeral and the prose reference match.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Completion criteria — a bound is checkable only when the agent can tell done from not-done without judgment**: "the project's floor" is never defined anywhere in the document — no threshold, score, or reference is given for what counts as clearing it. An agent following this iterate step has no checkable way to know when to stop iterating; it must guess at an undefined bound.
  - quote: "repeat until every FM clears the project's floor on each, then re-mine failure modes on the next material code change"
  - proposed fix: Replace with a concrete, checkable bound, e.g. 'repeat until every FM scores at or above the project's stated minimum (define this once, e.g. ≥3/5) on each of the 10 dimensions.'
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Context pointers — cut identity the body already states; the pointer's job is when to reach, not what it is**: This always-loaded frontmatter description spends most of its length restating identity facts the body already establishes in detail — idempotence (Safety envelope), reversibility (Safety envelope, undo), the mutate() chokepoint (its own section), and machine-readable output (CLI surface's --json/--robot) — rather than encoding when to reach for the skill. That's permanent per-turn context load carrying no additional routing signal.
  - quote: "Add or upgrade a CLI doctor subcommand that is idempotent, reversible, and backup-aware (fixes via one mutate() chokepoint), with machine-readable health output for agent callers."
  - proposed fix: Trim the description to the trigger only, e.g. 'Use when adding or upgrading a doctor/health/repair CLI subcommand meant to be invoked non-interactively by an AI agent (no TTY, no human).' and let the body carry the idempotent/reversible/mutate()/JSON details it already states.
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Completion criteria — contradicting bounds**: The prose instructs varying the effort flag by situation (medium/high/xhigh), but the worked bash example a few lines below hardcodes `-c model_reasoning_effort="high"` with no instruction to substitute the value chosen from the bullet above. The agent has no checkable signal for whether it must edit the literal command or may run it as shown, so a security-audit or quick-sanity-check invocation could silently run at the wrong effort level.
  - quote: "Effort: **`high`** by default. Bump to **`xhigh`** for architecture, security
   audits, or hard algorithm/concurrency questions. Drop to `medium` for quick
   sanity checks."
  - proposed fix: Replace the literal `"high"` in the command with a placeholder like `"$EFFORT"` and add a line telling the agent to set that value first, e.g. 'Set EFFORT to medium/high/xhigh per the guidance above, then run:'.
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Completion criteria — checkable step artifact**: Step 2's command reads the prompt from `$CLAUDE_JOB_DIR/tmp/codex-consult.md`, but step 1 ('Assemble a self-contained prompt') never instructs the agent to write the assembled text to that exact path. Step 1's completion condition is satisfied once the prompt content is composed, without any signal that it must also be persisted to this specific file — so an agent following the steps literally can complete step 1 and then hit a missing-file error on step 2.
  - quote: "Pipe the prompt via stdin to avoid quoting hell:

   ```bash
   env -u OPENAI_API_KEY codex exec -s read-only --skip-git-repo-check \
     -c model_reasoning_effort="high" - < "$CLAUDE_JOB_DIR/tmp/codex-consult.md"
   ```"
  - proposed fix: Add an explicit sub-step to step 1: 'Write the assembled prompt to $CLAUDE_JOB_DIR/tmp/codex-consult.md' so the completion condition matches what step 2 actually consumes.
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Leading words — undefined coined terms**: "circuit breaker", "PreToolUse doghouse guard", and "caam activate codex <profile>" are project-specific coined terms used without any definition or pointer to where they're explained. An agent with no other context cannot tell what triggers this state, what `<profile>` should be, or what 'fall back' concretely means, so the instruction 'Respect it' gives no actionable path.
  - quote: "If the circuit breaker is open, the PreToolUse doghouse guard will block this
   and tell you to fall back or `caam activate codex <profile>`. Respect it."
  - proposed fix: Either define these terms inline in one sentence (what the circuit breaker/doghouse guard is and does) or add a pointer to the doc that explains them and lists valid `<profile>` values.
  - target: /home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md
- **Pruning and drift — anti-pattern list duplication (polarity)**: Six of the nine anti-pattern items restate, negated, rules the document already gives positively elsewhere: 'Skipping checksum verification' mirrors non-negotiable #7; '`gnu` target on Linux' mirrors #4 and the musl comment on the platform-detection snippet; '`flock` as your only lock' mirrors #6 and the Atomic lock section; 'Hard-failing on optional features' mirrors #8 and the checksum/Sigstore snippet's 'missing tool = warn+continue' comment; 'Raw unstyled output' mirrors the output-stack snippet's NO_COLOR/non-TTY handling; 'Ignoring proxy env' mirrors #3 and the Proxy array snippet. The doctrine names this exact failure mode: 'an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror.' This inflates the list's apparent weight and adds maintenance/token cost without new information.
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
  - proposed fix: Cut anti-pattern items that only negate an already-stated non-negotiable or snippet comment (checksum, musl/gnu, flock-only, hard-fail-on-optional, unstyled-output, ignoring-proxy). Keep only items carrying information not stated positively elsewhere, e.g. the `--version`-timeout item, and the PATH/backup items if they add detail (the check method, the sed/awk prohibition) the positive statements don't already cover.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Completion criteria — contradictory bounds**: Non-negotiable #7 states the checksum step is skipped 'only on explicit --no-verify', but `verify_checksum()` silently skips verification (warn + return 0, treated as success) whenever neither `sha256sum` nor `shasum` is found, with no `--no-verify` flag involved. This is the doctrine's 'general ceiling in one place, specific range crossing it in another' pattern: the agent implementing this skill cannot tell whether the stated invariant ('skip only on explicit --no-verify') or the code's actual behavior (silent skip on missing tool) is the real rule, and the gap undermines the document's own core principle that the installer must 'verify what it downloads.'
  - quote: "else warn "no SHA256 tool; skipping checksum"; return 0; fi"
  - proposed fix: Either update non-negotiable #7 to state both skip conditions ('skip on explicit --no-verify, or with a loud warning if no SHA256 tool is available'), or change the code to hard-fail when no hashing tool exists so behavior matches the stated 'skip only on explicit --no-verify' invariant.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Single source of truth [craft]**: The full convergence definition (≥10 rounds, 2 consecutive quiet rounds, every-hypothesis-resolved) is stated in complete, near-identical form three times: this Quick-Start block, the ABORT IF bullet ('the ≥10-round convergence floor is optional. It isn't...'), and the dedicated 'Convergence (non-negotiable)' section that already exists and links out to references/CONVERGENCE.md. Each copy is a separate place the numbers must be kept in sync if the criteria ever change, and each pays token cost on every load of this always-loaded Quick-Start summary.
  - quote: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings"
  - proposed fix: Keep the full definition only in the dedicated Convergence section; replace the Quick-Start and ABORT IF copies with a one-line pointer, e.g. 'Convergence floor is non-negotiable — see Convergence section.'
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Single source of truth [craft]**: This ABORT IF bullet restates, almost verbatim, the B10 taxonomy entry: 'Generated file | bindgen/protobuf/parser tables/`@generated` — exclude or fix the generator; NEVER hand-split.' The rule (never hand-split generated files, fix the generator instead) is the same meaning in two authoritative-sounding places, costing a maintenance edit in two spots if the rule ever changes.
  - quote: "generated files are excluded or fixed at the generator, **never hand-split**"
  - proposed fix: Keep the full rule only in the Monolith Taxonomy B10 entry; have the ABORT IF bullet just point to it, e.g. '⚠ You're about to split a generated file — see Taxonomy B10, never hand-split.'
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Completion criteria (a general ceiling contradicted by a specific range that crosses it is a completion defect)**: The duration table permits modals/drawers up to 500ms, but the very next rule states '**Rule: UI animations should stay under 300ms.**' with no exemption for modals. The agent cannot tell whether a 400ms modal transition complies: the table says yes, the rule says no. This mirrors the doctrine's example of a general ceiling in one place contradicted by a specific range crossing it in another.
  - quote: "| Modals, drawers          | 200-500ms     |"
  - proposed fix: Either cap the modals/drawers row at 300ms (e.g. '200-300ms') to match the stated rule, or explicitly exempt modals/drawers from the under-300ms rule the way marketing/explanatory animations already are ('Can be longer').
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth (duplication — the same meaning repeated in more than one place costs maintenance and tokens)**: This exact `.button` / `.button:active { transform: scale(0.97) }` CSS block is copy-pasted verbatim from the earlier 'Buttons must feel responsive' section into the 'Use blur to mask imperfect transitions' section, restating the same rule (button press feedback) twice rather than referencing it once.
  - quote: ".button {
  transition: transform 160ms ease-out;
}

.button:active {
  transform: scale(0.97);
}

.button-content {
  transition: filter 200ms ease, opacity 200ms ease;
}"
  - proposed fix: Drop the repeated `.button`/`.button:active` rule from the blur example and show only the new `.button-content` blur addition, with a short reference back to 'Buttons must feel responsive' for the press-feedback styling.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Single source of truth (duplication — same meaning inflated in rank by appearing twice instead of once)**: The Review Checklist restates content already given verbatim in the Review Format example table (`transition: all 300ms` → `transition: transform 200ms ease-out`) and in the Performance Rules section ('Only animate transform and opacity'). Other rows in the same checklist (e.g. the ease-in and popover rows) correctly avoid this by pointing back ('see ... above'), showing the duplication here is avoidable inconsistency rather than necessary restatement.
  - quote: "| `transition: all`                          | Specify exact properties: `transition: transform 200ms ease-out` |"
  - proposed fix: Replace the inline restatement with a backreference, consistent with the other checklist rows, e.g. 'transition: all' → 'See "Only animate transform and opacity" above'.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Completion criteria [craft] — "Two bounds that contradict — a general ceiling in one place, a specific range crossing it in another — are a completion defect... the agent cannot tell whether a value between them complies, whichever bound it obeys."**: Gate question 3 states a hard, universal ceiling of 300ms that 'every candidate must survive.' But the budget table two lines later lists 'Modals, drawers | 200–500ms,' and the Hunt section's own recipes exceed it further: the hold-to-confirm recipe specifies '2s linear on press,' and the gesture-seam springs specify 'duration: 0.5' (500ms). None of these are flagged as exceptions the way 'Marketing / explanatory | Can be longer' is. An agent gating a modal or hold-to-confirm candidate against the stated 300ms ceiling cannot tell whether the recipe the document itself recommends actually passes the Gate.
  - quote: "The suggestion must work within the standard budgets (UI under 300ms):"
  - proposed fix: Either scope the ceiling explicitly (e.g., 'entrances/exits under 300ms; deliberate holds and spring physics are exempt') or raise the stated ceiling to cover the modal/drawer range, and mark the hold-to-confirm and spring durations as explicit exceptions the same way marketing/explanatory is marked.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md
- **Single source of truth / duplication [craft] — "keep each meaning in one authoritative place... Duplication, the same meaning in more than one place, costs maintenance and tokens."**: The intro paragraph already states this exact scope boundary — 'It does not review existing animations (that's `review-animations`), audit and plan fixes for them (that's `improve-animations`), or write the implementation itself' — before Hard Rule 1 restates the same meaning ('Never modify source code. This skill reports; it does not implement.'). The restriction on implementing is now defined in two places, so a future edit (e.g., adding an implementation exception) risks updating one and missing the other.
  - quote: "This skill reports; it does not implement."
  - proposed fix: State the no-implementation boundary once. Keep the full explanation with sibling-skill pointers in the intro, and let Hard Rule 1 just say '1. Never modify source code — hand off instead: `ce-plan`... or `animate`...' without re-deriving why.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Pruning and drift — duplication (anti-pattern list restating positive rules)** — quote_not_found: Most rows of the "Never Ship" table are the same meaning already given positively earlier in the document (scale(0) is banned in step 4, ease-in is banned in step 5, the 100+/day gate is step 1's whole table, keyframes-on-rapid-elements is step 6, width/height animation and transform-origin:center are step 4, x/y/scale props are step 4, ungated hover and missing reduced-motion are step 7). The doctrine names this exact pattern — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice" — as a duplication defect, not a legitimate self-check.
  - quote: "| `transform: scale(0)` entrance | `scale(0.95)` + `opacity: 0` |
| `ease-in` on a UI element | `ease-out` or a strong custom curve |
| Animation on a keyboard shortcut or 100+/day action | No animation |"
- **Completion criteria — contradictory bounds** — verifier: This general ceiling directly contradicts the duration table above it, which gives modals/drawers a specific range of 200–500ms — a range that crosses the 300ms ceiling. Read at the point it's stated, the agent cannot tell whether a 350ms modal transition complies: the specific table says yes, the bold ceiling says no. The exception ("outside modals/drawers or marketing/onboarding") only appears later, in the separate Never Ship table, not alongside the claim itself.
  - quote: "**UI animations stay under 300ms.** A 180ms dropdown feels more responsive than a 400ms one."
- **Context pointers — one trigger per branch** — verifier: Because this skill is a single undisclosed body (no sub-file pointers), every trigger phrase resolves to the identical full-document load. 'gesture-driven UI', 'spring animations', 'drag/swipe/sheet interactions', and 'momentum and interruptible transitions' all route to the same cluster of sections (§1–§6, §10–§11) — a run reached via any one of these phrases takes the exact same path as a run reached via the others. Per the doctrine's test ('does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it? If not, collapse them'), these are one branch paid for four times.
  - quote: "Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency) behind Apple-style interfaces."
- **Completion criteria** — verifier: This gives no checkable bound — 'the perception threshold' names no number, unlike every sibling rule in the same section and document (which specify exact damping/response values, px hysteresis, 0.998 deceleration constants, -0.02em tracking, etc.). An agent cannot tell whether a given per-frame delta complies without external judgment.
  - quote: "Keep the per-frame positional change below the perception threshold to avoid strobing."
- **Single source of truth / duplication** — verifier: The Quick Reference table restates numeric values already given in full in §4's damping/response table, §5's velocity-normalization formula, §6's projection formula, and §15's tracking values. Since the whole document loads as one unit, these facts are already in context by the time the table is reached — the table is a second authoritative-looking place for the same numbers, creating a two-place edit burden (changing a default in §4 requires remembering to update the table too) without adding new routing or execution signal.
  - quote: "| Default UI spring | Critically damped, no overshoot | `damping 1.0`, `response 0.3–0.4` |"
- **Splitting by invocation** — verifier: Typography is a genuinely distinct branch — §15's content (tracking, leading, Dynamic Type) shares no material with the motion-physics, materials/translucency, haptics, or eight-principles sections. Per the doctrine, a distinct trigger word should fire its material on its own rather than riding along inside one ~350-line monolithic body. As written, any invocation for a typography-only question pays the full context cost of loading springs, velocity handoff, rubber-banding, haptics, translucency, and the eight design principles alongside it.
  - quote: "typography (optical sizing, tracking, leading)"
- **Single source of truth (duplication via polarity)** — verifier: This anti-pattern is the negated restatement of a rule the document already gives positively in at least two other places: "These are bright-line rules. Violations should be auto-corrected" (Mechanical Rules section) and "The mechanical rules from Q16 become the enforceability backbone" (Build mode synthesis), plus the template's own "mechanical rules are gold" note. The same meaning — mechanical rules keep the voice enforceable — is now encoded a third time, negated, inflating its apparent importance and creating three places to keep in sync.
  - quote: "**The Unenforceable Voice:** all vibes, no mechanical rules. Result: voice drifts within weeks."
- **One trigger per branch** — verifier: The description lists 'bot detection' and 'OAuth consent screens' as two separate triggers, but the parenthetical example given for bot detection ('Google's "browser may not be secure"') is, per the Problem section's own diagram, exactly the OAuth consent flow. A run reaching this skill via 'OAuth consent screen blocked' and one reaching it via 'bot detection message on Google console' take the same path — it's one branch named twice, not two.
  - quote: "bot detection (Google's "browser may not be secure"), 2FA,
  CAPTCHA, or OAuth consent screens."
- **Single source of truth (polarity duplication)** — verifier: This row negates a rule already stated positively in the Critical rules bullet: 'Include FULL URLs with query params (`?project=xyz`) and open them in Brave.' Same meaning, two places.
  - quote: "| Assume Will knows the IDs | He needs them inline | `project=my-project-123` |"
- **Completion criteria** — verifier: 'Clear' is a judgment call, not a checkable condition — the agent can't tell done from not-done without guessing what counts as clear. It sits inside an otherwise checkable checklist ('All identifiers included', 'Programmatic wire-in commands ready'), so this one uncheckable qualifier lets the whole item be satisfied impressionistically.
  - quote: "- [ ] Clear "report back" format"
- **Pruning and drift — duplication disguised as polarity ("an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice")** — verifier: This anti-pattern is the same meaning as the 'Ambition gate' step already states positively: "ship ≥5 substantive changes across ≥3 dimensions before calling it done. A scorecard alone is not a deliverable." The doctrine specifically calls out this pattern — an anti-pattern list negating a rule already given positively elsewhere — as the commonest disguise of duplication, costing tokens and maintenance without adding information.
  - quote: "**A polite scorecard with no applied fixes** (when improvement was asked for). Ship changes, not a report."
- **Pruning and drift — duplication disguised as polarity** — verifier: This restates, in negated form, what the document already states positively twice: "Ship a **stack** as one coherent commit" (Named operators section) and "**Apply on the current branch** — ship the operator *stacks* above, one coherent commit per stack" (loop step 5). Same meaning appears a third time here as a negated anti-pattern.
  - quote: "**Fixing one flag's error in isolation** — apply the operator stack so the whole surface class improves together."
- **Completion criteria — two bounds that contradict leave the agent unable to tell which one it must satisfy** — verifier: The actual procedure (loop step 4) defines prioritization with two factors, while the '11 dimensions' section gives a different formula with three factors: "priority = frequency × score_gap × blast_radius". An agent following the loop has no instruction to weigh blast_radius at all, while the other section implies it's part of the ranking; the two are never reconciled, so it's unclear whether blast_radius is required or optional in practice.
  - quote: "**Prioritize** — rank by (how often an agent hits it) × (how bad the gap is); pick the top-leverage batch."
- **Pruning and drift — duplication disguised as polarity (an anti-pattern list restating, negated, rules the document already gives positively is the same meaning written twice; audit such lists against the rules they mirror)** — verifier: Every line in this Anti-patterns section is the negated restatement of a rule the document already gives positively elsewhere: fix-then-detect vs. 'Detect-then-fix, never fix-then-detect' and the mutate() chokepoint description; reformatted backups vs. 'Backups are verbatim. No reformatting...'; DeletePath/rm -rf vs. 'The Op enum has NO DeletePath' and 'Never rm -rf, git reset --hard, or DROP TABLE'; random/ad-hoc ids vs. the content-derived-id rule and the additive-only exit-code dictionary; cross-FS rename vs. the identical caveat already in the mutate() step 6 note. This inflates the section's apparent importance and its token/maintenance cost without adding new meaning.
  - quote: "- **Fix-then-detect**, or any disk write that bypasses `mutate()`. Grep the doctor module for writes not routed through it.
- **Backups that reformat / "tidy while fixing"** — breaks byte-for-byte reversibility silently.
- **`DeletePath` / `rm -rf` / `git reset --hard` / `DROP TABLE`** under `--fix` — rename-to-quarantine instead.
- **Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default** — all break the agent contract.
- **Cross-filesystem rename** as the "atomic" write — it isn't; keep the temp file on the target's FS."
- **One trigger per branch** — verifier: The two sentences name the same single branch — 'writing a curl|bash installer for a CLI' — twice in near-synonymous phrasing ('curl | bash installer for a CLI tool' vs 'curl-pipe-bash install.sh one-liner for a CLI'). Applying the doctrine's own test — does a run reaching the document through one phrase take a different path than through the other? — the answer is no, so per 'synonyms that rename a single branch are one branch written twice,' this pays always-loaded context load twice for one routing decision.
  - quote: "Write a production-grade `curl | bash` installer for a CLI tool. Use when writing a curl-pipe-bash install.sh one-liner for a CLI (Rust/TS/Go)."
- **One trigger per branch [craft]** — verifier: Four triggers map to only two branches the document actually distinguishes (Quick mode for a single file vs. Standard mode for a repo-wide run): 'de-monolithize' and 'modularize repo' both route to the generic repo-wide branch, while 'split giant file' and 'file too big' both route to the single-file Quick branch. Per the recipe-selector table, a run reaching the skill through either member of a pair takes the identical path, so each pair is one trigger paid for twice on every load of this always-loaded description.
  - quote: "Use when de-monolithize, split
  giant file, modularize repo, or file too big."
- **Single source of truth / duplication disguised as polarity [craft]** — verifier: This Anti-Patterns row restates, in negated form, the same rule already given positively twice elsewhere: the Isomorphism Contract ('every existing import path still resolves', API diff EMPTY/additions-only) and the ⊙ FAÇADE operator card ('Re-export shim preserving every import path; API diff must stay empty' — near-verbatim phrase repeated). The doctrine specifically calls out auditing anti-pattern lists for this exact mirroring.
  - quote: "Deep-import consumers, tests, and pickles disagree; API diff must stay empty"
- **Single source of truth / duplication disguised as polarity [craft]** — verifier: The phrase 'one mechanical move per commit' is stated as positive migration guidance in the Decomposition Design section ('one mechanical move per commit (`git mv`-friendly, blame-preserving)') and then restated verbatim as the rationale for this negated Anti-Patterns row — the same meaning written twice under the doctrine's polarity-disguised-duplication pattern.
  - quote: "Kills `git blame` and reviewability; one mechanical move per commit"
