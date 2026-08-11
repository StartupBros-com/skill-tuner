# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 15 trial(s), $3.2585 spent
- verify: 132 trial(s), $1.9094 spent

## Run manifest

- run: `batch3-probe-fresh` (2026-08-10T23:51:01Z → 2026-08-11T00:34:13Z)
- claude CLI: `2.1.224` | skill-tuner: `0.7.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ 2917224d90e0 |
| target | `/home/will/dotfiles/claude/skills-local/papercut/SKILL.md` | `9c1d48a3d74e` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | `277645e3ec2e` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/stash-mining/SKILL.md` | `95d459a0b6cf` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/verify/SKILL.md` | `eac2b1c41ea1` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/verify-review/SKILL.md` | `c8681e193e60` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/ssh-local/SKILL.md` | `5af00e3203d8` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/kill-ai-slop/SKILL.md` | `0979bb273dbe` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/improve-animations/SKILL.md` | `117304d5682d` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/review-animations/SKILL.md` | `61cf8ac0c4c8` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/pick-ui-library/SKILL.md` | `4b889bd6c083` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/prototype/SKILL.md` | `2ad8401c4dea` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/scaffold-agents-md/SKILL.md` | `a123016fd704` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/memory-mine/SKILL.md` | `836b0a2e55ce` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/hov-brand-voice/SKILL.md` | `8c71af1d80f5` | worktree @ cf3033257c8f |
| target | `/home/will/dotfiles/claude/skills-local/system-performance-remediation-local/SKILL.md` | `2bab889d51b7` | worktree @ cf3033257c8f |

## Marginal-value probe verdict

**findings_confirmed: 21**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- targets: 15
- probe calls: 15
- verify calls: 132 (3 skeptic(s) per finding)
- refuted: 23
- overflow (beyond max_findings cap, not verified): 3

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/papercut/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md` | 3 | 0 |
| `/home/will/dotfiles/claude/skills-local/stash-mining/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/verify/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/verify-review/SKILL.md` | 1 | 4 |
| `/home/will/dotfiles/claude/skills-local/ssh-local/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/kill-ai-slop/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/improve-animations/SKILL.md` | 1 | 0 |
| `/home/will/dotfiles/claude/skills-local/review-animations/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/pick-ui-library/SKILL.md` | 0 | 1 |
| `/home/will/dotfiles/claude/skills-local/prototype/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/scaffold-agents-md/SKILL.md` | 0 | 2 |
| `/home/will/dotfiles/claude/skills-local/memory-mine/SKILL.md` | 1 | 0 |
| `/home/will/dotfiles/claude/skills-local/hov-brand-voice/SKILL.md` | 1 | 4 |
| `/home/will/dotfiles/claude/skills-local/system-performance-remediation-local/SKILL.md` | 4 | 1 |

### Confirmed findings

- **Duplication via polarity (Pruning and drift / single source of truth)**: This is the negated restatement of the rule the sentence immediately before it already gives positively: "Duplicates are fine and in fact wanted... repetition is exactly how something gets prioritized." The doctrine names this exact pattern — an instruction that restates, negated, a rule already given positively is the same meaning written twice — and separately warns that negation drags the discouraged behavior (suppressing) into context rather than reinforcing only the wanted one.
  - quote: "Never suppress a papercut because you suspect it was logged before."
  - proposed fix: Delete the sentence and fold its intent into the preceding one, e.g. "Duplicates are fine and in fact wanted — always log one even if you suspect it's already there — since the rollup ranks by how many distinct sessions hit a signature."
  - target: /home/will/dotfiles/claude/skills-local/papercut/SKILL.md
- **Pruning and drift — duplication disguised as polarity ("an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror")**: Every bullet here is the negated restatement of a rule the document already states positively elsewhere: 'rm instead of git rm' mirrors Top 5 #1 and the Safety kernel's '`git rm`, never `rm`'; the `.gitignore` bullet mirrors Top 5 #2 and the kernel's shadowing-audit bullet; 'Deleting on filename alone' mirrors Top 5 #5 and the kernel's reference-check bullet; 'Batch-deleting after one yes' mirrors the kernel's verbatim-authorization bullet; the `sed` bullet mirrors Top 5 #3; 'Pushing the recovery branch' mirrors the kernel's 'never push'. This is the exact duplication-by-polarity pattern the doctrine names — the same meanings written a third time, inflating their rank on the ladder and adding maintenance/token cost with no new information.
  - quote: "## Anti-patterns

