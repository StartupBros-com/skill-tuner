# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3066 spent
- verify: 6 trial(s), $0.1931 spent

## Run manifest

- run: `dogfood-run-skill-4` (2026-08-08T08:00:50Z → 2026-08-08T08:04:57Z)
- claude CLI: `2.1.224` | skill-tuner: `0.1.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d3c66d4e8af3` | worktree @ 5d080cf37eb6 |
| target | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md` | `87e0c850131e` | worktree @ 5d080cf37eb6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 1**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/.claude/skills/run-skill-tuner/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Leading words [craft] — coining your own works only if you define it clearly: a made-up word recruits no priors, so you pay in definition tokens what a pretrained word gives free.**: "dcg-guarded" is an undefined coined term. Nothing else in the document explains what "dcg" stands for or what makes a shell "dcg-guarded," so the agent cannot tell when this restriction applies or verify the claim — it's asked to accept an opaque label as the sole reason to avoid `find`'s delete action.
  - quote: "Use that form, not `find`'s delete action, which dcg-guarded shells refuse."
  - proposed fix: Either spell out what dcg-guarded means inline (e.g., "which some sandboxed/permission-guarded shells refuse") or drop the jargon and state the concrete symptom (e.g., "which some shells block as a destructive-command guard").

### Refuted findings

- **Negation [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available, not less; state the target behaviour so the banned one is never named.** — verifier: This sentence names the exact banned actions ("click", "screenshot") rather than stating the positive target behavior (how to actually drive and verify the tool). Per the doctrine's research-backed rule, naming "click" and "screenshot" makes those actions more available to the agent, not less, instead of simply directing it to the CLI-appropriate method (checking exit codes/stdout).
  - quote: "There is nothing to click and no window to screenshot."
