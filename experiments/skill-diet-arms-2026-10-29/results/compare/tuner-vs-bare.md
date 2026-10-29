# Paired comparison — paired-json

**Verdict: inconclusive**  (non-inferiority margin delta = 0.1 findings per case)

- score paired across 8 cases (/tmp/hv-skill-diet-1278341/compare/paired/tuner.json vs /tmp/hv-skill-diet-1278341/compare/paired/bare.json)
- mean difference: +0.125 per case (sd 0.354, se 0.125)
- 95% CI: [-0.17, +0.42]
- case record: 1 won, 0 lost, 7 tied
- robustness: bootstrap 95% CI [+0.00, +0.38], exact sign test p=1.000, effect size dz +0.35
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 12 cases (+4 on this run)

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| t1 | 1 | 1 | +0 |
| t1 | 0 | 0 | +0 |
| t1 | 0 | 0 | +0 |
| t1 | 1 | 1 | +0 |
| t1 | 1 | 1 | +0 |
| t2 | 0 | 1 | +1 |
| t2 | 0 | 0 | +0 |
| t2 | 1 | 1 | +0 |

