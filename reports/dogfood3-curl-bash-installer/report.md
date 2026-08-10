# skill-tuner eval report

Conditions compared: **probe** vs **verify**.

- probe: 1 trial(s), $0.2721 spent
- verify: 9 trial(s), $0.3694 spent

## Run manifest

- run: `dogfood3-curl-bash-installer` (2026-08-10T06:56:30Z → 2026-08-10T07:01:33Z)
- claude CLI: `2.1.224` | skill-tuner: `0.3.1`
- model pin: `claude-sonnet-5` → answered by: `claude-sonnet-5`

| Role | Input | sha256 | Source |
| --- | --- | --- | --- |
| doctrine | `/home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md` | `6b452dafbc18` | worktree @ 40482c9ba52a (dirty) |
| target | `/home/will/.claude/skills/curl-bash-installer/SKILL.md` | `5f608eab8b76` | worktree |

## Marginal-value probe verdict

**findings_confirmed: 3**

- doctrine: /home/will/SITES/skill-tuner/.claude/worktrees/outclass-campaign/skills/skill-tuner/SKILL.md
- target: /home/will/.claude/skills/curl-bash-installer/SKILL.md
- probe calls: 1
- verify calls: 9 (3 skeptic(s) per finding)
- refuted: 0

### Confirmed findings

- **Context pointers — 'a branch being a distinct case the document handles'**: The pointer advertises three language branches (Rust/TS/Go), but the body only implements the Rust branch: non-negotiable #4 says platform detection maps 'OS+arch → Rust target triple' and non-negotiable #9's build-from-source fallback is 'rustup (if needed) → git clone --depth 1 → cargo build --release'. There is no Go target-triple/GOOS-GOARCH handling and no go-build fallback, so an agent routed here for a Go or TS CLI gets content that silently doesn't cover its case.
  - quote: "Use when writing a curl-pipe-bash install.sh one-liner for a CLI (Rust/TS/Go)."
  - proposed fix: Either narrow the description to 'CLI (Rust)' and split TS/Go into their own skill/section, or add the missing TS/Go platform-detection and build-from-source branches so the claimed scope matches the body.
- **Completion criteria — 'Two bounds that contradict... are a completion defect in the same family'**: Non-negotiable #7 states checksum verification should 'skip only on explicit --no-verify', but the implementation also silently skips (returning success) whenever neither sha256sum nor shasum is present, with no --no-verify flag involved. An agent following the rule text and one following the code snippet reach different behavior for the same case.
  - quote: "else warn "no SHA256 tool; skipping checksum"; return 0; fi"
  - proposed fix: Make the code match the stated bound: if no SHA256 tool is found and --no-verify was not passed, hard-fail with an actionable error instead of skipping, or change the non-negotiable to 'skip on --no-verify or absence of a hashing tool' so the two agree.
- **Pruning and drift — Duplication: 'an anti-pattern list that restates, negated, rules the document already gives positively is the same meaning written twice — audit such lists against the rules they mirror'**: Most of these bullets are the negated restatement of rules already given positively elsewhere: checksum vs non-negotiable #7, musl vs non-negotiable #4 (also restated verbatim in the platform-detection snippet's own caption), hard-failing on optional features vs non-negotiable #8's soft-skip/hard-fail asymmetry, flock-only vs non-negotiable #6, ignoring proxy vs non-negotiable #3, and settings/JSON backup vs the Agent auto-config section's 'timestamped backup → jq-or-Python3 merge'. Each is the same meaning written twice, inflating its rank on the ladder and adding maintenance/token cost without new routing signal.
  - quote: "- **Skipping checksum verification** — supply-chain risk; always verify SHA256.
- **`gnu` target on Linux** — not portable; use `musl` (static).
- **Editing settings/JSON without a backup**, or with `sed`/`awk` — `cp file file.bak.$(date +%s)` first, merge with `jq`/Python3.
- **Assuming `~/.local/bin` is on PATH** — check `:$PATH:`, offer to fix, don't assume.
- **Hard-failing on optional features** (missing cosign/gum) — warn and continue.
- **`flock` as your only lock** — absent on macOS; flock-first + mkdir-fallback.
- **Raw unstyled output** — route through `info/ok/warn/err`; honor `NO_COLOR`/non-TTY so piped/CI output has no ANSI.
- **`<tool> --version` with no timeout** — wrap in `timeout 1` (some CLIs hang).
- **Ignoring proxy env** — `PROXY_ARGS` on every curl call."
  - proposed fix: Drop the bullets that only negate an already-stated non-negotiable (checksum, musl, hard-fail-on-optional, flock-only, ignoring-proxy, JSON-backup) and keep only anti-patterns with no positive counterpart elsewhere (e.g. the --version timeout and PATH-assumption entries).
