# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2063 spent
- verify: 6 trial(s), $0.1557 spent

## Run manifest

- run: `dogfood2-cass-rerank-local` (2026-08-08T10:49:18Z → 2026-08-08T10:52:23Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md` | `39f309dee303` | worktree @ ad275a5b37c6 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/cass-rerank-local/SKILL.md
- probe calls: 1
- verify calls: 6 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Relevance and sediment [craft]**: This paragraph is loaded body content every time the skill fires, yet its own last sentence admits the debate it describes no longer applies to current operation ("sidesteps that choice entirely"). It's stale rationale about a superseded model-selection decision, not a gotcha or unwritten convention the agent needs to act on — exactly the sediment the doctrine warns accumulates when removing feels riskier than adding.
  - quote: "Model-choice history: the original "granite-r2 is best" result came from an eval with leaked synthetic queries and single-positive labels. The 2026-07 rebuild (pi-evals #891) reversed it — granite-r2 came LAST and was the only reranker that hurt vs baseline. The gateway lane exposes `local-rerank` only, which sidesteps that choice entirely."
  - proposed fix: Remove the model-choice history paragraph from the skill body; move it to a changelog entry or commit message in the dotfiles repo where historical rationale belongs, and leave only the single current fact if it's load-bearing ("the gateway lane exposes local-rerank only").
- **Co-location [craft]**: The always-loaded description tells the agent to fall back to "plain cass" for broad scans, but the critical caveat that plain cass must be run with `--robot` (never bare, per the body's "NEVER run bare `cass`" warning and the table's `cass search "..." --robot`) lives only in the skill body. In precisely the branch this description triggers — a broad scan, where the agent is routed away from this skill — the agent has no guarantee it ever reads that body section, so applying the fallback correctly depends on having read a different section it may never reach.
  - quote: "fall back to plain cass for broad scans"
  - proposed fix: State the required flag in the description itself, e.g. "fall back to `cass search ... --robot` for broad scans (never bare `cass`)", so the safety-critical caveat travels with the instruction instead of depending on a section the fallback branch may skip.
