# skill-tuner

**Tells you whether a change to an agent-consumed document actually worked** — with an interval, a margin you set, and a receipt that can be re-checked after the model moves under you.

It does not help you write skills. Plenty of guides do that. What nothing does is tell you whether the edit you just made was an improvement or a coin flip.

## The problem, with receipts

Eval harnesses report deltas. Anthropic's own [skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator) runs a proper experiment — eval cases, an isolated subagent per run, graded expectations, `with_skill` vs `without_skill` benchmarking — and `aggregate_benchmark.py` reports mean and stddev. Its improvement record stores a bare `grading_result: "won" | "lost" | "tie"` beside a pass rate.

**A threshold with no interval behind it cannot say *we could not tell*, so it answers every time — and on a noisy measurement most of those answers are luck.**

We know because it happened to us. One question — is this doctrine better than the one it forked from? — asked three times with a raw-count rule:

| documents | rule's answer | reality |
| --- | --- | --- |
| 1 | **LOST** | noise (plus a markdown-blind quote guard) |
| 6 | **WON** | noise — a lucky draw on three documents |
| 16 | **LOST** | a regression is real — 95% CI [−1.19, −0.18] excludes zero — but its size against any stated margin stayed unresolved |

Two of three were wrong. The same rule produced both. That cost ~$30 and a day to discover, and it is the single reason this project exists in its current form.

## What it does

```
tune.py compare --skill-creator <benchmark-dir> \
  --baseline without_skill --candidate with_skill --delta 0.05
```

```
# Paired comparison — skill-creator benchmark

**Verdict: inconclusive**  (non-inferiority margin delta = 0.05 pass_rate per case)

- pass_rate paired across 6 cases (with_skill vs without_skill)
- mean difference: +0.017 per case (sd 0.279, se 0.114)
- 95% CI: [-0.28, +0.31]
- case record: 3 won, 2 lost, 1 tied
- a bare total comparison would say: PASS
- to clear the margin at this mean and spread you would need about 68 cases (+62 on this run)
```

On that benchmark `with_skill` averages 0.550 against 0.533. A total comparison calls it a win. It is not distinguishable from zero, and you would need about 68 cases before it could be.

Three things, none of which a first-party harness gives you:

- **A verdict, not a delta** — paired by case, 95% interval, a non-inferiority margin *you* state, and four outcomes including `inconclusive`. A percentile bootstrap, an exact sign test, and a paired effect size print beside the t-interval, so a verdict leaning on a normality assumption is visible too. It prints what a bare comparison would have concluded next to its own, so the difference is visible rather than argued.
- **Provenance** — every input content-hashed and git-pinned, model and CLI version recorded. `tune.py verify <run>` re-checks a finished run for **$0** and tells you what drifted. It caught a real input change within hours of being written.
- **An adversarial probe** — applies an authoring doctrine to a document, judges each finding with an independent skeptic panel, and downgrades any finding whose quote is not actually in the target, regardless of how the panel voted.

## Using it

**`/skill-tuner:tune <path>`** — point it at a `SKILL.md`, `AGENTS.md` or `CLAUDE.md` and your agent will probe it, fix what the probe confirms, re-probe until those findings are gone, and prove the description still routes if it changed.

Findings arrive pre-verified — three independent skeptics in fresh contexts, plus a code-level check that the quoted text actually appears in the document — so the agent acts on them rather than re-litigating them. Refuted findings are shown too, labelled with what killed them.

The command is deliberately explicit about what it may **not** claim: a before/after count on one document is not evidence of improvement. For that you need a paired comparison across many documents, which is what `tune.py compare` is for.

The runner never fires on the model's own initiative. It spends your tokens, so it starts on your instruction, and reports the estimate before the first call and the actual after.

For a one-off, without the loop:

```
python3 skills/skill-tuner/scripts/tune.py probe --target path/to/SKILL.md --yes --budget-usd 3 --verify-trials 3
```

## Works with skill-creator, not against it

