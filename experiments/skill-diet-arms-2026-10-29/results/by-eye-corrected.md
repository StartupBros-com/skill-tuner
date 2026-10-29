# By-eye corrected scores (secondary; the regex grader's scores in summary.md stay primary)

predeclare.md: K failures are read by eye. Four of the six K failures were regex misses, not arm failures (D items stay as the regex scored them; predeclare.md scopes by-eye reading to K items):

- diet-t1-1 K1 -> pass: line 22: `shipit purge <release-id> --yes` permanently deletes a release's artifacts. (regex wanted irreversib|cannot be undone)
- diet-t2-1 K5 -> pass: line 18: Chain every release behind the check, never run `shipit release` alone: `shipit check && shipit release --target staging` ... (regex wanted before|never skip|without on the same line)
- wfa-t2-2 K5 -> pass: line 18: Every release passes the gate first: a release to any target, prod included, starts with a green `shipit check`.
- wfa-t2-3 K5 -> pass: line 18: `shipit check` gates every `shipit release`, prod and staging alike ...

The one K failure that stands: diet-t1-2 K3 cut the `--notes-json` example shape and wrote `in the exact shape shown by shipit release --help`.

## Retained cases after correction (6; 23 dropped as identical)

| case | bare | diet | tuner | wfa | re0 |
| --- | --- | --- | --- | --- | --- |
| t1/D1 | 1.00 | 1.00 | 1.00 | 1.00 | 0.67 |
| t1/D5 | 0.00 | 1.00 | 0.00 | 1.00 | 0.00 |
| t1/D7 | 0.00 | 0.67 | 0.00 | 0.67 | 0.00 |
| t1/K3 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 |
| t2/D1 | 0.00 | 0.67 | 1.00 | 0.33 | 0.33 |
| t2/D9 | 0.00 | 1.00 | 0.00 | 0.00 | 0.67 |

| arm | pass rate (retained) | normalized gain vs bare |
| --- | --- | --- |
| bare | 0.33 | - |
| diet | 0.83 | +0.75 |
| tuner | 0.50 | +0.25 |
| wfa | 0.67 | +0.50 |
| re0 | 0.44 | +0.17 |

## Paired verdicts on corrected retained cases (tune.py compare --paired-json, delta 0.10)

| candidate vs baseline | verdict | mean diff | 95% CI | case record |
| --- | --- | --- | --- | --- |
| diet vs bare | not_worse | +0.500 | -0.07, +1.07 | 4 won, 1 lost, 1 tied |
| tuner vs bare | inconclusive | +0.167 | -0.26, +0.60 | 1 won, 0 lost, 5 tied |
| wfa vs bare | inconclusive | +0.333 | -0.11, +0.78 | 3 won, 0 lost, 3 tied |
| re0 vs bare | inconclusive | +0.111 | -0.25, +0.47 | 2 won, 1 lost, 3 tied |
| diet vs tuner | inconclusive | +0.333 | -0.33, +1.00 | 3 won, 2 lost, 1 tied |
| diet vs wfa | inconclusive | +0.167 | -0.32, +0.65 | 2 won, 1 lost, 3 tied |
| diet vs re0 | not_worse | +0.389 | -0.08, +0.85 | 5 won, 1 lost, 0 tied |
