# Falsifiers and evidence

The result that would kill each rule in `SKILL.md`, plus the runs behind the
`[measured]` ones. Disclosed rather than inline: a falsifier tells you when to
*stop trusting* a rule, which is a question you ask while auditing the
doctrine, not while applying it. Measured against the doctrine's own
progressive-disclosure rule, keeping this material in the main file cost
22.8% of its length and measurably reduced how many defects it found
(`reports/swapgate4-summary.md`).

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
- **Model-invoked vs user-invoked** — a user-invoked skill an agent reaches
  reliably without being named, or a model-invoked skill nobody types and no
  other skill calls.
- **Router skills** — a router skill that does not reduce "I forgot this
  existed" incidents versus the un-routed set.

## The two loads

- Moving a document between the two loads produces no measurable change in
  agent token spend or in human recall.

## Structure and disclosure

- **Progressive disclosure** — disclosing reference that every branch needs
  produces no drop in completion quality.
- **Co-location** — scattering a concept's rules across three headings with
  no measurable drop in the agent applying all of them.
- **Sprawl** — doubling a document's length with no drop in attention to any
  single rule.
- **Splitting** — a split that changes neither completion thoroughness nor
  routing reach.

## Steps, completion, and demand

- **Completion criteria** — a sharpened bound that leaves the
  premature-completion rate unchanged.
- **Demand** — a high-demand and a low-demand wording that produce the same
  depth of work.
- **Subagent dispatch has a cost ceiling** — a red-team re-run showing
  uncapped subagent fan-out costs the same as capped fan-out.

## Language levers

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
- **Description pruning lands only at routing parity** — a parity-checked
  prune that measurably undertriggers once it reaches live use.
- **The probe finds what audits miss** — a probe pass on a heavily-audited
  document that turns up zero additional defects.

## Evidence index

Sources for the `[measured]` tags. All session-measured on the authors'
harness; they will be re-cited to the public evidence ledger when it lands.

- **Routing-parity eval**, session `wf_582da968` (2026-08-06): three
  descriptions cut 37% (~327→~204 tokens), routed 30/30 against the
  originals' 28/30, paraphrases 6/6, near-miss rejection 8/8.
- **No-op drift check** (2026-08-05, claude v2.1.221): directives pruned as
  no-ops in 2025 were found live again in current defaults — verdicts are
  time-relative, not permanent.
- **Marginal-value probe** (dotfiles PR #203): 2 adversarially-confirmed
  defects found immediately after an 11-agent audit had passed the same
  document.
- **Fan-out cost ceiling**: 2026-08-06 red-team, CONFIRMED. Full ledger:
  dotfiles PR #247.

## Where this doctrine's own claims stand

This doctrine forked from `writing-for-agents` and has not yet beaten it. On
16 shared documents it confirmed 19 defects to the ancestor's 30 (95% CI
[−1.19, −0.18], `reports/swapgate3-summary.md`). Stripping this file's
contents out of `SKILL.md` recovered most of that gap and moved the verdict
to inconclusive (`reports/swapgate4-summary.md`), which is why the split
exists. The remaining gap is not yet closed, and no rule here should be cited
as outperforming its ancestor.
