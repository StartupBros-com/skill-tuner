# Paired comparison — paired-json

**Verdict: inconclusive**  (non-inferiority margin delta = 0.1 findings per case)

- score paired across 8 cases (/tmp/hv-skill-diet-1278341/compare/paired/diet.json vs /tmp/hv-skill-diet-1278341/compare/paired/wfa.json)
- mean difference: +0.125 per case (sd 0.434, se 0.153)
- 95% CI: [-0.24, +0.49]
- case record: 3 won, 2 lost, 3 tied
- robustness: bootstrap 95% CI [-0.13, +0.42], exact sign test p=1.000, effect size dz +0.29
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 17 cases (+9 on this run)

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 0.667 | 0.667 | +0.000 |
| t1 | 1.000 | 0.667 | -0.333 |
| t1 | 1.000 | 0.667 | -0.333 |
| t2 | 0.333 | 0.667 | +0.333 |
| t2 | 0.000 | 1.000 | +1.000 |
| t2 | 0.333 | 0.667 | +0.333 |

