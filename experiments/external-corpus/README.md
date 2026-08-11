# External corpus: the probe on ground we didn't write

Every prior number in this repo came from the operator's own skills — a
corpus that has now been tuned to the instrument's floor. This experiment
runs the probe on two third-party OSS corpora, then fixes the densest
documents and re-probes them, to answer two questions our own corpus no
longer can: what does defect density look like in the wild, and does
fixing probe findings produce a measurable, confidence-intervaled defect
reduction?

Corpora (shallow clones, 2026-08-11): `davidondrej/skills` (MIT, 49
skills) and `anthropics/skills` (18 skills; no top-level LICENSE, so
fixed copies stay in scratch and only probe receipts — short quotes — are
committed). 8 skills sampled from each, sized mid-to-large;
`max_findings` raised to 8 after the cross-judge experiment showed the
5-cap truncating defect-dense docs.

## Density (probe under doctrine v3, 3-skeptic verification)

| corpus | confirmed | refuted | docs | confirmed/doc | spend | confirmed/$ |
|---|---|---|---|---|---|---|
| davidondrej/skills | 21 | 14 | 8 | 2.6 | $3.50 | 6.0 |
| anthropics/skills | 20 | 20 | 8 | 2.5 | $4.33 | 4.6 |
| our fresh corpus (batch 3, same doctrine) | 21 | — | 15 | 1.4 | — | — |

External corpora run **~1.8× the defect density** of our corpus at its
first-probe state — consistent with the campaign's premise that the
tuning loop finds and removes real, common classes of defects.

Notables, both directions:

- `effective-agent-skills` — davidondrej's own skill-*authoring*
  doctrine, the closest thing to a competitor document in the sample —
  carries 3 confirmed defects under doctrine v3.
- Anthropic's `skill-creator` (33KB) probed **clean**: zero confirmed
  findings. So did davidondrej's `prod-push` (and our own `goal-brief`
  in batch 4). The probe is not a machine that finds defects everywhere;
  on well-maintained documents it comes back empty, which is what makes
  its nonzero counts elsewhere meaningful.

## Defect reduction (fix → re-probe, paired per doc)

The 5 densest docs (goal-loop 5, pptx 5, algorithmic-art 5, cmux 4,
canvas-design 4 = 23 findings) were fixed by a fleet in scratch — quotes
verified before every edit, 23/23 applied, originals untouched — and
re-probed under the identical config.

| doc | before | after | reduction |
|---|---|---|---|
| goal-loop | 5 | 1 | +4 |
| pptx | 5 | 1 | +4 |
| cmux | 4 | 2 | +2 |
| algorithmic-art | 5 | 3 | +2 |
| canvas-design | 4 | 2 | +2 |

**Mean reduction +2.80 defects/doc, bootstrap 95% CI [+2.00, +3.60],
5W/0L/0T** — the interval is clear of zero with every document improved;
23 confirmed defects became 9 (−61%) for $2.83 of re-probe. (The exact
sign test reads p=0.062 because 5W/0L is its minimum attainable value at
n=5; the bootstrap interval is the operative bound.) This is the
"obviously better" run: on documents that still have defects, one
fix-and-verify pass removes most of them, with a CI attached.

Two honest caveats:

- **Partial circularity.** The instrument that found the defects also
  certifies their removal. The cross-judge audit
  (`experiments/cross-judge/`) is what breaks the circle at the
  instrument level: a non-Claude judge confirmed skeptic-passed findings
  at 47–48% with no leg asymmetry, so "confirmed defect" is not a
  claude-family hallucination class. A fully independent version of THIS
  table would re-run the cross-judge on these 5 docs.
- **The residual 9 are not failures.** Re-probing a changed document
  yields new findings at the instrument's ~2/doc steady state (the
  playbook's stopping rule); several of the 9 are second-pass
  discoveries, not survivors of the fixes — 23/23 fixes verified their
  target quotes before editing.

Notes:

- One fix (algorithmic-art's five-synonym trigger list) edits a
  description. Landing that upstream would require the routing-parity
  battery per our own playbook; in scratch it only affects the
  defect count.
- Upstream PRs shipped 2026-08-11 with the operator's go:
  [davidondrej/skills#3](https://github.com/davidondrej/skills/pull/3)
  (goal-loop + cmux, 9 edits) and
  [anthropics/skills#1543](https://github.com/anthropics/skills/pull/1543)
  (pptx + algorithmic-art + canvas-design, 13 edits; the un-batteried
  description edit excluded). The verified findings for the other probed
  davidondrej skills were deliberately not contributed.

## Files

- `../../configs/external-david.json`, `external-anthropic.json`,
  `external-fixed.json` — the three probe configs
- `../../reports/external-{david,anthropic,fixed}-001/` — banked receipts
- `analyze_reduction.py` — paired reduction, bootstrap CI, sign test ($0)
