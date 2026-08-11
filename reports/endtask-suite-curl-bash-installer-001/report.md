# End-task A/B

# Paired comparison — endtask

**Verdict: not_worse**  (non-inferiority margin delta = 0.1 pass_rate per case)

- pass_rate paired across 6 cases (current vs ancestor)
- mean difference: +0.000 per case (sd 0.053, se 0.022)
- 95% CI: [-0.06, +0.06]
- case record: 1 won, 1 lost, 4 tied
- robustness: bootstrap 95% CI [-0.04, +0.04], exact sign test p=1.000, effect size dz +0.00
- a bare total comparison would say: PASS

| Case | baseline | candidate | diff |
| --- | --- | --- | --- |
| build-from-source-consent | 1.000 | 1.000 | +0.000 |
| checksum-signature-supply-chain | 0.833 | 0.917 | +0.083 |
| daemon-service-uninstall-guard | 1.000 | 0.917 | -0.083 |
| idempotent-hook-merge | 0.917 | 0.917 | +0.000 |
| no-sudo-atomic-lock | 0.929 | 0.929 | +0.000 |
| proxy-airgap-checksum | 1.000 | 1.000 | +0.000 |


**PARTIAL: budget cap reached.**
