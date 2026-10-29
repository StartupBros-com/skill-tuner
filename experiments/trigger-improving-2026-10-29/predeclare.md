# Predeclaration: the "improving" trigger round (2026-10-29, issue #74)

Written before the first paid call; the commit that adds this file is the
proof of order. The question, from the operator after #72 landed: should
`skills/skill-tuner/SKILL.md`'s description also fire on "optimize / improve
/ enhance this skill"?

## Candidate

One word. `candidates/improving.SKILL.md` (sha256 `f86017628b24`) differs from
main's `skills/skill-tuner/SKILL.md` (sha256 `62f3338b8914`) by the description
line only:

> Use when creating, editing, **improving**, or shortening skills, AGENTS.md, or CLAUDE.md.

Why one word and not improve/optimize/enhance: the doctrine's own *One trigger
per branch* rule says synonyms that rename a single branch pay three times and
route once, and edit, improve, enhance and optimize are one branch (make an
existing agent document better). "Optimize" is skill-creator's word (its
installed description claims "optimize an existing skill" verbatim) and is
tested here as the collision, not added.

## Instruments

1. **Routing parity** (PLAYBOOK rule 4). `configs/trigger-improving-routing-desc.json`:
   model `claude-sonnet-5-5`, 4 trials per case per condition, `neutral_ids: true`,
   battery `configs/trigger-improving-routing-battery.json` (13 cases: 3 obvious
   and 2 paraphrase should-fires phrased with improve, better, enhance, rework;
   6 near-misses, two of them skill-creator's stated jobs and four of them the
   trigger words on non-agent targets; 2 none-of-the-above). Distractors: the
   five from swapgate8 plus skill-creator's installed SKILL.md (plugin cache
   revision `f8c5e7a1dcb7`). Run id `trigger-improving-routing`. Cap $3.
2. **Live arm** (the skill-diet vet's harness: `env -i`, fresh `CLAUDE_CONFIG_DIR`,
   `claude-sonnet-5-5`, 10 turns, 600 s cap, no slash token). Arms `live-cur`
   (main's description) and `live-imp` (the candidate). Both arms carry
   skill-tuner **and** skill-creator's full skill tree as user skills in the
   config dir. Briefs `imp` ("Improve it") and `opt` ("Optimize it"), otherwise
   identical to each other. 3 reps per arm per brief, 12 sessions. Cap $1.50.
   Measurement: each run's `skill_calls` line.

## Answer key

- Battery: should-fire cases key to skill-tuner. Near-miss and none cases key to
  "not skill-tuner"; skill-creator is a correct answer for its two planted
  negatives ("optimize this skill's description so it triggers", "run evals and
  benchmark").
- Live `imp` brief: a run is a hit when it invokes skill-tuner through the Skill
  tool, whether or not it also invokes skill-creator.
- Live `opt` brief: a bare "optimize this skill" is keyed as correct for either
  skill. Both counts are reported; nothing lands or fails on this brief.

## Land conditions (both required)

1. Parity: candidate should-fire accuracy ≥ original's AND candidate near-miss
   rejection ≥ original's. If the candidate routes either planted negative to
   skill-tuner in more trials than the original does, the land is refused
   whatever the should-fire accuracy says.
2. Live: the candidate fires skill-tuner on at least 2 of 3 `imp` runs.

If either fails: the description stays as main has it, the refusal goes into
the summary and `FALSIFIERS.md`, and the round's configs and runs are banked
anyway.

## Not measured, and approximations

- No gate leg: the body bytes are unchanged, only the description moves.
- skill-creator runs as a user skill in the arm; the operator's harness serves
  it as a plugin skill (`skill-creator:skill-creator`). Same description text,
  different listing.
- `writing-for-agents` (the operator's always-on user copy of this doctrine)
  is in neither instrument: it has the same body as the target, and its
  description follows the plugin by its own UPSTREAM.md pin, a dotfiles
  decision outside this repo.
- Nothing here measures the operator's live sessions: the installed plugin
  cache serves 0.10.0 until the fold-in release ships these bytes.
- Spend estimate: routing 13 × 4 × 2 = 104 calls, about $0.62 (the pre-flight's
  $0.05/call default will print about $5.20; swapgate8 measured that default
  at roughly 8x); live 12 sessions, about $0.85 at swapgate8's $0.07 per
  session.

## Deviations

Appended below with UTC timestamps as they happen.
