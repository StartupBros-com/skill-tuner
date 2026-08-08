# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 16 trial(s), $4.3103 spent
- verify: 153 trial(s), $3.0280 spent

## Run manifest

- run: `swapgate3-probe-candidate` (2026-08-07T23:51:33Z → 2026-08-08T00:49:00Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/skills/skill-tuner/SKILL.md` | `48b5df5d70d9` | git:origin/main @ 32c9b18bf6d3 |
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

**findings_confirmed: 19**

- doctrine: /home/will/SITES/skill-tuner/skills/skill-tuner/SKILL.md
- targets: 16
- probe calls: 16
- verify calls: 153 (3 skeptic(s) per finding)
- refuted: 32

### Per target

| Target | confirmed | refuted |
| --- | --- | --- |
| `/home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md` | 2 | 3 |
| `/home/will/dotfiles/claude/skills-local/animate/SKILL.md` | 0 | 3 |
| `/home/will/dotfiles/claude/skills-local/apple-design/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | 0 | 4 |
| `/home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md` | 3 | 2 |
| `/home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | 2 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md` | 3 | 1 |
| `/home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/codex-consult/SKILL.md` | 0 | 2 |
| `/home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md` | 1 | 3 |
| `/home/will/dotfiles/claude/skills-local/design-drift/SKILL.md` | 1 | 1 |
| `/home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md` | 1 | 2 |
| `/home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md` | 1 | 1 |

### Confirmed findings

- **Single source of truth — duplication of one meaning across sections**: This restates, nearly verbatim, the rule already given under 'Pick the lightest engine that fits': 'Pin `model` (sonnet/haiku for mechanical sweeps — don't let them inherit the session model).' The same meaning (pin model or it silently inherits the session model) is asserted in two places instead of stated once and referenced.
  - quote: "Pass `model` explicitly — unpinned subagents silently inherit the session model."
  - proposed fix: State the model-pinning rule once (e.g. under Cost routing) and have the engine-picking section reference it rather than restate it.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Leading words — a coined term must be defined, not assumed**: 'Doghouse' is used as if it were a known term but is never defined anywhere in the document. Per the leading-words rule, a coined term recruits no priors and must pay its own definition cost; here it's used bare, forcing the reader/agent to guess its meaning.
  - quote: "If Codex is unavailable (doghouse tripped, auth outage), fall back to a Sonnet-class subagent"
  - proposed fix: Define on first use, e.g. 'doghouse (Codex's automatic rate-limit lockout) tripped', or replace with a plain description like 'Codex rate-limited'.
  - target: /home/will/dotfiles/claude/skills-local/agent-swarm/SKILL.md
- **Completion criteria [craft]**: This checklist item gives no checkable bound — 'the perception threshold' names no value or method to test against, unlike nearly every other quantitative rule in this document (10px hysteresis, 0.998 deceleration, 0.55 rubber-band constant, 0.2Hz oscillation limit). A vague bound invites the agent to consider the criterion satisfied without doing the legwork of actually checking frame deltas.
  - quote: "Keep the per-frame positional change below the perception threshold to avoid strobing."
  - proposed fix: Give a concrete, checkable bound, e.g. 'Keep per-frame positional change under ~1-2px at 60fps for slow motion; use motion blur above that.'
  - target: /home/will/dotfiles/claude/skills-local/apple-design/SKILL.md
- **Completion criteria**: The bound looks precise (a number) but 'confidence' is never defined or computed anywhere in the document — unlike the neighboring metrics fingerprint_coverage ('found-with-same-signature ÷ total') and the ≥30%/≥0.7 signature-sampling thresholds, which are explicit formulas. An agent has no way to check whether it is above or below 0.7, so the bound can't actually gate auto-classification vs. surfacing to the user; it invites the agent to eyeball 'confidence' and rationalize whatever verdict it already leans toward.
  - quote: "**Confidence < 0.7 ⇒ don't auto-classify; surface to the user.**"
  - proposed fix: Tie the threshold to a metric already defined in the doc, e.g.: 'If fingerprint_coverage and same-signature agreement can't both be computed (renamed files, empty diff, or the verdict rests on git log -S / reflog archaeology rather than direct measurement), don't auto-classify — surface the branch to the user.'
  - target: /home/will/dotfiles/claude/skills-local/branch-harmonization/SKILL.md
