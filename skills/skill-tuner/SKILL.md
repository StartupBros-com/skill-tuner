---
name: skill-tuner
description: Evidence-tagged rules for writing documents agents consume. Use when creating or editing skills, AGENTS.md, or CLAUDE.md.
---

A reference for writing any document an agent consumes — a skill, an `AGENTS.md`, a `CLAUDE.md`, or a doc reached by a pointer from one of those. It descends from the `writing-for-agents` doctrine and keeps its shape.

Every rule carries exactly one evidence tag: `[research]` (grounded in published findings about model behaviour), `[measured]` (grounded in an eval or red-team run against this harness), or `[craft]` (compositional advice with no direct experiment behind it yet). Read the tag as a confidence label, not decoration — a `[craft]` rule is worth following, not worth defending past the point a `[measured]` rule contradicts it. The falsifier for each rule, and the runs behind the `[measured]` ones, live in [`FALSIFIERS.md`](FALSIFIERS.md); they are what you consult when auditing this doctrine, not when applying it.

## Context pointers

A **context pointer** is a reference held in the agent's context that names out-of-context material and encodes the condition for reaching it. A skill's `description` is one; a line in `AGENTS.md` naming a doc is the same object. The pointer's *wording*, not its target, decides whether the agent reaches the material and how reliably. A must-have target behind a weakly worded pointer is a variance bug: sharpen the wording first, and inline the material only if sharpening fails.

A pointer does two jobs — state what the material is, and list the **branches** that should trigger reaching it, a branch being a distinct case the document handles. Every word of an always-loaded pointer costs on every turn, so it earns harder pruning than the body.

- **Front-load the leading word** [craft] — the pointer is where the word does its triggering work, so it goes where the agent reads first. A pointer that opens with throat-clearing ("This skill provides guidance on...") spends its most valuable position on nothing.
- **One trigger per branch** [craft] — synonyms that rename a single branch are one branch written twice. To spot it, ask of each trigger: does a run reaching the document through *this* phrase take a different path than a run reaching it through the one beside it? If not, collapse them. Three phrases for one branch pay three times and route once.
- **Cut identity the body already states** [craft] — a pointer restating what the body says about itself adds permanent context load for no routing signal. The pointer's job is *when to reach*, not *what it is*.
- **Model-invoked or user-invoked** [craft] — a model-invoked skill keeps a `description` and buys autonomous and cross-skill reach at the price of permanent context load. A user-invoked one (`disable-model-invocation: true`) pays zero context load but makes the human the index. Pick model-invocation only when the agent, or another skill, must reach the material unprompted. When user-invoked skills multiply past what a human remembers, one router skill — itself user-invoked — names the others and when to reach for each, collapsing many-to-remember into one; it can hint, never fire.

## The two loads

Every document and every pointer spends one of two budgets, and the choice is the main structural decision you make.

- **Context load** [craft] — the cost of always-loaded material on the agent's window, paid every turn whether it fires or not. Material behind a pointer trades most of this away.
- **Cognitive load** [craft] — the cost on the human: knowing which documents exist and when to reach for each. Material behind a pointer bills here instead; material with no pointer at all rides entirely on it, which is how documents get forgotten.

Neither budget is free, so "put it behind a pointer" is a trade, not a win. Disclose when the material is branch-specific and the human will plausibly remember it exists; inline when every run needs it.

## Structure and disclosure

Content is either **steps** (ordered actions) or **reference** (definitions and rules consulted on demand), and it sits on a three-rung ladder: in-file step, in-file reference, disclosed reference behind a pointer. Push too little down and the top bloats; push too much down and you hide material the agent needs. Branching is the test that decides the rung.

- **Progressive disclosure** [craft] — inline what every branch needs; disclose what only some branches reach. Leaving branch-only reference in-file among steps turns attending to it into a coin flip: the agent cannot tell material meant for its path from material meant for a path it isn't on.
- **Co-location** [craft] — keep a concept's definition, rules, and caveats under one heading, so reading one part brings its neighbours. This is distinct from duplication: duplication repeats one meaning in two places, co-location failure scatters one meaning across many without repeating it. Spot it by asking whether applying a rule correctly requires having read a different section.
- **Sprawl** [craft] — a document can be too long even when every line is live and unique. Attention thins across the excess, and every extra line is one more to keep relevant. The cure is the ladder and the split, not line-editing: trimming adjectives off a document that is structurally too big buys nothing.
- **Splitting** [craft] — split by sequence when post-completion steps tempt the agent to rush the step in front of it, since hiding them drives the legwork. Split by invocation when a distinct trigger word should fire material on its own, or when another skill must reach it. Either cut spends one of the two loads, so split only when the cut earns it.

