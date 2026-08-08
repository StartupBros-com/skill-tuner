# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3274 spent
- verify: 15 trial(s), $0.3449 spent

## Run manifest

- run: `dogfood2-cli-agent-ergonomics` (2026-08-08T10:34:30Z → 2026-08-08T10:40:10Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/cli-agent-ergonomics/SKILL.md` | `6c65c9665c35` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 4**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/cli-agent-ergonomics/SKILL.md
- probe calls: 1
- verify calls: 15 (3 skeptic(s) per finding)
- refuted: 1

### Confirmed findings

- **Demand [craft] — watch for criteria that mix checkable and uncheckable terms**: The numeric bounds (≥5, ≥3) are checkable, but "substantive" is a judgment call with no definition. One stray uncheckable qualifier inside an otherwise precise gate lets the agent satisfy it impressionistically, exactly the failure mode the doctrine warns against.
  - quote: "ship ≥5 substantive changes across ≥3 dimensions before calling it done"
  - proposed fix: Replace "substantive" with a checkable proxy, e.g. "ship ≥5 changes that each close a Recurring-fixes checklist item, across ≥3 of the 11 dimensions."
- **Duplication / Single source of truth [craft]**: This restates a meaning the document already gives twice: the shared axiom "stdout is data / stderr is diagnostics" and the 🚫 axiom "Every failure → stderr + non-zero exit." A third restatement adds maintenance and token cost without new signal.
  - quote: "stderr only"
  - proposed fix: Drop "stderr only" from the Error anti-patterns list; the earlier axioms already establish it.
- **Duplication [craft] — "an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice"**: This is the exact pattern the doctrine names: the 🩹 Errors teach axiom already states positively that "'See --help' alone is failure" and requires the exact command. The anti-pattern list repeats the same rule in negated form.
  - quote: "never bare "see --help" without naming the flag"
  - proposed fix: Remove this line from Error anti-patterns and let the 🩹 axiom stand as the single authoritative statement of the rule.
- **Duplication / Single source of truth [craft]**: The same claim — that stdout/stderr contamination via leaking log lines is the most common bug — is restated almost verbatim later as "the single most-caught bug: verbose/log lines leaking into stdout under `--verbose`, breaking `| jq`" in Recurring fixes item 7. One meaning is stated in two places.
  - quote: "Fixes the #1 recurring bug: ANSI/log lines leaking into piped stdout."
  - proposed fix: State the "#1 bug" claim once (in Recurring fixes item 7) and have the Output-Contract Quartet entry simply cross-reference it rather than restate it.

### Refuted findings

- **Negation [research] — a prohibition must stand paired with its positive target** — verifier: This leads with a ban and gives a reason but never states the positive target, contrary to the doctrine's requirement that even a justified prohibition be paired with what to do instead so attention lands on the desired behavior.
  - quote: "no ANSI/emoji in errors (breaks non-TTY `grep`)"