- **`rm` instead of `git rm`** — the single most common irreversible mistake.
- **`.gitignore` add without the `git ls-files` shadowing audit** — silently masks tracked files.
- **Deleting on filename alone** — always reference-grep; a junky name can be a load-bearing fixture.
- **Batch-deleting after one "yes"** — deletes are per-plan verbatim, individual, backed up first.
- **Rewriting source refs with `sed`** — Edit-tool, one at a time, logged.
- **Pushing the recovery branch** — the user pushes; the recovery story must outlive the run."
  - proposed fix: Delete the Anti-patterns section entirely, or replace it with a one-line pointer back to Top 5 mistakes / Safety kernel (e.g. 'See Top 5 mistakes and Safety kernel above — every failure mode is listed there once.') rather than restating each rule negated.
  - target: /home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md
- **Pruning and drift — single source of truth (each meaning kept in one authoritative place)**: This bullet repeats, almost component-for-component, what 'The One Rule' callout already states at the top of the document ('Build the recovery net first (pre-mutation file copies + path manifest + content hashes + `.gitignore` snapshot), verify it, then mutate'). Both list the same four artifacts and the same verify-before-mutate requirement, and even use two different names for the same object ('recovery net' vs 'recovery bundle'), which dilutes a single leading-word anchor into two.
  - quote: "**Backup before destructive.** Copy every candidate's current content + a path manifest + content
  hashes + a `.gitignore` before/after snapshot into a recovery bundle; verify byte-equality. Git
  history is the backstop for tracked files; the bundle recovers untracked ones."
  - proposed fix: Keep the enumerated artifact list only in 'The One Rule' callout; shorten the Safety kernel bullet to a one-line pointer, e.g. '**Backup before destructive.** Build the recovery net per The One Rule above; verify byte-equality before any mutation.' Standardize on one term ("recovery net") throughout.
  - target: /home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md
- **Pruning and drift — relevance and sediment (every line must still bear on what the document does)**: This is a permanently-loaded HTML comment (raw text is visible to the agent even though it renders invisibly in Markdown) describing the skill's editorial lineage from a retired 120-file predecessor. It has no bearing on how to triage repo junk — it's provenance metadata, not execution guidance — and pays context load on every load of the skill for zero routing or task value.
  - quote: "<!-- Distilled 2026-07-04 from the retired 120-file `git-repo-janitor` skill: kept the
     25-axiom safety kernel + 7-verdict taxonomy; dropped the multi-agent swarm tiers,
     wizard adjudication, multi-model triangulation, session-mining, and 31 subagents. -->"
  - proposed fix: Remove the comment from the skill body; if the lineage is worth preserving, put it in a commit message or CHANGELOG entry outside the always-loaded skill file.
  - target: /home/will/dotfiles/claude/skills-local/repo-junk-triage/SKILL.md
- **Relevance and sediment [craft] — every line must still bear on what the document does**: This comment describes the skill's own editorial history (what was distilled from and dropped) rather than anything needed to mine, verify, recover, or drop stashes. It never bears on the task the agent executes when this skill fires, so it costs context load on every invocation for information relevant only to a human maintainer reviewing the diff.
  - quote: "<!-- Distilled 2026-07-04 from the retired 81-file `git-stash-janitor` skill: kept the
     14-axiom kernel (stash-as-merge-commit, the format-patch footgun, index-shift-safe
     dropping) + 5-verdict taxonomy; dropped the swarm tiers, wizard adjudication,
     multi-model triangulation, session-mining, and 18 subagents. -->"
  - proposed fix: Remove the comment from the skill body; put the provenance note in the commit message or changelog for the distillation instead.
  - target: /home/will/dotfiles/claude/skills-local/stash-mining/SKILL.md
- **Demand — criteria mixing checkable and uncheckable terms**: Every other item in this list is a literal, grep-able string pattern, but "hardcoded tokens" is not a pattern at all — it requires the agent to judge what counts as a hardcoded token. Per the doctrine's Demand rule, one uncheckable qualifier stitched into an otherwise precise list lets the agent satisfy the whole audit impressionistically rather than mechanically, undermining the checkability of the rest of the list.
  - quote: "**Secrets** — flag patterns: `sk-`, `sk_live`, `pk_live`, `api_key=`, `secret=`, `password=`, hardcoded tokens"
  - proposed fix: Either drop "hardcoded tokens" (the listed literal patterns already cover the common cases) or replace it with a concrete, checkable pattern, e.g. a regex for long base64/hex strings assigned to variables named `token`, `key`, or `secret`.
  - target: /home/will/dotfiles/claude/skills-local/verify/SKILL.md
