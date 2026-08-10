# Case study: what the Ponytail numbers actually license

The Ponytail skill's benchmark saga is 2026's most public instance of the
failure this project exists to prevent: a single-shot benchmark claimed
80–94% less code; a public critique (Scott Logic) broke the baseline; the
maintainer rebuilt the benchmark agentically and republished **54%**;
JetBrains' independent 80-task replication then found a **−15.4% median**
(p=0.088) on harder tasks. Three numbers, three methodologies, no
confidence interval anywhere in the dispute — every round was settled by
social challenge and re-measurement rather than by stating what the data
licensed in the first place.

Nobody had run a paired analysis on the public data. It takes one command
and costs nothing.

## The data

The only per-task paired numbers published anywhere in the dispute are the
maintainer's own corrected benchmark
([`benchmarks/results/2026-06-18-agentic.md`](https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/results/2026-06-18-agentic.md)):
12 real-repo feature tasks, LOC = git-diff added lines, mean of n=4
Claude-Code-Haiku-4.5 runs per cell, baseline arm vs ponytail arm.
JetBrains and Scott Logic publish aggregates only (JetBrains mentions
"evaluation artifacts" without linking them). Transcription:
`ponytail-data.py`; reproduce with the two `compare --paired-json` lines
below.

## The analysis ($0, `tune.py compare --paired-json`)

Per-task LOC reduction against a null of zero:

| metric | mean/task | 95% CI | record | sign test | dz |
| --- | --- | --- | --- | --- | --- |
| absolute LOC | +100.2 | [+16.3, +184.1] | 11W / 0L / 1T | p = 0.001 | +0.76 |
| percent | **+35.4%** | **[+15.0, +55.9]** | 11W / 0L / 1T | p = 0.001 | +1.10 |

## What the data licenses — and what it does not

- **The reduction is real beyond reasonable doubt.** Eleven of twelve
  tasks reduced, none regressed; the exact sign test alone settles the
  direction at p = 0.001. Nothing in this analysis is hostile to Ponytail.
- **The famous number is a totals artifact.** "54% less code" is
  1015/2217 — a ratio of totals dominated by three large frontend tasks
  (date-picker 404→23, color-picker 287→23, wizard 571→312). The typical
  *task* saw **35.4%**, and the interval an honest report would have led
  with spans **15% to 56%**.
- **The heterogeneity is the story.** Per-task effects run 0% to 94.3%
  (sd 32 points): scaffold-heavy frontend components collapse; small
  backend endpoints barely move (21→17, 44→44). A one-number claim about
  this distribution misleads in both directions at once.
- **The replication "dispute" mostly dissolves.** JetBrains' −15.4%
  median on 80 harder SkillsBench tasks is not a contradiction of this
  data; it sits at the low end of the interval above, exactly where a
  task-mix shifted toward backend-style work would land. Two aggregates
  that look like a fight are one distribution reported without its spread.
- **Boundaries.** n=12 tasks from one repo, one model (Haiku 4.5), cell
  means over 4 runs (within-cell variance unpublished), LOC as the metric
  (says nothing about correctness — the same source's safety tier and
  JetBrains' quality counts address that separately). This analysis
  inherits every one of those limits; it adds only the interval the
  discussion never had.

## The point

Every party in this dispute had the data to state a calibrated claim on
day one. The correction cycle — viral number, public challenge, rebuild,
independent replication, press coverage — spent months and three
organizations' effort re-litigating what one paired interval says in one
line: *ponytail reduces code by a per-task mean of ~35% [15, 56], wildly
task-dependent, direction near-certain.* That line is what this tool
prints.
