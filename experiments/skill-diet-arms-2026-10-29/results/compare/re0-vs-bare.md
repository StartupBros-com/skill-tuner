# Paired comparison — paired-json

**Verdict: inconclusive**  (non-inferiority margin delta = 0.1 findings per case)

- score paired across 8 cases (/tmp/hv-skill-diet-1278341/compare/paired/re0.json vs /tmp/hv-skill-diet-1278341/compare/paired/bare.json)
- mean difference: +0.083 per case (sd 0.295, se 0.104)
- 95% CI: [-0.16, +0.33]
- case record: 2 won, 1 lost, 5 tied
- robustness: bootstrap 95% CI [-0.08, +0.29], exact sign test p=1.000, effect size dz +0.28
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 13 cases (+5 on this run)

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| t1 | 1.000 | 0.667 | -0.333 |
| t1 | 0.000 | 0.000 | +0.000 |
| t1 | 0.000 | 0.000 | +0.000 |
| t1 | 1.000 | 1.000 | +0.000 |
| t1 | 1.000 | 1.000 | +0.000 |
| t2 | 0.000 | 0.333 | +0.333 |
| t2 | 0.000 | 0.667 | +0.667 |
| t2 | 1.000 | 1.000 | +0.000 |

