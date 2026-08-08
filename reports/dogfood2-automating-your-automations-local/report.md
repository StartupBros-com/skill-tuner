# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3160 spent
- verify: 15 trial(s), $0.3607 spent

## Run manifest

- run: `dogfood2-automating-your-automations-local` (2026-08-08T09:57:16Z → 2026-08-08T10:01:18Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `d3c2e90ee9c1` | worktree @ a0487393147b (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- probe calls: 1
- verify calls: 15 (3 skeptic(s) per finding)
- refuted: 3

### Confirmed findings

- **Completion criteria [craft]**: The document states three different formulas for the same 'priority/score' concept: the principle table's 'Frequency × Pain = Priority', the Loop's unweighted three-factor product 'frequency × time_saved × error_rate', and Step 2's normalized four-factor weighted sum 'Score = freq_norm×0.4 + time_norm×0.3 + fail_norm×0.2 + simplicity_norm×0.1'. The checkable bound 'Only automate if Score ≥ 0.3' only makes sense against the normalized version, so an agent following the Loop's raw multiplicative formula cannot tell whether a given pattern complies with the 0.3 threshold.
  - quote: "frequency × time_saved × error_rate"
  - proposed fix: State the score formula once (the normalized weighted sum from Step 2) and have the Loop and principle table reference it rather than restating a different formula.
- **Demand [craft]**: 'for all pattern types' is an uncheckable qualifier inside an otherwise checkable Done-When list — 'pattern types' is never enumerated anywhere in the document, so the agent can satisfy this line impressionistically without a way to confirm 'all' were covered.
  - quote: "History mined (atuin or bash) for all pattern types"
  - proposed fix: Replace with the concrete, checkable set already used elsewhere in the doc, e.g. 'History mined for repeated commands, multi-step workflows, high-failure commands, and per-repo repetition.'

### Refuted findings

- **One trigger per branch [craft]** — verifier: The description lists two triggers — 'analyzing command patterns' and 'finding automation opportunities' — but the skill body runs one mandatory, undifferentiated loop (mine→cluster→score→propose→build→validate→install) regardless of which phrase brought the agent here. A run reached through either phrase takes the identical path, so these are one branch written twice rather than two distinct branches, and the second phrase pays context load with no added routing signal.
  - quote: "Use when
  analyzing command patterns or finding automation opportunities."
- **Negation [research]** — verifier: This rule leads with a ban ('Never skip') rather than naming the target behavior, and it is trivially phrasable positively, so it doesn't meet the doctrine's bar that a prohibition earns its place only when it cannot be phrased positively. It also doesn't pair the ban with an explicit positive instruction — 'data wins' is a justification, not a statement of what to do.
  - quote: "**Never skip 1-3.** Intuition about what's repetitive is unreliable; data wins."
- **Pruning and drift — environment as source of truth [craft]** — verifier: The alias count is a cheap, one-command lookup (the very grep shown two lines later) restated as a static fact, and it is duplicated in the source table (`~/.bashrc` (~40 aliases)). Per doctrine, one-command lookups should be left to the environment since a document restating them will go stale as the user's aliases change, and caching only earns its load when the lookup is expensive — this one isn't.
  - quote: "You already keep ~40 aliases; find commands you type a lot but haven't shortcut"