- **Cut identity the body already states**: The description (an always-loaded pointer) restates the entire 'junior developer' framing and the four-verdict taxonomy, both of which are given in full in Step 2's canonical blockquote and Step 4's verdict table. This is identity the body already states, spending permanent context load on content with no routing signal — the description's job is to say when to reach the skill, not to pre-summarize its internal framing and outputs.
  - quote: "Treats every finding as flagged by a junior developer who may not fully understand the codebase, and uses the current session's implementation context to decide whether each is a real issue, a misunderstanding, over-engineering, or overly cautious."
  - proposed fix: Trim the description to the routing-relevant facts: what artifact it verifies, and that it must run in the originating chat, e.g. "Forensic skeptical verification pass over /ce-code-review findings, using this session's implementation context to catch reviewer misunderstandings. Run in the same chat that produced the diff." Drop the verdict-taxonomy sentence entirely — it belongs only in Step 4.
  - target: /home/will/dotfiles/claude/skills-local/verify-review/SKILL.md
- **Cut identity the body already states [craft]**: The description's opening clause ("connections, tunnels, keys, file transfers") restates almost word-for-word what the body's own Core Capability line already says ("> **Core Capability:** Secure shell connections, key management, tunneling, and file transfers."). This is identity the body already states, adding permanent context load on every load with zero routing signal, since it does not tell the agent *when* to reach the skill.
  - quote: "SSH remote access - connections, tunnels, keys, file transfers, plus agent-safe"
  - proposed fix: Drop the identity restatement from the description and keep only the branch triggers: e.g. "Use when connecting to servers, ssh/scp/rsync, tunneling, or an agent needs to run a remote command headless; also covers this machine's host inventory (mac-mini) and agent-safe non-interactive flags." Let the body's Core Capability line own the identity statement.
  - target: /home/will/dotfiles/claude/skills-local/ssh-local/SKILL.md
- **Single source of truth / duplication [craft]**: This command is an almost-verbatim repeat of the password-auth recipe already given in the Non-Interactive section (identical flags, only the hostname and trailing command differ). The same meaning — the non-interactive password-auth invocation — lives in two places, so a future flag change (e.g. adding a new safety option) requires editing both and risks drift.
  - quote: "SSHPASS="$secret" sshpass -e ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
    -o PreferredAuthentications=password -o PubkeyAuthentication=no mac-mini 'hostname'"
  - proposed fix: In the Known Hosts section, don't restate the full command; instead reference the recipe above, e.g. "Use the password-auth recipe above with `mac-mini` in place of `user@host`."
  - target: /home/will/dotfiles/claude/skills-local/ssh-local/SKILL.md
- **Duplication / sediment [craft]**: This comment repeats the document's own section headings verbatim with no additional information, meaning it is loaded into context on every use for zero routing or navigation benefit beyond what the markdown headers already provide.
  - quote: "<!-- TOC: Non-Interactive (agents) | Known Hosts | Quick Start | Common Workflows | Essential Commands | Config | AGENTS.md Blurb | References -->"
  - proposed fix: Remove the TOC comment; the `##` headings already give the agent (and any renderer) the document structure.
  - target: /home/will/dotfiles/claude/skills-local/ssh-local/SKILL.md
- **Cut identity the body already states [craft]**: This enumerates the full 34-tell catalogue that already lives in references/taxonomy.md. The description's job is to state when to reach for the skill, not to restate what the skill's body/references already document about itself — this is permanent load with no added routing signal.
  - quote: "Detects and fixes the catalogue of tells: indigo→violet gradients, gradient-clip headlines, the default semantic palette, one-hue status boxes, atmospheric gradients, serif-italic emphasis, highlighted keywords, AI copywriting voice ("not just X — it's Y"), emoji everywhere, glowing status dots, colored-left-border callouts, pastel icon tiles, glassmorphism, over-rounding, oversized shadows, borders that die at corners, badge & pill spam, AI-drawn SVG icons, kickers over every heading, flat type hierarchies, invented stat rows (10k+ / 99.9% / 24/7), 01/02/03 section markers, cards nested in cards, the default Inter/Space Grotesk look, and more."
  - proposed fix: Cut the list to a short characterization (e.g. "Detects and fixes the catalogue of generic AI-default visual and copy tells") and point to references/taxonomy.md for the enumerated list.
  - target: /home/will/dotfiles/claude/skills-local/kill-ai-slop/SKILL.md
