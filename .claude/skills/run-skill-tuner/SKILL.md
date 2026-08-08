---
name: run-skill-tuner
description: Run, drive, smoke-test and debug skill-tuner. Use when asked to run skill-tuner, start or test the eval runner, probe a document, compare two runs, verify a banked run, or check that the CLI still works after a change.
---

skill-tuner is a **CLI**, not a server or a GUI — `skills/skill-tuner/scripts/tune.py`
with five subcommands. There is nothing to click and no window to screenshot.

The thing that shapes how you drive it: **the eval subcommands spend real
money.** Every one shells out to `claude -p`. But most of the surface is
reachable for free — `verify` and `compare` make zero model calls by design,
the 119-test suite runs on a fake adapter, and the refuse-to-spend guards are
observable precisely because they fire *before* the first call.

All paths below are relative to the repo root.

## Run (agent path) — start here

```bash
./.claude/skills/run-skill-tuner/smoke.sh
```

12 checks, ~30 s, **$0.00**, no network. Covers the environment preflight, the
unit suite, the stdlib-only guard, all three spend guards, `verify`, `compare`,
the too-few-cases refusal, and the differential check against skill-creator's
own reader. Exits non-zero if any check fails.

Verified output:

```
environment
  ok   doctor.sh: environment ready

unit suite (fake adapter — never calls a model)
  ok   Ran 119 tests
  ok   shipped runner imports stdlib only (R7)

refuse-to-spend guards (observable because they fire before the call)
  ok   unmetered run refused before any call (AE3)
  ok   prints a cost estimate before spending (R8)
  ok   aborts non-interactively without --yes
  ok   a refused pre-flight leaves no run directory behind

verify — re-checks a banked run, zero model calls
  ok   verify swapgate5-probe-doctrine-v2 -> DRIFTED (exit 1)

compare — paired verdict from banked reports, zero model calls
  ok   compare -> Verdict: not_worse
  ok   verdict carries a confidence interval
  ok   refuses to judge fewer than 3 cases

reader matches skill-creator's own (skipped when not installed)
  ok   Both readers extract the same values from every tree shape.

12 passed, 0 failed
```

To include one real probe against a scratch document (**~$0.15**):

```bash
./.claude/skills/run-skill-tuner/smoke.sh --live
# ok   live probe: findings_confirmed=2 refuted_count=0 spent=$0.1354
```

## Direct invocation — what most changes need

Touching `compare.py`, `provenance.py` or `skillcreator.py`? Call them
directly. No model, no cost:

```bash
cd skills/skill-tuner/scripts && python3 -m unittest discover tests
# Ran 119 tests ... OK
```

Run **from that directory** — the tests import sibling modules by bare name.

Judge two banked runs, or re-check one for drift — both free:

```bash
python3 skills/skill-tuner/scripts/tune.py compare \
  --baseline swapgate3-probe-incumbent \
  --candidate swapgate5-probe-doctrine-v2 --exclude design-drift

python3 skills/skill-tuner/scripts/tune.py verify swapgate5-probe-doctrine-v2
```

## Spending money on purpose

```bash
python3 skills/skill-tuner/scripts/tune.py probe \
  --target path/to/SKILL.md --run-id my-run --yes --budget-usd 2 --verify-trials 3
```

`--target` builds the config in memory; `--config <file>` is the committed,
reproducible alternative. Reports land in `reports/<run-id>/`
(`report.json`, `report.md`, `trials.jsonl`).

## Gotchas

- **`verify` exits 1 when a run has drifted.** That is a verdict, not a
  failure — the tool worked. Any wrapper must treat "produced a verdict" as
  success, or it will report a healthy tool as broken. The banked
  `swapgate5-probe-doctrine-v2` currently *does* report DRIFTED, because a
  dotfiles input moved after the run.
- **`set -o pipefail` breaks `tune.py … | grep -q`.** The CLI exits non-zero
  by design when it refuses to spend, and a pipeline inherits any stage's
  failure — so grep matches and the check still reports false. Capture into a
  variable, then match with `<<<`.
- **Never `tail` the test output.** The suite prints cost estimates to stdout
  while unittest writes its verdict to stderr; the last few interleaved lines
  are usually noise. Grep the whole capture for `^OK$`.
- **`claude -p` takes the prompt as `-p`'s argument.** Flags go *after* it.
  `claude -p --output-format json "text"` silently makes `--output-format`
  the prompt.
- **A doctrine file starting with `---` becomes a CLI flag** if passed as a
  bare argument: `error: unknown option '---'`. The runner's own prompts lead
  with instruction text, so this only bites ad-hoc invocations.
- **`claude` writes warnings to stderr**, so `2>&1 | python3 -c 'json.load…'`
  corrupts the JSON parse. Redirect the streams separately.
- **`compare` refuses fewer than 3 cases** rather than producing a
  meaningless interval. That is deliberate.
- **`--delta` is required with `--skill-creator`.** The 1.0 default is a
  margin in findings-per-document; on a 0–1 pass rate it would wave through
  every regression.
- **`check_stdlib_only.py` derives its local-module list from the tree**, so a
  new sibling module is fine. It used to be hardcoded, and every new module
  read as an R7 violation on the day it was added.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `RuntimeError: API-key auth reports dollar cost; refusing to run without --budget-usd` | Working as intended. Pass `--budget-usd N`, or `--allow-unmetered` if you mean it. |
| `RuntimeError: Pre-flight confirmation required for a non-interactive run; pass --yes` | Add `--yes`. Non-interactive runs must not spend on an unattended prompt. |
| `FileNotFoundError: no report.json in reports/<id>` | That run never wrote anything. Pick a directory that contains `report.json`. |
| `ModuleNotFoundError` running the tests | You are not in `skills/skill-tuner/scripts`. |
| `no manifest — this run predates provenance recording` from `verify` | Correct for any run made before U9. It cannot be verified; re-run it. |
| Empty `reports/<id>/` directories piling up | Fixed — resolving a run dir no longer creates it. Any you still see predate that fix; clear them with `find reports -maxdepth 1 -type d -empty -exec rmdir {} \;`. Use that form, not `find`'s delete action, which dcg-guarded shells refuse. |

## Test

```bash
cd skills/skill-tuner/scripts && python3 -m unittest discover tests   # 119 tests
python3 scripts/check_stdlib_only.py                                  # R7 guard
python3 scripts/validate_skillcreator_reader.py                       # vs skill-creator
```

The last one needs skill-creator installed and exits 0 with a note when it
isn't.
