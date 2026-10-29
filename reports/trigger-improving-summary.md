# The "improving" trigger round (#74): refused, and the reason is the competitor

Should `skills/skill-tuner/SKILL.md`'s description also fire on "improve /
optimize / enhance this skill"? One word, "improving", went to the two
instruments PLAYBOOK rule 4 names for a description change, with
skill-creator (the official plugin, enabled and model-invocable in the
operator's harness, whose description claims "modify and improve existing
skills" and "optimize an existing skill") installed beside skill-tuner in the
live arm for the first time. **The word does not land.** The battery would
have landed it: 52/52 against 49/52, the whole gain on the improve brief,
which main's description loses to skill-creator in 3 of 4 pick-one trials.
The live arm refused it: with skill-creator present, neither description
opens skill-tuner on that brief (0/3 and 0/3); without skill-creator, the
current description already opens it 2/3 and the candidate 3/3. The missing
word was never the mechanism in a live session. The competitor is.

Predeclared before the first paid call
(`experiments/trigger-improving-2026-10-29/predeclare.md`, commit `6b001fb`);
deviations are logged there with timestamps. Candidate
`candidates/improving.SKILL.md` (sha256 `f86017628b24`) differs from main's
SKILL.md (`62f3338b8914`) by the description line only:

> Use when creating, editing, **improving**, or shortening skills, AGENTS.md, or CLAUDE.md.

## Routing parity (`reports/trigger-improving-routing/`)

`configs/trigger-improving-routing-desc.json`: `neutral_ids: true`, 4 trials
per case per condition, 13 cases, 6 distractors (swapgate8's five plus
skill-creator's installed SKILL.md, sha `dcd4803e61e9`). 104 calls, $0.58.
Manifest clean (8 inputs, 0 dirty); `tune.py verify` reports no drift.

| condition | should-fire accuracy | near-miss rejection |
| --- | --- | --- |
| original (main's description) | 49/52 (94%) | 32/32 |
| candidate ("improving") | **52/52 (100%)** | 32/32 |

Discordant pairs: 3 gained, 0 lost, sign test p = 0.25. Verdict on this
instrument alone: land. The three gained trials are one case, the improve
brief itself (`skill-tuner__obvious__1`): under main's description the
battery sent it to skill-creator in 3 of 4 trials, under the candidate to
skill-tuner in 4 of 4. The two planted negatives, skill-creator's stated jobs
("optimize this skill's description so it triggers", "run evals and
benchmark"), went to skill-creator 4/4 under both descriptions: the added word
pulled neither. The README near-miss went to readme-writing 4/4 under both;
the SQL, CLI-error and test-suite near-misses and the CI none-case went to
none 4/4 under both; the release-announcement none-case went to de-slopify in
one trial under each.

## Live arm (the skill-diet vet's harness)

`env -i`, fresh `CLAUDE_CONFIG_DIR`, `claude-sonnet-5-5`, 10 turns, no slash
token, the shipit fixture. The brief is the vet's t1 brief with "Shorten it so
it costs less to load" replaced by "Improve it: make it a better skill for an
agent to work from" (`imp`) or "Optimize it: …" (`opt`). skill-creator's full
installed skill tree (plugin cache `f8c5e7a1dcb7`, SKILL.md sha
`dcd4803e61e9`) sits beside skill-tuner as a user skill in the arm's config
dir; both show in every run's skills list (`init.json`). A hit is a Skill tool
call naming the skill. 18 runs, 18 ok, $1.05.

| arm | skill-creator installed | brief | skill-tuner fired | skill-creator fired |
| --- | --- | --- | --- | --- |
| current description | yes | improve | 0/3 | 0/3 |
| candidate ("improving") | yes | improve | **0/3** | 0/3 |
| current description | yes | optimize | 0/3 | 0/3 |
| candidate ("improving") | yes | optimize | 1/3 | 0/3 |
| current description | **no** | improve | 2/3 | — |
| candidate ("improving") | **no** | improve | 3/3 | — |

The predeclared land condition was the candidate firing on at least 2 of 3
improve runs with the competitor present. It fired on none. The two control
arms (added after that result, logged 17:56Z) were not a land condition; they
answer the mechanism question. Three readings:

- **A competing description suppresses both skills, not just one.** With
  skill-creator visible, the model opened neither skill in 12 of 12 runs with
  the improve and optimize briefs; it ran `--help`, rewrote the fixture skill
  and finished in 5 to 7 turns. The one exception (candidate, optimize, rep 3)
  opened skill-tuner. skill-creator itself was never opened, with its own
  words in the brief.
- **Without the competitor the current description already routes.** 2/3 on
  "improve it" under the description main ships, 3/3 under the candidate. The
  one-run gap is inside the run-to-run spread the vet skill warns about and is
  not read as a gain. This is the same picture swapgate8's live probe gave
  for "shorten": the live harness opens the skill when the brief's verb is in
  the description's list, and sometimes when it is not.
- **The two instruments disagree, in the opposite direction from swapgate8.**
  The battery hands the model six short descriptions and asks it to pick one;
  on the one word it moved the improve brief from skill-creator (3/4) to
  skill-tuner (4/4). The live session decides whether to open a skill at all
  with twenty listed; it opened neither under either description. swapgate8
  saw the reverse: parity on the battery and a 1/3 to 3/3 gain live. Parity
  is necessary and not sufficient, and PLAYBOOK rule 4 now says so.

## Decision

**Refused.** `skills/skill-tuner/SKILL.md` keeps main's description. The
battery's land is recorded, not acted on: the predeclared rule required both
instruments, and the live arm is the one that matches how the skill is
reached. What the round establishes is narrower and more useful than the
word: in a harness
where skill-creator is enabled and model-invocable, "improve this skill"
briefs reach neither skill, and no description word on skill-tuner's side
changes that. The lever the operator holds is skill-creator's listing
(`/skill-tuner:portfolio` is the tool for that question; its first question
for each skill is whether the model should start it on its own), not another
trigger on this skill. "Optimize" stays skill-creator's word.

The `[craft]` *One trigger per branch* rule stands as written: the candidate
added one word for one branch and parity on the battery was never the hard
part.

## Spend

| run | calls | spent | cap |
| --- | --- | --- | --- |
| routing-parity (`trigger-improving-routing`) | 104 | $0.58 | $3 |
| live arms (12 sessions, skill-creator installed) | 12 | $0.70 | $1.50 |
| control arms (6 sessions, no skill-creator) | 6 | $0.36 | (same cap) |
| **round** | | **$1.63** | |

The routing pre-flight estimated $5.20 at the $0.05/call default and spent
$0.58, the same 9x overstatement swapgate8 logged. Doctrine investigation
cumulative: $53.50 through swapgate8 (`reports/swapgate8-summary.md`) + $1.63
= **$55.13**.

Runs are saved under `experiments/trigger-improving-2026-10-29/results/runs/`
(status, tools, reply, init, final fixture SKILL.md per run);
`results/index.tsv` records each run's doctrine sha, skill-creator presence
and blinding scan (no hits).

## Also in this round

`docs/release-notes/v0.10.1.md` drafts the fold-in release note. The release
train in this repository has been frozen since 2026-10-24 (hov-stack
restructure plan U20: workflows disabled, `v*` tag ruleset, release App
suspended), so no VERSION bump happens here; the bump is the author's step in
hov-stack after the squash import (U24). The plan's default migration note
says "nothing else changed"; skill-tuner's lists eleven unreleased pull
requests.