- **Relevance and sediment**: This is leftover upstream description that was never scrubbed for the local fork. The 'LOCAL FORK' callout, Hard Rule 1 ('Never modify source code, and never write plan files'), and Phase 4 ('This skill does not plan, implement, or track... Do not pre-empt any of that by writing files yourself') all state the opposite: this skill stops at findings and hands planning to ce-plan. An agent reading only the top of the document would believe writing implementation plans is in scope, then hit a directly contradicting Hard Rule a few paragraphs later — sediment from the pre-fork version left in place, exactly the failure mode the doctrine warns adding-feels-safe/removing-feels-risky produces.
  - quote: "It does ONE thing: survey animation and motion code, then produce prioritized findings and implementation plans."
  - proposed fix: Change the sentence to match the fork's actual scope, e.g. 'It does ONE thing: survey animation and motion code, then produce prioritized, vetted findings — it does not write plans (see Handoff).' Also revise the preceding sentence ('...writing the spec — and hand execution to any agent') so it doesn't imply this skill authors the spec itself; that's ce-plan's job in this fork.
  - target: /home/will/dotfiles/claude/skills-local/improve-animations/SKILL.md
- **Cut identity the body already states [craft] — a pointer restating what the body says about itself adds permanent context load for no routing signal.**: The frontmatter description restates, almost word-for-word, the Operating Posture line in the body ("Default to flagging. Approval is earned, not assumed."). The description's job is to say when to reach the skill, not to re-declare a posture the body immediately states again — this is identity duplication that costs tokens on every load of the file with no added routing signal.
  - quote: "Default to flagging; approval is earned."
  - proposed fix: Trim the description to what helps selection/routing (e.g. "Reviews animation and motion code against Emil Kowalski's high-craft animation standards.") and let the Operating Posture section in the body be the single place "default to flagging" is stated.
  - target: /home/will/dotfiles/claude/skills-local/review-animations/SKILL.md
- **Completion criteria — criteria must be checkable, and mixing checkable with uncheckable terms lets the agent satisfy the whole thing impressionistically**: This is the explicit completion criterion for Phase 5, but it mixes checkable clauses ("reachable from the picker", "no console errors") with uncheckable qualifiers ("behaves correctly", "honestly"). "Behaves correctly" and "honestly" require judgment calls with no stated test, so the agent can satisfy the whole bound impressionistically by treating the vague terms as met without verification, exactly the failure the doctrine names: 'one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.'
  - quote: "every variant is reachable from the picker and behaves correctly; no console errors; the table names each variant's tradeoff honestly."
  - proposed fix: Replace the vague qualifiers with checkable tests, e.g.: "every variant is reachable from the picker; every specified interaction (hover, click, keyboard) produces its stated response; no console errors or warnings; the table states one concrete benefit and one concrete cost per variant, each tied to a named scenario."
  - target: /home/will/dotfiles/claude/skills-local/prototype/SKILL.md
- **Leading words — a coined term recruits no priors and must be defined, or it pays load without giving the agent anything to think with**: "The frequency rule" is invoked as if it were an established, already-understood principle, but it is never defined anywhere in the document. Unlike a pretrained term (e.g. "lesson", "tracer bullet"), this is a coined label with no prior definition supplied, so the agent has no way to apply it beyond this single sentence — it reads as an appeal to unstated authority rather than a usable concept.
  - quote: "by the frequency rule the variant swap gets no animation"
  - proposed fix: Either define the term inline ("by the rule that the more often an interaction repeats, the less motion it should carry") or drop the label and state the guidance directly: "switching is instant with no animation — flipping happens 100+ times per session, and animating a high-frequency action only adds friction."
  - target: /home/will/dotfiles/claude/skills-local/prototype/SKILL.md
- **Single source of truth (Pruning and drift)**: This stat is fully restated in the body — 'directed capture lifted recall 16.1% → 74.2% on a frozen session-derived suite' — with a citation path. Keeping the same fact in both the description and the body is duplication of meaning, not a leading-word repetition, and it has already drifted: the description rounds to 16%/74% while the body gives 16.1%/74.2%. That's the exact maintenance-cost the doctrine warns about — two numbers for one fact, now disagreeing.
  - quote: "The write-path fix measured by the 2026-07 memory face-off (16% -> 74% recall)."
  - proposed fix: Drop the stat from the description (keep only 'Additive-only; the dream pass consolidates later' plus a short when-to-reach cue) and leave the precise 16.1%→74.2% figure with its citation as the single authoritative statement in the body's Evidence line.
  - target: /home/will/dotfiles/claude/skills-local/memory-mine/SKILL.md
