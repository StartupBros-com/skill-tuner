# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3216 spent
- verify: 15 trial(s), $0.3298 spent

## Run manifest

- run: `dogfood3-automating-your-automations-local` (2026-08-10T06:15:10Z → 2026-08-10T06:21:26Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md` | `5584709576c0` | worktree @ 0492e1e9e5f2 (dirty) |

## Marginal-value probe verdict

**findings_confirmed: 2**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/dotfiles/claude/skills-local/automating-your-automations-local/SKILL.md
- probe calls: 1
- verify calls: 15 (3 skeptic(s) per finding)
- refuted: 3

### Confirmed findings

- **Single source of truth [craft] — keep each meaning in one authoritative place; duplication costs maintenance and tokens with no routing signal, and both instances here are in-file (not behind a pointer), so neither pays for the other via disclosure.**: This restates, almost verbatim, the fact already given a few paragraphs earlier in the source table: "**package.json** | `~/SITES/*/package.json` scripts | Your task runner (no Makefiles) — run-often = alias candidates". Both are always-loaded in the same section, so the identity claim ("task runner", "no Makefiles") is paid for twice.
  - quote: "**Your task runner is `package.json` scripts (many repos, no Makefiles).** Cross-reference what you *run* vs what's *defined*:"
  - proposed fix: Drop the restated identity clause from the prose header and keep only the new instruction: "**Cross-reference what you run vs what's defined:**"
- **Single source of truth [craft] — duplication of the same meaning in more than one in-file location costs tokens without adding routing signal.**: This repeats the fact already stated in the source table a few lines above — "**shell aliases** | `~/.bashrc` (~40 aliases) | Existing shortcuts; the gap = frequent-but-unaliased commands" — restating both the count (~40 aliases) and the gap concept.
  - quote: "You already keep ~40 aliases; find commands you type a lot but haven't shortcut:"
  - proposed fix: Trim to the actionable instruction only, e.g. "Find commands you type a lot but haven't shortcut:", relying on the table above for the alias count.

### Refuted findings

- **One trigger per branch [craft] — synonyms that rename a single branch are one branch written twice; collapse triggers that route to the same path.** — verifier: "Analyzing command patterns" and "finding automation opportunities" are the same branch stated twice — mining history for patterns *is* how the skill finds automation opportunities, and both phrasings route to the identical seven-step loop. This pays routing-description tokens twice for one trigger.
  - quote: "Use when analyzing command patterns or finding automation opportunities."
- **Relevance and sediment [craft] — every line must still bear on what the document does; without pruning discipline, stale/unrelated material sediments in as permanent context load.** — quote_not_found: This comment is always-loaded context but has no bearing on the skill's task (mining shell history for automation). `jsm install-all` and `FORK-SYNC.md` are never mentioned or explained anywhere else in the document, and `FORK-SYNC.md` is absent from the Reference Index table, so the pointer is orphaned — the agent has no way to act on it.
  - quote: "<!-- Local fork — see references/FORK-SYNC.md before running `jsm install-all` -->"
- **Negation [research] — steering by prohibition drags the forbidden behaviour into context and makes it more available; state the target behaviour positively instead, and pair any unavoidable prohibition with its positive target.** — verifier: The instruction leads with the ban ("skip") rather than stating the desired behaviour, and "data wins" is a justification, not a positive rephrasing of the action to take. This is exactly the failure mode the document should be guarding against: the loop already exists because the model wants to shortcut to proposing/building, so naming "skip" here makes the shortcut more salient rather than less.
  - quote: "**Never skip 1-3.** Intuition about what's repetitive is unreliable; data wins."
