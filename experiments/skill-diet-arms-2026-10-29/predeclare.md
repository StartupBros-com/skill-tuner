# Predeclaration: skill-diet behavioural fixture (harness-vet phase 4)

Written before any arm ran. Frozen at the commit that adds this file; later edits
go in the README's "Deviations" section, never here.

## Job

An agent edits a skill that teaches a CLI, in three realistic ways, with one of
four pieces of guidance loaded (or none). The vet asks whether the candidate
(nicobailon/skill-diet @ 5f41df1) makes the agent do that job better than what the
harness already owns (skill-tuner doctrine v3, `skills/skill-tuner/SKILL.md` +
`FALSIFIERS.md` at the worktree head) and the best of what exists (the slated
contenders below). Candidate text is data; it is executed only inside these
sandboxes.

## Arms (5)

| arm | what the run's config dir holds | prompt |
| --- | --- | --- |
| bare | nothing | `<brief>` |
| diet | candidate repo minus `.git` as `skills/skill-diet/` (SKILL.md, references/, scripts/, README.md, …) | `/skill-diet <brief>` |
| tuner | `skills/skill-tuner/{SKILL.md,FALSIFIERS.md}` from this worktree | `/skill-tuner <brief>` |
| wfa | ancestor mattpocock/skills `skills/productivity/writing-for-agents/` @ 3216582: SKILL.md, SKILL-MECHANICS.md, agents/openai.yaml | `/writing-for-agents <brief>` |
| re0 | LilMGenius/paperthin @ 7d5dc62: `skills/depth/re0`, `skills/depth/debloat`, `skills/depth/ssotize` (debloat and ssotize installed because re0's siblings hand off to them; the pack's other 25 skills are not installed) | `/re0 <brief>` |

Slate rationale: discovery admitted 44 upstreams, all complements, no substitute.
The ancestor fills slot 1 by rule. Slot 2 goes to paperthin's re0 because it is the
only other skill-shaped rewrite doctrine admitted ("rewrites rather than appends",
"a pass that finds nothing changes nothing"), runnable on this runtime. Slot 3 is
left empty rather than padded: yknothing/skills-refiner is a five-skill audit
toolkit without a rewrite step, and every other admitted upstream is a CI linter,
drift checker or eval runner, none of which an agent loads while editing. The
sizing choice (a wider slate) is recorded as unresolved, not taken.

The slash token is the invocation in every non-bare arm so the comparison isolates
content; whether each skill fires on its own is measured by the routing probes
below and reported separately (an arm that never opened its skill is a routing
finding, not a quality finding). The tuner arm has no `tune` skill or runner
installed; the agent applies the doctrine by hand, which is the only shape
comparable to the other three text-only arms.

Model `claude-sonnet-5-5` in every arm, `--max-turns 40`, 900 s cap, tools
`Bash,Read,Glob,Grep,Write,Edit`, `--permission-mode acceptEdits`. Each run gets
its own `CLAUDE_CONFIG_DIR`, `XDG_CONFIG_HOME`, `XDG_CACHE_HOME` under a run root
`/tmp/ws-<hex>/`, starts from `env -i` plus an allowlist (HOME, USER, LOGNAME,
PATH with the fake CLI prepended, LANG, TERM, SHELL, XDG_RUNTIME_DIR,
MISE_CONFIG_DIR, ANTHROPIC_BASE_URL, ANTHROPIC_CUSTOM_HEADERS, ANTHROPIC_API_KEY
when set, CLAUDE_CODE_DISABLE_CLAUDE_MDS=1, CLAUDE_CODE_MAX_RETRIES,
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY), and no CLAUDE.md anywhere under the
run root. N = 3 reps per arm × task.

## Fixture