- **Single source of truth [craft]**: This standalone '## Reference' section restates, almost verbatim, what Step 1 of the Application Workflow already says ('Open `references/house-of-vibe-brand-voice.md` for the complete voice guide, SSR-validated copy patterns, and CTA rules'). Same pointer, same target, same identity description given twice in the body — duplication that inflates the reference file's apparent importance without adding routing signal.
  - quote: "For the complete brand voice guide with SSR-validated copy patterns, CTA rules, hero copy, guarantee copy, and funnel-stage deployment strategy, see `references/house-of-vibe-brand-voice.md`."
  - proposed fix: Remove the separate '## Reference' section and let Step 1 of the Application Workflow be the single pointer to the reference file; fold any unique detail (hero copy, guarantee copy, funnel-stage deployment strategy) into that one mention.
  - target: /home/will/dotfiles/claude/skills-local/hov-brand-voice/SKILL.md
- **Single source of truth / Duplication [craft]**: This is the identical fix already given verbatim under 'Fix: Tune VM Parameters' → 'Apply immediately' (`sudo sysctl -w vm.vfs_cache_pressure=200 vm.min_free_kbytes=2097152`). The same meaning — the VM tuning remediation values — is authored twice in two separate procedural sections, so changing the recommended values requires a two-place edit and the doc pays double token cost for one fact.
  - quote: "# 2. Fix VM tuning (the root cause on most heavy-workload machines)
sudo sysctl -w vm.vfs_cache_pressure=200 vm.min_free_kbytes=2097152"
  - proposed fix: In 'Full Memory Pressure Remediation' step 2, replace the repeated command with a pointer back to the earlier section, e.g. "Apply the VM tuning fix (see 'Fix: Tune VM Parameters' above)."
  - target: /home/will/dotfiles/claude/skills-local/system-performance-remediation-local/SKILL.md
- **Single source of truth / Duplication [craft]**: The drop_caches command is written out in full three times: under 'Fix: Tune VM Parameters', under 'Quick Cache Drop (Safe)', and again under 'Full Memory Pressure Remediation' step 3. This is the same meaning restated three times rather than defined once and referenced.
  - quote: "sudo sh -c "sync; echo 3 > /proc/sys/vm/drop_caches"  # Drops clean page cache, dentries, inodes"
  - proposed fix: Keep the canonical form only in 'Quick Cache Drop (Safe)' and have the other two sections reference it by name instead of repeating the full command.
  - target: /home/will/dotfiles/claude/skills-local/system-performance-remediation-local/SKILL.md
- **Completion criteria [craft]**: The table states a single '5+ min' threshold for both vercel and git add, but the implementing commands under 'Stuck Vercel/Git Commands' use `$2 > 600` (10 min) for vercel and `$2 > 120` (2 min) for git add — neither matches the stated '5+ min', and the two differ from each other. The agent has no way to know which number is authoritative.
  - quote: "| 5 | **Stuck CLI** | `vercel inspect`, `git add .` 5+ min | Low — restart-safe |"
  - proposed fix: Update the table row to reflect the actual implemented thresholds, e.g. "`vercel inspect` 10+ min, `git add .` 2+ min".
  - target: /home/will/dotfiles/claude/skills-local/system-performance-remediation-local/SKILL.md
- **Demand — checkable completion bound [craft]**: This is the completion condition for step 4 of 'Full Memory Pressure Remediation', but 'dropping rapidly' has no checkable bound — the document elsewhere defines a concrete threshold (avg10 < 5% is 'Healthy') that this step could have used instead.
  - quote: "# avg10 should be dropping rapidly"
  - proposed fix: Replace with a checkable bound consistent with the thresholds table already in the doc, e.g. "avg10 should be trending toward <5% (the Healthy threshold from the pressure table above)."
  - target: /home/will/dotfiles/claude/skills-local/system-performance-remediation-local/SKILL.md

### Refuted findings

