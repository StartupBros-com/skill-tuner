# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.3827 spent
- verify: 12 trial(s), $0.3448 spent

## Run manifest

- run: `dogfood2-apple-design` (2026-08-08T10:01:18Z → 2026-08-08T10:05:54Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/apple-design/SKILL.md` | `ccd612736f52` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 0**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/apple-design/SKILL.md
- probe calls: 1
- verify calls: 12 (3 skeptic(s) per finding)
- refuted: 4

### Refuted findings

- **Sprawl / Progressive disclosure** — verifier: The description names at least five clearly distinct branches (motion/gesture mechanics, translucent materials, typography, reduced-motion, and the eight design-foundation principles), each handled by its own section (§1-11, §12, §15, §14, §16-17). Yet the body inlines all of them into one ~300-line monolithic file with no split or disclosed sub-document. A task that only needs §15's typography rules still pulls in spring-physics formulas, gesture-recognition code, haptics, and the design-principles essay, diluting attention exactly as the Sprawl rule predicts, and none of the branch-only material is pushed behind its own pointer as Splitting recommends.
  - quote: "Apple's approach to interface design and fluid, physical motion, translated for the web. Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency) behind Apple-style interfaces."
- **Demand** — verifier: This sentence closes an otherwise checkable list ("Audit debounces, artificial timers, transition waits, and the ~300ms tap delay") with an uncheckable catch-all — "isn't essential" requires judgment the agent can satisfy impressionistically, letting it declare the audit complete without a verifiable basis for what counts as inessential.
  - quote: "Anything on the input path that isn't essential is a regression."
- **Co-location** — verifier: This rule — that whether a gesture reverses or commits should be decided by the sign of velocity rather than position — appears only in the Quick Reference table. It is never stated, defined, or explained anywhere in the body, including §3 (Interruptibility) and §6 (Momentum projection), which are the natural homes for a reversal-decision rule. An agent applying this row correctly needs context the document never provides.
  - quote: "| Decide reverse vs. commit | Use velocity **sign**, not position | at release |"
- **Leading words** — verifier: "Response" is used as the section-1 leading word for interaction latency ("## 1. Response — kill latency") and then redefined in §4 as an unrelated spring-timing parameter. Reusing one token for two different concepts undermines the anchoring the leading-word mechanism relies on — later mentions of "response" (e.g. in the defaults table and Quick Reference, "response 0.3–0.4") can't be disambiguated by the term alone, and the two meanings are semantically close enough (both concern speed/timing) to actively invite conflation rather than merely coexist.
  - quote: "**Response** — how quickly the value reaches the target, in seconds."
