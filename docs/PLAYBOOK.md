# The campaign playbook

How to run a full measured skill-improvement campaign with this tool —
distilled from the August 2026 campaign that fixed 96 verified defects
across four batches (covering every skill in the operator's canonical
corpus), gated three doctrine candidates (shipping one, refusing two), and
produced every receipt in `reports/`. Each rule below was paid for; the
receipt is cited where it was.

## The loop

1. **Probe or gate, never guess.** A fresh corpus gets `probe`
   (full-leg, banks a baseline); a change against a banked baseline gets
   `gate` (sequential — stops early when the answer is clear, ~49% cheaper
   on decisive runs, full price on close ones; `swapgate6` replay).
2. **Fix from findings, not from taste.** Probe findings arrive
   3-skeptic-verified with quotes and proposed fixes — a fixer fleet can
   apply them mechanically. Two disciplines: fix the defect not the
   sentence, and check environment claims on disk first (the panel
   verifies text, not filesystems — it confirmed a false path claim
   twice before this rule existed).
3. **Land canonical-first — and never point a fixer fleet at live paths.**
   Edit where git owns the truth (dotfiles/repo) and let syncs converge
   outward. Concretely: copy targets into sync-safe scratch, fleet edits the
   scratch copies, land via PR, then converge live from merged canonical.
   This rule existed in its weaker "edit canonical first" form after batch 2
   and the batch-4 fleet still lost 5 of 6 edits — it targeted live
   `~/.claude/skills/` paths and a background sync reverted them mid-run.
   The race only closes when fleet prompts never contain a live path.
4. **Descriptions only land at routing parity.** Battery per
   `routing-parity`; candidates that keep every concrete trigger noun and
   cut only identity clauses pass (batch-3 battery: 6/6 land); candidates
   that drop trigger vocabulary fail (batch-2: 4/10 refused). A refuse at
   near-identical aggregate accuracy now carries the discordant-pair
   annotation — read it before re-rolling.
5. **Re-probe to the instrument's floor, then stop.** The probe finds ~2
   genuine defects per pass on almost any document — that is its value on
   fresh corpora and its stopping problem on tuned ones. Stop on a clean
   pass or on findings disjoint from every earlier pass; report residuals
   (one loop ran 8 passes learning this). A doc that returns exactly
   `max_findings` findings hit the cap, not the floor — treat it as "more
   remains" and re-probe it (the cross-judge recall pilot found 10
   endorsed defects past one at-cap doc's reported 5).
6. **Behavioral doubt gets an `endtask` A/B.** Same briefs under both skill
   versions, deterministic grader, paired verdict. The
   compliance-via-repetition worry about deduplication was tested this
   way and did not materialize (curl-bash A/B: exact tie).
7. **Doctrine changes go through the gate. All of them.** The campaign is
   two-for-two: every expert-endorsed doctrine addition ever gated —
   v3.1's four review-recommended sentences, and a live hot-patched rule —
   was refused with a confirmed regression. Expert consensus endorsed
   every one of those sentences; only the measurement dissented. There are
   no exceptions for "obviously good" edits, because both of those were.

## Costs and envelopes (measured)

- Full probe leg, 15 docs, 3 skeptics: **~$7–8.50**. Sequential gate:
  same worst case, ~half on decisive runs.
- `--doctrine-system` saves ~6–11% per leg (not the microbenchmark's
  25–30% — cache TTL expires between probe calls). Opt-in;
  `adapter_shape` keeps cross-envelope runs from ever being compared.
- Single-target probe: ~$0.30–0.70. Routing battery: ~$0.05/call, ~$2–5.
  Endtask generation through `call_adapter`: ~$0.04–0.15/call — an ad-hoc
  `claude -p` without the guarded envelope runs agentically at ~10x.
- `compare`, `verify`, and replay tooling: always $0.

## Claims discipline

- One document's before/after counts license nothing (the founding
  LOST/WON/WORSE receipt). Paired across ≥3 documents with a stated margin
  licenses one of four verdicts; report the robustness line with it.
- A near-boundary win is quoted as near-boundary (v3's +0.03 lower bound);
  replications are run when the corpus or envelope moves and published
  whichever way they land (`rebank-sys-summary.md`: better → not_worse
  with the mechanism explained).
- Aggregate ratios hide distributions — lead with the paired per-case
  interval (`docs/case-studies/ponytail.md`: "54%" was a totals artifact
  over a 0–94% spread; the defensible claim was 35% [15, 56]).
- Yields are comparable only within one doctrine hash, one adapter shape,
  one model pin, one corpus state. The tooling now enforces or prints all
  four; believe it over memory.