- **Single source of truth**: This routing rule (when not to use this skill, and which skill to redirect to) is restated in the body's "When NOT to use this skill" section: "The brand voice is already defined and encoded in a project-specific skill: use that skill directly (e.g. hov-brand-voice, prbot-brand-voice)." The two copies have already drifted out of sync -- the description lists three example skills (including email-brand-voice) while the body's list only has two -- which is exactly the maintenance cost the doctrine's Single source of truth rule warns duplication produces.
  - quote: "Does NOT apply existing voices -- for that, use the brand-specific voice skill (hov-brand-voice, email-brand-voice, prbot-brand-voice, etc)."
  - proposed fix: State the redirect rule once. Keep it in the description (needed for routing before the skill loads) and have the body's "When NOT to use this skill" bullet simply say "see description" or reuse the same canonical example list instead of a hand-maintained second copy.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Context pointer**: The description spends permanent context load enumerating the Voice Profile's full field list, but that structure is already fully and authoritatively documented in the body's "## The Voice Profile (Output Format)" template (which has more sections than are even named here: Voice Summary, Core Personality Traits, Rhythm and Structure, POV and Address, Channel and Stage Calibration, Maintenance, etc.). The Context pointer rule says the pointer should cut identity the body already states -- routing only needs to know the skill produces a Voice Profile, not the itemized field list.
  - quote: "Outputs a complete Voice Profile with tone spectrum, vocabulary, mechanical rules, on-brand and off-brand example phrases, aspiration and anti-aspiration models, and a quality test."
  - proposed fix: Trim to something like "...Outputs a structured Voice Profile document ready to encode as a project skill." and let the body's Output Format template be the sole place the field list is enumerated.
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Completion criteria / Demand**: This is offered as one of the results that mark a Voice Profile as "good," i.e. a completion bound, but "sharp enough" is an uncheckable qualifier with no objective bar for what counts as sharp. Per Completion criteria, a vague bound invites premature completion (the profile gets called done once it merely feels sharp); per Demand, the wording doesn't force the legwork a concrete bound would.
  - quote: "Mechanical rules are sharp enough to catch violations automatically"
  - proposed fix: Replace with a checkable bound, e.g. "Every Mechanical Rule is phrased so a specific violation can be pointed to in a sample sentence -- not just 'be more casual.'"
  - target: /home/will/dotfiles/claude/skills-local/brand-voice-builder/SKILL.md
- **Context pointer [craft] — keep one trigger per branch, collapse synonyms that rename a single branch**: "Google OAuth consent" (first parenthetical) and "OAuth consent screens" (final trigger list) name the same branch twice under different wording, spending extra description tokens — which are always-loaded context — on a synonym rather than a distinct trigger.
  - quote: "Set up cloud consoles that block headless automation (Google OAuth consent, Stripe webhooks, GCP credentials) by opening the exact URL in the local Windows Brave browser and handing paste-ready click steps, then wiring the reported credentials into Supabase/Vault/Vercel/.env. Use when a console step cannot be scripted: bot detection, "browser may not be secure", 2FA, CAPTCHA, or OAuth consent screens."
  - proposed fix: Drop the redundant second mention, e.g. end the trigger list with "bot detection, 'browser may not be secure', 2FA, or CAPTCHA" and let the earlier "Google OAuth consent" example cover that branch.
  - target: /home/will/dotfiles/claude/skills-local/browser-console-setup/SKILL.md