`fixture/shipit.v1` is a fake release CLI (bash; simulated, nothing leaves the
machine) with `check`, `release --target <staging|prod> [--notes-json] [--dry-run]`,
`rollback --target`, `status`, `purge <id> --yes`, and a help page per command.
Unknown flags exit 2 with `shipit: unknown flag`. `fixture/shipit.v2` is identical
except `status` is renamed `info` (`status` becomes an unknown command). The arm's
work dir holds `skills/shipit/SKILL.md` (the planted skill, `fixture/skill/`) and,
for T4, `data/` (five files of distinct sizes, `fixture/data/`).

Planted defects in `fixture/skill/SKILL.md` (D) and honest controls that must
survive (K). Each is a regex over the final `skills/shipit/SKILL.md`; the answer
key never enters an arm.

| id | planted text | pass condition |
| --- | --- | --- |
| D1 | check-before-release rule stated twice (Releasing step 1 and Rules bullet) | exactly one line contains `shipit check` together with `before`, `never skip`, or `without` |
| D2 | stale flag: `shipit release --env staging` (CLI uses `--target`) | `--env` absent |
| D3 | "## History" section (human-only narrative) | no `History` heading, no `forty minutes`, no `make deploy` |
| D4 | semver definition the model already knows | `MAJOR.MINOR.PATCH` and `incompatible API changes` absent |
| D5 | cached "## Options" help dump | not (`--no-color` and `--timeout <seconds>` both present) |
| D6 | dry-run concept in three places (Before you start, Checking, trailing line) | at most 2 lines match `dry[- ]?run` (case-insensitive) |
| D7 | 8-step inline rollback incl. `--retries 5` and "File the failed release id" | both strings absent |
| D9 | (T2 only) the new lesson appended as a story | none of `last week`, `shipped a broken`, `broken manifest` present |
| K1 | purge safety line | `purge` and `--yes` present, plus `irreversible` or `cannot be undone` or `can't be undone` |
| K2 | `check` exits 0 on a missing manifest with `no manifest` on stderr | `no manifest` present |
| K3 | `--notes-json` hard-shape example | `--notes-json` present and `"items"\s*:\s*\[\s*\{\s*"id"` matches |
| K4 | description triggers | frontmatter `description:` mentions releas(e|ing) and rollback or roll(ing)? back |
| K5 | check-before-release rule survives | at least one line as in D1 |

Task-specific items:

| id | task | pass condition |
| --- | --- | --- |
| T3-A | T3 | `shipit status` absent from the skill |
| T3-B | T3 | `shipit info` present |
| T3-C | T3 | events show at least one Bash tool call whose command contains `shipit` (the agent consulted the CLI rather than editing blind) |
| T4-A | T4 | `biggest.sh` exists in the work dir |
| T4-B | T4 | `bash biggest.sh` (run by the grader in the work dir, 20 s cap) prints `b.txt`, `d.dat`, `a.bin` as the first three file names in that order and the numbers 12000, 8000, 5000 appear in its output |

Items scored per task:

- T1 (diet; `fixture/briefs/t1.txt`, CLI v1): D1–D7, K1–K5 (12 items).
- T2 (add a lesson; `t2.txt`, v1): D1, D9, K1–K5 (7 items). D1 here is the
  fold-not-append test: the planted file already carries the rule twice.
- T3 (CLI renamed status→info; `t3.txt`, v2): T3-A, T3-B, T3-C, K1–K5 (8 items).
  Whether the arm also fixes `--env` (D2) is recorded, not scored: the brief did not
  ask for it.
- T4 (irrelevant task, displacement control; `t4.txt`, v1, skill still installed
  and slash-invoked): T4-A, T4-B (2 items). Misrouting is measured by the probes.

Recorded, not scored: final SKILL.md bytes (planted: 3,044 B), tokens via
`tiktoken o200k_base`, whether the arm ran `shipit --help`/`shipit release --help`
(evidence beside D2), Skill tool calls, tool-use counts, cost, turns, wall time.

## Scoring and the formal verdict

