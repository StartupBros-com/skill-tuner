# Paired comparison — paired-json

**Verdict: inconclusive**  (non-inferiority margin delta = 0.1 findings per case)

- score paired across 8 cases (/tmp/hv-skill-diet-1278341/compare/paired/wfa.json vs /tmp/hv-skill-diet-1278341/compare/paired/bare.json)
- mean difference: +0.167 per case (sd 0.504, se 0.178)
- 95% CI: [-0.25, +0.59]
- case record: 3 won, 1 lost, 4 tied
- robustness: bootstrap 95% CI [-0.13, +0.50], exact sign test p=0.625, effect size dz +0.33
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 17 cases (+9 on this run)

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 0.000 | 1.000 | +1.000 |
| t1 | 0.000 | 0.667 | +0.667 |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 1.000 | 1.000 | +0.000 |
| t2 | 0.000 | 0.333 | +0.333 |
| t2 | 0.000 | 0.000 | +0.000 |
| t2 | 1.000 | 0.333 | -0.667 |