- **Progressive disclosure**: This is a model-invoked skill, so its whole body loads on every trigger regardless of heading. The repair runbook (env-var tuning, stall diagnosis, timing/memory figures) is only relevant to the rare branch where the lexical index is broken, not to the common 'search my sessions' path that most invocations take. Keeping it inline among the primary steps taxes every ordinary search with content only one branch needs, instead of pushing it behind a pointer to a separate file reached only when the index-broken branch is actually hit.
  - quote: "setsid env \
  CASS_TANTIVY_REBUILD_STAGED_MERGE_WORKERS=1 \
  CASS_TANTIVY_REBUILD_STAGED_SHARD_BUILDERS=1 \
  CASS_TANTIVY_REBUILD_PAGE_PREP_WORKERS=1 \
  CASS_TANTIVY_REBUILD_PENDING_SHARD_BUILD_MAX_JOBS=1 \
  CASS_TANTIVY_REBUILD_BATCH_FETCH_CONVERSATIONS=25 \
  CASS_TANTIVY_REBUILD_STAGED_SHARD_MAX_MESSAGE_BYTES=16777216 \
  CASS_TANTIVY_MAX_WRITER_THREADS=1 \
  nohup cass search "anything" --limit 3 > /tmp/cass-repair.log 2>&1 < /dev/null &"
  - proposed fix: Move the repair runbook (from 'That usually means the lexical index is broken' through the 'Verified 2026-07-29' line) into a separate reference file, e.g. `cass-rerank-repair.md`, and replace it in this skill with a one-line pointer: 'If cass-rerank returns no results for everything, the lexical index may be broken — see cass-rerank-repair.md for the diagnostic and inline-repair procedure.'
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Relevance and sediment**: The comment itself states that the granite-r2-vs-other-rerankers history no longer affects anything the agent does, since the gateway already fixed the model choice. A line that by its own admission doesn't bear on current behavior is sediment: it costs context load on every invocation of this model-invoked skill without informing how the agent should act.
  - quote: "The gateway lane exposes `local-rerank` only, which sidesteps that choice entirely."
  - proposed fix: Drop the granite-r2 win/loss narrative from the skill body (it belongs in a commit message or architecture doc, not an always-loaded skill), keeping only the operative fact if any is still needed, e.g. 'The gateway lane exposes local-rerank only; reranker choice is not agent-configurable.'
  - target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- **Leading words [craft]**: The axiom is displayed with the glyph ① (circled numeral 1) but is referred to in prose as 'Axiom 0'. A coined leading symbol only pays for itself if it is defined clearly and consistently; here the symbol and its name disagree, so the anchor is ambiguous rather than a clean pretrained-free concept the agent can key on.
  - quote: "**① First-try inevitability.** The first command an agent guesses must work or be redirected with a
  useful hint. A surface that fails this on its *canonical* task is a P0 finding regardless of other scores. **Axiom 0 wins ties.**"
  - proposed fix: Make the glyph and the label agree — either rename the prose to 'Axiom ① wins ties' or change the glyph to a symbol that reads as zero (e.g. ⓪) if 'Axiom 0' is the intended canonical name.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Leading words [craft]**: The same glyph 🚫 is minted as the named-operator symbol for two distinct axioms (never-silent-fail and no-bare-TUI). A leading word/symbol only anchors execution if it maps to one concept; reusing it for two different rules means neither is clearly defined and later bare references to 🚫 (e.g. in the Intent-Recovery Triad) are ambiguous without the trailing text.
  - quote: "- **🚫 Never silent-fail.** A command that fails but exits 0 with empty stdout is the agent's worst
  nightmare — it can't even detect the failure to retry. Every failure → stderr + non-zero exit.
- **🚫 No TUI on bare invocation.** Bare `<tool>` launching a TUI blocks any agent that didn't expect it.
  Either `<tool>` shows useful help/triage and exits, or `<tool> tui` is the explicit interactive entry — never both."
  - proposed fix: Give 'No TUI on bare invocation' its own distinct glyph (e.g. 🧭 or 🖥) so 🚫 uniquely identifies never-silent-fail throughout the document.
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Completion criteria [craft]**: The quantifiers (≥5, ≥3) are checkable, but 'substantive' is an uncheckable qualifier layered on top of them — an agent could satisfy the letter of the bound with five trivial edits (renames, comments) and call the gate cleared, inviting the premature-completion failure this rule warns against.
  - quote: "**Ambition gate** — ship ≥5 substantive changes across ≥3 dimensions before calling it done. A scorecard alone is not a deliverable."
  - proposed fix: Replace 'substantive' with a checkable test, e.g. '≥5 changes that alter observable CLI behavior (output, exit code, or flag semantics) — not renames or comments — across ≥3 dimensions.'
  - target: /home/will/dotfiles/claude/skills-local/cli-agent-ergonomics/SKILL.md
