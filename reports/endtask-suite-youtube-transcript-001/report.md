# End-task A/B

# Paired comparison — endtask

**Verdict: not_worse**  (non-inferiority margin delta = 0.1 pass_rate per case)

- pass_rate paired across 7 cases (current vs ancestor)
- mean difference: -0.018 per case (sd 0.075, se 0.028)
- 95% CI: [-0.09, +0.05]
- case record: 1 won, 2 lost, 4 tied
- robustness: bootstrap 95% CI [-0.07, +0.03], exact sign test p=1.000, effect size dz -0.24
- a bare total comparison would say: FAIL

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| explicit-output-dir | 1.000 | 1.000 | +0.000 |
| non-english-list-subs-first | 1.000 | 1.000 | +0.000 |
| nonsensical-cwd-root | 1.000 | 1.000 | +0.000 |
| rate-limit-429-stop | 1.000 | 0.875 | -0.125 |
| short-clip-print-text | 0.800 | 0.900 | +0.100 |
| very-long-transcript-path-only | 0.900 | 0.800 | -0.100 |
| yt-dlp-invocation-correctness | 1.000 | 1.000 | +0.000 |