A case is one (task, item). Its score for an arm is the pass rate over that
arm's valid reps (0, 1/3, 2/3, 1). Cases whose score is identical in every arm
are dropped before comparison (they cannot separate arms). Each arm's remaining
cases go into a paired-json file; the formal verdict per pair comes from the
incumbent's own instrument, run from a scratch cwd (it writes
`reports/compare_log.jsonl` relative to cwd):

    python3 skills/skill-tuner/scripts/tune.py compare --paired-json \
      --baseline <baseline>.json --candidate <arm>.json --delta 0.10

Pairs: diet, tuner, wfa, re0 each vs bare; diet vs tuner (the gating pair); diet
vs wfa; diet vs re0. Also reported per arm: absolute pass rate, and normalized
gain over bare `(arm − bare) / (1 − bare)` on the retained cases.

Decision rules, pinned:

- Doctrine EXTRACT (a concept ported into `skills/skill-tuner/SKILL.md`, via a
  follow-up issue and `tune.py gate`, never a direct edit from this vet) needs
  either diet vs tuner = `better`, or a named item with diet ≥ 2/3 and tuner ≤ 1/3
  that maps to one candidate concept (for example D2 → the drift step of C6/C13).
  Items that both arms pass are no evidence for either.
- T2 ADOPT-alongside (installing skill-diet globally) needs diet vs tuner =
  `better` and diet vs wfa and vs re0 not `worse`, and a routing probe that does
  not show it taking the doctrine's trigger. Anything less is SKIP with a
  do-not-retry condition.
- A `not_worse` or `inconclusive` on the gating pair means the candidate did not
  beat what the harness owns on this fixture; the verdict then rests on the
  component-level reading, and the eval note says so.
- Displacement: an arm whose T4 pass rate is at least 1/3 below bare's is flagged.
- A bare pass rate of 1.0 on an item is a ceiling; the item is dropped by the
  identical-score rule if every arm also hits it, and reported as "models already
  do this" otherwise.

## Routing and collision probes (separate from the arms)

Same sandbox, model and tools, `--max-turns 10`, no slash token. Each probe
installs the skill as the pack ships it (model-invoked unless its frontmatter says
otherwise) and records whether a `Skill` tool call for it appears in the events.

- Routing: for each of skill-diet, skill-tuner, writing-for-agents, re0 — T1 brief
  (should fire) and T4 brief (should not), 3 reps each: 24 runs.
- Collision: skill-diet, skill-tuner and writing-for-agents installed together, T1
  brief, 3 reps: which fires, in what order.

## Failure handling

A run whose status line is not `ok` (no result event, `is_error`, stall after 600 s
without an assistant event, or exit by the 900 s cap with no result) is re-run
once under a fresh hex. A second failure is recorded as a missing rep. A case uses
the valid reps it has (n reported); if any arm has fewer than 2 valid reps on a
task, that task's cases are excluded for every arm. The runner exits non-zero on a
failed invocation (extract.py), and the batch accepts a run only from its own
status line.

## Blinding

Before each run, the prompt text, the run root path and the names two levels deep
under it are scanned for `eval|evals|test|tests|judge|rubric|score|compare|
benchmark|candidate|arena`; hits go into `results/index.tsv`. Expected: none from
harness-authored text. The candidate's own files (`scripts/eval.mjs`,
`references/eval.md`) and paperthin's text carry these words by their authors'
choice; those are not harness labels and are recorded as such.

## Known limits, stated before running

- One fixture, N = 3, one model: a smoke test with a spread, not a population
  estimate. A delta inside the rep-to-rep spread is noise.
- The grader is regex over the file. A rewrite that keeps a meaning in different
  words can fail a K item (false accusation) or pass a D item by accident; every
  K failure is read by eye and the reading is recorded beside the number.
- Second-order effect (does the slimmed skill make a later agent use `shipit`
  better) is out of scope.
- The tuner arm gets the doctrine without its runner; the candidate arm gets its
  scripts, which it may run on the fixture skill. That asymmetry is in the
  candidate's favour and is noted.
- The first advisor review of this vet was lost in an unrelated incident
  mid-session; the second review's sequencing (fixture before slate, no arm
  before discovery returned) is what this file follows.