- **One trigger per branch** — verifier: These five examples all route to the exact same action (log a papercut via `papercut add`) — none diverges into a different path, which is the doctrine's test for collapsing synonymous triggers into one. The same enumeration is then spelled out again, nearly verbatim, in the body's 'no error signature' bullet list, so the always-loaded description pays five times over to route to a single branch and duplicates content the body already states.
  - quote: "a confusing or undocumented setup step, a misleading error, a stale cache, a command that succeeded but did the wrong thing, a gotcha you had to work around"
- **One trigger per branch [craft]** — verifier: These three phrasings all describe the same single branch — a user wants to triage a pile of accumulated stashes — and route to the identical mine/verify/drop flow. None of them sends the agent down a different path than the others beside it, so per the doctrine's test they should collapse into one trigger. As written they pay context load three times for one routing signal.
  - quote: ""clean up my stashes", "stash archaeology", "are any of these stashes worth keeping""
- **Single source of truth / duplication — anti-pattern lists that restate positively-given rules negated are the same meaning written twice** — verifier: Every bullet here is the negated restatement of a rule the document already gives positively: format-patch is covered in 'The two footguns', stash pop/apply and low-index-first dropping and verbatim authorization are covered in 'Safety kernel', symbol-name-match sampling is covered in 'Archaeology' point 4, and 'never push' is stated in both the Safety kernel and the Handoff step. This is the exact anti-pattern-list duplication the doctrine calls out — it costs tokens and maintenance for zero new information, and inflates the rank of these six rules on the ladder past what a single mention would give them (the 'never push' rule alone is now stated three separate times across the document).
  - quote: "## Anti-patterns

- **`git format-patch` on a stash** — the footgun; loses untracked files. Use `stash show -p --binary`.
- **`git stash pop`/`apply`** — mutate outside the verified diff; recover via the bundle diff instead.
- **Dropping low-index-first** — indexes shift; drop highest-first and re-resolve messages.
- **Classifying `superseded` on a symbol-name match** — sample signatures first.
- **Batch-dropping after one "yes"** — every drop is per-plan verbatim, individual, backed up.
- **Pushing the recovery branch** — the user pushes; the recovery story must outlive the run."
- **Completion criteria — contradictory bounds** — verifier: The Modes table states the default phases are format → lint → typecheck, but this rule's closing clause, "Only typecheck matters," reads as a competing, narrower completion bound that appears to contradict running format and lint at all. The agent has no way to tell whether "only typecheck matters" overrides the three-phase default or is merely a rationale for skipping build — the same ambiguity the doctrine flags when a general bound and a specific one disagree.
  - quote: "**Never** run `pnpm build` as part of standard verify — it's slow and not needed for code quality checks. Only typecheck matters."
- **Single source of truth / duplication** — verifier: This operational constraint is already stated in the description ('Run in the same chat that produced the diff.'). Restating it as the opening line of the body is the same meaning in two places, inflating its apparent importance and creating a maintenance seam if the wording ever needs to change.
  - quote: "Run this in the **same chat session that produced the code under review**."
- **Completion criteria** — verifier: This is the checkable-completion bound for what a `confirmed` finding's fix description must satisfy, but it is entirely subjective — there is no way for the agent to tell 'done' from 'not-done' without judgment. It reads as emphasis rather than a criterion, letting the agent satisfy it impressionistically.
  - quote: "the most elegant, permanent, world-class fix that a 10x developer would be impressed with"
- **Duplication (polarity)** — verifier: This negated boundary restates, in reverse polarity, the definition of `needs-deeper-look` already given positively in Step 4's verdict table ('Cannot determine from this session's context. Needs more investigation before fixing or dismissing.'). It's the same rule written twice under the guise of a guardrail.
  - quote: "Do not silently downgrade a real issue. If the finding is genuinely ambiguous, the correct verdict is `needs-deeper-look`, not a soft dismissal."
- **Negation without a positive target** — verifier: This prohibition leads with the ban and never says what to do instead — 'Not in scope' just restates the negation rather than pairing it with a positive target, which the doctrine requires even for hard guardrails.
  - quote: "Do not commit, push, or open PRs.** Not in scope."
- **One trigger per branch [craft]** — verifier: "port forwarding" and "tunnels" both route to the same section (Local Port Forward / SSH Agent forwarding), so they are two synonyms naming one branch rather than two distinct branches. A run reaching the doc through "port forwarding" takes the same path as one reaching it through "tunnels".
  - quote: "Use when connecting to servers, ssh/scp/rsync, port
  forwarding, tunnels, or an agent needs to run a remote command headless."
