# Falsifiers and evidence

The result that would kill each rule in `SKILL.md`, plus the citations behind
the `[research]` tags and the runs behind the `[measured]` ones. Disclosed
rather than inline: a falsifier tells you when to *stop trusting* a rule,
which is a question you ask while auditing the doctrine, not while applying
it. Measured against the doctrine's own progressive-disclosure rule, keeping
this material in the main file cost 22.8% of its length and measurably
reduced how many defects it found (`reports/swapgate4-summary.md`).

Tags in `SKILL.md` stay inline. The tag is the confidence signal and costs a
token; the paragraph explaining how to disprove it does not need to be in
the agent's context to shape an edit.

## Context pointers

- **Front-load the leading word** — a pointer whose trigger word is moved to
  the end routes as well as one that front-loads it.
- **One trigger per branch** — a pointer listing synonym triggers routes
  better than one that collapses them, on a blind battery with distractors.
- **Cut identity the body states** — restating the body's identity in the
  pointer measurably improves routing.
- **Description pruning lands only at routing parity** — a parity-checked
  prune that measurably undertriggers once it reaches live use.
- **Model-invoked vs user-invoked** — a user-invoked skill an agent reaches
  reliably without being named, or a model-invoked skill nobody types and no
  other skill calls.
- **Router skills** — a router skill that does not reduce "I forgot this
  existed" incidents versus the un-routed set.

## The two loads

- **Context load** — a model whose task performance is flat as always-loaded
  material grows across the tested range.
- **Cognitive load** — moving a document between the two loads produces no
  measurable change in agent token spend or in human recall.

## Structure and disclosure

- **Progressive disclosure** — disclosing reference that every branch needs
  produces no drop in completion quality.
- **Co-location** — scattering a concept's rules across three headings with
  no measurable drop in the agent applying all of them.
- **Sprawl** — doubling a document's length with no drop in attention to any
  single rule, including its mid-document rules.
- **Splitting** — a split that changes neither completion thoroughness nor
  routing reach.

## Steps, completion, and demand

- **Completion criteria** — a sharpened bound that leaves the
  premature-completion rate unchanged; or contradictory bounds that agents
  resolve consistently without a stated precedence.
- **Demand** — a high-demand and a low-demand wording that produce the same
  depth of work.
- **Subagent dispatch has a cost ceiling** — a red-team re-run showing
  uncapped subagent fan-out costs the same as capped fan-out.

## Leading words

- **Leading words** — a leading-word refactor with no measurable change in
  execution behaviour. No direct research support exists for this rule yet;
  the `[craft]` tag stands until an A/B confirms or kills it.
- **Negation** — a negated instruction that suppresses the named behaviour as
  reliably as its positive rephrasing, across repeated trials.

## Pruning and drift

- **Single source of truth** — a duplicated rule that never drifts out of
  sync with its source across repeated edits.
- **Relevance and sediment** — a document left unpruned for a year with no
  accumulation of dead lines.
- **No-op verdicts are time-relative** — a no-op verdict from one model
  version that stays correct, unchecked, across three consecutive upgrades.

## Citations behind the `[research]` tags

Each citation was fetched and adversarially re-verified against its claimed
finding on 2026-08-08 before being recorded here; one quantitative claim
("30-50% drop by 50K tokens") failed that check and was discarded.

- **Negation**: Jang, Ye & Seo, *Can Large Language Models Truly Understand
  Prompts? A Case Study with Negated Prompts* (arXiv:2209.12711). All tested
  LM families perform worse on negated prompts, with an inverse scaling law
  — larger models do worse, not better.
- **Context load**: Chroma, *Context Rot: How Increasing Input Tokens
  Impacts LLM Performance* (trychroma.com/research/context-rot) — all 18
  tested frontier models degrade on simple, difficulty-held-constant tasks
  as input grows. Anthropic, *Effective context engineering for AI agents* —
  context as "a finite resource with diminishing marginal returns" under an
  "attention budget", "a performance gradient rather than a hard cliff".
- **Sprawl**: Liu et al., *Lost in the Middle: How Language Models Use Long
  Contexts* (arXiv:2307.03172, TACL 2024) — mid-document material is
  measurably harder to use than the same material at either end, even for
  explicitly long-context models. Plus Chroma's context-rot result above.

Supporting-but-not-graduating: these were verified too, but each stops one
step short of its rule's operative claim, so the rule keeps its current tag.

- *Progressive disclosure*: Anthropic's Agent Skills post documents the
  three-tier loading model; NN/g's progressive-disclosure research is
  human-factors, not agent-document evidence.
- *Front-load the leading word*: serial-position effects are confirmed
  across LLMs (arXiv:2406.15981) and IFScale found bias toward earlier
  instructions (arXiv:2507.11538), but both study denser regimes than a
  one-line pointer.
