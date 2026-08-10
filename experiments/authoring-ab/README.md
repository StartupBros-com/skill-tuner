# Authoring A/B: doctrine v3 vs its ancestor, on the doctrine's actual job

Every doctrine gate so far measures defect-*finding* — apply the doctrine to
a document, count adversarially-verified findings. That metric crowned v3
(swapgate6) and refused v3.1 (swapgate7), and it carries a known Goodhart
risk: the doctrine under test helps define the defects being counted. This
experiment is the independent second metric: agents *write* skills under
each doctrine, and the outputs are graded by instruments neither doctrine
authored.

## Design

- **Tasks**: 6 realistic authoring briefs (`briefs.json`) — a PDF-extractor
  skill, a staging-deploy runbook, a migration-review checklist, a metrics
  digest, incident triage, alt-text rules. Each brief carries concrete
  load-bearing facts (commands, thresholds, gotchas).
- **Conditions**: `ours` = doctrine v3 (the shipped skill-tuner doctrine);
  `ancestor` = the frozen upstream `writing-for-agents` snapshot v3 beat at
  swapgate6. Doctrine text inline; everything else identical.
- **Envelope**: every call through `tune.call_adapter` — the same guarded
  single-completion envelope as every banked receipt. 24 generations cost
  **$1.93** (the first end-task A/B's ad-hoc runner paid ~10x per call for
  bypassing this chokepoint).
- **Grading, two independent instruments**:
  1. `grader.py` — deterministic, doctrine-neutral: 8 assertions per output
     drawn from Anthropic's published skill guidance (frontmatter/name/
     description-with-trigger, spec length limits, an example present, no
     placeholder debris) and task fidelity (the brief's load-bearing facts
     carried). Neither doctrine's special vocabulary appears in any check.
  2. `judge.py` — blind pairwise, rubric from Anthropic's guidance, both
     presentation orders; a judge that prefers slot A both times counts as
     a tie (8 of 12 pairs showed exactly that position bias — the
     debiasing is not optional).

## Results

Deterministic metric (`tune.py compare --paired-json`, δ = 0.05 pass-rate):

**Verdict: not_worse** — mean **+0.031**/brief, 95% CI **[−0.04, +0.10]**,
record 3 won / 1 lost / 2 tied, dz +0.48, bootstrap agreeing. Blind
pairwise, order-consistent only: **ours 3, ancestor 1, tie 8**.

## Reading, calibrated

On its actual job, doctrine v3 produces skills statistically
indistinguishable-to-slightly-better than its ancestor's, on both
instruments, with the lean in v3's favor and n too small to resolve
"better". Combined with swapgate6, the full claim is now: **v3 finds
measurably more verified defects (better, CI excludes zero) and writes
at least as well (not_worse on a doctrine-neutral metric)** — the
defect-finding win is not purchased at the price of authoring quality,
and the Goodhart loop is bounded by an independent measurement.

## Limits

- n = 6 briefs, 2 trials: powered for gross differences only; the CI
  says ~a dozen more briefs would be needed to resolve the positive lean.
- The deterministic assertions sit near ceiling (0.81–1.0), limiting
  discrimination — same pattern as the curl A/B; harder fidelity checks
  are the upgrade path.
- One judge model (claude-sonnet-5) for the pairwise; the 67% position-
  inconsistency rate is itself a finding about single-order LLM judging.

Total cost: 24 generations $1.93 + 24 judge calls ≈ $1.10 ≈ **$3.05**.
Reproduce: `runner.py` → `grader.py` → `judge.py` → the compare line above.