- **One trigger per branch [craft]** — verifier: These four phrasings all route to the same single branch (invoke the whole skill) — there's no differentiated behavior per phrase. Listing synonyms for one branch pays token cost repeatedly for a single routing decision.
  - quote: "Use when the user asks to "kill AI slop", "de-slop", "remove the AI look", "make this not look AI-generated", or clean up a landing page / UI / docs that feels templated."
- **Negation [research]** — verifier: This names the banned behavior without stating the positive target in the same breath, which the doctrine requires even for hard guardrails — the negation strengthens the very concept (reformatting) it's meant to suppress.
  - quote: "Never reformat unrelated code."
- **Negation [research]** — verifier: This leads with the ban and never states what to do instead in the same sentence, activating the forbidden "mass-edit" concept rather than anchoring on the desired behavior.
  - quote: "Do not mass-edit before the user has seen the report."
- **Duplication / single source of truth — 'an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror.'** — verifier: Most of the Aggressive Escalation Triggers list is the same meaning as the Ten Non-Negotiable Standards written a second time in negated/pattern form: ease-in ↔ Standard 3, keyboard/high-frequency animation ↔ Standard 2, >300ms ↔ Standard 4, center-origin popover ↔ Standard 5, keyframes on toasts ↔ Standard 6, layout-property animation ↔ Standard 7, missing reduced-motion / ungated hover ↔ Standard 8, symmetric timing ↔ Standard 9. This is the polarity-disguised duplication the doctrine specifically calls out, and it inflates both sections' apparent weight without adding new meaning.
  - quote: "- `ease-in` on any UI interaction; weak built-in easing on a deliberate animation
- Animation on a keyboard shortcut, command-palette toggle, or 100+/day action
- UI duration > 300ms with no stated reason
- `transform-origin: center` on a trigger-anchored popover/dropdown/tooltip
- Keyframes on toasts, toggles, or anything added/triggered rapidly
- Animating layout properties (`width`/`height`/`margin`/`padding`/`top`/`left`)
- Missing `prefers-reduced-motion` handling on movement
- Ungated `:hover` motion
- Symmetric enter/exit timing on a press-and-release or hold interaction"
- **Completion criteria / Demand — 'Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.'** — verifier: The Approve bound mixes checkable clauses (durations/easing within bounds, reduced-motion respected) with impressionistic qualifiers ("no obvious motion," "handled where needed") that require judgment rather than a yes/no check. The Block bound has the same problem ("a non-GPU animation with an easy GPU fix" — "easy" is not checkable). A reviewer can satisfy the whole verdict by judgment call on the hedged terms alone, undermining the 'default to flagging' posture the skill otherwise insists on.
  - quote: "**Approve** — no feel-breaking regressions, no obvious motion that should be deleted, durations and easing within bounds, interruptibility handled where needed, reduced-motion respected."
- **Pruning and drift — Single source of truth / duplication (the commonest disguise is polarity: an anti-pattern list restating, negated, rules the document already gives positively)** — verifier: Each bullet restates a task→library mapping already given in the table above (Toasts→Sonner, UI primitives→base-ui, Animating numbers→NumberFlow, Virtualization→Virtuoso, State management→zustand, className conditionals→clsx/cva), just wrapped in a 'symptom' framing instead of a task framing. This is the same meaning written twice: step 1 already instructs the agent to 'identify the task, not the library the user named,' which is exactly the translation this section performs redundantly. It costs load and creates a second place that must be kept in sync with the table if a pick ever changes.
  - quote: "## Common mismatches to catch

