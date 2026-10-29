# Doctrine gate round for #68 and #69 (swapgate8): landed as not_worse, never as better

Three changes to `skills/skill-tuner/SKILL.md` went to their predeclared
instruments and all three landed. The description's new trigger word landed
on routing parity plus a live routing probe. The two body edits, gated
together against a fresh baseline, came back **38 vs 34** confirmed
findings, 95% CI **[−0.56, +1.09]**, **not_worse** at δ = 1.0 with the
sequential test undecided after all 15 documents. That is the first body
change to pass this project's gate, and it passed as *not worse*: the
interval straddles zero, the sign test does not resolve (p = 0.77), and
nothing here licenses "better".

The round was predeclared before the first paid call
(`experiments/doctrine-gate-2026-10-29/predeclare.md`); every deviation from
that plan is logged there with a timestamp. The three changes came from the
skill-diet harness-vet (`docs/vets/2026-10-29-skill-diet-harness-vet.md`):

- **c68** (#68): a new *Pruning and drift* bullet, "Rule, not incident",
  tagged `[craft]`.
- **c69a** (#69a): the environment-as-source-of-truth sentences moved out of
  the *Single source of truth* paragraph into their own bullet, wording
  unchanged, `[craft]` carried over.
- **c69b** (#69b): one trigger word, "shortening", added to the frontmatter
  description.

## A new comparability island

Every instrument in this round pinned `claude-sonnet-5-5`. The swapgate3 to
swapgate7 series pinned `claude-sonnet-5` under the pre-v0.8.2 envelope,
`compare` refuses to pair across envelopes, and 13 of the 15 gate-set
documents had changed since the last banked leg, so the round opened with a
fresh baseline (leg 0) rather than reusing a banked one. The swapgate8
numbers sit beside the series table, not in it: same 15 `skills-local`
documents, same `max_findings 5` and `verify_trials 3`, different model,
different envelope, different document bytes. A full leg on the new model
cost $2.75 to $3.07 against the series' $7.25 to $8.30.

## c69b, the description: landed on two instruments

**Routing parity** (PLAYBOOK rule 4, `reports/swapgate8-routing-desc/`):
`neutral_ids: true`, 4 trials per case, 12-case battery (5 should-fire
including the vet's own brief, 5 near-misses that use the new trigger word
on non-agent documents and code, 2 none-of-the-above), 5 distractors.

| condition | accuracy | near-miss rejection |
| --- | --- | --- |
| original | 48/48 (100%) | 28/28 |
| candidate | 48/48 (100%) | 28/28 |

**Verdict: land.** Parity, not gain: the battery routes the vet's brief to
skill-tuner 4/4 under *both* descriptions, so it did not reproduce the live
failure the vet observed.

**Live routing probe** (the vet's harness, skill installed, no slash token,
the t1 brief, 10 turns, 3 reps per condition,
`experiments/doctrine-gate-2026-10-29/results/runs/live-*`):

| description | runs that invoked skill-tuner |
| --- | --- |
| current | 1/3 |
| candidate | 3/3 |

The vet's same-harness probe earlier the same day scored the current
description 0/3. The battery and the live harness disagree about the
current description, and the live harness is the one that matches how the
skill is actually reached: a 12-case battery with ids hidden asks the model
to pick from six short descriptions, while a live session decides whether
to open a skill at all. Both predeclared land conditions held (parity AND
live ≥ 2/3), so the description landed first and was baked into every
gated candidate before leg 0 ran: gated bytes equal shipped bytes.

## The gate (PLAYBOOK rule 7)

**Leg 0** (`swapgate8-probe-incumbent`, 09:38 to 10:07Z): the current
doctrine with only the landed description, 15 documents, **34 confirmed**,
28 refuted, 201 calls (15 probe + 186 verify), **$3.07**. Doctrine input
`desc-only.SKILL.md` sha256 `13414f9453ad` at a clean commit (`49a4dda`);
all 15 targets clean at dotfiles `46f806da`.

**Leg 1** (`swapgate8-gate-combined`, 10:07 to 10:32Z): `tune.py gate
--delta 1.0` (α = 0.05, σ₀ = 2.0), the combined candidate (c68 + c69a,
sha256 `62f3338b8914`) against leg 0, targets re-hashed before the leg with
zero drift. **38 confirmed**, 18 refuted, 183 calls, **$2.75**.

| statistic | value |
| --- | --- |
| mean difference | +0.267 findings/document |
| 95% CI (t) | [−0.56, +1.09] |
| bootstrap CI | [−0.47, +1.00] |
| sign test | p = 0.77 |
| documents | 7 won, 5 lost, 3 tied |
| sequential (mSPRT) | undecided after 15/15 |
| fixed-n verdict of record | **not_worse** at δ = 1.0 |
| `tune.py gate` exit | 0 |

The sequential test never stopped: the margin-side likelihood ratio peaked
at 7.24 after 14 documents and fell to 4.20 on the last one, short of the
1/α = 20 bound, so the leg ran to full price and the fixed-n verdict on all
15 pairs decided, exactly as a plain `compare` would have. The candidate's
refuted count fell from 28 to 18; swapgate7 read a refuted-count rise as
the signature of additions steering probes toward weaker framings, and the
same reading in reverse is noted here without being leaned on.

**Isolation.** Because the combined candidate passed, the c68 and c69a legs
did not run and the isolated effect of each body edit is unmeasured. Either
edit could be carrying the other.

Both manifests verify clean (`tune.py verify`, zero model calls) at landing.

## Mechanism check (not a land bar)

The vet's fixture, re-run with the combined candidate as the slash-invoked
`/skill-tuner` arm, 3 reps per task, graded by the vet's `grade.py`; the
control is the vet's same-day current-doctrine arm (3 reps per task,
`experiments/skill-diet-arms-2026-10-29/results/runs.tsv`).
Disclosure: the candidate text was drafted knowing this fixture's answer
key, so a pass shows the rule fires on this fixture, not that it
generalises.

| task | item | what it checks | current doctrine | combined candidate |
| --- | --- | --- | --- | --- |
| t2 | D9 | incident narrative removed (c68's claim) | 0/3 | **3/3** |
| t2 | D1 | the check rule stated exactly once | 3/3 | 1/3 (by eye 2/3) |
| t2 | K5 | the check rule present at all | 3/3 | 2/3 (by eye 3/3) |
| t1 | D5 | `--help` option table not restated (c69a's claim) | 0/3 | 0/3 |
| t1 | D7 | incident-derived rollback steps dropped | 0/3 | 0/3 |

By eye: all three current-doctrine runs kept the incident (a History
section or an outage sentence beside the rule); all three candidate runs
dropped it and wrote the rule once as a positive step. Of the two graded
D1 misses, rep 1 is a grader miss (the rule reads "is preceded by a
passing check", and the grader keys on "before", "never skip" or
"without"), rep 2 is a real mild duplication (the Checking paragraph
repeats "re-run the check before any release"). The `no manifest` pass
criterion is stated twice in all three candidate runs and in two of three
control runs, so that duplication is not attributable to the candidate.
c69a's bullet moved nothing on t1: both arms keep the option table and
the rollback retry lines in every rep. Runs are saved under
`experiments/doctrine-gate-2026-10-29/results/runs/tuner-combined-*`.

## Decision

**All three landed.** `skills/skill-tuner/SKILL.md` is byte-identical to
`experiments/doctrine-gate-2026-10-29/candidates/combined.SKILL.md`, sha256
`62f3338b891464aa1abf49fe9fb17598b76acb33b4a6aeec173e43ab00195228`, the
doctrine input recorded in the gate manifest.

The `[craft]` tags on both body edits stay. Issue #68 proposed that the tag
would become `[measured]` if the gate passed. The gate measures the
doctrine's defect-finding yield on fifteen documents, not the rule's own
claim (that an agent given a story reads it as the one case to avoid);
FALSIFIERS already says that the doctrine measuring not worse validates no
individual rule, and the mechanism check's answer-key disclosure means D9
3/3 cannot stand in for the A/B the falsifier names. Each landed bullet has
its falsifier recorded in `FALSIFIERS.md`.

The installed plugin copy (`hov/skill-tuner` 0.10.0) still serves the
pre-landing bytes and the old description; the live routing gain reaches
sessions that load the skill through the plugin only when the next plugin
release ships these bytes. Landing is canonical-first (PLAYBOOK rule 3) and
this note is the only action.

## Deviations from the predeclaration

- Mechanism check ran on `tuner-combined` during leg 0, before any gate
  verdict (logged 09:50Z). Combined landed, so those runs stand.
- PLAYBOOK rule 6's standing endtask suite was not run (declared up
  front): its inputs are tuned dotfiles skills against frozen ancestors,
  untouched by a doctrine text change. The operator may run it at release.
- The routing pre-flight estimated $4.80 at the $0.05/call default and spent
  $0.57 over 96 calls; the default overstates routing calls by about 8x
  (logged 09:50Z).

## Totals

| run | calls | spent | cap |
| --- | --- | --- | --- |
| routing-parity (`swapgate8-routing-desc`) | 96 | $0.57 | $3 |
| live routing probe (6 sessions) | 6 | $0.43 | $1 |
| leg 0 baseline (`swapgate8-probe-incumbent`) | 201 | $3.07 | $12 |
| leg 1 gate (`swapgate8-gate-combined`) | 183 | $2.75 | $12 |
| mechanism check (6 sessions) | 6 | $0.41 | $1 |
| **round** | | **$7.23** | |

Doctrine investigation cumulative: the swapgate3 to swapgate7 series
$46.27 (`reports/swapgate7-summary.md`) + swapgate8 $7.23 = **$53.50**.
