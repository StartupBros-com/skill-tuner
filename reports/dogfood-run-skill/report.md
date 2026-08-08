# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3038 spent
- verify: 6 trial(s), $0.1476 spent

## Run manifest

- run: `dogfood-run-skill` (2026-08-08T07:44:02Z → 2026-08-08T07:48:00Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `970bcba28e0d` | worktree @ 5d080cf37eb6 |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **One trigger per branch (Context pointers)**: "start or test the eval runner" duplicates two branches that already have their own dedicated trigger phrases: "start...the eval runner" routes to the same probe/spend-money section as "probe a document", and "test...the eval runner" routes to the same smoke.sh section as "check that the CLI still works after a change". Applying the doctrine's own test — does reaching the doc through this phrase take a different path than the phrase beside it? — no, both halves collapse onto branches already covered, paying context load three times for what routes to two places.
  - quote: "Use when asked to run skill-tuner, start or test the eval runner, probe a document, compare two runs, verify a banked run, or check that the CLI still works after a change."
  - proposed fix: Drop "start or test the eval runner" and let the existing "probe a document" and "check that the CLI still works after a change" cover those branches: "Use when asked to run skill-tuner, probe a document, compare two runs, verify a banked run, or check that the CLI still works after a change."
- **Single source of truth (Pruning and drift)**: The unit-test invocation `cd skills/skill-tuner/scripts && python3 -m unittest discover tests` is already given verbatim earlier under "Direct invocation" with its expected output (`# Ran 119 tests ... OK`). Repeating it in the "Test" section makes the same meaning live in two places; if the invocation ever changes (a flag added, a working-directory change), both copies must be updated in lockstep or they drift apart.
  - quote: "cd skills/skill-tuner/scripts && python3 -m unittest discover tests   # 119 tests
python3 scripts/check_stdlib_only.py                                  # R7 guard
python3 scripts/validate_skillcreator_reader.py                       # vs skill-creator"
  - proposed fix: Remove the unittest line from the "Test" section and keep only the two commands not stated elsewhere (check_stdlib_only.py, validate_skillcreator_reader.py), with a short pointer back to "Direct invocation" for the unit-test command.
