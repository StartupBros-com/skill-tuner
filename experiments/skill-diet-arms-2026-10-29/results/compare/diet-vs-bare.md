# Paired comparison — paired-json

**Verdict: inconclusive**  (non-inferiority margin delta = 0.1 findings per case)

- score paired across 8 cases (/tmp/hv-skill-diet-1278341/compare/paired/diet.json vs /tmp/hv-skill-diet-1278341/compare/paired/bare.json)
- mean difference: +0.292 per case (sd 0.603, se 0.213)
- 95% CI: [-0.21, +0.80]
- case record: 4 won, 3 lost, 1 tied
- robustness: bootstrap 95% CI [-0.08, +0.71], exact sign test p=1.000, effect size dz +0.48
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 12 cases (+4 on this run)

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 0.000 | 1.000 | +1.000 |
| t1 | 0.000 | 0.667 | +0.667 |
| t1 | 1.000 | 0.667 | -0.333 |
| t1 | 1.000 | 0.667 | -0.333 |
| t2 | 0.000 | 0.667 | +0.667 |
| t2 | 0.000 | 1.000 | +1.000 |
| t2 | 1.000 | 0.667 | -0.333 |