- *Completion criteria*: underspecified prompts are 2x as likely to regress
  across model changes (arXiv:2505.13360) — instability, not premature
  completion specifically. IFEval (arXiv:2311.07911) validates checkability
  as a gradable property.
- *Demand*: IFScale — best models reach only 68% at 500 simultaneous
  instructions; capacity limits are real, the legwork lever is untested.
- *Cut identity*: MCP tool-description ablations (arXiv:2602.14878) —
  removing schema-duplicating description text did not hurt performance;
  studies parameter/schema overlap, not skill-pointer identity.
- *Single source of truth*: instruction-conflict scores rise with count and
  predict following-rate drops (arXiv:2510.14842); conflicting instructions
  resolve inconsistently (arXiv:2606.22470) — the conflict mechanism, not
  duplication-drift itself.

## Evidence index

Sources for the `[measured]` tags. All session-measured on the authors'
harness.

- **Routing-parity eval**, session `wf_582da968` (2026-08-06): three
  descriptions cut 37% (~327→~204 tokens), routed 30/30 against the
  originals' 28/30, paraphrases 6/6, near-miss rejection 8/8.
- **No-op drift check** (2026-08-05, claude v2.1.221): directives pruned as
  no-ops in 2025 were found live again in current defaults — verdicts are
  time-relative, not permanent.
- **Marginal-value probe** (dotfiles PR #203): 2 adversarially-confirmed
  defects found immediately after an 11-agent audit had passed the same
  document. This receipt formerly lived in `SKILL.md` as a rule ("the probe
  finds what audits miss"); it is a claim about the runner, not an authoring
  rule, so it moved here and to the README.
- **Fan-out cost ceiling**: 2026-08-06 red-team, CONFIRMED. Full ledger:
  dotfiles PR #247.

## Where this doctrine's own claims stand

This doctrine forked from `writing-for-agents`. Three gates failed to beat
it; the fourth measured better. All against the banked ancestor leg on
shared documents (probe = confirmed defects found when the doctrine is
applied):

- **v1** (16 docs): 19 confirmed vs 30. 95% CI [−1.19, −0.18] — a real
  regression, size versus the margin unresolved. Originally published as
  "worse"; the 2026-08-08 statistics review found the worse-verdict anchored
  at zero instead of −delta, and the corrected label is *inconclusive with
  regression confirmed*. The data did not move, the label did
  (`reports/swapgate3-summary.md`).
- **v1, apparatus stripped** (15 docs): 22 vs 29, inconclusive
  (`reports/swapgate4-summary.md`) — which is why this file exists.
- **v2** (15 docs): 27 vs 29, 95% CI [−0.76, +0.49], **not_worse** at
  δ = 1.0 (`reports/swapgate5-summary.md`).
- **v3.1 candidate** (15 docs, 2026-08-10): four review-endorsed sentences
  restored from the ancestor; 24 vs v3's 42, 95% CI [−2.21, −0.19],
  regression confirmed — **refused and reverted**
  (`reports/swapgate7-summary.md`). Expert consensus endorsed every one of
  those sentences; only the gate dissented.
- **v3** (15 docs, 2026-08-08): 42 vs 29, 95% CI [+0.03, +1.70],
  **better** — bootstrap CI agrees, sign test alone would not resolve; a
  near-boundary win, published with the same calibration as the losses
  (`reports/swapgate6-summary.md`).
- **v3 replication** (15 docs, 2026-08-10, post-tuning corpus,
  system-prompt envelope): 34 vs 27, mean +0.467/doc, 95% CI
  [−0.31, +1.25], **not_worse** — the near-boundary better did not survive
  a corpus in which 51 defects (heavily v3's favorite duplication class)
  had been fixed; direction held (`reports/rebank-sys-summary.md`).
- **Cross-family judge audit** (2026-08-11): all 61 confirmed findings
  from both replication legs re-adjudicated blind and adversarially by a
  non-Claude frontier judge (gpt-5.6-sol). Survival 47% (v3) vs 48%
  (ancestor), Fisher exact p = 1.000 — **no leg asymmetry**, so the
  measured v3 advantage is not a claude-family judging artifact; the
  paired re-verdict on surviving findings keeps v3's direction
  (+0.200/doc, CI [−0.47, +0.87]). The recall direction found no family
  blind spot beyond the probe's own `max_findings` cap, which does
  truncate defect-dense docs (`experiments/cross-judge/README.md`).

The incumbent in these gates was frozen from upstream on 2026-08-05 and
includes upstream's 2026-07-23 rename/restructure and its last content
change (2026-07-28), plus one local sentence this project added (the
time-relative no-op amendment) — the comparison is against current upstream
content, made strictly harder by that amendment. (An earlier revision here
called the snapshot pre-rename and stale; upstream's commit log disproved
that.) The doctrine as a whole measured better once; no individual rule is
thereby validated.