skill-creator runs the experiment; skill-tuner decides what it means. Integration is at the **file** boundary — it reads `grading.json` / the benchmark tree and never imports their code, because their scripts have no API contract and the marketplace bumps plugin SHAs nightly.

Use theirs for eval cases, grading, trigger tuning and benchmarking. Use this for the verdict.

## What this does not measure

Two axes are out of scope, and the ecosystem's loudest 2026 numbers live on them. Whether a skill makes an agent **better at its end task** is skill-creator's benchmark question (and SkillsBench's, at academic scale) — this tool reads those results, it does not produce them. Whether a skill is **safe to install** — prompt injection, exfiltration — is a scanner's question (Snyk's ToxicSkills audit found injection in 36% of 22,511 public skills). skill-tuner grades the authoring and gates the edit: point it at a document you already trust, beside a benchmark you already run.

## Receipts

Live runs against `claude -p`, reproducible from committed configs. The routing eval **refused** a description prune that lost accuracy; the probe **confirmed 19 defects** across sixteen already-shipped documents. A gate that only ever says yes is not a gate, so both outcomes are published.

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

- **Single source of truth — duplication of one meaning across sections**: restates, nearly verbatim, a rule already given under 'Pick the lightest engine that fits'…
- **Leading words — a coined term must be defined, not assumed**: 'Doghouse' is used as if it were a known term but is never defined anywhere in the document…
- **Completion criteria [craft]**: this checklist item gives no checkable bound — 'the perception threshold' names no value or method to test against…
- …and 16 more, with quotes and proposed fixes, in `reports/swapgate3-probe-candidate/report.md`
<!-- receipts:end -->

Reproduce:

```
python3 skills/skill-tuner/scripts/tune.py probe --config configs/swapgate5-probe-doctrine-v2.json --run-id my-run --yes --budget-usd 11
python3 skills/skill-tuner/scripts/tune.py verify my-run
```

Session-measured on the authors' harness (2026-08-08). Costs and what actually reduces them are measured in [`docs/COSTS.md`](docs/COSTS.md) — including two optimizations we found and deliberately did **not** switch on, because they change the prompt envelope and would invalidate every banked baseline.

## The doctrine is the worked example, not the product

`skills/skill-tuner/SKILL.md` is an authoring doctrine where every rule carries an evidence tag and a falsifier — and, new in v3, every `[research]` tag carries a fetched-and-verified citation in [`FALSIFIERS.md`](skills/skill-tuner/FALSIFIERS.md). It descends from [mattpocock/skills](https://github.com/mattpocock/skills)' `writing-for-agents` (MIT). Upstream renamed and restructured that skill on 2026-07-31; every comparison below is against the pinned pre-rename snapshot this doctrine actually forked from, and a re-baseline against the current upstream has not yet been run.

**We have never shown it beats its ancestor.** Measured on 15 shared documents, three times:

| version | confirmed | 95% CI | verdict |
| --- | --- | --- | --- |
| v1 | 18 vs 29 | [−1.27, −0.20] | inconclusive — regression confirmed* |
| v1, apparatus stripped | 22 vs 29 | [−1.30, +0.37] | inconclusive |
| **v2** | **27 vs 29** | **[−0.76, +0.49]** | **not_worse** |

\* v1 was originally published as **worse**. A 2026-08-08 statistics review found the worse verdict anchored at zero rather than −δ, so it fired on any confirmed regression even inside the declared-tolerable band; the corrected reading of the same interval is a confirmed regression of unresolved size against the margin. The data did not move — the label did, and the fix is in `compare.py` with a regression test.

That is the honest state: *not worse*, never better. It is published because it is the point. Every other authoring guide asserts its rules work and has measured nothing; this one measured, lost, and shipped the data — and the harness refused its own doctrine twice on the way.

If you want a doctrine, use either. If you want to know whether the one you picked is doing anything, that's what the rest of this repo is for.

## Attribution

Doctrine descends from `writing-for-agents` (MIT). Reads benchmark output from Anthropic's `skill-creator` (Apache 2.0), which it complements rather than replaces.
