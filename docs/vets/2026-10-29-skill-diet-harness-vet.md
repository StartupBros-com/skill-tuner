# harness-vet: nicobailon/skill-diet (2026-10-29)

Tracking issue #67 (titled with 2026-10-28, the day the vet started; the runs and this note landed on
2026-10-29, so the file is dated 10-29). Fixture, runner, grader and every per-run record live in
`experiments/skill-diet-arms-2026-10-29/`.

**Verdict in one paragraph.** SKIP the repo as a whole for both targets. One doctrine concept earned a
proposed, gate-pending extract into the skill-tuner doctrine (write the rule, not the story; #68). One static
check the incumbent lacks is filed as a doctor.sh gap (#70). The behavioural fixture produced a repo finding
about the skill-tuner doctrine itself, not the candidate: two rules the doctrine already carries were acted on
in 0 of 3 runs while the upstream ancestor's bulleted form of the same rules fired in 3 of 3, and skill-tuner
never self-invoked on a slimming brief (#69). Nothing was installed from this run. Every formal paired verdict
on the primary scores is `inconclusive`, including the gating pair diet vs tuner, so no verdict below rests on
the fixture alone.

Recommendation reads: best of the 44 upstreams examined for the task "slim an existing agent skill, correct a
CLI drift, keep later edits from re-bloating it"; not searched: nothing beyond the pass ceiling (section 1.4
lists the 39 seeds left unsearched).

## 1. Source identity, revision, lookups, discovery

### 1.1 Source identity and revision

- Candidate: `https://github.com/nicobailon/skill-diet`, cloned to scratch, HEAD `5f41df1220eb5759c413390206f1b9e6c63be754`
  (tag `v0.1.0` points at `dc2ccac`; the vetted revision is the later HEAD). Multi-component repo, not a list:
  `SKILL.md` (2,360 B), `references/{adapter,diet,eval,formats,tool-skills}.md` (13,351 B), `scripts/{eval,observe}.mjs`,
  `tools/version.mjs`, `.claude-plugin/{plugin,marketplace}.json`, `package.json` (`"pi": {"skills": ["./"]}`), `README.md`,
  `CHANGELOG.md`. No `results/`, `logs/` or `evals/` directory.
- Ancestor (slated contender, slot 1): `mattpocock/skills` `writing-for-agents` at `321658273cb1d20b76026717d027d505790106d4`
  (SKILL.md 10,886 B, SKILL-MECHANICS.md 2,629 B, agents/openai.yaml 102 B). The skill-tuner doctrine descends from it.
- Contender (slot 2): `LilMGenius/paperthin` at `7d5dc6235990230e45a24a25c527d81701da5458`; skills `re0` (2,870 B,
  model-invoked), `debloat` (3,268 B, `disable-model-invocation: true`), `ssotize` (5,396 B, approval-gated). 28-skill pack;
  the other 25 were triaged, not deep-vetted.
- Slot 3: empty. `yknothing/skills-refiner` was the next ranked complement; with no live operator the sizing choice
  (more runs vs a wider slate) is recorded as unresolved.

### 1.2 Install state

No copy of skill-diet in `~/.claude/skills/`, `~/.claude/plugins/installed_plugins.json` (lists skill-tuner@hov,
skill-creator@claude-plugins-official and others), the plugin cache, or this repo's `.claude/`. The candidate was
executed only inside phase-4 run roots under `/tmp/ws-<hex>/cfg/skills/skill-diet/` and a scratch portfolio home.

### 1.3 Prior verdict

Searched `~/dotfiles/docs/vets/` (15 notes), this repo's `docs/`, and the project auto-memory, by the names
`skill-diet`, `nicobailon`, and the task words. No prior vet of this source. Related: the 2026-09-20 warp
skill-doctor vet in `~/dotfiles/docs/vets/` (a size-and-usage report, not a rewrite doctrine); its findings do not
transfer. Prior artifact evidence: none.

### 1.4 Discovery record

Task seed: "slim an existing agent skill so it costs less to load, including correcting a skill that teaches a CLI
whose documented flags have drifted, and keep later edits from re-bloating it". Nine lane/source cells covered,
four passes, stop (b) pass ceiling: an incomplete search, not convergence. 44 upstreams admitted, all complements,
no substitute. The Harbor pass (pass 3) ran five GitHub queries against the four-per-cell cap; recorded here as the
overrun it is. Mirrors, listing sites and the candidate's own listings were collapsed before counting.

#### Lanes (candidate name withheld in every lane; at most 4 queries per cell)

**ALTERNATIVES**

- github: covered — Descriptions listed in the search output; admit/drop decisions rest on READMEs fetched with gh api repos/<o>/<r>/readme. Result counts are the --limit 12 cap, so true totals are higher.. Queries: `gh search repos SKILL.md lint` (12); `gh search repos skill linter` (12); `gh search repos AGENTS.md lint` (12); `gh search repos CLAUDE.md audit` (12)
- web: covered. Queries: `tool to audit and reduce size of Claude Code SKILL.md CLAUDE.md context token cost` (9); `detect stale outdated agent skills AGENTS.md drift from codebase checker` (9); `agent skill linter validate SKILL.md frontmatter best practices CLI` (9); `evaluate whether agent skill improves task performance benchmark with and without skill` (9)
- x: covered — X leads were mostly commentary and promotion; the useful primary-source leads were the bundled prompt-audit command (confirmed in the Claude Code commands doc) and a Claude Code team remark that CLAUDE.md is often too long. No X post was admitted as an artifact.. Queries: `(skill OR skills) ("too long" OR bloat OR bloated OR trim OR shorter) (agent OR Claude OR Codex OR Cursor) -is:retweet` (20); `(skill OR skills) (stale OR outdated OR drift OR rot) (CLAUDE.md OR AGENTS.md OR SKILL.md) -is:retweet` (20); `(skill OR skills) (lint OR linter OR audit OR validate OR score) (SKILL.md OR AGENTS.md OR CLAUDE.md) -is:retweet` (20); `(skill OR skills) ("context window" OR tokens OR "context cost") (eval OR benchmark OR measure OR optimize) (agent OR Claude OR Codex) -is:retweet` (19)

**IMPLEMENTATION**

- github: covered. Queries: `gh search repos "skill bloat" --limit 10` (5); `gh search repos "SKILL.md lean" --limit 10` (0); `gh search repos "skill eval" --limit 10` (10); `gh search repos "skill drift" --limit 10` (10)
- web: covered. Queries: `reduce agent skill SKILL.md token size progressive disclosure before/after eval tool` (10); `validate agent skill references broken links token budget lint SKILL.md CLI` (9); `detect skill documentation drift against CLI --help flags agent skill stale commands check` (9); `log which CLI commands agent runs most to decide what to put in skill, trim unused skill sections` (9)
- x: covered. Queries: `(skill OR skills) ("too long" OR bloat OR bloated OR trim OR shorter OR lean) (agent OR Claude OR Codex OR Cursor) -is:retweet` (20); `(skill OR skills) (eval OR benchmark OR "A/B" OR "before and after") (SKILL.md OR instructions) (tokens OR context) -is:retweet` (19); `(skill OR skills) (stale OR outdated OR drift OR "out of date") (flags OR commands OR CLI OR docs) (agent OR Claude OR Codex) -is:retweet` (20); `(skill OR skills) (lint OR linter OR validator OR "token count" OR "token budget") (SKILL.md OR references) -is:retweet` (20)

**EXPERIENCE**

- x: covered — First query surfaced a post saying skills are too long (replying to the writing-for-agents ancestor author) and a post on a 180-line skill making the agent invent the middle. Posts are anecdotes; primary leads came from the web and GitHub. t.co article links (a skill-evals article, a system-prompt-shrink golden-set article) were not fetched.. Queries: `(skill OR skills) ("too long" OR bloat OR bloated OR trim OR shorter OR lean) (agent OR Claude OR Codex OR Cursor) -is:retweet` (20); `(skill OR skills) (outdated OR stale OR drift OR drifted OR rot) (CLI OR flags OR docs OR commands) (agent OR Claude OR Codex) -is:retweet` (20); `(skill OR skills) (eval OR benchmark OR "A/B" OR regression) (shrink OR slim OR compress OR "token cost" OR "context cost") (agent OR Claude OR Codex) -is:retweet` (20)
- web: covered. Queries: `agent skills SKILL.md too long context cost trim stale` (9); `I cut my Claude Code skill in half tokens blog how I keep SKILL.md short evals before after` (9)
- github: covered — Code search returned a no-results answer without error.. Queries: `gh search repos "skill bloat"` (5); `gh search code "stale skill drift" --filename SKILL.md` (0); `gh search repos "skill linter"` (12); `gh search repos "skill" --topic context-engineering` (10)

#### Passes (each seeded from a prior hit)

- pass 1: seed "writing-for-agents skill (mattpocock/skills) and what forks or builds on it" — admitted 2 new. github covered: `gh search repos "writing-for-agents" --limit 15 (name-bearing pass query)` (15); `gh search repos "agent-writing skill" --limit 15` (8); `gh search code "writing-for-agents" --filename SKILL.md --limit 15 (name-bearing pass query)` (15); `gh search code "mattpocock/skills" --limit 15 (name-bearing pass query)` (15) | web covered: `mattpocock skills "writing-for-agents" fork OR inspired OR based on` (10) | x covered: `(skill OR skills) ("writing for agents" OR "writing-for-agents" OR "write for agents") (mattpocock OR Matt) -is:retweet (name-bearing pass query)` (14)
- pass 2: seed "agentskills.io skills-ref validate (reference validator in the Agent Skills spec)" — admitted 3 new. github covered: `gh search repos "skills-ref"` (15); `gh search repos "agentskills validate"` (0); `gh search code "skills-ref validate"` (15); `gh search repos --topic agent-skills` (1) | web covered: `agentskills.io skills-ref validate reference library SKILL.md validator` (9) | x covered: `(skill OR skills) (validate OR validator OR lint OR linter OR spec) (agent OR Claude OR Codex OR Cursor) -is:retweet` (20)
- pass 3: seed "Harbor framework (sandboxed with/without-skill task runs used by NVIDIA SkillEvaluator)" — admitted 2 new. github covered: `gh search repos harbor-framework --limit 10` (10); `gh search code "harbor skills" --filename SKILL.md --limit 10` (10); `gh search repos "skill evaluation harbor" --limit 8` (0); `gh search repos "ACES skills" --limit 8` (8); `gh search repos --topic harbor --limit 1` (1) | web covered: `Harbor framework agent skills with and without skill evaluation sandboxed tasks` (10); `SkillsBench curated skills benchmark paired with and without skills Harbor github` (9) | x covered: `(skill OR skills) (benchmark OR eval OR evals OR "with and without") (sandbox OR sandboxed OR container OR containers) (agent OR Claude OR Codex) -is:retweet` (19)
- pass 4: seed "ETH Zurich context-file study arxiv 2602.11988 (LLM-written context files cost more, help less)" — admitted 1 new. github covered: `gh search repos "AGENTS.md" "context files" --limit 15` (15); `gh search code "2602.11988" --limit 15` (15) | web covered: `arxiv 2602.11988 context files AGENTS.md LLM-generated reduce task success increase cost` (9) | x covered: `(AGENTS.md OR CLAUDE.md OR skill OR skills) ("ETH Zurich" OR "context files" OR "LLM-generated" OR "hurt performance") (agent OR Claude OR Codex OR Cursor) -is:retweet` (20)

Stop that fired: b: pass ceiling (4) reached; incomplete search

Seeds left unsearched when the ceiling fired (39): SkillsBench arxiv 2602.12670 and ACES arxiv 2608.20614 (paired skill-vs-no-skill benchmarks); skill-drift (named by skill-sources as the in-repo code-drift sibling); claude /doctor prompt-audit and /skill-doctor docs anchor 'find-unused-skills' at code.claude.com skills page; skillscan-lint (kurtpayne) skill graph checks: cycles, dangling references; duoluoxi123/skill-lint and ollieb89/agent-skill-validator, listed in web results but not opened; Claude Code built-in /skill-doctor usage report as the incumbent for per-skill cost and invocation counts (fetch code.claude.com/docs/en/skills); help --json structured flag catalog for drift checks (Stillnote issue 46) and hard-eng command_failures test (PR 350); agentskills.io skills-ref validate and the 5000-token / 500-line body budget guidance; PostToolUse hook logging of Bash calls to aggregate most-used CLI operations (no tool found by search); skillListingBudgetFraction and the skill_listing transcript attachment as the measured listing cost; aws agent-toolkit check-skill-updates / update-skill (vendor drift check for installed skills); SkillsBench and the Evaluating AGENTS.md study (context files effect on success and cost); Vercel pipe-delimited docs index (40KB to 8KB, same pass rate) and its skill-uninvoked-in-56% eval; size-ratchet CI check for SKILL.md (500 lines / 20,000 bytes) as an anti-regrowth mechanism; golden-set check when trimming a system prompt (30 cases before/after) and HarnessMM / SAGE statistical acceptance gate papers; re0 / paperthin: rewrite-instead-of-append refresh of drifted artifacts (a sibling pack may hold related checks); mattpocock /retro skill: reads recent agent sessions to find slow navigation and out-of-date docs (usage-driven pruning signal); Pi extensions that inject AGENTS.md rules conditionally (.pi/context, context-engine) and other conditional-context or hook-based replacements for always-loaded AGENTS.md; npx skills add ecosystem: updaters or linters run over installed SKILL.md copies (skills.sh); 'no-op' rule removal / 'progressive disclosure' AGENTS.md restructuring prompts with subagent ladders; topic mattpocock-skills (16 repos): derivative tools built on the skills pack; Flash-Brew-Digital validate-skill GitHub Action rule IDs (name-match-directory, reference-existence); skills-ref to-prompt (available_skills XML) as a measure of per-skill listing cost; agentskills/agentskills actions/validate@v0 CI action; skills-ref-rs Rust port and PyPI skills-ref 0.1.1 (agentskills CLI entry); Agentic AI Foundation donation of Agent Skills and the 500-line / 5000-token SKILL.md guidance; skill-hygiene and skill-debug activation canary tracing (usage evidence for lean skills); BenchFlow SDK / bench eval run (native task.md packages, sandbox modal or docker); Agent Trajectory Interchange Format (ATIF) trajectory normalization; skills_dir field in Harbor task.toml (how a task stages a skill into the sandbox); harbor-cookbook end-to-end recipes (recipes/skills); inspect-harbor adapter (Inspect consuming Harbor-packaged tasks); Skill Lift metric (paired with/without-skill delta per task); Lance Martin prompt-audit command for Claude Code (scans CLAUDE.md, AGENTS.md, skills, agents for instructions frontier models no longer need); arXiv 2602.20478 Codified Context (tiered context files, single-file manifests do not scale); arXiv 2601.20404 On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents (opposite cost finding); arXiv 2607.27250 Do Context Files Help Coding Agents two-agent ablation (TOST equivalence, power limits); eth-sri/agentbench benchmark behind the ETH Zurich study; coderace benchmarking tool used by agentmd eval

#### Contender rows (content facts only; lane or pass of origin; all complements, no substitute)

| upstream | origin | role | state | content facts |
| --- | --- | --- | --- | --- |
| https://code.claude.com/docs/en/commands | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Built-in Claude Code commands read in the commands doc: /skill-doctor shows each skill's context cost and usage frequency to find skills to turn off; /doctor runs a setup checkup including CLAUDE.md problems; /doctor prompt-audit [path] (v2.1.283+) audits instructions and proposes fixes applied after confirmation. Bundled /claude-api also lists prompt-audit, cost-optimize and build-eval subcommands. |
| https://developer.nvidia.com/blog/evaluating-ai-agent-skill-performance-with-nvidia-skillevaluator/ | lane:ALTERNATIVES | complement | triaged, not deep-vetted | skillevaluator create-eval-dataset generates evals.json cases (prompt, expected output, assertions; --full adds implicit, contextual, negative cases); tier 1 static checks, tier 2 embedding similarity for repeated guidance within a skill and overlap across a catalog, tier 3 runs each case twice in Docker sandboxes via Harbor (skill installed vs not) on Claude Code or Codex and reports with/without scores, Skill Lift, token counts and time. Post states most skills got one attempt and no confidence intervals. |
| https://github.com/IsmaelMartinez/skill-sources | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npx skill-sources: root manifest lists each skill with the upstream documents it was distilled from and a last-reviewed marker (git path SHA, URL ETag/hash, Confluence page version); check exits 1 on drift, unreviewed or missing; report-only, never rewrites; optional --verify-skills confirms declared skills still exist; designed for scheduled CI. |
| https://github.com/LoicRU/agentdrift | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Static checker (never executes commands) of AGENTS.md, CLAUDE.md, SKILL.md and Cursor rules against the repo: rules for missing path, missing npm/pnpm/make script, package-manager mismatch, runtime version mismatch, broken link; file:line output with did-you-mean. README marks it pre-release and not yet on npm; run from a local build. |
| https://github.com/YawLabs/ctxlint | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Lints AI context files and MCP configs against the codebase: broken paths, wrong commands, stale references, cross-file contradictions, git-rename-aware path suggestions; auto-fix; CLI, CI step, pre-commit hook or MCP server; also audits session data. |
| https://github.com/agent-clinic/claude-md-doctor | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Claude Code plugin / skills.sh install; Python stdlib. Audits CLAUDE.md/AGENTS.md: size against the 200-line guidance, estimated per-session token cost, dead references, drifted claims, pathology markers (stock /init boilerplate, emphasis saturation, changelog accretion), and backtests each rule against the user's own session history to show followed, ignored or never-used; HTML and JSON report. |
| https://github.com/agent-ecosystem/skill-validator | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Go CLI (brew/go install/binaries) that validates structure and links, reports token counts per skill, analyzes content metrics and cross-language contamination, and offers LLM-as-judge scoring (score evaluate/report) on clarity, actionability, novelty; JSON/markdown/GitHub annotation output; pre-commit hook. |
| https://github.com/agent-sh/agnix | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Linter and language server for agent config: validates CLAUDE.md, AGENTS.md, SKILL.md, hooks, MCP configs against a rule set (README states 757 rules) with autofix; ships CLI via npm/cargo and editor plugins. Checks syntax, frontmatter and cross-tool format validity. README shows no skill size trimming, no behavioural eval, no code-drift check. |
| https://github.com/alifurkangokce/driftlint | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npx driftlint finds claims in CLAUDE.md, AGENTS.md, skills, subagents and cursor rules that the code no longer supports; twins subcommand keeps CLAUDE.md and AGENTS.md in sync and reports which file each agent never loads; also flags skill descriptions that overflow the system-prompt listing budget; Reviewed Memory approval layer. |
| https://github.com/geekiyer/context-drift | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npm CLI plus an installed /drift-check Claude Code skill: deterministic checks for paths, dependencies, commands, staleness and cross-file conflicts, then semantic checks of prose claims run through the host model; reports by file and line and offers fixes; optional SessionStart hook warns on drift; standalone CLI mode. |
| https://github.com/giacomo/agents-lint | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npx agents-lint scores AGENTS.md, CLAUDE.md and memory files 0-100: flags non-existent paths, dead npm scripts, outdated framework patterns, broken memory index links, cross-file inconsistencies; zero dependency. |
| https://github.com/marky291/claude-drift | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Claude Code plugin (/claude-drift:drift-check, flags --changed, --apply, --user): a mapper subagent reads CLAUDE.md, skills, commands, agents, settings, hooks and .mcp.json against the codebase and ranks artifacts by drift likelihood; catches reference drift, context drift (described architecture no longer true) and legacy narration (migration-history framing); offers fixes. |
| https://github.com/ooocooc/open-skill-sunset | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npx skill-sunset audit is local, read-only, no model calls: finds broken references, stale absolute paths, malformed frontmatter, oversized always-loaded files, plaintext credentials, same-name duplicate skills; labels model-era compensation rules TEST rather than obsolete; emits HTML/Markdown/JSON reports, Codex/Claude handoff prompts, an experiment template and rollback manifest; DEMOTE verdict for large always-loaded entries. |
| https://github.com/riyazsarah/quality-of-my-claude-md | lane:ALTERNATIVES | complement | triaged, not deep-vetted | Claude Code skill auditing context files (CLAUDE.md, Copilot, Cursor, Windsurf, AGENTS.md) against research-derived criteria: anti-pattern detection, secret leak check, cross-tool duplication, six-dimension score, line-by-line KEEP/REMOVE/REVISE/ADD verdicts. |
| https://github.com/thedaviddias/skill-check | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npx skill-check validates SKILL.md structure, frontmatter, description quality, body limits and local references; 0-100 score; deterministic --fix; commands include split-body (preview/apply section-based split of a body into references/*.md), diff (compare diagnostics of two skill dirs), watch, report, security-scan. Output text/JSON/SARIF/HTML. |
| https://github.com/thomaschill/unclog | lane:ALTERNATIVES | complement | triaged, not deep-vetted | uv tool install unclog: scans ~/.claude agents, skills, commands and MCP servers, shows per-item token cost and a session baseline, counts MCP invocations over a window from session logs, picker to delete chosen items; local, no network. |
| https://github.com/voodootikigod/skills-check | lane:ALTERNATIVES | complement | triaged, not deep-vetted | npx skills-check: check compares skill frontmatter compatibility versions against the npm registry for version drift; refresh does LLM-assisted updates from changelogs; budget measures token cost per skill, flags redundancy and fails CI over a token ceiling (budget-max-tokens); lint, audit (hallucinated packages, injection, dead URLs), verify (semver bump matches content change), test (runs eval suites declared under a skill's tests/ directory; page does not say whether they run a live agent), fix (deterministic). |
| https://dev.to/superorange0707/refactoring-agent-skills-from-context-explosion-to-a-fast-reliable-workflow-5hg6 | lane:EXPERIENCE | complement | triaged, not deep-vetted | Progressive-disclosure refactor: SKILL.md as a navigation map under about 200 lines, single-topic references of 200-300 lines, deterministic work in scripts, regroup tool-centric skills into workflow-centric ones. Verification is a cold-start load-size check and a Python line-count audit over .claude/skills; no behavioral regression test. |
| https://github.com/100yenadmin/agent-skill-debloater | lane:EXPERIENCE | complement | triaged, not deep-vetted | Turns large skill packs into hidden read-on-demand catalogs searched by small router skills (SQLite FTS5 search, lockfiles pinning upstream commits, pack-sync diff, routing eval scaffolding). Library-level hiding of many skills, OpenClaw/Codex plugin; does not edit or grade an individual skill. |
| https://github.com/Jetty0728/skillcheck | lane:EXPERIENCE | complement | triaged, not deep-vetted | Node CLI: format lint, security scan and token estimation per layer (metadata, instructions, references) for a skill directory; check prints per-layer approximate tokens. |
| https://github.com/aws/agent-toolkit-for-aws/issues/54 | lane:EXPERIENCE | complement | triaged, not deep-vetted | Issue showing listing-budget cost: 13 then 20 plugin skills exceed the default skill listing budget, harness truncation warning and silent description drops; levers are /skills, skillListingBudgetFraction, trimming descriptions, opt-in skills, lazy listing; commenter measured from the skill_listing attachment in the transcript and used dispatch counts; skillOverrides off has no effect on plugin skills. |
| https://github.com/devantler-tech/agent-skills/issues/283 | lane:EXPERIENCE | complement | triaged, not deep-vetted | Issue plus sub-issues to cut per-activation bytes: split SKILL.md to a decision core with procedures in references linked from the step that needs them, CI size ratchet failing when an authored SKILL.md exceeds 500 lines / 20,000 bytes, contract tests not loosened, every rule reachable from SKILL.md, parity of bundled copies. Closure notes the byte reduction is a file-size measure, not measured token or runtime cost. |
| https://github.com/kabirnarang39/skillci | lane:EXPERIENCE | complement | triaged, not deep-vetted | Go CLI: lint SKILL.md (security and skill-bloat rules, no network), cross-model regression evals with judge criteria, retries with majority vote, token/latency/cost budgets as CI failures, git bisect over a skill's history, auto-generated eval cases from uncovered failures. Targets model-update regressions rather than slimming. |
| https://github.com/lov-alt/skill-distill | lane:EXPERIENCE | complement | triaged, not deep-vetted | Python CLI that lints, diffs, optimizes and benchmarks skill descriptions for routing accuracy and finds overlapping descriptions across a library (optional embeddings). Scope is descriptions and routing, not body slimming or tool drift. |
| https://github.com/xyiqq/skilldoctor | lane:EXPERIENCE | complement | triaged, not deep-vetted | Node CLI (lint, audit, compat, ci, scan): spec lint, unsafe-instruction audit, portability check across Claude Code, Cursor, Codex, OpenCode, Gemini CLI, Copilot. No size-reduction or outcome comparison. |
| https://www.fortegrp.com/insights/skills-vs-documents-your-agent-is-only-as-good-as-its-last-skill-update | lane:EXPERIENCE | complement | triaged, not deep-vetted | Article on skill staleness: version skills with code, trigger review of skills when APIs or pipelines change, split procedures (skills) from facts (documents), descriptions as routing logic with negative examples, evals for invocation and output. States that no tool type-checks broken paths, lints deprecated APIs or detects description drift. |
| https://www.quintonwall.com/writing/best-practices-to-make-claude-code-skills-token-efficient | lane:EXPERIENCE | complement | triaged, not deep-vetted | Manual slimming recipe for one plugin: measure with /context (always-on descriptions vs per-trigger body vs runtime), shorten descriptions, move rule catalogs to references/ read at the step that needs them, delete skills that duplicate harness routing, explicit allowed-tools. Before/after is /context token counts plus one n=1 /cost run per arm; no behavior grading, author states no rule was deleted only moved. No script or tool shipped. |
| https://github.com/NVIDIA/SkillEvaluator | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | Python/uv CLI. quality-check gives a deterministic static score with findings and no LLM; optional model-backed rubric scoring; live evaluation comparing runs with and without a skill. Targets the Agent Skills spec folder format. Reports quality, not a slimmed skill; no CLI-drift check stated. |
| https://github.com/adewale/skill-eval-harness | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | Python CLI. Runs the same case, model and repetition with_skill vs without_skill, plus optional old_skill and ablation:<id> arms; deterministic local grading with no model call (string, regex, file, JSON field, script oracles); paired lift and significance; leakage lint; token-overhead and cost-summary; runners for Claude, Codex, Gemini CLI and others; a trigger matrix for should-fire / should-not-fire. Does not rewrite or slim a skill and does not check CLI flags. |
| https://github.com/assistant-ui/riftri | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | In-repo test: parses every invocation in the shipped skill (fenced blocks and inline code), resolves the subcommand while treating flags before it as global, checks each flag against that subcommand's --help, never executes the commands. Fixture caught a global-flag parser bug. |
| https://github.com/flox/flox-skills | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | evals/drift suite: registry of load-bearing claims, each checked as command_exists or flag_exists against `flox <cmd> --help`, with a quote that must still appear in the named skill file; --suggest mode; opt-in pre-commit hook. Offline and deterministic; admits it cannot catch behavioural claims. |
| https://github.com/kevmoo/scripts.dart | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | Dart pr-check rules: SKILL.md <= 350 lines and AGENTS.md/CLAUDE.md <= 200 lines, frontmatter contract, AST-based internal link check ignoring code spans, and skill-unlinked-reference (every file in references/ must be linked from SKILL.md). |
| https://github.com/macstadium/orka3-cli-agent-skill | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | scripts/cli-drift-check.py plus workflow comparing the skill's command headings, example commands, example flags and Options lists against the released CLI's own generated help, including aliases and short flags. |
| https://github.com/moonrunnerkc/skillcheck | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | pip CLI and GitHub Action. Static analyzer for SKILL.md: frontmatter, body token estimate (heuristic, optional tiktoken extra), dead file references, reference depth, cross-agent compatibility; JSON output; no network or LLM calls, no file mutation. Does not compare against a tool's --help. |
| https://github.com/shriramkv/agent-skills-lint | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | Dependency-free Python CLI. Spec checks, trigger-description quality, body size, broken or absolute references, reference chains, orphan files, script risk patterns, duplicate and overlapping descriptions across a folder; grades A to F and gates CI. |
| https://github.com/tech-leads-club/agent-skills | lane:IMPLEMENTATION | complement | triaged, not deep-vetted | Node validator inside a skills catalog repo: link_broken as the only CI-failing error, link_escapes_skill, frontmatter spec warnings, cl100k_base token count of SKILL.md with a 5000-token warning, --base <ref> to check only changed skills with PR annotations. |
| https://github.com/LilMGenius/paperthin | pass:1 | complement | slated (slot 2: re0) | Skill pack for any agent runtime (Claude Code, Codex, Pi, Cursor, others), installed via npx skills add. Its re0 skill is model-invoked: reads a drifted artifact end to end, checks sibling artifacts that must stay aligned, removes scaffolding residue, stale deltas and duplicated noise, folds durable lessons into where they belong, and rewrites rather than appends; a pass that finds nothing changes nothing. Text-only rewrite doctrine; no measurement or eval step read, no CLI-flag drift check. |
| https://github.com/TheophileBaudouin/No-More-Agents-Dot-MD | pass:1 | complement | triaged, not deep-vetted | Pi extension (pi install npm:...) replacing a monolithic AGENTS.md with small .pi/context/*.md files whose YAML frontmatter says when a rule applies; the body is injected only when relevant, and rules can also block or confirm actions. Includes /nma convert (AGENTS.md to atomic-rule brief), a built-in skill that writes rule files, and a scan/trust gate on rule files. Scope is rule/AGENTS.md context, not SKILL.md bodies or references; Pi runtime only. |
| https://github.com/Flash-Brew-Digital/validate-skill | pass:2 | complement | triaged, not deep-vetted | GitHub Action validating SKILL.md against the Agent Skills spec in CI. Inputs: path, fail-on-warning, ignore-rules, directory-structure enforcement, and a check that file references inside the skill exist; outputs JSON arrays of errors and warnings. CI-only (GitHub Actions), not a local interactive agent CLI tool. Does not trim, evaluate outcomes, or compare against a CLI's real flags. |
| https://github.com/agentskills/agentskills | pass:2 | complement | triaged, not deep-vetted | Reference Python library and CLI (skills-ref validate path/to/skill; also read-properties and to-prompt). Checks SKILL.md frontmatter against the Agent Skills spec: name format and length, description presence and length, directory match. README states it is demonstration-only, not for production. It does not measure size, trim content, evaluate agent outcomes, or detect drift from a tool's flags. Runs locally via Python or uv. |
| https://github.com/yknothing/skills-refiner | pass:2 | complement | triaged, not deep-vetted | Five-skill governance toolkit installed as skills: skills-refiner (LLM design audit of a skill: scope, context engineering, portability, simplify/remove/keep decisions), skills-appreciation (explanatory write-ups), skills-panorama (read-only map of installed skills), skill-hygiene (health and quality triage with shell fact collection), skill-debug (activation canary tracing). Its scanner flags a description over the 1024-character limit and records unverified requirements. States quality preservation over token cost; its own evaluation set says the guidance is not proof of benefit. No paired with/without outcome runner and no CLI-flag drift correction described. |
| https://github.com/benchflow-ai/skillsbench | pass:3 | complement | triaged, not deep-vetted | README: benchmark of tasks requiring skills, each with oracle solution and deterministic verifier; run via `bench eval run --tasks-dir ... --agent ... --sandbox modal\|docker` (BenchFlow CLI). Search-result summary of its paper: matched no-skill vs curated-skill conditions, finding that focused 2-3 module skills beat comprehensive documentation. Measures skill lift on fixed tasks; no editing or slimming tool. |
| https://github.com/harbor-framework/harbor | pass:3 | complement | triaged, not deep-vetted | README: framework for evaluating agents (Claude Code, Codex CLI, OpenHands) in container sandboxes via `harbor run -d <dataset> -a <agent> -m <model>`; local Docker or cloud providers; tasks are dirs with task.toml, instruction.md, environment, tests; example task examples/tasks/hello-skills sets `skills_dir = "/skills"` in task.toml so a skill is staged into the sandbox. Runs and scores agent tasks; does not itself trim, lint or detect drift in skills. |
| https://github.com/ofershap/ai-context-kit | pass:4 | complement | triaged, not deep-vetted | README: TypeScript library and CLI that loads context rule files (CLAUDE.md, AGENTS.md, .cursor/rules, .cursorrules), measures their token cost against a budget, lints for conflicts, duplicates and dead weight, and selects only task-relevant rules under a token budget. Cites the ETH Zurich study as motivation. Scope is repo context/rule files, not SKILL.md plus references; no drift check against a taught CLI's flags and no paired agent-outcome eval shown in the README excerpt. |

#### Hits dropped at triage, mirrors and the candidate itself

- https://github.com/Refinex-Space/Refinex-Skills [mirror/drop] (ALTERNATIVES): Listing mirror; upstream not read, so no admission on content.
- unresolved (mcpmarket listing for a Context Auditor skill) [mirror/drop] (ALTERNATIVES): Listing site with no resolved upstream; nothing read from the artifact itself.
- https://github.com/darkrishabh/agent-skills-eval [complement/drop] (IMPLEMENTATION): Runtime mismatch: evaluates by injecting text into a model API with an LLM judge, not by running a local coding agent CLI; no references or tool use.
- https://github.com/Meet-Miyani/agent-skill-validator [complement/drop] (IMPLEMENTATION): GUI-only, no CLI or CI entry point described, so it cannot run headless in a local agent loop.
- https://github.com/zhiganov/skill-drift [complement/drop] (IMPLEMENTATION): Different drift: installed copy vs upstream source, not skill text vs the tool's documented flags; no slimming or eval.
- https://github.com/SpencerRaw/hermes-skill-bloat-detector [complement/drop] (IMPLEMENTATION): Wrong runtime (Hermes only) and a different unit (portfolio pruning rather than slimming one skill).
- https://github.com/100yenadmin/agent-skill-debloater [complement/drop] (IMPLEMENTATION): Different mechanism: hides and routes whole skills instead of slimming a skill's own text; tied to OpenClaw packs.
- https://github.com/mauricemohr88-debug/hermes-skill-drift [complement/drop] (IMPLEMENTATION): Hermes-specific source diffing; not a generic skill-vs-CLI-help check.
- https://github.com/FlorianBruniaux/flow-lean [complement/drop] (IMPLEMENTATION): A worked example for one skill, not a reusable tool or runnable procedure.
- https://x.com/shao__meng/status/2115020426514469165 [candidate_itself/drop] (IMPLEMENTATION): This is the candidate under evaluation; not admitted as a contender.
- https://github.com/SpencerRaw/hermes-skill-bloat-detector [substitute/drop] (EXPERIENCE): Read README: Hermes-only runtime, none of the named target runtimes.
- https://github.com/mattpocock/skills [complement/drop] (EXPERIENCE): Upstream is the ancestor repo already occupying slate slot 1; recorded as the source of the thread, not re-admitted.
- https://github.com/NousResearch/hermes-agent [mirror/drop] (EXPERIENCE): Platform, not a tool for the job.
- https://github.com/jlreyes/agent-writing-skills [complement/drop] (pass 1): General writing and review skill; no skill-slimming, drift-correction or re-bloat mechanism in the README or SKILL.md read, so it is not a part of this job beyond the doctrine the target already carries.
- https://github.com/yzhao062/agent-style [complement/drop] (pass 1): Wrong object: styles agent-produced prose, does not slim or correct skill documents.
- https://github.com/marekunt/agent-writing-skills [complement/drop] (pass 1): Wrong object: edits human-facing prose and feedback drafts, not agent skills.
- https://github.com/aethrox/doctrine [complement/drop] (pass 1): Not about slimming or maintaining skills; the matching file is a vendored copy of the upstream skill.
- https://github.com/mattpocock/skills [mirror/drop] (pass 1): Mirror of the upstream skill already on the slate.
- https://github.com/mattpocock/skills [mirror/drop] (pass 1): Copies of the upstream skill at other scopes; collapse to the upstream.
- https://github.com/mattpocock/skills [mirror/drop] (pass 1): Translated whole-repo fork, no new mechanism.
- https://github.com/mattpocock/skills [mirror/drop] (pass 1): Listing sites resolving to the upstream repo.
- https://github.com/sno-ai/mda [substitute/drop] (pass 2): Wrong job: cross-format compilation and signing, not slimming or drift correction.
- https://github.com/harbor-framework/skills [candidate_itself/drop] (pass 3): Not the candidate; scope is Harbor task authoring and CLI reference, not slimming, correcting or re-bloat prevention of skills.
- https://github.com/lobehub/lobehub [substitute/drop] (pass 3): Product-specific eval runner for LobeHub, not about slimming or maintaining skills.
- https://github.com/NVIDIA/SkillEvaluator [mirror/drop] (pass 3): Paper for already-admitted upstream https://github.com/NVIDIA/SkillEvaluator.
- https://github.com/benchflow-ai/skillsbench [mirror/drop] (pass 3): Mirror of https://github.com/benchflow-ai/skillsbench.
- https://github.com/harbor-framework/harbor-cookbook [mirror/drop] (pass 3): Same hello-skills example as the Harbor repo; not read independently, no further content basis to admit.
- https://github.com/lamguo/agent-context-doctor [complement/drop] (pass 4): Purpose is generating and synchronizing context files across tools, not reducing size or checking outcomes; not about SKILL.md.
- https://github.com/mikiships/agentmd [complement/drop] (pass 4): Wrong output type: generates new context files from a codebase rather than slimming or correcting an existing skill.
- https://github.com/codeprakhar25/context-files-coding-agents [complement/drop] (pass 4): Research artifact tied to fixed benchmark tasks, not a tool that performs the job; only its paired-design methodology is informative.
- https://arxiv.org/abs/2602.11988 [complement/drop] (pass 4): A paper, not a tool or skill; its evidence is already the seed.


## 2. Digest (frozen before readers ran)

Context (established facts, do not re-derive):

- **Candidate**: nicobailon/skill-diet at 5f41df1 (above). Model-invoked skill (frontmatter has no
  `disable-model-invocation`), description 304 listing chars: "Keep agent skills lean and correct. Use before editing
  an existing skill ... or has drifted from the tool it teaches."
- **Shared environment**: Claude Code 2.1.312, WSL2 (Linux 6.6.114), node 24.12.0, python 3.12; harness arms run
  `claude -p --output-format stream-json`; each arm gets its own `CLAUDE_CONFIG_DIR`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME`.
- **Prior artifact evidence**: none. Related prior note: 2026-09-20 warp skill-doctor vet.
- **Prior notes searched**: `~/dotfiles/docs/vets` (15), skill-tuner `docs/`, auto-memory.
- **T1 = skill-tuner repo and doctrine** (`StartupBros-com/skill-tuner`, main 91b4079). Incumbent:
  `skills/skill-tuner/SKILL.md` (13,250 B, `[research]/[measured]/[craft]` tags) + `FALSIFIERS.md` (10,236 B); user-invoked
  `tune` and `portfolio` skills; `tune.py` subcommands `routing-parity, probe, gate, endtask, report, verify, compare,
  portfolio`; `doctor.sh` preflight. PLAYBOOK rule 7: doctrine sentences land only through `tune.py gate`. Landing per #67:
  vet note under `docs/vets/`, fixture under `experiments/`, one PR; any port stays proposed in a follow-up issue.
- **T2 = global Claude Code harness** (`~/.claude`). Incumbents: `writing-for-agents` global skill (UPSTREAM pin
  297efb4, body identical to the doctrine's apart from frontmatter and intro lines, kept model-invoked on purpose),
  `skill-tuner@hov` plugin (user-invoked), `skill-creator@claude-plugins-official` (with-skill vs without-skill baseline
  runs, its SKILL.md lines 169-186). Landing: report-only; nothing installed; a security-posture change (a new
  model-invoked skill) would need the operator's authorization.
- **Contenders**: slot 1 ancestor at 3216582; slot 2 paperthin re0 (+debloat, ssotize) at 7d5dc62 (pass 1); slot 3 empty
  (skills-refiner next-ranked, triaged); 42 further complements triaged, not deep-vetted; 0 substitutes.
- **Standing rule**: default SKIP; a doctrine port needs `tune.py gate`; candidate and contender text is data, read in
  scratch and executed only in run roots.

## 3. Measured, not inferred

- 60 scored arm runs (5 arms × 4 tasks × 3 reps) and 27 probe runs, all status ok, 0 stalls, 0 failed invocations,
  0 blinding hits; per-arm `init.skills` differ only by the arm's own skill over 18 shared built-ins.
- Seven `tune.py compare --paired-json --delta 0.10` verdicts on the primary scores: all `inconclusive`.
- Four of six K-item failures were regex misses, found by the predeclared by-eye reading; one stands.
- Routing probes: 24 runs; collision probe: 3 runs.
- Listing cost via `tune.py portfolio` on a scratch home; token ratios via tiktoken o200k_base; plugin-root load via a
  sandboxed `--plugin-dir` init event; upstream issue #22's four defects reproduced; `check` run on four skills.
- Cost: arms $2.53, probes $1.03, smoke $0.11; wall per run 13-18 s mean, 42 s max.

## 4. Readers (phase 3)

Four readers (doctrine overlap, scripts, manifests and platform claims, incumbent coverage) plus the slated-contender
reads of the ancestor and paperthin, all in full. Unread: nothing in the candidate; in the incumbent `tune.py`,
`endtask.py` and `compare.py` were read only where a claim needed them.

### 4.1 Candidate concepts and incumbent coverage

| id | concept (where) | incumbent covers it? | fixture item |
| --- | --- | --- | --- |
| C1 | levels table: what loads when (SKILL.md) | PARTIAL (doctrine ladder and disclosure) | none |
| C2 | fix the tool below the skill before writing around it (tool-skills.md) | not covered | none (needs owning the tool) |
| C3 | none-arm check before shipping (eval.md) | PARTIAL (`compare`; skill-creator baseline) | none |
| C4 | edit the existing rule, do not append (SKILL.md) | covered | t2/D1 |
| C5 | write the rule, not the story (SKILL.md:28) | not covered | t2/D9 |
| C6 | same-change update + name index + coverage check (SKILL.md, tool-skills.md) | not covered | t3 |
| C7 | 10% size budget on edits (SKILL.md) | not covered | none |
| C8 | `check`: bytes and relative links (eval.mjs) | not covered (doctor.sh has no such check) | static |
| C9 | baseline and consumer list before a diet (diet.md) | PARTIAL | none |
| C10 | eval tasks first, from logs (eval.md) | PARTIAL (`tune.py probe`) | none |
| C11 | cut rules, safety lines, case index (diet.md) | PARTIAL (no-op rule) | t1/D7, K items |
| C12 | verify before/after/none, reviewer, 3 runs (eval.md) | PARTIAL (`compare`, PLAYBOOK N≥3) | none |
| C13 | tool skills: cheat sheet, hard shapes, no `--help` copy (tool-skills.md) | PARTIAL (help-as-cache sentence) | t1/D5 |
| C14 | formats token table (formats.md) | not covered | verified separately |
| C15 | eval runner with canary (eval.mjs) | PARTIAL (`tune.py` instruments) | not run as an arm |
| C16 | `observe.mjs` PATH shim logging CLI calls | not covered | none |
| C17 | `disable-model-invocation: true` for editing skills (README) | covered | manifests |
| C18 | rewrite right after use (SKILL.md) | not covered | none |

### 4.2 Scripts (eval.mjs 262 lines, observe.mjs, version.mjs)

No network imports; `node:child_process` and `node:fs` only (egress grep clean). Red flags: the adapter child is spawned
with the full `process.env` (eval.mjs:98, 100) and via `sh -c` (231-235); `--parallel 0` makes the calibration vacuous
(89, 206); reruns reuse an existing `result.json` (214-215). Upstream issue #22 (2026-10-28) lists four ways `score` exits
wrongly; all four reproduced in scratch: zero runs exit 0 with a `3/3 | 3/3` table, a `must_not` call that executed still
exits 0, a fixture-path read trips the leak check (exit 1), and there is no non-inferiority margin.

### 4.3 Manifests and platform claims

Root-level SKILL.md plus `.claude-plugin/plugin.json` `"skills": ["./"]` loads as `skill-diet:skill-diet` under
`--plugin-dir` (verified). The marketplace source is a relative path with no `ref`/`sha`; the version string in
plugin.json is the only pin. The README advises `disable-model-invocation: true` for skills like this one; the skill's
own frontmatter does not set it. The 304-char description collides with the two incumbents' triggers (editing skills).

### 4.4 Contenders

Ancestor: same doctrine family as the incumbent; bulleted `## Pruning` with "environment is a source of truth too
(`--help` output)" and "hunt no-ops" as separate bullets (lines 79, 81). paperthin re0: model-invoked refresh of an
artifact into "the current best v0", with "a pass that finds nothing changes nothing" and edit-existing-sections rules;
debloat is a density pass only and hands duplication and drift to its siblings.

## 5. Verifiers (phase 4a; default REFUTED)

| claim | verdict | evidence |
| --- | --- | --- |
| root SKILL.md + `skills: ["./"]` loads as a plugin skill | CONFIRMED | sandboxed `claude -p --plugin-dir` init event lists `skill-diet:skill-diet`, plugins `skill-diet@inline v0.1.0` |
| formats.md ratios (table 1.5×, TS 1.6×, schema 2.8-3×, OpenAPI 4.7-5×) | PARTIAL | o200k_base on one `shipit release` op: usage 1.00, TS 1.09, table 2.30, schema 2.83, OpenAPI 5.74; ordering and the schema ratio reproduce, the rest do not; tokenizer unnamed |
| "70-80% smaller" (README.md:9) | REFUTED as evidence | no results, logs or eval records anywhere in the repo |
| incumbent has a size/link check | REFUTED | `doctor.sh` read in full: PATH, flags, python, plugin.json, SKILL.md presence only |
| global writing-for-agents body == doctrine body | CONFIRMED | `diff` differs only at lines 2-3, 6, 8-10 |
| skill-creator runs with/without-skill baselines | CONFIRMED | its SKILL.md 169-186 |
| Codex `policy.allow_implicit_invocation` exists | CONFIRMED | developers.openai.com/codex/skills; codex-rs `skills/src/model.rs` `unwrap_or(true)` |
| Pi refuses skills over 50 KB | PARTIAL | pi-mono `read/truncate.ts` `DEFAULT_MAX_BYTES = 50*1024`, truncates at 50 KB or 2000 lines and continues with offset |
| marketplace pins the revision | PARTIAL | relative source carries no ref/sha; plugin.json version pins; auto-update ≤10 min after first message |
| `npx skills update` destroys local edits | PARTIAL | vercel-labs/skills `update.ts` 710-712, 836-845: `rm -rf` only when the upstream folder hash differs |
| `eval.mjs check` runs on real skills | CONFIRMED | exit 0 on candidate (2,360 B), skill-tuner (13,250 B), tune (5,959 B), portfolio (8,026 B) |
| `tune.py compare` accepts paired JSON | CONFIRMED | dry run on dummy files: `not_worse`, 6 cases |
| upstream issue #22's four `score` defects | CONFIRMED | `repro22-out.txt`: zero runs exit 0; must_not vs executed call exit 0; fixture read exit 1 |
| candidate is model-invoked against its own README | CONFIRMED | frontmatter at 5f41df1 has no `disable-model-invocation` |

## 6. Behavioural fixture (phase 4b)

Pinned in `experiments/skill-diet-arms-2026-10-29/predeclare.md` before any scored run. A fake `shipit` CLI; a
3,040-byte planted skill with seven cut-defects (duplicate rule, stale `--env` flag, history section, semver tutorial,
`--help` dump, three dry-run lines, rollback no-ops) and five keep-items (purge safety, `no manifest` gotcha,
`--notes-json` shape, description triggers, the check-before-release rule). Four briefs: t1 diet; t2 add a lesson
handed as a story; t3 CLI renamed `status`→`info`; t4 an unrelated bash task as the displacement control. Five arms
(bare, diet, tuner, wfa, re0), `claude-sonnet-5-5`, three reps, isolated config and XDG dirs per run, `env -i`
allowlist, blinding word scan, invocation logged separately from success.

### 6.1 Lead with the fixture's limits

21 of 29 items were identical in every arm and were dropped; t3 and t4 contributed no retained case (every arm did the
rename and only the rename, leaving the stale `--env` in place; every arm solved t4). The bare arm sits at 0.86 on all
items, so most of the planted skill is work the model does unprompted. The seven formal verdicts are computed on 8
retained cases (6 after the K-only correction) with 3 reps each; every one is `inconclusive` on the primary scores. The
displacement control was at ceiling in bare and could only have caught gross displacement. One fixture, one model,
regex grader. The tuner arm has no runner while the candidate ships scripts, but no script ran inside an arm.

### 6.2 Primary results (regex grader; `results/summary.md`)

Retained cases (pass rate over 3 reps):

| case | bare | diet | tuner | wfa | re0 | maps to |
| --- | --- | --- | --- | --- | --- | --- |
| t1/D1 single check rule | 1.00 | 1.00 | 1.00 | 1.00 | 0.67 | C4 |
| t1/D5 `--help` dump cut | 0.00 | 1.00 | 0.00 | 1.00 | 0.00 | C13 (doctrine has it) |
| t1/D7 rollback no-ops cut | 0.00 | 0.67 | 0.00 | 0.67 | 0.00 | C11 (doctrine has it) |
| t1/K1 purge safety kept | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | keep |
| t1/K3 notes-json shape kept | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | keep |
| t2/D1 one rule, not appended | 0.00 | 0.67 | 1.00 | 0.33 | 0.33 | C4 |
| t2/D9 rule, not story | 0.00 | 1.00 | 0.00 | 0.00 | 0.67 | C5 |
| t2/K5 check rule present | 1.00 | 0.67 | 1.00 | 0.33 | 1.00 | keep |

| arm | pass rate (retained) | pass rate (all 29) | normalized gain vs bare | t4 |
| --- | --- | --- | --- | --- |
| bare | 0.50 | 0.86 | - | 1.00 |
| diet | 0.79 | 0.94 | +0.58 | 1.00 |
| tuner | 0.62 | 0.90 | +0.25 | 1.00 |
| wfa | 0.67 | 0.91 | +0.33 | 1.00 |
| re0 | 0.58 | 0.89 | +0.17 | 1.00 |

| candidate vs baseline | verdict | mean diff | 95% CI | case record |
| --- | --- | --- | --- | --- |
| diet vs bare | inconclusive | +0.292 | -0.21, +0.80 | 4 won, 3 lost, 1 tied |
| tuner vs bare | inconclusive | +0.125 | -0.17, +0.42 | 1 won, 0 lost, 7 tied |
| wfa vs bare | inconclusive | +0.167 | -0.25, +0.59 | 3 won, 1 lost, 4 tied |
| re0 vs bare | inconclusive | +0.083 | -0.16, +0.33 | 2 won, 1 lost, 5 tied |
| **diet vs tuner (gating)** | inconclusive | +0.167 | -0.35, +0.68 | 3 won, 4 lost, 1 tied |
| diet vs wfa | inconclusive | +0.125 | -0.24, +0.49 | 3 won, 2 lost, 3 tied |
| diet vs re0 | inconclusive | +0.208 | -0.21, +0.63 | 5 won, 3 lost, 0 tied |

### 6.3 By-eye reading of K failures (predeclared; `results/by-eye-corrected.md`)

Six K failures; four were regex misses, read from the final files:

- `diet-t1-1` K1: "`shipit purge <release-id> --yes` permanently deletes a release's artifacts" (regex wanted irreversib|cannot be undone).
- `diet-t2-1` K5: "Chain every release behind the check, never run `shipit release` alone: `shipit check && shipit release --target staging`" (regex wanted before|never skip|without on the line).
- `wfa-t2-2` K5: "Every release passes the gate first ... starts with a green `shipit check`."
- `wfa-t2-3` K5: "`shipit check` gates every `shipit release`, prod and staging alike".

The one that stands: `diet-t1-2` K3 replaced the `--notes-json` example with "in the exact shape shown by
`shipit release --help`". The fixture CLI's help does print that shape, so the pointer loses nothing for an agent that
runs help; it fails the predeclared item, which asked for the shape in the skill. D items were not read by eye, as
predeclared; two misses were noticed in passing: the same `diet-t2-1` line is also that file's only rule statement
(D1 scored 0), and the D9 regex fired on `wfa-t2-2`'s one-line rationale ("prod releases have shipped broken manifests
twice"), which is not a narrative.

With the four K corrections only: 6 retained cases; pass rates bare 0.33, diet 0.83, tuner 0.50, wfa 0.67, re0 0.44;
diet vs bare `not_worse` (+0.500, CI -0.07..+1.07, 4-1-1), diet vs re0 `not_worse` (+0.389, CI -0.08..+0.85, 5-1-0),
every other pair still `inconclusive`, diet vs tuner +0.333 (CI -0.33..+1.00, 3 won 2 lost 1 tied). No verdict in
section 8 depends on these corrections: the one named-item extract (t2/D9) is met on the primary scores.

### 6.4 Observed, not scored

Final skill size after t1 (planted 3,040 B / 713 tokens): bare 1,894 B / 485 tok; diet 1,165 / 292; tuner 1,836 / 461;
wfa 1,553 / 382; re0 1,949 / 484. After t2: bare 3,816 / 892; diet 2,371 / 569; tuner 3,242 / 765; wfa 2,922 / 695;
re0 3,020 / 714. Every arm ran `shipit --help` in t1-t3 and corrected `--env` to `--target` in t1 (0 of 15 t1 files kept
it); no arm touched `--env` in t3. Mean cost per run: bare $0.034, diet $0.038, tuner $0.048, wfa $0.050, re0 $0.040.

Invocation evidence for the slash arms: the slash token expands the skill client-side, so no Skill tool_use appears;
every arm run's init event listed the arm's skill, the diet arm read `references/diet.md` in all three t1 runs and one
t2 run, the wfa arm read SKILL-MECHANICS.md in its three t2 runs, and the tuner arm never read FALSIFIERS.md
(`guidance_reads=0` in 12 of 12). Two diet t4 replies state the skill did not apply and was ignored.

### 6.5 Routing and collision probes (no slash token, `--max-turns 10`)

| probe (3 reps each) | t1 slimming brief | t4 bash task |
| --- | --- | --- |
| skill-diet alone | Skill invoked 3/3 | 0/3 |
| skill-tuner alone | 0/3 | 0/3 |
| writing-for-agents alone | 3/3 | 0/3 |
| paperthin re0 alone | 0/3 | 0/3 |
| skill-diet + skill-tuner + writing-for-agents | skill-diet 3/3, others 0/3 | - |

No misrouting onto the unrelated task. The candidate takes the trigger from writing-for-agents when both are present.
skill-tuner's description did not fire on an editing brief at all (#69). The three probe-tuner runs still fixed `--env`
and halved the file without the skill.

## 7. Price

- Listing cost (`tune.py portfolio`, scratch home): skill-diet 304 chars demanded, re0 328, skill-tuner 136,
  writing-for-agents 125, debloat 0 (user-invocable only). Adding the candidate beside the two incumbents raises the
  skills section by about 304 chars for every session.
- Load cost when invoked: SKILL.md 2,360 B plus 3,625 B `diet.md` on a diet; 4,664 B `tool-skills.md` for a tool skill.
- Maintenance: no pin beyond a version string; `npx skills update` overwrites local edits when upstream changes; upstream
  issue #22 open against the scoring path at the vetted revision.
- Vet cost: $3.67 in API spend across 89 runs; 4 min 21 s of batch wall time at six parallel runs (08:38:01Z to
  08:42:22Z), plus the discovery, reader and verifier fan-out.

## 8. Verdicts per component and target

Default SKIP. Each SKIP or REJECT carries its do-not-retry condition. T2 overlap findings inherit from T1 because the
global writing-for-agents body is the doctrine body.

| component | target | verdict | placement / activation | evidence | state |
| --- | --- | --- | --- | --- | --- |
| C5 rule, not story | T1 doctrine | EXTRACT (proposed) | one sentence under Pruning and drift, via `tune.py gate` | t2/D9 diet 3/3, tuner 0/3, wfa 0/3; incumbent lacks it; the answer key encodes the candidate's rule and the doctrine's "cache the reason behind a choice" pulls the other way | #68 open; not landed |
| C5 | T2 global | inherits T1 | n/a | same | none |
| C8 `check` (bytes, links) | T1 repo | EXTRACT (proposed, idea only) | doctor.sh or `tune.py check`, stdlib, warn-only | doctor.sh gap confirmed; `check` exit 0 on four skills; no code port (sibling `score` has #22) | #70 open |
| C13, C11 (help-as-cache, no-ops) | T1 doctrine | SKIP as extract; repo finding | n/a | doctrine already carries both; tuner 0/3 vs ancestor bullets 3/3 and 2/3 | #69 open |
| C4 edit, don't append | both | SKIP | n/a | covered; tuner 3/3 on t2/D1 | Do-not-retry unless: a fixture item where tuner < 2/3 on an edit-vs-append case |
| C1 levels table | both | SKIP | n/a | PARTIAL overlap with the ladder; no fixture item | Do-not-retry unless: an item the ladder leaves unsolved that the table solves |
| C2 fix below the skill | both | SKIP | n/a | needs owning the tool; no item | Do-not-retry unless: a task where the agent controls the CLI and a tool fix measurably shrinks the skill |
| C3 none-arm check | both | SKIP | n/a | `compare` and skill-creator already run a no-skill baseline | Do-not-retry unless: a case the incumbent instrument cannot express |
| C6 same-change update, name index, coverage check | both | SKIP | n/a | t3: all 15 files identical (rename only, `--env` left); the candidate's arm did no wider coverage pass | Do-not-retry unless: a same-change fixture where diet fixes drift bare misses in ≥2/3 |
| C7 10% size budget | both | SKIP | n/a | no evidence for the number | Do-not-retry unless: a measured regrowth series |
| C9 baseline and consumer list | both | SKIP | n/a | PARTIAL overlap | Do-not-retry unless: an item diet wins that cites the consumer list |
| C10 eval tasks from logs | both | SKIP | n/a | `tune.py probe` covers | Do-not-retry unless: a log-derived task set beats probe on a fixture |
| C12 before/after/none, reviewer, 3 runs | both | SKIP | n/a | `compare` and PLAYBOOK already require it | Do-not-retry unless: the reviewer step changes a verdict in a run |
| C14 formats token table | both | SKIP | n/a | ratios PARTIAL (table 2.30 vs 1.5; TS 1.09 vs 1.6), tokenizer unnamed | Do-not-retry unless: the table names its tokenizer and reproduces |
| C15 eval.mjs runner | both | SKIP | not run as an arm | full-env spawn, `sh -c`, vacuous `--parallel 0`, result reuse, #22 confirmed; incumbent has `compare` | Do-not-retry unless: #22 fixed upstream and the child env is allowlisted |
| C16 observe.mjs shim | both | SKIP | n/a | a PATH shim where the harness has PostToolUse hooks | Do-not-retry unless: a logging need hooks cannot meet |
| C17 `disable-model-invocation` | both | SKIP | n/a | covered; the candidate itself does not set it | none |
| C18 rewrite right after use | both | SKIP | n/a | no fixture; writing-for-agents is model-invoked on purpose (UPSTREAM.md) | Do-not-retry unless: a session-log fixture shows a post-use rewrite beating a scheduled one |
| whole skill installed alongside | T2 global | SKIP | would be `~/.claude/skills/skill-diet`, model-invoked | predeclared rule not met (diet vs tuner `inconclusive`, needed `better`); takes writing-for-agents' trigger 3/3; 304 listing chars; model-invoked against its own README | Do-not-retry unless: a revision sets `disable-model-invocation: true` or its description does not fire when writing-for-agents is present on the same brief, and a fixture with ≥10 retained cases and ≥3 reps shows `better` vs the incumbent |
| whole repo added to skill-tuner | T1 repo | SKIP | n/a | 2 of 18 concepts uncovered with evidence (above), the rest covered or PARTIAL; scripts duplicate `tune.py` with weaker checks | Do-not-retry unless: upstream ships eval records with ≥3 reps per arm that the incumbent instruments cannot reproduce |

## 9. Proposed changes (none landed by this PR)

| issue | change | rationale | pin | owner | rollback |
| --- | --- | --- | --- | --- | --- |
| #68 | gate one "rule, not story" sentence into the doctrine | t2/D9 3/3 vs 0/3; tension with "cache the reason" named | candidate SKILL.md:28 at 5f41df1 | repo | revert the sentence |
| #69 | gate bullet form of help-as-cache and no-op rules; a description that names slimming an existing skill | tuner 0/3 vs ancestor 3/3; skill-tuner self-invoked 0/3 | ancestor 3216582 lines 79, 81 | repo | revert |
| #70 | doctor.sh bytes line and relative-link check | incumbent gap; static | candidate `check` behaviour at 5f41df1, not its code | repo | revert |

## 10. Shared versus target-specific findings; dropped hits

Shared (artifact, per revision): no network egress in scripts; `score` defects (#22); model-invoked against own advice;
no revision pin. T1-specific: the two activation findings and the routing miss (#69). T2-specific: the collision with
writing-for-agents and the 304-char listing cost. Dropped discovery hits with reasons are listed in section 1.4.

## 11. Audit dividend and do-not-retry

- Upstream `nicobailon/skill-diet#22` (filed 2026-10-28 by a third party) reproduced in full at 5f41df1; nothing new to
  file upstream from this run.
- `tune.py compare` writes `reports/compare_log.jsonl` relative to the cwd; a dry run from the worktree left a stray
  file (removed; papercut logged). `aggregate.py` runs it from scratch for that reason.
- `tune.py` cannot run under `python3 -I`: `import portfolio` / `import compare` need the script directory on
  `sys.path`. Harmless for the repo's own use; a trap for callers that isolate untrusted inputs.
- Grader: K1 regex widened before the batch (smoke run); K5/D1 regex missed three rule phrasings; D9 counts a one-line
  rationale as story. Fixed only in the record, not retroactively in scores.
- Slash-expanded skills leave no Skill tool_use in `stream-json`; invocation evidence for a slash arm is the init
  skills list plus reference reads.
- Discovery: the Harbor pass ran five GitHub queries against a four cap.
- Repo-level dividend: #69 (doctrine rules present but inactive in 3/3; description does not fire on a slimming brief).

Do-not-retry the whole-candidate question unless: a new upstream revision changes the frontmatter invocation mode or
description, or ships eval records with ≥3 reps per arm, or the skill-tuner doctrine changes in a way that makes the
C5 or C13/C11 items moot (gate outcome of #68/#69).

## 12. Closing checklist

- [x] Candidate readable in scratch at a resolved commit; install state and prior verdict written before reading.
- [x] Discovery: 9 cells covered, 4 passes with seeds, stop (b) recorded as incomplete, 44 contenders with lane/pass,
      drops with one-line reasons, mirrors collapsed, slate ≤3 with the ancestor in slot 1.
- [x] Digest frozen and carried into every reader and verifier prompt.
- [x] Every component in a reader report; unread files listed (none in the candidate).
- [x] Verifiers default REFUTED; each CONFIRMED cites file:line or a command run.
- [x] Fixture predeclared; arms isolated; N=3; invocation logged separately; blinding scan clean; identical items dropped;
      normalized gain beside absolute; paired instrument rendered the formal verdicts; displacement control run.
- [x] Price measured with the incumbent's own instrument.
- [x] Verdict per component per target; every SKIP carries a do-not-retry condition.
- [x] Nothing installed; no doctrine sentence landed; ports proposed in #68, #69, #70 with pins and rollbacks.
- [x] Fixture and per-run records committed under `experiments/`; candidate and contender text not copied into the repo.
