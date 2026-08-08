---
name: skill-tuner
description: Evidence-tagged rules for writing documents agents consume. Use when creating or editing skills, AGENTS.md, or CLAUDE.md.
---

This is the model-invoked half of skill-tuner: a reference for writing any document an agent consumes — a skill, an `AGENTS.md`, a `CLAUDE.md`, or a doc reached by a pointer from one of those. It descends from the `writing-for-agents` doctrine and keeps its shape, but every rule below carries a receipt — exactly one evidence tag, `[research]` (grounded in published findings about model behaviour), `[measured]` (grounded in an eval or red-team run against this harness), or `[craft]` (compositional advice with no direct experiment behind it yet). Read the tag as a confidence label, not decoration: a `[craft]` rule is worth following, not worth defending past the point a `[measured]` rule contradicts it.

## Pointers & descriptions

- **Context pointer** [craft] — a reference held in the agent's context that names out-of-context material and encodes the condition for reaching it: a skill's `description`, a line in `AGENTS.md` naming a doc. The pointer's wording, not its target, decides whether the agent reaches the material — front-load the leading word, keep one trigger per branch (collapse synonyms that rename a single branch), cut identity the body already states.

- **The two loads** [craft] — every document or pointer spends either context load (always-loaded material, paid every turn whether it fires or not) or cognitive load (the human's job of knowing which document to reach for and when). Material behind a pointer trades most of its context load for a cognitive-load bill on the human; material with no pointer at all rides entirely on cognitive load.

- **Model-invoked vs. user-invoked** [craft] — a model-invoked skill keeps a `description`, buying autonomous and cross-skill reach at the price of permanent context load; a user-invoked skill (`disable-model-invocation: true`) pays zero context load but makes the human the index. Pick model-invocation only when the agent, or another skill, must reach the material unprompted.

- **Router skills** [craft] — when user-invoked skills multiply past what a human remembers, one router skill — itself user-invoked — names the others and when to reach for each, collapsing many-to-remember into one. It can only hint, never fire them.

## Structure & disclosure

- **Information hierarchy** [craft] — content is steps (ordered actions) or reference (definitions and rules consulted on demand), ranked on a three-rung ladder: in-file step, in-file reference, disclosed reference (pushed to a file reached by a pointer). Push too little down and the top bloats; push too much down and you hide material the agent actually needs.

- **Progressive disclosure** [craft] — move material down the ladder, out of the main file and behind a pointer, so the top stays legible. Branching is the test: inline what every branch needs, disclose what only some branches reach; leaving branch-only reference in-file among steps turns attending to it into a coin-flip.

- **Co-location** [craft] — keep a concept's definition, rules, and caveats under one heading instead of scattered across the document, so reading one part brings its neighbours with it. Distinct from duplication (one meaning repeated in two places): co-location scatters one meaning across many places without repeating it.

- **Sprawl** [craft] — a document can be too long even when every line is live and unique; attention thins across the excess and every extra line is one more to keep relevant. The cure is the ladder and the split, not line-editing.

- **Splitting** [craft] — split by sequence when post-completion steps tempt the agent to rush the step in front of it (hiding them drives legwork); split by invocation when a distinct trigger word should fire a skill on its own, or another skill must reach it. Either cut spends one of the two loads, so split only when the cut earns it.

## Completion & demand

- **Completion criteria** [craft] — every step ends on a condition telling the agent the work is done; a vague bound invites premature completion, attention slipping to being done rather than doing. Sharpen the bound first — it's local and cheap; only split the sequence to hide post-completion steps if the bound is irreducibly fuzzy and you've observed the rush.

- **Demand** [craft] — wording sets how much a criterion requires: "every modified model accounted for" forces legwork that "produce a change list" does not. Demand is not step-bound — "every rule applied" binds a body of flat reference the same way "every step done" binds a sequence.

- **Subagent-dispatch escape hatch has a cost ceiling** [measured] — hiding post-completion steps only works across a real context boundary, a hand-off or subagent dispatch, never an inline call. That escape hatch is not free: fan-out must stay capped — a verify fleet no wider than its producers, every data-driven fan-out hard-capped — or the dispatch meant to buy legwork instead buys runaway spend. Source: dotfiles PR #247 evidence ledger, 2026-08-06 red-team, CONFIRMED finding.

## Language levers

- **Leading words** [craft] — a leading word is a compact concept already in the model's pretraining (lesson, tracer bullet) that the agent thinks with wherever the document repeats it as a token; it anchors execution in the body and invocation in a pointer. Coining your own works only if you define it clearly — a made-up word recruits no priors, so you pay in definition tokens what a pretrained word gives free.

- **Negation** [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available, not less (ironic-process rebound): "don't think of an elephant" leaves the elephant as the only thing said. State the target behaviour instead, so the banned one is never spoken; keep prohibition only as a hard guardrail, paired with its positive target.

## Pruning & drift

- **Single source of truth** [craft] — keep each meaning in one authoritative place; duplication (the same meaning in more than one place) costs maintenance and inflates that meaning's rank on the ladder past its real importance. The environment (`package.json`, config, `--help`) is a source of truth too — a document restating a one-file lookup is a cache, and caching only earns its load when the lookup is expensive.

- **Relevance and sediment** [craft] — every line must still bear on what the document does; a line loses relevance by never mattering to the task or by going stale as the behaviour it describes changes. Without a pruning discipline the default fate is sediment: stale layers piling up because adding feels safe and removing feels risky.

- **No-op verdicts are time-relative** [measured] — test each sentence against the model's actual default, not the reader's assumption: if the model already does it, the sentence pays load to say nothing, and it goes on the block. That verdict is not permanent — a 2026-08-05 inspection of a running claude v2.1.221 binary found 2025-era preamble and length directives gone from current defaults, meaning sentences correctly pruned earlier had silently gone live again. Re-run the test after every model or CLI upgrade, not once. Source: dotfiles PR #247 evidence ledger.

- **Description pruning lands only at routing parity** [measured] — prune a description per one-trigger-per-branch, then check it against a blind battery built from skill bodies (never descriptions), including distractors and near-misses, at two or more trials per condition; land the prune only at parity or better. A 2026-08-06 eval (session `wf_582da968`) cut three descriptions 37% (~327→~204 tokens) and still routed 30/30 versus the originals' 28/30, paraphrases 6/6, near-miss rejection 8/8 — the recall loss feared from cutting synonym-stacked language did not appear at n=30/condition. Source: dotfiles PR #247 evidence ledger.

- **The probe finds what audits miss** [measured] — a live application of this doctrine found 2 adversarially-confirmed defects, a negation-led bullet and an uncheckable qualifier, in a CLAUDE.md section immediately after an 11-agent audit had already passed it. That gap is the marginal-value bar this doctrine has to keep clearing to earn its slot. Source: dotfiles PR #247 evidence ledger, landed PR #203.

- **Self-application** [craft] — this document follows its own rules: it coins few terms and reuses them rather than minting synonyms per section (context pointer, leading word, no-op, each used, not restated), it co-locates a mechanism's rules under one heading instead of scattering them, and it phrases rules positively, naming the target behaviour rather than the ban. Validated by the same probe above, which caught a negation-led bullet and an uncheckable qualifier that survived a heavier audit.

## The eval half

skill-tuner pairs this doctrine with a bundled eval runner — the half that turns a rule's evidence tag into a number instead of an assertion. The routing-parity eval measures whether a pruned or reworded description still routes correctly: it builds a blind battery from skill bodies, adds distractors and near-misses, and scores hit rate before and after a change. The marginal-value probe measures whether applying this doctrine to a document finds defects a prior review already missed — the check behind the "probe finds what audits miss" rule above. Reports land under `reports/` in the invoking repo, one per run, and are inputs to a human decision rather than a verdict on their own. Runs cost tokens — a routing-parity pass drives a full blind battery through the model under test — and the runner only ever starts on the human's explicit instruction; nothing in this doctrine or in ordinary skill-authoring work triggers it on its own.
