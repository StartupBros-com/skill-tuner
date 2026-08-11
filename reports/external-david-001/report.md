# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 8 trial(s), $2.0163 spent
- verify: 105 trial(s), $1.4875 spent

## Run manifest

- run: `external-david-001` (2026-08-11T05:19:53Z → 2026-08-11T05:46:29Z)
- claude CLI: `2.1.224` | skill-tuner: `0.8.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `107b31c2034d` | worktree @ 9a91f44d4a9f |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/skill-authoring/effective-agent-skills/SKILL.md` | `a8d1f3be30ee` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/cmux/SKILL.md` | `b1958377f39a` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/browser-harness/SKILL.md` | `ab0ed9c1d815` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md` | `45939291c42b` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/ops-and-setup/prod-push/SKILL.md` | `54e1c1b6b294` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/ops-and-setup/global-agent-guardrails/SKILL.md` | `07341ee9ac33` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/thinking-and-docs/teach/SKILL.md` | `7a210e5caf9e` | worktree @ 081d4d52cddb |
| target | `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/deepapi/SKILL.md` | `827a9e2a97c0` | worktree @ 081d4d52cddb |

## Marginal-value probe verdict

**findings_confirmed: 21**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- targets: 8
- probe calls: 8
- verify calls: 105 (3 skeptic(s) per finding)
- refuted: 14

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/skill-authoring/effective-agent-skills/SKILL.md` | 3 | 4 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/cmux/SKILL.md` | 4 | 1 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/browser-harness/SKILL.md` | 3 | 1 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md` | 5 | 2 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/ops-and-setup/prod-push/SKILL.md` | 0 | 4 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/ops-and-setup/global-agent-guardrails/SKILL.md` | 2 | 0 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/thinking-and-docs/teach/SKILL.md` | 2 | 1 |
| `/home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/deepapi/SKILL.md` | 2 | 1 |

### Confirmed findings

- **Single source of truth / Duplication [craft]**: This exact meaning is stated four separate times across the document: §6 ('One skill = one capability or one discipline. Resist bundling concerns into "the X workflow."'), §7 ('If one skill does design + planning + implementation + testing + deployment, you've built a framework, not a skill. Split it.'), here in §10, and again in §13 ('One skill, one concern. Composition beats bundling.'). None is designated authoritative, so changing this rule requires a four-place edit.
  - quote: "**One skill = one concern.** Resist bundling."
  - proposed fix: State the rule once (e.g. in §6), and in §7/§10/§13 either drop it or replace with a one-line cross-reference to the single statement.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/skill-authoring/effective-agent-skills/SKILL.md
- **Duplication [craft]**: This is near-verbatim duplicated by the §11 'Security checklist' ('Audit `scripts/` for outbound network calls, file access outside expected scope, command execution', 'Verify the skill name isn't typosquatting a popular one', 'Run in a sandboxed environment first'). Same meaning, two authoritative-looking locations.
  - quote: "Audit `scripts/` for unexpected network calls, file access outside expected scope, or hidden instructions in references. Watch for typosquatted skill names. Sandbox execution environments."
  - proposed fix: Keep the checklist form in §11 as the single source of truth and replace the §7 anti-pattern body with a pointer to it, e.g. 'Don't trust unfamiliar skills — see the Security checklist (§11) before installing.'
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/skill-authoring/effective-agent-skills/SKILL.md
- **Negation [research]**: This anti-pattern is pure prohibition — it lists three banned filenames and never states what should be in the folder instead. The doctrine requires a prohibition to stand paired with its positive target so attention lands on what to do, not just what's forbidden.
  - quote: "No README.md, no CHANGELOG.md, no INSTALLATION_GUIDE.md inside the skill folder. Skills are for agents."
  - proposed fix: Pair it with the positive target, e.g. 'Keep the skill folder scoped to SKILL.md, scripts/, references/, and assets/ — agent-facing content only, not README.md, CHANGELOG.md, or INSTALLATION_GUIDE.md.'
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/skill-authoring/effective-agent-skills/SKILL.md
- **Cut identity the body already states [craft]**: This restates the identity claim the body's own opening paragraph already makes ('cmux is a native macOS terminal app for running multiple AI coding agents in parallel. It exposes a CLI (`cmux`) and a Unix-socket JSON-RPC API...'). The pointer's job is when to reach the material, not what it is, so this clause adds permanent context load on every turn without adding routing signal.
  - quote: "Control the cmux macOS terminal app (CLI + socket API) — cmux workspaces, panes, surfaces, browser automation, notifications, settings, hooks."
  - proposed fix: Drop the identity clause from the description and keep only the triggering conditions, e.g. 'MUST be read before running any `cmux` command. Trigger ONLY when the user explicitly says "cmux"...' — let the body's opening paragraph be the sole place identity is stated.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/cmux/SKILL.md
- **Single source of truth [craft]**: This is the identical rule already stated verbatim earlier in the document ('**Always anchor automation to `CMUX_WORKSPACE_ID`** — the visually focused workspace may not be the agent's caller workspace.' under Detect cmux in a Shell). Keeping the same meaning in two places means both copies must be edited in sync or they drift.
  - quote: "1. **Anchor to `CMUX_WORKSPACE_ID`.** Never assume the visually focused workspace is the target."
  - proposed fix: State the anchoring rule once (in Critical Rules, where it belongs alongside the other non-disruptive-automation rules) and replace the earlier occurrence with a short forward reference, or vice versa.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/cmux/SKILL.md
- **Single source of truth — environment is a source of truth too [craft]**: This caches the live value of a `cmux.json` setting that is a cheap one-command lookup (`cmux settings cmux-json`). Config state is exactly the kind of fact that changes independently of the doc and will go stale; the doctrine reserves caching for what can't be looked up (unwritten conventions, gotchas), not for a value the environment already holds authoritatively.
  - quote: "The user keeps BOTH off (set 18-07-2026) — don't re-enable."
  - proposed fix: Drop the dated snapshot of the toggle values. If the intent is 'don't flip these without asking,' state that as the durable rule and have the agent check current values via `cmux settings cmux-json` when it matters, rather than embedding a point-in-time state.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/cmux/SKILL.md
- **Single source of truth [craft]**: This restates the same meaning already given in full in the Socket API section ('If you hit `Failed to connect to socket`, you're likely an external process under `cmuxOnly` — switch mode in Settings > Automation or run from inside a cmux terminal.'). Two authoritative copies of the same fix cost tokens and maintenance for no new information.
  - quote: "**Pi/Pi-like socket connection failures from external processes** → default `cmuxOnly` mode; either run inside a cmux terminal or change socket mode."
  - proposed fix: Remove the Common Pitfalls line and instead point back to the Socket API section, e.g. 'Socket connection failures from external processes — see Access modes above.'
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/cmux/SKILL.md
- **Pruning and drift — Single source of truth / duplication**: The entire '## Hermes Agent integration' section, including the frontmatter-pitfall note and the Brave Browser note, appears twice in the document, word-for-word except for one trailing clause in the frontmatter warning. This is the same meaning stated in two places, doubling both token cost and the maintenance burden of keeping the two copies in sync.
  - quote: "## Hermes Agent integration

Installed at `~/Developer/browser-harness` as editable `uv tool install -e .`. Binary at `~/.local/bin/browser-harness`. Skill at `~/.hermes/skills/browser-harness/`."
  - proposed fix: Delete the second occurrence of the '## Hermes Agent integration' section entirely and keep only the first.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/browser-harness/SKILL.md
- **Pruning and drift — Single source of truth / duplication**: The 'Authenticated content extraction (proven pattern)' section — including the full code block and its four bullet caveats — is restated a second time later in the document with only cosmetic wording changes (e.g. 'their active sessions' → 'active sessions', dropped 'e.g.'). The same pattern is then condensed a third time as the 'Login-walled content extraction' bullet in the Gotchas section. Three copies of one meaning inflate the document and create three places to update if the pattern changes.
  - quote: "## Authenticated content extraction (proven pattern)

browser-harness connects to the user's real browser with active sessions — ideal for login-walled sites where `web_extract` or Hermes's built-in `browser_navigate` fail (X/Twitter articles, LinkedIn, paywalled sites)."
  - proposed fix: Keep a single authoritative version of the extraction pattern (with its code block) in one place, and reduce the Gotchas bullet to a one-line pointer to that section rather than a re-explanation.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/browser-harness/SKILL.md
- **Steps, completion, and demand**: The same instruction is stated twice with different demand strength: near the top it requires reading 'every file' in the matching directory, while the 'Domain skills (opt-in)' section at the bottom restates it as "search `agent-workspace/domain-skills/<host>/` before inventing an approach" — a softer, less checkable verb that lets the agent satisfy the rule by skimming rather than reading every file. The two versions also disagree on the placeholder name (`<site>` vs `<host>`), leaving it unclear which bound governs.
  - quote: "read every file in the matching `agent-workspace/domain-skills/<site>/` directory before inventing an approach"
  - proposed fix: State the instruction once, with one verb and one placeholder name, e.g. keep 'read every file in agent-workspace/domain-skills/<site>/ before inventing an approach' as the single authoritative statement and remove the reworded restatement in the bottom section.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/browser-harness/SKILL.md
- **Negation [research] — prohibition steers by naming the forbidden behaviour, and even a hard guardrail must pair with its positive target so attention lands on what to do.**: This literal string is meant to be pasted into the downstream agent's goal contract. It leads with the ban and names the exact reward-hacking moves (delete, skip, weaken, narrow) without ever stating the positive target, which the doctrine says makes the banned behaviours more available, not less.
  - quote: "Do not delete, skip, weaken, or narrow tests to make the goal pass."
  - proposed fix: Pair the ban with a positive instruction, e.g. "Keep the existing test suite intact; add new tests only to cover new behavior. Do not delete, skip, weaken, or narrow existing tests to make the goal pass."
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md
- **Completion criteria [craft] — two bounds that contradict leave the agent unable to tell which specification is authoritative.**: The document defines and repeatedly uses a 5-part contract ("## The 5-part contract (every goal needs this)": Objective, Constraints, Validation command, Stop condition, Documentation), but the meta-prompting section instructs the second AI session to use a '4-part contract,' contradicting the count established earlier with no indication of which one governs.
  - quote: "emit a structured `/goal` markdown block using the 4-part contract"
  - proposed fix: Change '4-part contract' to '5-part contract' to match the section it's defined in, or explicitly name which item is dropped and why.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md
- **Single source of truth [craft] — keep each meaning in one authoritative place; restating it elsewhere is duplication that costs a second edit whenever the rule changes.**: This restates, almost verbatim, item 5 of "The 5-part contract" ('Documentation — one sentence instructing the agent to write concise, targeted docs for every change, either creating new .md files or updating existing ones') and the template's `**Document:**` line. The same meaning is stated three times, so a future change to the documentation rule requires three edits instead of one.
  - quote: "**Documentation is mandatory.** Every `/goal` prompt must include a single sentence committing the agent to concise, targeted docs — new `.md` files or focused updates to existing docs."
  - proposed fix: Delete the redundant 'Documentation is mandatory' bullet from Writing rules and rely on the 5-part contract definition as the single source; if emphasis is needed, cross-reference it instead of restating it.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md
- **Context pointers [craft] — 'Cut identity the body already states': a pointer restating what the body already says about itself adds permanent context load for no routing signal.**: This identity information is restated almost word-for-word in the body twice: '`/goal` is a slash command that turns an agent prompt into a **persistent agent** looping `plan → act → test → review → iterate`...' and 'Agents with the `/goal` feature right now: **Codex, Claude Code, and Hermes Agent**.' The always-loaded description pays permanent context load to say what the body already states, with no added routing signal.
  - quote: "the persistent self-checking agent loop (plan → act → test → review → iterate), available in agents like Codex, Claude Code, and Hermes Agent"
  - proposed fix: Trim the description to only the routing triggers, e.g. "Use when the user mentions `/goal`, 'goal loop', or 'Ralph loop', wants to kick off a long-running autonomous agent run, asks how to write a goal prompt, or wants a goal instruction drafted." and let the body carry the identity/agent-list detail.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md
- **Single source of truth [craft] — the same meaning stated in more than one place costs maintenance and inflates its rank on the ladder.**: The list of supported agents ('Codex, Claude Code, and Hermes Agent') is stated a third time here, having already appeared in the description and in 'What `/goal` is'. Adding or removing a supported agent now requires three synchronized edits instead of one.
  - quote: "An agent with the `/goal` feature — right now: Codex, Claude Code, or Hermes Agent"
  - proposed fix: State the supported-agent list once (in 'What `/goal` is') and have the Requirements section reference it, e.g. 'An agent with the `/goal` feature (see above)'.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/agent-orchestration/goal-loop/SKILL.md
- **One trigger per branch [craft]**: These four phrases are near-synonyms for the same branch — a user mentioning any of them wants the same thing (general info about this guard), and none routes to a different path than the others. Per the doctrine's test ('does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it?'), these should collapse into one trigger instead of paying always-loaded context four times over.
  - quote: "or when the user mentions command guard, guardrails, dangerous command hook, or PreToolUse safety."
  - proposed fix: Collapse to a single trigger, e.g. '...or when the user mentions this command guard or PreToolUse safety.'
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/ops-and-setup/global-agent-guardrails/SKILL.md
- **Cut identity the body already states [craft]**: The pointer restates identity the body already states: the body's opening line ('A "bouncer" that blocks catastrophic shell commands before any AI agent runs them') covers the same 'what this is' ground, and the full nine-agent roster is repeated verbatim in the Per-agent wiring table. The parenthetical command list and full agent enumeration add permanent context load (this description is always loaded) without adding routing signal beyond 'catastrophic commands, all agents.'
  - quote: "One shared denylist of catastrophic shell commands (rm -rf on / or ~, dd/mkfs, sudo rm, fork bombs, curl|sh, git push --force, gh repo delete) enforced as a PreToolUse/pre-exec guard across every AI coding agent on the machine — Cursor, Claude Code, Codex, OpenCode, Pi, Hermes, Grok, Droid, Devin."
  - proposed fix: Trim the description to the routing-relevant claim, e.g. 'Shared denylist of catastrophic shell commands enforced as a pre-exec guard across all AI coding agents on the machine,' and let the body's file map and wiring table carry the specific commands and agent list.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/ops-and-setup/global-agent-guardrails/SKILL.md
- **Pruning and drift — Single source of truth [craft]**: This restates, almost verbatim, what the Teaching Workspace bullet already says about the same files: "`./reference/*.html`: ... They are the raw units of learning. They should be beautiful documents which print out well, and are designed for quick reference." Both passages define reference documents as the compressed/quick-reference form of a lesson and both give overlapping example lists ("cheat sheets, reference algorithms, syntax, yoga poses, glossaries" vs. "Syntax and code snippets... Algorithms and flowcharts... Yoga poses and sequences... Glossaries"). This is the same meaning stated twice in two places, costing tokens and creating two spots to update if the definition changes.
  - quote: "They should be the compressed essence of the lesson, in a format designed for quick reference."
  - proposed fix: Keep one authoritative description of reference documents (in the ## Reference Documents section) and shrink the Teaching Workspace bullet to a one-line pointer, e.g. "`./reference/*.html`: reference materials for the topic — see ## Reference Documents below."
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/thinking-and-docs/teach/SKILL.md
- **Pruning and drift — Single source of truth [craft]**: This near-verbatim repeats the identity already given in the Teaching Workspace bullet: "`MISSION.md`: A document capturing the _reason_ the user is interested in the topic." Both sentences define "mission" as "the reason the user is interested in the topic," so the definition lives in two places rather than one authoritative spot.
  - quote: "Every lesson should be tied into the mission - the reason that the user is interested in learning about the topic."
  - proposed fix: Drop the restated definition from ## The Mission and start that section directly with the operational guidance (e.g. "If the user is unclear about the mission..."), trusting the Teaching Workspace bullet as the single place mission is defined.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/thinking-and-docs/teach/SKILL.md
- **Cut identity the body already states / single source of truth [craft]**: This routing rule is fully restated in the body: 'Always prefer the dedicated endpoint; web search is the fallback for the open web only' under Picking the Right Endpoint, with a worked example. The always-loaded description pays permanent context cost to restate a rule the body already elaborates in detail, with no added routing signal beyond what the preceding sentence in the same description already conveys.
  - quote: "Platform data has dedicated DeepAPI endpoints — prefer them over web search."
  - proposed fix: Drop the sentence from the description and let the body's 'Picking the Right Endpoint' section be the sole statement of the prefer-dedicated-endpoint rule.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/deepapi/SKILL.md
- **Cut identity the body already states [craft]**: Naming the two environment variables here restates identity/mechanism the body's 'Required Environment' section already owns in full, and reads as if these variables are specific to image generation when they are required for every endpoint call — misleading scoping paid for on every turn.
  - quote: "generate images with DEEPAPI_API_BASE_URL and DEEPAPI_API_KEY"
  - proposed fix: End the sentence at 'generate images' and let 'Required Environment' remain the single place the env var names are stated.
  - target: /home/will/.claude/jobs/2c802246/tmp/ext-david/skills/research-and-web/deepapi/SKILL.md

### Refuted findings

- **One trigger per branch [craft]** — verifier: "create a skill" and "new skill" route to the same branch (authoring a new skill), and "update this skill" / "improve a skill" route to the same branch (editing an existing skill). A run reaching this description via any phrase in each pair takes the identical path, so per the doctrine's test each pair should collapse to one trigger. As written, four phrases pay four times to cover two branches.
  - quote: "Use when the user says "create a skill", "new skill", "update this skill", "improve a skill", "why isn't my skill triggering", or anything else involving authoring or editing SKILL.md files."
- **Cut identity the body already states [craft]** — verifier: This clause enumerates the document's own section headings (anatomy §4, progressive disclosure §3, do/don't §6-7, testing §9, security §11) rather than encoding when to reach the document. It restates the body's identity instead of doing routing work, spending permanent context load on a table of contents.
  - quote: "How to write effective agent skills — what to do, what not to do, anatomy, progressive disclosure, design patterns, anti-patterns, testing, security."
- **Duplication by polarity [craft]** — verifier: This anti-pattern restates, negated, the rule already given positively in 'Description as routing contract' (§6: 'Include three elements: What... When... Differentiator...'), and the same meaning is stated again in §8 ('Draft the description first. What + when + differentiator'), the §12 checklist ('Description includes what + when + differentiator'), and §13 ('The description routes; the body executes'). The doctrine specifically calls out anti-pattern lists that mirror positive rules the document already gives.
  - quote: "Don't write vague descriptions"
- **One trigger per branch [craft]** — verifier: This is presented as the 'Good' exemplar of a description, but 'PDF forms' and 'fillable forms' name the same branch (a PDF with form fields) rather than distinct paths — a run reaching the skill through either phrase does the same thing. The doctrine's own test ('does a run reaching the document through this phrase take a different path than the one beside it? If not, collapse them') would fail this example.
  - quote: "Fill PDF form fields, extract form data, flatten completed PDFs. Use when the user mentions PDF forms, fillable forms, or programmatic field population."
- **One trigger per branch [craft]** — verifier: The four listed phrases ('cmux pane', 'cmux workspace', 'cmux surface', 'an agent running in cmux') are not distinct branches that route differently — they're all just instances of the literal token 'cmux' appearing in the user's message, restating the single preceding rule ('the user explicitly says "cmux"') three extra times.
  - quote: "Trigger ONLY when the user explicitly says "cmux" — a cmux pane, cmux workspace, cmux surface, or an agent running in cmux."
- **Leading words — Negation** — verifier: This bullet leads with the ban and every clause after it is also a negation, with no positive target stated for what to do instead (contrast with the preceding 'run.py stays tiny' / 'Core helpers stay short' bullets, which state the positive behavior before the negation). Per the negation rule, a prohibition should stand paired with its positive target so attention lands on what to do, not just on what's forbidden.
  - quote: "Don't add a manager layer. No retries framework, session manager, daemon supervisor, config system, or logging framework."
- **Negation [research] — a prohibition must stand paired with its positive target.** — verifier: Another literal string destined for the goal contract that leads with two bans and never states what the agent should do instead, dragging 'refactor unrelated code' and 'add dependencies' into context rather than suppressing them.
  - quote: "Do not refactor unrelated code. Do not add dependencies."
- **One trigger per branch [craft] — synonyms that rename a single branch are one branch written twice; collapse triggers that route to the same place.** — verifier: Both phrases route to the same 'Writing a goal' section with no differentiated path — a run reaching the doc via 'asks how to write a goal prompt' takes the identical path as one reaching it via 'wants a one-paragraph goal instruction drafted.' Per the doctrine's test, these should collapse into one trigger.
  - quote: "asks how to write a goal prompt, or wants a one-paragraph goal instruction drafted"
- **One trigger per branch [craft]** — verifier: All five phrases route to the exact same procedure — there is no branch in the document where 'ship it' behaves differently from 'deploy' or 'push to prod'. This is one branch written five times in an always-loaded description, paying five times in context load to route once.
  - quote: "Use when the user says "push", "push to github", "push to prod", "ship it", or "deploy"."
- **Single source of truth / duplication (polarity) [craft]** — verifier: This restates, negated, the fact already given positively earlier in the document: "Direct pushes to `main`. No PRs, no side branches." It is the same meaning written twice — the doctrine specifically calls out anti-pattern/hard-rule lists that mirror rules the document already gives.
  - quote: "Never push side branches."
- **Single source of truth / duplication (polarity) [craft]** — verifier: This duplicates the meaning already stated at the top of the document: "Only run this after the user explicitly told you to push. Never push on your own." Same rule, same polarity even, restated in the Hard rules checklist — the doctrine's guidance to audit such lists against the rules they mirror applies directly.
  - quote: "NEVER push without the user's explicit go-ahead."
- **Single source of truth / duplication [craft]** — quote_not_found: The near-identical instruction "If it is dirty with WIP that is not yours, stop and tell the user — never stash around it" already appears in the 'Landing work from a worktree' section. The same meaning (and nearly the same wording) is stated twice, so changing this policy requires editing two places.
  - quote: "If tracked dirt remains that is not yours, stop and tell the user — never stash around it."
- **Steps, completion, and demand — Demand [craft]** — verifier: The word-count requirement is checkable, but the parenthetical "if possible" is a stray uncheckable qualifier attached to the character-count requirement in the same sentence. It lets the agent treat the whole rule impressionistically — satisfying only the word-count half while waving off the character-count half as merely aspirational, exactly the mixed checkable/uncheckable pattern the doctrine flags.
  - quote: "For quizzes, each answer should be exactly the same number of words (and characters, if possible)."
- **Negation [research]** — verifier: The rule leads with the ban and never states the positive target — where/how the key should be handled instead — so per the doctrine's negation rule it drags the forbidden behaviors into context without anchoring the agent on the correct one.
  - quote: "Never commit, print, log, paste, or expose `DEEPAPI_API_KEY`."
