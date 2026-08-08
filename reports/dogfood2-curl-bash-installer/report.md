# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2697 spent
- verify: 15 trial(s), $0.4243 spent

## Run manifest

- run: `dogfood2-curl-bash-installer` (2026-08-08T10:11:48Z → 2026-08-08T10:16:57Z)
- claude CLI: `2.1.224` | skill-tuner: `0.2.0`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `d4a02a81c20b` | worktree @ eed4bf37a1f7 |
| target | `/home/will/.claude/skills/curl-bash-installer/SKILL.md` | `3d4b2a32605a` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 3**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/curl-bash-installer/SKILL.md
- probe calls: 1
- verify calls: 15 (3 skeptic(s) per finding)
- refuted: 2

### Confirmed findings

- **Cut identity the body already states [craft]**: The description spends its always-loaded routing budget on a statement of what the skill *is* (self-contained, real bash) rather than *when to reach* it. The body already establishes this identity in the header comment ('This version is self-contained: real snippets inline, no external line-refs') and in the 'Core snippets (real, self-contained)' heading, so the description adds zero routing signal for permanent per-turn cost.
  - quote: "Self-contained (real bash
  inline)."
  - proposed fix: Drop 'Self-contained (real bash inline)' from the description; keep identity claims in the body only.
- **Relevance and sediment [craft]**: This is always-loaded provenance narration about a retired predecessor skill — it never bears on how to write the installer and doesn't change based on the task. It's exactly the sediment the doctrine warns accumulates when removal feels riskier than addition; it also duplicates the PATTERNS.md pointer that the body states properly in its own section.
  - quote: "<!-- Distilled 2026-07-04 from the retired 30-file `installer-workmanship` skill, whose method was to
     study-and-emulate two upstream install.sh exemplars that don't exist on this machine. This version
     is self-contained: real snippets inline, no external line-refs. Locking + OS-detection re-anchored
     on the operator's own production exemplar (see Core principle below).
     Agent auto-config + optional service: references/PATTERNS.md -->"
  - proposed fix: Delete the comment, or move the provenance note to the commit message / changelog and keep only the PATTERNS.md pointer, stated once, in the body section that already names it.
- **Single source of truth [craft]**: The document already inlines complete, real locking and OS-detection code in the 'Core snippets' section (detect_platform, acquire_lock) and its own header comment boasts of being self-contained with 'no external line-refs' specifically to fix the predecessor skill's flaw of pointing at 'exemplars that don't exist on this machine.' This pointer reintroduces that exact flaw: it names a second, unreachable authority for the same behavior and contradicts the document's own self-containment claim.
  - quote: "Reference exemplar for real cross-platform locking/OS-detection:
> `~/SITES/pro-gate/lib/pro-gate-lib.sh`."
  - proposed fix: Remove the pointer to `~/SITES/pro-gate/lib/pro-gate-lib.sh` and let the inline detect_platform/acquire_lock snippets be the sole authority for locking and OS-detection.

### Refuted findings

- **One trigger per branch [craft]** — verifier: The lead clause and the 'Use when' clause name the same single branch (writing a curl|bash install.sh for a CLI) in two different phrasings. A run reaching the skill through 'production-grade curl|bash installer' takes the identical path as one reaching it through 'curl-pipe-bash install.sh one-liner' — no distinct branch is added, so per the doctrine's test these should collapse.
  - quote: "Write a production-grade `curl | bash` installer for a CLI tool. Use when writing a
  curl-pipe-bash install.sh one-liner for a CLI (Rust/TS/Go)."
- **Duplication / polarity restatement in anti-pattern lists [craft]** — quote_not_found: These anti-pattern bullets are the same meanings already given positively in the '14 non-negotiables' list (#7 Checksum, #4 musl-preferred platform detection, #8 soft-skip/hard-fail signature, #6 flock-first with mkdir fallback, #3 proxy on every call), just negated. The doctrine names exactly this pattern as duplication wearing polarity as a disguise, inflating the anti-pattern list's rank on the ladder for no new meaning.
  - quote: "- **Skipping checksum verification** — supply-chain risk; always verify SHA256.
- **`gnu` target on Linux** — not portable; use `musl` (static).
- **Hard-failing on optional features** (missing cosign/gum) — warn and continue.
- **`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback.
- **Ignoring proxy env** — `PROXY_ARGS` on every curl call."