- **Relevance and sediment [craft]**: This is a provenance/changelog note about a retired sibling skill. It never bears on what an agent should do with the current document — it's history, not instruction or reference the task needs — so it pays context load every time the skill fires for a line that belongs in commit history rather than the instruction body.
  - quote: "<!-- Distilled 2026-07-04 from the retired 166-file `world-class-doctor-mode-for-cli-tools` skill:
     kept the One Rule + core axioms, the CLI surface, the mutate() chokepoint / safety envelope,
     the (detector,fixer,fixture,test) tuple, the 10-dim rubric, and the portable cookbook. Dropped
     the multi-model swarm tiers, session-mining, external issue-tracker plumbing, the per-run 0-1000
     scoring machinery, 18 subagents, and 39 scripts. JSON shapes + rubric + cookbook: references/DOCTOR-SPEC.md -->"
  - proposed fix: Move the distillation history to the commit message or a CHANGELOG entry, and keep only the live pointer line in the file: "<!-- JSON shapes + rubric + cookbook: references/DOCTOR-SPEC.md -->".
  - target: /home/will/dotfiles/claude/skills-local/cli-doctor-mode/SKILL.md
- **Progressive disclosure — disclose only what some branches reach**: The final-summary box (non-negotiable #12) and uninstall instructions (non-negotiable #13) are required on every run of every installer this skill produces — not just the agent-hook branch. Pushing their implementations (draw_box, uninstall) behind the same disclosed pointer as the genuinely conditional agent-hook and daemon-service material hides content every branch needs, which the doctrine flags as pushing too much down.
  - quote: "The full detection + JSON-merge-with-backup pattern (the
load-bearing reusable piece), the `draw_box` implementation, and the uninstall/service snippets are in
[references/PATTERNS.md](references/PATTERNS.md)."
  - proposed fix: Inline the draw_box and uninstall snippets in the main document near non-negotiables #12/#13 or in Core snippets; keep only the agent-detection/JSON-merge pattern and the conditional systemd/launchd service snippet behind the references/PATTERNS.md pointer.
  - target: /home/will/dotfiles/claude/skills-local/curl-bash-installer/SKILL.md
- **Single source of truth [craft]**: This restates, in different wording, the same convergence definition given later under '## Convergence (non-negotiable)' ('A round is quiet when... Converged = two consecutive quiet rounds AND ≥10 total rounds AND zero unresolved hypotheses...'). Two independently-worded copies of the same quantitative rule in one document risk drifting out of sync on future edits and inflate the rule's rank on the ladder past what a single authoritative statement needs.
  - quote: "Convergence = ≥10 full rounds AND 2 consecutive rounds with <3 genuinely-new findings AND every hypothesis resolved (SEAM_CONFIRMED / SEAM_REFUTED / DEFERRED+rationale with `Deferred reviewed: yes`)."
  - proposed fix: State the convergence definition once in the '## Convergence' section and have the Quick-Start line point to it instead of restating the thresholds, e.g. 'Convergence: see Convergence (non-negotiable) below.'
  - target: /home/will/dotfiles/claude/skills-local/de-monolithize-your-codebase-isomorphically-local/SKILL.md
- **Progressive disclosure**: Section 4 ("Propose a system (optional)") is explicitly branch-only — it fires only when the ask is to author a DESIGN.md, not for the core detection workflow every invocation reaches. Yet it carries several paragraphs of dense reference material (evidence tiers, this monorepo caveat, the lint-result quirks, the centroid-snapping regression story, method sources) inline in the main skill file rather than behind a pointer. Every reader of the base audit workflow (steps 1-3, 5) pays to scan past this propose-only reference, and the doctrine's branching test says material only some branches reach should be disclosed, not left inline among steps.
  - quote: "**Monorepo caveat.** The declared tier surfaces whichever app declares tokens — on a multi-app monorepo that is usually ONE app's theme, and the aggregate drift-derived palette drops to accents. For a per-app system, point the proposer at the app directory, not the monorepo root."
  - proposed fix: Move the propose-only reference detail (evidence tiers, monorepo caveat, lint-result caveats, centroid-snapping history, method sources) into a separate file, e.g. `references/propose.md`, and replace step 4 with a short summary plus a pointer: "See references/propose.md for evidence-tier semantics, monorepo caveats, and known proposer pitfalls."
  - target: /home/will/dotfiles/claude/skills-local/design-drift/SKILL.md
