# Paired comparison — paired-json

**Verdict: inconclusive**  (non-inferiority margin delta = 0.1 findings per case)

- score paired across 8 cases (/tmp/hv-skill-diet-1278341/compare/paired/diet.json vs /tmp/hv-skill-diet-1278341/compare/paired/tuner.json)
- mean difference: +0.167 per case (sd 0.617, se 0.218)
- 95% CI: [-0.35, +0.68]
- case record: 3 won, 4 lost, 1 tied
- robustness: bootstrap 95% CI [-0.21, +0.62], exact sign test p=1.000, effect size dz +0.27
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 24 cases (+16 on this run)

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 0.000 | 1.000 | +1.000 |
| t1 | 0.000 | 0.667 | +0.667 |
| t1 | 1.000 | 0.667 | -0.333 |
| t1 | 1.000 | 0.667 | -0.333 |
| t2 | 1.000 | 0.667 | -0.333 |
| t2 | 0.000 | 1.000 | +1.000 |
| t2 | 1.000 | 0.667 | -0.333 |

