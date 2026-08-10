# Case study: SkillOpt's gate, and the re-analysis the public data cannot yet support

Microsoft's [SkillOpt](https://github.com/microsoft/SkillOpt) (arXiv
[2605.23904](https://arxiv.org/abs/2605.23904), MIT) is the best-resourced
direct rival to this project's thesis: a fully automated skill-document
optimizer — rollout → reflect → bounded edit → validation gate — validated
across 52 (model × benchmark × harness) cells, with headline gains of
+19–25pp. It is genuinely impressive work. This case study is about one
component: the gate.

## What their gate is (verifiable in their public source)

The accept/reject decision in `gate.py` is a bare float comparison: an
edit lands when it **strictly improves a single held-out validation
score**. No interval, no margin, no repeat runs, no "could not tell"
outcome — the exact decision rule whose failure this repo's README opens
with (the same rule passed and failed the same doctrine pair at n=1, 6,
and 16 here). On a noisy validation measurement, a strictly-improves
threshold accepts noise at a rate the artifact cannot itself report.

## The re-analysis we wanted to run — and why it cannot be run today

The falsifiable test of the thesis: take SkillOpt's per-edit accept
decisions with their underlying before/after validation scores, and
re-judge each acceptance with a paired interval (`compare --paired-json`).
Every acceptance that flips to *inconclusive* is a measured instance of a
shipping optimizer landing noise; zero flips would be equally important
evidence against this project's emphasis. Either result is publishable.

The data does not exist publicly:

- The paper's Table 1 reports **single-run point estimates, seed 42**, no
  variance, no CIs.
- The per-run `edit_apply_report.json` that the trainer writes — exactly
  the artifact the re-analysis needs — is local-only and never published.
- Their own extended-ablation post (499 runs) states plainly that raw
  per-run artifacts "are not included in the public repository" and the
  sweep "cannot currently be independently reproduced."
- The closest public granularity is SkillOpt-Sleep's `RESULTS.md`:
  night-batched score trajectories for ~6 cells and one 3-seed spot-check
  for a single cell — real paired variance, but for a companion
  experiment, far below the coverage the re-analysis needs.

## What can be said today

1. **The gate's statistical shape is a fact, not an inference** — the
   strictly-improves float comparison is in the public source.
2. **The reproducibility gap is their own statement**, not ours.
3. **The re-analysis is fully specified and one dataset away.** If the
   per-edit validation scores for even one of the 52 cells are ever
   published, the command is a one-liner against this repo's verdict
   engine, and this file will be updated with the result — whichever way
   it lands.

No claim is made here that SkillOpt's accepted edits are noise; the claim
is narrower and harder: **nobody, including its authors, can currently
show they are not**, and the tooling to show it either way is free and
public in this repository.
