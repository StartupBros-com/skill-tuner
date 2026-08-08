# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3101 spent
- verify: 6 trial(s), $0.1831 spent

## Run manifest

- run: `dogfood-run-skill-5` (2026-08-08T08:06:37Z → 2026-08-08T08:10:00Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `74a1a6fbdad9` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Negation [research] — steering by prohibition should be paired with its positive target; a rule that leads with the ban and never says what to do instead is the tell.**: Every other row in the Troubleshooting table pairs its diagnosis with an explicit positive action ("Pass --budget-usd N", "Add --yes", "Pick a directory that contains report.json", "re-run it", "clear them with find ..."). This row states only the negative condition ("You are not in X") and never gives the actual fix, leaving the agent to infer the `cd` step itself.
  - quote: "| `ModuleNotFoundError` running the tests | You are not in `skills/skill-tuner/scripts`. |"
  - proposed fix: Change the Fix cell to state the action directly, e.g. "Run `cd skills/skill-tuner/scripts` before invoking the tests."
- **Relevance and sediment [craft] — a line loses relevance by going stale as the behaviour it describes changes; without a pruning discipline this becomes sediment.**: This asserts the live, present-tense status of one specific banked run as a fact in a document meant to persist across time. Once that run is re-banked or the drifted input is fixed, this sentence (and the matching "-> DRIFTED (exit 1)" line in the Verified output block above) becomes false, misleading a future reader who sees a passing verify and assumes the doc or the tool is broken.
  - quote: "The banked `swapgate5-probe-doctrine-v2` currently *does* report DRIFTED, because a dotfiles input moved after the run."
  - proposed fix: State the mechanism generically instead of asserting a specific run's current status, e.g. "verify reports DRIFTED whenever an input recorded in a run's manifest (such as a dotfile) changes after the run was banked — this is expected, not a bug." Drop the named-run claim, or mark it explicitly as a point-in-time example that may no longer hold.
