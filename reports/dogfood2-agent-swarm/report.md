# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2658 spent
- verify: 18 trial(s), $0.3432 spent

## Run manifest

- run: `dogfood2-agent-swarm` (2026-08-08T10:21:18Z → 2026-08-08T10:27:29Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/agent-swarm/SKILL.md` | `aa5026605129` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 3**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/agent-swarm/SKILL.md
- probe calls: 1
- verify calls: 18 (3 skeptic(s) per finding)
- refuted: 3

### Confirmed findings

- **Cut identity the body already states [craft]**: This clause restates identity information — what the skill's mechanism is — that the body already covers in full under 'The core shift' and 'The primitive map' table. The pointer's job is to encode when to reach the document, not to re-explain what it contains; this spends permanent context load on every turn for zero additional routing signal.
  - quote: "using the native stack —
  parallel Claude Code subagents, the Workflow tool, Codex delegation, and worktree
  isolation — instead of a coordination protocol"
  - proposed fix: Trim the description to the trigger conditions only, e.g. 'Run a large or parallelizable task across many agents instead of a coordination protocol. Use when...' and let the body's core-shift section carry the native-stack explanation.
- **Relevance and sediment [craft]**: This is historical creation metadata (when it was written, what it replaced) that never bears on how the agent should execute the task. It rides along as sediment rather than earning its place in the loaded body.
  - quote: "<!-- New skill (not a jsm fork), 2026-07-04. Replaces the trashed jsm swarm mechanism
     (ntm + agent-mail + beads) with the operator's native primitives. Skills that need
     campaign-scale parallelism reference this instead of re-deriving swarm coordination. -->"
  - proposed fix: Delete the comment; if the migration history matters, keep it in the commit message or a CHANGELOG, not in the always-reachable skill body.
- **Single source of truth / Duplication [craft]**: This restates the same routing decision already given in full under 'Pick the lightest engine that fits' (Codex delegation bullet: implementation batches ≥5–7 units via `codex exec --cd`, bulk grunt via token-eater's grok launcher). Unlike the adjacent 'Mechanical' bullet in the same section, which cross-references back with '(see above)', this line duplicates the meaning outright, creating two places that must be kept in sync.
  - quote: "**Implementation batches** → Codex (`codex exec --cd`); **bulk grunt** → grok / token-eater."
  - proposed fix: Replace with a cross-reference, matching the mechanical bullet's pattern: 'Implementation batches / bulk grunt → see “Pick the lightest engine that fits” above.'

### Refuted findings

- **One trigger per branch [craft]** — verifier: These three phrases all route to the same branch — a large task decomposable into many independent units — and none of them sends the agent down a different path through the document than the others. This is the doctrine's own named failure: three phrases for one branch pay three times and route once.
  - quote: "whole-codebase campaigns (refactor / audit / migration / dead-code sweep), broad multi-file sweeps, N-independent-units work"
- **Co-location [craft]** — verifier: The coined term 'loop-until-dry' is used here, in the engine-selection bullet, before it is ever defined — its definition appears several sections later under 'The patterns worth knowing.' Applying this bullet correctly requires having already read a different, later section.
  - quote: "fan-out-then-verify, loop-until-dry discovery, or scaling depth to a token budget"
- **The subagent escape hatch has a cost ceiling [measured]** — verifier: This is data-driven fan-out (the number of rounds depends on what keeps turning up) with no stated hard cap on total rounds or total agents — only a dryness-based stopping condition. The doctrine requires every data-driven fan-out to be hard-capped, since a dryness condition alone can be satisfied slowly, letting the dispatch meant to buy legwork buy runaway spend instead.
  - quote: "keep spawning finders until K consecutive rounds surface nothing new — dedup against everything seen, not just what's kept"