- **Toasts built by hand or with a modal library** → Sonner exists for exactly this.
- **A `<div>`-based dropdown/dialog with manual focus handling** → base-ui, which handles accessibility, focus trapping, and dismissal.
- **Animating a number by re-rendering text** → NumberFlow handles digit transitions properly.
- **Rendering a 1,000+ row list directly** → Virtuoso before reaching for pagination hacks.
- **A `useState`-per-component web of props for shared state** → zustand.
- **Template-literal className ternaries three conditions deep** → clsx (or cva if it's variant-shaped)."
- **Single source of truth — keep each meaning in one authoritative place; duplication costs maintenance and tokens** — verifier: Hard Rule 4 already states this exact meaning: "Its exact markup, styles, and behavior are specified in [PICKER.md](PICKER.md) — copy them verbatim." Phase 4 restates it rather than cross-referencing back to the rule. The document demonstrates the correct pattern elsewhere — Phase 6 says "delete the prototype surface per Hard Rule 5" instead of re-explaining the cleanup rule — making this restatement in Phase 4 an inconsistent duplication of the same meaning in two places, so changing the PICKER.md instruction later requires editing both spots.
  - quote: "The picker's markup, styles, keyboard wiring, and placement come from [PICKER.md](PICKER.md), verbatim — load it now and build exactly that."
- **Completion criteria — contradictory bounds** — verifier: This mandates a fixed, generic sentence in every generated AGENTS.md, which is boilerplate by definition — yet the skill's own description says "repo-specific content only, no boilerplate" and step 3's preamble says "every line repo-specific — never restate global rules." The doctrine treats a general ceiling in one place crossed by a specific instruction elsewhere as "a completion defect in the same family: the agent cannot tell whether a value between them complies, whichever bound it obeys." Here the agent can't tell if the literal closing text is a mandated exception to "no boilerplate" or a violation of it.
  - quote: "Closing: "Verify your work. If any command fails or you couldn't run it, say which and why.""
- **Single source of truth** — verifier: This enumerates specific global conventions to write into the forked repo's file, duplicating content that — per the very next step's instruction, "never restate global rules from ~/.claude/CLAUDE.md" — is supposed to live only in the global CLAUDE.md. The document tells the agent not to restate global rules while simultaneously listing which global rules to restate, an internal contradiction about the same meaning (house rules) in two places.
  - quote: "house rules (pnpm/uv, worktrees + draft PRs, conventional commits) still apply here"
- **One trigger per branch [craft]** — verifier: The trailing catch-all 'or any customer-facing content for House of Vibe' already subsumes 'marketing copy, landing pages, sales pages, emails, ads, social posts' — none of those route the agent to different handling than the catch-all does. Per the doctrine's test ('does a run reaching the document through this phrase take a different path than a run reaching it through the one beside it? If not, collapse them'), this is one branch enumerated seven times plus a catch-all, paying context load on every turn for no added routing signal.
  - quote: "Use when writing or editing marketing copy, landing pages, sales pages, emails, ads, social posts, workshop copy, member communications, or any customer-facing content for House of Vibe."
- **Cut identity the body already states [craft]** — verifier: This sentence describes what the document contains (a table of contents), not when to reach for it. The body's own H1 and first line ('Machine-readable brand voice guide for House of Vibe (houseofvibe.ai)') already establish identity; this description sentence adds no routing signal, only permanent per-turn context load restating what the skill is.
  - quote: "Covers voice pillars, member terminology, anti-patterns, CTA rules, and funnel-stage tone guidance."
- **Demand [craft]** — verifier: The list mixes checkable criteria ('anti-patterns' and 'correct terminology' are both enumerable against fixed lists earlier in the doc) with an uncheckable one ('funnel-appropriate pillar balance' has no stated ratio or measurable bound — 'proportions shift by funnel stage' is never quantified). Per the doctrine, one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole step impressionistically.
  - quote: "Verify against the quality checklist in the reference doc. Check for anti-patterns, correct terminology, and funnel-appropriate pillar balance."
- **Single source of truth — duplication disguised as polarity [craft]** — verifier: This anti-pattern restates, in negated form, a rule the document already gives positively in Locked member terminology: 'Enter the House (not enroll/sign up)'. Both entries tell the agent not to use 'enroll' — the same meaning written twice, once as a generic negative ban and once as a positive substitution. The doctrine flags exactly this pattern: audit anti-pattern lists against the positive rules they mirror.
  - quote: "Course language (no "modules," "lessons," "enroll," "syllabus")"
- **Completion criteria [craft]** — verifier: This diagnostic applies a single blanket 1-hour (3600s) threshold to bun test, cargo test, vercel, and git add together, but the document elsewhere gives each pattern a different, contradicting threshold: the Kill Hierarchy table and the 'Stuck Tests (12+ hours)' section use 43200s for tests, while 'Stuck Vercel/Git Commands' uses 600s and 120s respectively. A process at, say, 2 hours would show up as 'stuck' here but not qualify for action under the later, authoritative thresholds — the agent cannot tell which bound governs.
  - quote: "ps -eo pid,etimes,pcpu,args --sort=-etimes | grep -E 'bun test|cargo test|vercel|git add' | awk '$2 > 3600'"
