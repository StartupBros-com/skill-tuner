# skill-diet arm fixture (2026-10-29)

Behavioural fixture for the harness-vet of [nicobailon/skill-diet](https://github.com/nicobailon/skill-diet) at
`5f41df1220eb5759c413390206f1b9e6c63be754`. The vet note is `docs/vets/2026-10-29-skill-diet-harness-vet.md`;
the pins, items and decision rules were written to `predeclare.md` before any scored run.

## Layout

| path | what |
| --- | --- |
| `predeclare.md` | arms, model, limits, items, scoring and decision rules, frozen before the batch |
| `fixture/shipit.v1`, `fixture/shipit.v2` | fake `shipit` CLI (bash); v2 renames `status` to `info` (lines 4 and 14 differ) |
| `fixture/skill/SKILL.md` | the planted skill (3,040 bytes) with seven cut-defects and five keep-items |
| `fixture/briefs/t1..t4.txt` | the four briefs: diet (t1), add a lesson (t2), CLI rename (t3), unrelated bash task (t4) |
| `fixture/data/` | five files for t4; `make-fixture.sh` regenerates v2 and the data files |
| `arms/make-run.sh` | builds one isolated run root under `/tmp/ws-<hex>` with its own `CLAUDE_CONFIG_DIR` and XDG dirs, installs the arm's skill, runs the blinding word scan |
| `arms/run-one.sh` | runs `claude -p` under `env -i` with an allowlist, a stall watchdog and a wall cap; writes `events.jsonl` |
| `arms/extract.py` | turns `events.jsonl` into `init.json`, `tools.txt`, `reply.txt`, `status.txt`; exits 1 on a failed invocation |
| `arms/grade.py` | deterministic regex grader; the answer key lives here and in `predeclare.md` only |
| `arms/job.sh`, `arms/batch.sh` | one run end to end; the 60-run arm batch plus 27 routing and collision probes |
| `arms/aggregate.py` | cases, paired-json files, `tune.py compare` verdicts, `results/summary.md` |
| `results/summary.md` | primary results (regex grader) |
| `results/by-eye-corrected.md` | secondary table after the predeclared by-eye reading of K failures |
| `results/tokens.tsv` | o200k_base token count of every final skill file |
| `results/runs/<arm>-<task>-<rep>/` | per-run record: final `SKILL.md` or `biggest.sh`, `reply.txt`, `tools.txt`, `status.txt`, `grade.json`, `init-skills.json` |
| `results/runs.tsv`, `results/index.tsv`, `results/batch.log` | run ledger, blinding scan results, batch log |
| `results/compare/*.md` | the seven `tune.py compare --paired-json` reports |

Candidate, ancestor and contender files were installed into each run's scratch config directory only; none are
copied into this tree. The `events.jsonl` transcripts stayed under `/tmp` (they carry nothing the per-run record
does not, apart from raw tool inputs).

## Arms

| arm | installed into `$CLAUDE_CONFIG_DIR/skills/` | prompt |
| --- | --- | --- |
| bare | nothing | brief |
| diet | candidate repo minus `.git` as `skill-diet/` | `/skill-diet <brief>` |
| tuner | `skills/skill-tuner/{SKILL.md,FALSIFIERS.md}` from this repo at 91b4079 | `/skill-tuner <brief>` |
| wfa | mattpocock/skills `writing-for-agents` at 3216582 (SKILL.md, SKILL-MECHANICS.md, agents/openai.yaml) | `/writing-for-agents <brief>` |
| re0 | LilMGenius/paperthin `re0`, `debloat`, `ssotize` at 7d5dc62 | `/re0 <brief>` |

Model `claude-sonnet-5-5`, `--max-turns 40`, 900 s cap, tools Bash/Read/Glob/Grep/Write/Edit, `acceptEdits`,
`CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, three reps per arm and task. Probes (`probe-<arm>`, `collide`) drop the slash
token and cap turns at 10; they are logged, not scored.

## Deviations from predeclare.md

1. **K1 regex widened before any scored run.** The smoke run of the candidate arm (rep 0, excluded) wrote
   "deletes remote artifacts irreversibly" and the original regex (`irreversible`) missed it. `grade.py` K1 now
   accepts `irreversib|cannot be undone|can't be undone|can not be undone`. `predeclare.md` still carries the
   original wording; this file is the record of the change.
2. **Rep 0 rows are smoke runs** (one bare t4, one diet t1) and are excluded by `aggregate.py`.
3. **By-eye reading of K failures** (predeclared) found four regex misses out of six K failures; they are listed
   with the quoted lines in `results/by-eye-corrected.md`. D items were not read by eye, as predeclared, though
   one D1 and one D9 regex miss were noticed and are described in the vet note.
4. **`tokens_o200k` is null in `grade.json`.** `grade.py` runs under `python3 -I`, which hid the user-site
   `tiktoken`; `results/tokens.tsv` holds the counts computed afterwards with the same encoding.
5. **`aggregate.py` first ran `tune.py` under `-I`** and the compare calls failed (`import compare` needs the
   script directory on `sys.path`). The flag was dropped for the trusted repo script and the aggregation re-run;
   no scores changed.

## Reproduce

```bash
cd experiments/skill-diet-arms-2026-10-29
SCR=/path/to/scratch   # holds cand/, ancestor/, contenders/paperthin/ at the pinned revisions
bash arms/job.sh diet t1 1          # one run; prints the grade line
bash arms/batch.sh 6                # the whole batch, six at a time
python3 -I arms/aggregate.py . /path/to/scratch/compare
```

`tune.py compare` writes `reports/compare_log.jsonl` relative to its cwd, which is why `aggregate.py` runs it from
the scratch directory.