## Steps, completion, and demand

Every step ends on a condition telling the agent the work is done. Where that condition is vague, attention slips from *doing* the work to *being done* with it, and the model completes early while believing it complied.

- **Completion criteria** [craft] — a bound is checkable when the agent can tell done from not-done without judgment. "Verify the config" is not; "re-read the config via the API and confirm the field equals the value you wrote" is. Sharpen the bound first — it is local and cheap — and only split the sequence to hide post-completion steps if the bound is irreducibly fuzzy and you have observed the rush.
- **Demand** [craft] — wording sets how much a criterion requires. "Every modified model accounted for" forces legwork that "produce a change list" does not. Demand is not step-bound: "every rule applied" binds a body of flat reference exactly as "every step done" binds a sequence. Watch for criteria that mix checkable and uncheckable terms — one stray uncheckable qualifier inside an otherwise precise list lets the agent satisfy the whole thing impressionistically.
- **The subagent escape hatch has a cost ceiling** [measured] — hiding post-completion steps only works across a real context boundary, a hand-off or subagent dispatch, never an inline call. That hatch is not free: fan-out must stay capped — a verify fleet no wider than its producers, every data-driven fan-out hard-capped — or the dispatch meant to buy legwork buys runaway spend instead.

## Language levers

- **Leading words** [craft] — a leading word is a compact concept already in the model's pretraining (*lesson*, *tracer bullet*) that the agent thinks with wherever the document repeats the token. It anchors execution in the body and invocation in a pointer. Coining your own works only if you define it clearly: a made-up word recruits no priors, so you pay in definition tokens what a pretrained word gives free. A word too weak to beat the model's default ("be thorough" when it is already thorough) is a no-op wearing emphasis.
- **Negation** [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available, not less; "don't think of an elephant" leaves the elephant as the only thing said. State the target behaviour so the banned one is never named. Keep prohibition only as a hard guardrail, and pair it with its positive target. The tell is a rule that leads with the ban and never says what to do instead.

## Pruning and drift

- **Single source of truth** [craft] — keep each meaning in one authoritative place, so changing the behaviour is a one-place edit. Duplication costs maintenance and inflates a meaning's rank on the ladder past its real importance. The environment is a source of truth too: `package.json`, config, `--help`. A document restating a one-command lookup is a cache, and caching earns its load only when the lookup is expensive. Cache what the agent cannot find by looking — the unwritten convention, the reason behind a choice, the gotcha no config confesses.
- **Relevance and sediment** [craft] — every line must still bear on what the document does. A line loses relevance by never mattering to the task, or by going stale as the behaviour it describes changes. Without a pruning discipline the default fate is sediment: stale layers piling up because adding feels safe and removing feels risky, until you core down through them to find what is live.
- **No-op verdicts are time-relative** [measured] — test each sentence against the model's actual default, not the reader's assumption: if the model already does it, the sentence pays load to say nothing. That verdict expires. Inspecting a running claude v2.1.221 found 2025-era preamble and length directives gone from current defaults, meaning sentences correctly pruned earlier had silently gone live again. Re-run the test after every model or CLI upgrade, not once.
- **Description pruning lands only at routing parity** [measured] — prune a description per one-trigger-per-branch, then check it against a blind battery built from skill bodies (never descriptions), including distractors and near-misses, at two or more trials per condition. Land the prune only at parity or better. A 2026-08-06 eval cut three descriptions 37% and still routed 30/30 against the originals' 28/30; the recall loss feared from cutting synonym-stacked language did not appear.
- **The probe finds what audits miss** [measured] — applying this doctrine to a document found 2 adversarially-confirmed defects, a negation-led bullet and an uncheckable qualifier, immediately after an 11-agent audit had already passed it. That gap is the bar this doctrine has to keep clearing to earn its slot.

## The eval half

skill-tuner pairs this doctrine with a bundled eval runner — the half that turns a rule's evidence tag into a number instead of an assertion. The routing-parity eval measures whether a pruned or reworded description still routes correctly: it builds a blind battery from skill bodies, adds distractors and near-misses, and scores hit rate before and after a change. The marginal-value probe measures whether applying this doctrine to a document finds defects a prior review already missed. Reports land under `reports/` in the invoking repo, one per run, and are inputs to a human decision rather than a verdict on their own. Runs cost tokens, and the runner only ever starts on the human's explicit instruction; nothing in this doctrine or in ordinary skill-authoring work starts it.