- **Negation [research] — state the target behaviour instead of the ban; keep prohibition only as a hard guardrail, paired with its positive target.**: This bullet and its accompanying table row ('No animation. Ever.') are both phrased as pure prohibition with no positive target stated (e.g., 'keep instant/immediate'). Neither is paired with a positive rephrasing, so the rule leans entirely on negation.
  - quote: "**Never animate keyboard-initiated actions.**"
  - proposed fix: Rephrase as the positive target: 'Keep keyboard-initiated actions instant — no transition or delay.' Reserve 'never' only as a trailing guardrail if needed.
  - target: /home/will/dotfiles/claude/skills-local/emil-design-eng/SKILL.md
- **Context pointer**: The doctrine says a pointer's wording should 'cut identity the body already states.' This clause in the frontmatter description restates identity the body's opening paragraph already covers ('It does not... write the implementation itself') and that Hard Rule 1 restates a third time ('Never modify source code... This skill reports; it does not implement.'). The description pays load to say something the body says anyway.
  - quote: "Read-only; it proposes motion with exact values, it does not implement it."
  - proposed fix: Trim the description to the routing-relevant search/reject clause only, e.g. "Search a codebase or UI for places that don't animate but should, and reject everything that shouldn't," and let the body's opening paragraph and Hard Rule 1 be the sole place the read-only/non-implementing identity is stated.
  - target: /home/will/dotfiles/claude/skills-local/find-animation-opportunities/SKILL.md

### Refuted findings

- **Context pointer — one trigger per branch (collapse synonyms that rename a single branch)** — verifier: The description stacks four separate phrasings — 'too big for one context', 'many independent units', 'whole-codebase campaigns', 'broad multi-file sweeps', 'N-independent-units work' — for what is really one branch (large/parallelizable task). Only 'adversarial verification' is a genuinely distinct trigger. This is exactly the synonym-stacking the pointer rule says to collapse.
  - quote: "whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work, or when you need multiple independent perspectives (adversarial verification)"
- **Context pointer — cut identity the body already states** — verifier: This trailing sentence describes what the skill *is* (its identity/position relative to other skills) rather than a trigger condition for reaching it. The body's own heading and opening callout already establish this identity, so the sentence spends pointer tokens without improving routing.
  - quote: "The shared swarm/delegation layer other skills route through for scale."
- **Subagent-dispatch escape hatch has a cost ceiling — every data-driven fan-out hard-capped** — verifier: Loop-until-dry is a textbook data-driven fan-out: it spawns agents based on an open-ended dryness condition with no stated maximum. The measured cost-ceiling rule requires every such fan-out be hard-capped, but this pattern gives only a stopping condition, not a ceiling — risking the runaway spend the rule was written to prevent.
  - quote: "keep spawning finders until K consecutive rounds surface nothing new — dedup against everything seen, not just what's kept"
- **Context pointer — cut identity the body already states** — verifier: The description already routes to these two sibling skills verbatim ("For critiquing existing motion use review-animations; for auditing a whole codebase use improve-animations"). The body restates the same routing information instead of cutting it, paying the same identity twice — exactly what the context-pointer rule says to avoid.
  - quote: "It does not audit a codebase (that's `improve-animations`), critique a diff (that's `review-animations`), or hunt for places that could animate (that's `find-animation-opportunities`)."
- **Single source of truth** — verifier: This duplicates the rule already given in step 4 ("**Never `scale(0)`.** Start from `scale(0.9–0.97)` + `opacity: 0`."). The duplication has already drifted: step 4 gives a range (0.9–0.97) while this row collapses it to a single fixed value (0.95) — the exact maintenance cost the doctrine warns duplication produces.
  - quote: "| `transform: scale(0)` entrance | `scale(0.95)` + `opacity: 0` |"
- **Completion criteria / Demand** — verifier: Step 5 states an unqualified bound — "**UI animations stay under 300ms.**" — but this row silently reopens it with an escape hatch ("with no reason") that is never defined anywhere in the document. This gives the agent an uncheckable qualifier to invoke whenever it wants to exceed the limit, undermining the sharp bound set in step 5.
  - quote: "UI duration over 300ms with no reason"
