# skill-tuner

Evidence-tagged authoring doctrine for agent-consumed documents, plus a bundled eval runner that proves each change on your own harness.

## Receipts

Two runs, both live against `claude -p`, both reproducible from committed configs. The routing eval **refused** a description prune that lost accuracy; the probe **confirmed 19 defects** across sixteen documents that had already shipped. A gate that only ever says yes is not a gate, so both outcomes are published.

<!-- receipts:start -->
### Routing-parity — `receipts-routing-001`

| Condition | Accuracy | Near-miss rejection |
| --- | --- | --- |
| original | 24/26 (92.3%) | 8/8 (100.0%) |
| pruned | 23/26 (88.5%) | 8/8 (100.0%) |

**Verdict: refuse**

Failing case ids: agent-swarm__obvious__2, agent-swarm__paraphrase__1

### Marginal-value probe — `swapgate3-probe-candidate`

**findings_confirmed: 19** (refuted: 32, targets: 16, probe calls: 16, verify calls: 153 at 3 skeptics per finding)

| Target | confirmed | refuted |
| --- | --- | --- |
| agent-swarm | 2 | 3 |
| animate | 0 | 3 |
| apple-design | 1 | 2 |
| automating-your-automations-local | 0 | 4 |
| branch-harmonization | 1 | 1 |
| brand-voice-builder | 3 | 2 |
| browser-console-setup | 1 | 1 |
| cass-rerank-local | 2 | 1 |
| cli-agent-ergonomics | 3 | 1 |
| cli-doctor-mode | 1 | 2 |
| codex-consult | 0 | 2 |
| curl-bash-installer | 1 | 3 |
| de-monolithize-your-codebase-isomorphically-local | 1 | 3 |
| design-drift | 1 | 1 |
| emil-design-eng | 1 | 2 |
| find-animation-opportunities | 1 | 1 |

- **Single source of truth — duplication of one meaning across sections**: This restates, nearly verbatim, the rule already given under 'Pick the lightest engine that fits': 'Pin `model` (sonnet/haiku for mechanical sweeps — don't let them inherit the se…
- **Leading words — a coined term must be defined, not assumed**: 'Doghouse' is used as if it were a known term but is never defined anywhere in the document. Per the leading-words rule, a coined term recruits no priors and must pay its own defi…
- **Completion criteria [craft]**: This checklist item gives no checkable bound — 'the perception threshold' names no value or method to test against, unlike nearly every other quantitative rule in this document (1…
- …and 16 more, with quotes and proposed fixes, in `reports/swapgate3-probe-candidate/report.md`
<!-- receipts:end -->

Reproduce (substitute your own skill paths and a config of the same shape — see `configs/receipts-routing-001.json` / `configs/swapgate3-probe-candidate.json` for the format):

```
python3 skills/skill-tuner/scripts/tune.py routing-parity --config configs/receipts-routing-001.json --run-id receipts-routing-001 --yes --budget-usd 5
python3 skills/skill-tuner/scripts/tune.py probe --config configs/swapgate3-probe-candidate.json --run-id swapgate3-probe-candidate --yes --budget-usd 11
python3 skills/skill-tuner/scripts/tune.py verify swapgate3-probe-candidate
```

Numbers are session-measured on the authors' harness (2026-08-07); they will be re-cited to the public evidence ledger when it lands. The probe run above cost $7.34 and reads every input from `origin/main`, so `tune.py verify` can tell you later whether it still describes anything.

### Reading the probe numbers honestly

`refuted: 32` is not noise the run failed to suppress — it is the adversarial half working. Every raised finding is judged by three independent skeptics in fresh contexts under a default-refute instruction, and a strict majority is required to confirm. A quote that does not appear in the target document is downgraded regardless of how the panel voted, so a fabricated citation cannot become a receipt; two of this run's refutations were exactly that.

Three of sixteen targets confirmed nothing. That is the expected shape of an honest probe: it is a defect finder, not a defect generator, and an empty result on a well-written document is the outcome the design protects.

### The eval blocked this project's own doctrine

The strongest thing we can say about the runner is what it did to us.

skill-tuner's doctrine descends from `writing-for-agents` and was supposed to improve on it. The plan gated launch on proving that: the doctrine ships only if it beats its ancestor on this same pipeline. Run three times, the gate said **LOST** at 1 document, **WON** at 6, and — once inputs were pinned, findings judged by a three-skeptic panel, and the verdict paired by document — **WORSE** at 16:

```
candidate 19 vs incumbent 30 confirmed across 16 documents
mean -0.688 findings/document, 95% CI [-1.19, -0.18], 1 won / 8 lost / 7 tied
```

The interval excludes zero, so the swap is blocked. The first two answers were noise from a rule that compared raw totals and therefore could never say *we could not tell*; `tune.py compare` says it.

We are publishing that because it is the product's actual claim. An authoring guide that cannot measure itself will tell you its rules work. This one measured, and the measurement said no.

Full record: [`reports/swapgate3-summary.md`](reports/swapgate3-summary.md).

## Attribution

skill-tuner descends from [mattpocock/skills](https://github.com/mattpocock/skills)' `writing-for-agents` skill (MIT licensed). It extends that doctrine with an empirical validation harness: evidence-tagged rules with falsifiers, a routing-parity eval runner, and a marginal-value probe protocol.
