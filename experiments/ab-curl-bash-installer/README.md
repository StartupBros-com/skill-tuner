# End-task A/B: curl-bash-installer, pre-tune vs post-tune

The first end-task receipt in this project — every earlier verdict measured
document quality (defect probes) or routing; this one measures whether the
tuned skill changes what an agent actually *produces*. Question: did the
batch-1 edits to `curl-bash-installer` (description cut ~60%, anti-pattern
rows deduplicated, three restatements collapsed, draw_box/uninstall inlined,
the `uninstall_service` guard) change end-task output quality?

## Design

- **Conditions**: `old_skill` = the skill at dotfiles#289's base commit
  (`ad275a5b`), `new_skill` = current (post #289/#291). Both presented
  identically: SKILL.md + references/PATTERNS.md inline in one prompt.
- **Tasks**: 5 realistic install.sh requests (`cases.json`) — Rust/musl CLI,
  bun-compiled TS CLI, Go daemon with systemd/launchd service, explicitly
  service-free minimal install with an airgap path, corporate-proxy +
  Sigstore. The no-service case deliberately exercises the class of bug the
  tuning process introduced-then-caught (#291).
- **Envelope**: one `claude -p` single completion per run — `--max-turns 1`,
  all tools disallowed, model `claude-sonnet-5`. 2 trials per condition per
  case; 18 of 20 runs completed (2 old-condition runs lost to 20-minute
  timeouts; every case retained ≥1 old run).
- **Grading** (`grader.py`): fully deterministic, no LLM judge. 12 static
  assertions derived from the skill's own 14 non-negotiables (bash -n,
  shellcheck errors, pipefail/trap/umask, proxy wiring, sha256, lock,
  uninstall, summary box, cache-buster, no unguarded call to an undefined
  helper) + one sandboxed execution check (E1).

## Verdict

`tune.py compare --skill-creator` at δ = 0.05 pass_rate/case:

| metric | mean diff | 95% CI | record (W/L/T) | verdict |
| --- | --- | --- | --- | --- |
| pass_rate_static (12 assertions) | **+0.000** | [+0.00, +0.00] | 0/0/5 | **not_worse — exact tie** |
| pass_rate (13, incl. E1) | −0.008 | [−0.05, +0.03] | 1/2/2 | not_worse |

Per-case (full metric): rust-musl 0.923 vs 0.923 · ts-bun 1.000 vs 0.962 ·
go-daemon 1.000 vs 1.000 · no-service 0.923 vs 0.962 · proxy-sigstore 1.000
vs 0.962. Every non-zero diff traces to E1 (below), not to a static
assertion.

**Reading**: the tuned skill — 60% shorter description, redundancy removed —
produces installers indistinguishable from the original's on every property
the skill itself declares non-negotiable. The compliance-via-repetition
concern from the diff review did not materialize on these tasks. This is a
non-inferiority result, which is the claim the edits needed: they were made
for context-load and maintenance, and the question was whether they broke
behavior. They did not.

## E1: excluded, and why that is itself a finding

E1 ran each installer in a sandbox (fresh HOME, fictional repo, 45 s cap)
expecting a loud, atomic failure. Instead, installers from **both**
conditions obeyed the skill's own non-negotiable #9 — build-from-source
fallback — and began installing a real Rust toolchain (`rustup`, live
network) into the sandbox. That is the skill working as written, so E1
measures a collision between the harness and rule #9, not a difference
between conditions; it is reported but excluded from the headline metric.
Side-finding for batch 2: an unattended `curl | bash` installer
auto-installing a full compiler toolchain as a *fallback* deserves a
confirm-or-flag gate in the skill — in both versions.

## Limits

- n = 5 cases, 8–10 runs per condition: powered to detect gross regressions,
  not subtle ones. `n_to_resolve` machinery applies if a stronger claim is
  ever wanted.
- Near-ceiling static scores (12–13/13) mean limited discrimination: a
  harder suite (execution against a real fixture release, checksum-tamper
  and proxy-sim scenarios) is the upgrade path.
- Assertion-level quality only; no human judgment of style or ergonomics.
- One skill. The result licenses no claim about the other 13 tuned skills.

## Cost ledger (honest, includes the mistakes)

- 18 scored generations: **$12.51**
- Envelope discovery: first attempt ran `claude -p` agentically (868 s,
  $2.87, killed), a max-turns-only attempt died `error_max_turns` ($0.51),
  diagnostics ~$0.60, killed partials est. $2–4. **Experiment total ≈ $19.**
- Grading and both verdicts: $0.

Reproduce: `python3 runner.py` (resumable; skips existing runs), then
`python3 grader.py`, then the two `tune.py compare` lines above.