- **Negation [research]** — verifier: This bullet is pure prohibition with no positive target stated in the same breath. The doctrine requires steering by naming the target behaviour so the banned one is never spoken, keeping negation only as a guardrail paired with its positive framing — as the very next bullet in this same list does correctly ('Always animate from the presentation value... never the target value'). This one stands alone as negation-only.
  - quote: "**Never lock out input during a transition.**"
- **Negation [research]** — verifier: The rule is phrased entirely as prohibition; 'legibility collapses' is a consequence, not a positive rephrasing of what to do instead. Per the doctrine, negation should be paired with its positive target so the banned behaviour isn't the only thing spoken — contrast with the compliant sibling bullets in the same section ('Put color on a solid layer, not the translucent foreground' states the positive action first).
  - quote: "**Never stack a light translucent surface on another** — legibility collapses."
- **Negation [research]** — verifier: This is a prohibition stated without a paired positive rephrasing of the target behaviour. The doctrine requires stating the target behaviour and keeping prohibition only as a guardrail paired with its positive target — the Anti-Patterns table elsewhere in this same document follows that pattern (Don't/Instead pairs), but this bullet is bare negation with no adjacent 'always do X' framing.
  - quote: "**Never skip 1-3.** Intuition about what's repetitive is unreliable; data wins."
- **Single source of truth [craft]** — verifier: The 0.3 threshold is restated as a separate fact later in the Anti-Patterns table ('Automate rare commands (Score < 0.3) | Skip — maintenance > benefit'). Duplicating the same numeric rule in two disconnected sections risks drift if the threshold is ever tuned in one place and not the other.
  - quote: "Only automate if Score ≥ 0.3."
- **Completion criteria [craft]** — verifier: This Done-When bound is vague — it doesn't specify against what standard time savings are measured, even though the document already has a sharp, checkable bound for this ('Automated ≥ 3× faster than manual' in Step 5 Validate). The looser restatement here invites the agent to consider any unspecified measurement sufficient, risking premature completion.
  - quote: "Time savings measured"
- **Context pointer [craft]** — verifier: These two trigger phrases describe the same underlying branch — mining history to surface automation opportunities — rather than two distinct routing conditions. The doctrine calls for one trigger per branch, collapsing synonyms that rename a single branch.
  - quote: "Use when analyzing command patterns or finding automation opportunities."
- **Context pointer** — verifier: The description stacks synonyms for one trigger branch ('Salvage and rationalize... left by parallel agents' / 'harmonizes competing variants rather than picking one winner' / 'Use for parallel-agent branch cleanup' all describe the same single condition — messy branches from parallel-agent work), and it restates identity the body already gives in full: 'the judgment layer over wt-sweep.sh/branch-triage.sh' duplicates the Pipeline diagram's 'THIS SKILL (the cognitive layer over the RESIDUE)', and 'harmonizes... rather than picking one winner' duplicates the opening 'core move' callout almost verbatim. This spends always-loaded context restating what the body says once.
  - quote: "Salvage and rationalize forgotten branches/worktrees left by parallel agents: the judgment layer over wt-sweep.sh/branch-triage.sh that harmonizes competing variants rather than picking one winner. Use for parallel-agent branch cleanup."
- **Negation** — verifier: Steering by prohibition here is redundant on top of the positive instructions immediately before and after it ("Ask in 5 batches" / "Wait for answers, react, refine"), which already fully convey the batching behavior. Per the doctrine's Negation rule, the forbidden action ("dumping all 17") should not be named at all -- the positive framing alone does the job.
  - quote: "Don't dump all 17 at once."
- **Negation** — verifier: This is a negation-led directive ("don't skip," "isn't wired") rather than a stated positive target, pulling the un-encoded/ignored outcome into context instead of leading with the required action.
  - quote: "Don't skip the encoding step: a profile that isn't wired into a skill gets ignored."
- **Single source of truth [craft]** — verifier: These three rules are restated as separate checklist items in the 'Pre-flight checklist' section ('URLs verified (correct page loads in Brave)', 'Element names match the current UI exactly', 'Clear "report back" format'), and again as rows in the Anti-patterns table ('Skip query params', 'Vague "click the button"'). The same meaning is repeated across three headings instead of stated once, which the doctrine flags as a maintenance cost and an inflated rank for that meaning.
  - quote: "**Critical rules:**
- Include FULL URLs with query params (`?project=xyz`) and open them in Brave.
- Use EXACT element text (copy from the current UI).
- Say precisely WHAT to report back and the format (e.g. `GOCSPX-...`, `whsec_...`)."
- **Single source of truth** — verifier: The same causal claim — that the original eval's results were inflated by leaked synthetic queries and single-positive labels, later corrected by the pi-evals #891 rebuild — is already stated in the header comment ('the original "granite-r2 is best" result came from an eval with leaked synthetic queries and single-positive labels. The 2026-07 rebuild (pi-evals #891) reversed it'). Restating it here means the fact has to be kept in sync in two places, and inflates its apparent importance beyond what a single mention would.
  - quote: "the big lifts in the original eval were an artifact of leaked queries and single-positive labels"
- **Negation [research]** — verifier: Two prohibitions stacked back-to-back with no positive target stated in the same breath — exactly the negation-led pattern the doctrine's own probe flagged as a defect elsewhere ('a negation-led bullet ... survived a heavier audit'). Per the ironic-process research this rule cites, naming the forbidden behavior twice in a row makes it more available, not less, without the compensating positive framing the rule requires at the point of use.
  - quote: "Never silent-fail. Never punish a reasonable misstep."
- **Negation [research]** — quote_not_found: This bullet stacks four prohibited behaviors with no positive target stated anywhere in the same sentence, unlike neighboring anti-pattern bullets (e.g. the DeletePath and cross-filesystem-rename bullets, which each pair the ban with 'do X instead'). Per the negation rule, prohibition-only wording drags the forbidden behavior into context and makes it more available, not less — it should be paired with its positive target rather than left as a bare list of bans.
  - quote: "Random/timestamp finding ids, ad-hoc exit codes, interactive prompts, calling home by default — all break the agent contract."
- **Completion criteria [craft]** — quote_not_found: "until clean" is a vague bound with no observable condition attached — every other step in the build loop ends on a checkable artifact (a fixture pair, a run of the round-trip test, a score per dimension), but this one gives the agent nothing concrete to check itself against, inviting the agent to stop after a cursory pass and call the work done.
  - quote: "Iterate — a fresh-eyes/adversarial re-read until clean; re-mine as the project evolves (no doctor is ever "done")."
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available, not less; state the target behaviour instead and keep prohibition only as a hard guardrail.** — verifier: This is a negation-led bullet naming the exact trigger topics to avoid (naming debates, "what does this code do", style nitpicks), which per ironic-process rebound makes those topics more salient rather than less. It isn't a hard guardrail (misusing Codex on a naming debate is wasteful, not dangerous), so it doesn't qualify for the doctrine's carve-out for prohibition. It's also redundant: the preceding 'worth it' list already implies its complement, so the negative restatement adds no information, only the rebound risk.
  - quote: "**Not worth it:** naming debates, "what does this code do", style nitpicks. For those, just answer directly."
- **Single source of truth [craft] — keep each meaning in one authoritative place; the environment (config, --help) is a source of truth too, and a document restating a one-file lookup is a cache that only earns its load when the lookup is expensive.** — verifier: The document itself identifies `~/.codex/config.toml` as the authoritative source for which model is used, yet the model name 'GPT-5.5'/'gpt-5.5' is separately hard-coded in the frontmatter description, the opening paragraph, and the step-2 heading ("OPENAI_API_KEY stripped so it uses the gpt-5.5 ChatGPT subscription") — five restatements of a fact that lives in one cheap-to-check config file. If the config is repointed to a newer model, four of the five statements go stale with no mechanism to catch the drift.
  - quote: "Model: omit `-m` — it inherits `gpt-5.5` from `~/.codex/config.toml`."
- **Context pointer — one trigger per branch, collapse synonyms** — verifier: The three 'Use when' phrases ('creating install.sh', 'a curl-pipe-bash installer', 'a one-liner install for a Rust/TS/Go CLI') all name the same single branch — writing this kind of installer script — restated in different words. The doctrine says to keep one trigger per branch and collapse synonyms that rename a single branch, not stack them.
  - quote: "Use when creating install.sh, a curl-pipe-bash installer,
  or a one-liner install for a Rust/TS/Go CLI."
- **Context pointer — cut identity the body already states** — verifier: The description's 'Self-contained (real bash inline)' restates identity the body's own header comment already gives in full: 'This version is self-contained: real snippets inline, no external line-refs.' Per Context pointer, the pointer should cut identity the body already states rather than duplicate it.
  - quote: "or a one-liner install for a Rust/TS/Go CLI. Self-contained (real bash inline)."
- **Completion criteria — sharpen vague bounds** — verifier: 'A clear message' is an uncheckable qualifier — any error text satisfies it, so it doesn't tell the agent what a done preflight step actually looks like, inviting premature completion of this non-negotiable.
  - quote: "**Preflight** — disk space (`df -Pk`), write perms, existing-install version, network reachability; fail early with a clear message."
- **Subagent-dispatch escape hatch has a cost ceiling [measured]** — verifier: This fan-out (and the identically-patterned 'seam-analyst + intra-file-grapher + coverage-mapper × monolith file' in Phase 2, 'experiment-executor × open EXP' in Phase 5, and 'soak-runner × campaigns' in Phase 11) scales subagent count directly off data the run discovers (number of top-level dirs/crates, monolith files, open experiments, campaigns) with no stated ceiling anywhere in the document. The doctrine's measured rule requires every data-driven fan-out to be hard-capped, or the escape hatch that buys legwork instead buys runaway spend.
  - quote: "monolith-census-mapper × top-level dirs"
- **Negation [research]** — verifier: This is pure negation-led steering with no positive target stated alongside it. Per the doctrine, prohibition drags the forbidden behavior (oversimplifying, dropping features) into context and makes it more available, not less; negation should only appear as a guardrail paired with its positive counterpart.
  - quote: "DO NOT OVERSIMPLIFY; DO NOT LOSE FEATURES"
- **Context pointer [craft]** — verifier: 'split giant file' and 'file too big' are two trigger phrasings for the same branch — a single oversized file (confirmed by the First-30-Seconds Smell Test table, which groups 'split this 14k-line file' with the same YES branch). The doctrine requires one trigger per branch, collapsing synonyms that rename a single branch, rather than listing renamed duplicates in the routing description.
  - quote: "giant file, modularize repo, or file too big."
- **Negation** — verifier: This is a negation-led bullet describing the proposer's scope, not a genuine hard guardrail (unlike the tool-enforced "never edit source" rule) — and two of its three clauses ("invent a brand", "pick fonts") are never paired with a positive target stating what the proposer does instead. The doctrine requires prohibitions to state the target behaviour and reserve bare negation for guardrails paired with a positive counterpart; only the third clause ("migrate call sites") gets that pairing ("Migration is a separate ce-plan step").
  - quote: "**What it will not do.** It does not invent a brand, pick fonts, or migrate call sites."
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available, not less.** — verifier: This block fully renders the exact anti-pattern the document wants suppressed, in a code fence with real syntax, right before the positive example. Per the doctrine, showing the forbidden output this concretely increases its availability to the model rather than decreasing it — the opposite of the intended effect.
  - quote: "Wrong format (never do this):

```
Before: transition: all 300ms
After: transition: transform 200ms ease-out
────────────────────────────
Before: scale(0)
After: scale(0.95)
```"
- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and inflates that meaning's rank past its real importance.** — verifier: The Review Checklist table restates the same substantive rules (transition: all, scale(0) entry, ease-in, transform-origin: center on popovers) with the same fixes already given in the Review Format table earlier in the document. Both tables encode the identical set of facts; a future change to a recommended value (e.g. the entry scale or duration) has to be made in two places or the tables silently drift apart.
  - quote: "Specify exact properties: `transition: transform 200ms ease-out`"
- **Single source of truth** — verifier: This restates the exact same meaning already given in Hard Rules as "No exceptions for 'it would look cool.'" The rule that 'looks cool' is not a valid justification is stated twice in two different headings (Hard Rules and The Gate). Per the doctrine, duplication of one meaning in more than one place costs maintenance and risks drift if one copy is edited later and the other isn't.
  - quote: ""It looks cool" is not on this list. If you can't name the purpose in one of these words, reject the candidate."
