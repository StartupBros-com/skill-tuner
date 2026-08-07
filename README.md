# skill-tuner

Evidence-tagged authoring doctrine for agent-consumed documents, plus a bundled eval runner that proves each change on your own harness.

## Receipts

<!-- receipts:start -->
### Routing-parity — `receipts-routing-001`

| Condition | Accuracy | Near-miss rejection |
| --- | --- | --- |
| original | 24/26 (92.3%) | 8/8 (100.0%) |
| pruned | 23/26 (88.5%) | 8/8 (100.0%) |

**Verdict: refuse**

Failing case ids: agent-swarm__obvious__2, agent-swarm__paraphrase__1

### Marginal-value probe — `receipts-probe-001`

**findings_confirmed: 0** (refuted: 0, probe calls: 1, verify calls: 0)

No confirmed findings on this pass.
<!-- receipts:end -->

Reproduce (substitute your own skill paths and a config of the same shape — see `configs/receipts-routing-001.json` / `configs/receipts-probe-001.json` for the format):

```
python3 skills/skill-tuner/scripts/tune.py routing-parity --config configs/receipts-routing-001.json --run-id receipts-routing-001 --yes --budget-usd 5
python3 skills/skill-tuner/scripts/tune.py probe --config configs/receipts-probe-001.json --run-id receipts-probe-001 --yes --budget-usd 5
```

Numbers are session-measured on the authors' harness (2026-08-07); they will be re-cited to the public evidence ledger when it lands.

## Attribution

skill-tuner descends from [mattpocock/skills](https://github.com/mattpocock/skills)' `writing-for-agents` skill (MIT licensed). It extends that doctrine with an empirical validation harness: evidence-tagged rules with falsifiers, a routing-parity eval runner, and a marginal-value probe protocol.
