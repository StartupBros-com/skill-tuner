# The standing endtask suite

Behavioral regression suite for the most invasively tuned skills in the
canonical corpus. The probe grades documents and the routing battery grades
descriptions; this grades what agents actually *produce* under a skill — the
evidence tier the others cannot reach. It exists because a judged
`not_worse` still leaves the question "did the fleet's edits change
behavior?", and because the first behavioral A/B (curl, easy cases) hit a
ceiling: an exact tie proves safety but has no headroom to detect
regression. These cases are deliberately hard — a competent-but-sloppy
answer fails several assertions per case.

## Entries

Each `<skill>/` holds:

- `ancestor.md` — the frozen pre-campaign (or at-adoption) skill text, the
  baseline condition. curl-bash-installer: 2026-07-04 pre-campaign.
  ssh-local: 2026-07-06 pre-campaign. youtube-transcript: 2026-08-10
  at-adoption (the skill was adopted and tuned the same day).
- `config.json` — endtask config: `ancestor` (baseline) vs `current` (the
  live dotfiles path — deliberately a moving target; the manifest records
  its hash at run time).
- `grader.py` — deterministic, stdlib-only, doctrine-neutral. Every grader
  was adversarially verified before its first paid run: executed against
  synthetic good / subtly-broken / garbage outputs, bugs fixed, re-run.
  The verification pass caught real bias — one draft grader hardcoded a
  flag name that exists only in the current skill version, which would
  have silently favored `current` in the A/B.

## Running it

One entry:

```bash
python3 skills/skill-tuner/scripts/tune.py endtask \
  --config configs/endtask-suite/<skill>/config.json \
  --grader configs/endtask-suite/<skill>/grader.py \
  --delta 0.10 --run-id endtask-suite-<skill>-NNN \
  --yes --budget-usd 8
```

δ = 0.10 pass-rate points is the standing non-inferiority margin. ~28
calls per entry (7 cases × 2 conditions × 2 trials), ~$1–4 through the
guarded envelope.

**When to run:** after a fleet edits one of these skills, and at every
doctrine release that changes what fleets do. `current` reads the live
dotfiles file, so a re-run always tests the newest text against the same
frozen ancestor; verdicts across runs are comparable per entry as long as
the grader and cases don't change (the manifest hashes both).

**Reading a verdict:** `not_worse` or `better` = the campaign's edits are
behaviorally safe on that skill. `worse` with the CI clear of −δ = a real
behavioral regression; find the failing cases in the report's per-case
table and treat them like the hot-patch gate refusal — revert or fix the
skill, not the grader. Do not edit assertions after seeing a verdict
(`reports/compare_log.jsonl` flags repeat pairings).
