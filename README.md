# skill-tuner

Evidence-tagged authoring doctrine for agent-consumed documents, plus a bundled eval runner that proves each change on your own harness.

## Receipts

Two runs, both live against `claude -p`, both reproducible from committed configs. The routing eval **refused** a description prune that lost accuracy; the probe **confirmed 11 defects** across six documents that had already shipped. A gate that only ever says yes is not a gate, so both outcomes are published.

<!-- receipts:start -->
### Routing-parity — `receipts-routing-001`

| Condition | Accuracy | Near-miss rejection |
| --- | --- | --- |
| original | 24/26 (92.3%) | 8/8 (100.0%) |
| pruned | 23/26 (88.5%) | 8/8 (100.0%) |

**Verdict: refuse**

Failing case ids: agent-swarm__obvious__2, agent-swarm__paraphrase__1

### Marginal-value probe — `swapgate2-probe-candidate`

**findings_confirmed: 11** (refuted: 11, targets: 6, probe calls: 6, verify calls: 66 at 3 skeptics per finding)

| Target | confirmed | refuted |
| --- | --- | --- |
| browser-console-setup | 0 | 3 |
| agent-swarm | 1 | 3 |
| design-drift | 0 | 4 |
| cli-doctor-mode | 3 | 1 |
| branch-harmonization | 3 | 0 |
| curl-bash-installer | 4 | 0 |

- **Single source of truth [craft] — keep each meaning in one authoritative place**: This HTML comment duplicates two things already stated elsewhere: the old→native mapping is already the entire content of the "Primitive map" table, and "skills that need campaign…
- **Negation [research] — state the target behaviour instead of the ban; keep prohibition onl…**: The sentence leads with the forbidden op ("NO DeletePath") before stating what the enum actually contains, dragging the banned behaviour into context first instead of naming the p…
- **Completion criteria [craft] — every step ends on a condition telling the agent the work i…**: "Until clean" is an unbound, uncheckable qualifier with no defined criterion anywhere else in the document — nothing tells the agent what "clean" means or how to verify it, unlike…
- …and 8 more, with quotes and proposed fixes, in `reports/swapgate2-probe-candidate/report.md`
<!-- receipts:end -->

Reproduce (substitute your own skill paths and a config of the same shape — see `configs/receipts-routing-001.json` / `configs/swapgate2-probe-candidate.json` for the format):

```
python3 skills/skill-tuner/scripts/tune.py routing-parity --config configs/receipts-routing-001.json --run-id receipts-routing-001 --yes --budget-usd 5
python3 skills/skill-tuner/scripts/tune.py probe --config configs/swapgate2-probe-candidate.json --run-id swapgate2-probe-candidate --yes --budget-usd 6
```

Numbers are session-measured on the authors' harness (2026-08-07); they will be re-cited to the public evidence ledger when it lands. The probe run above cost $2.68.

### Reading the probe numbers honestly

`refuted: 11` is not noise the run failed to suppress — it is the adversarial half working. Every raised finding is judged by three independent skeptics in fresh contexts under a default-refute instruction, and a strict majority is required to confirm. A quote that does not appear in the target document is downgraded regardless of how the panel voted, so a fabricated citation cannot become a receipt; one of this run's refutations was exactly that.

Two of six targets confirmed nothing. That is the expected shape of an honest probe: it is a defect finder, not a defect generator, and an empty result on a well-written document is the outcome the design protects.

## Attribution

skill-tuner descends from [mattpocock/skills](https://github.com/mattpocock/skills)' `writing-for-agents` skill (MIT licensed). It extends that doctrine with an empirical validation harness: evidence-tagged rules with falsifiers, a routing-parity eval runner, and a marginal-value probe protocol.
