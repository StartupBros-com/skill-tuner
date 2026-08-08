---
description: Find and fix real defects in a skill, AGENTS.md, or CLAUDE.md, then prove the description still routes.
argument-hint: <path to SKILL.md / AGENTS.md / CLAUDE.md>
---

Tune the document at `$1`.

You are running the loop the human just asked for, so the runner may spend
tokens. Report the estimate before the first call and the actual after.

## 1. Read it

Read `$1` in full, and the bundled doctrine at
`${CLAUDE_PLUGIN_ROOT}/skills/skill-tuner/SKILL.md`. You need both: the probe
tells you *what* is wrong, the doctrine tells you *what good looks like* when
you fix it.

## 2. Probe it

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-tuner/scripts/tune.py probe \
  --target "$1" --run-id tune-$(date +%s) --yes --budget-usd 3 --verify-trials 3
```

Every finding it reports has already survived three independent skeptics in
fresh contexts, plus a code-level check that the quoted text genuinely appears
in the document. **Treat confirmed findings as real and act on them.** They are
not suggestions to evaluate; the evaluating already happened.

Read the run's `report.md` for each finding's quote and proposed fix.

Refuted findings are listed too, with the mode that killed them
(`verifier` = the rule did not apply; `quote_not_found` = the probe invented
its evidence). Treat refuted findings as closed: their one remaining job is
the report's refuted line, where the human sees what the probe got wrong.

## 3. Fix what it found

Apply each confirmed finding. The doctrine's rules are the target shape —
positive phrasing over prohibition, one trigger per branch, checkable
completion bounds, one meaning in one place.

Fix the defect, not the sentence containing it. A finding about a vague
completion bound is asking for a bound that can be checked, not for the word
"clearly" to be deleted.

## 4. Re-probe

Run step 2 again against the edited file.

Done when: **every finding from step 2 is absent from the new report, and the
new report introduces no confirmed finding you have not addressed.** A fix that
trades one confirmed defect for another has not landed.

## 5. If you changed the description, prove it still routes

A reworded description is a routing change, and routing is the one thing here
that can be measured properly on a single document. Build a battery config
following `configs/receipts-routing-001.json`, with the original description
as `original` and yours as `pruned`, then:

```
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-tuner/scripts/tune.py routing-parity \
  --config <your-config> --run-id route-$(date +%s) --yes --budget-usd 3
```

Keep the new description only on a `land` verdict. On `refuse`, restore the
original and say which prompts it lost.

## What you may not claim

You probed one document. **A before/after count on one document is not
evidence of improvement** — this project has the receipts for that, having
recorded LOST, WON and WORSE for one question at n=1, 6 and 16 respectively.

So: report the defects you fixed and the routing verdict, both of which are
real. Do not report that the document is "better" as a measured fact, and do
not compare finding counts across the two probe runs as if the difference
meant something.

Measuring an actual improvement takes a paired comparison across many
documents — `tune.py compare`, which needs at least 3 and realistically many
more. Reach for it when changing something that affects a whole suite, such as
a shared convention or a doctrine, and never to grade a single edit.

## Report

- Confirmed defects found, and what you changed for each
- Anything refuted, so the human sees what the probe got wrong
- The routing verdict, if the description moved
- Actual spend, from the run output
