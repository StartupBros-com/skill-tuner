# Envelope re-baseline + replication test: v3 vs ancestor, round two

Two fresh legs under the doctrine-in-system-prompt envelope
(`--doctrine-system`, `adapter_shape: claude-p-doctrine-system-prompt`) on
the current 15-target corpus, per COSTS.md's rule that envelope changes
land at a re-baseline boundary. The ancestor doctrine is the committed
snapshot `doctrines/writing-for-agents-8b36d4f.md` (the dotfiles copy now
carries v3, so the frozen text had to enter the repo to stay probeable).
Pre-registered framing: this doubles as a replication test of swapgate6's
near-boundary **better**; a weaker result downgrades the README claim and
ships anyway.

## Replication verdict: not_worse, positive lean — better does not replicate

| | incumbent | v3 |
| --- | --- | --- |
| confirmed | 27 | 34 |

Mean **+0.467/doc**, 95% CI **[−0.31, +1.25]**, 9 won / 5 lost / 1 tied,
dz +0.33, bootstrap agreeing, sign test p=0.424. Direction holds; the zero
bound does not clear.

Two things changed at once relative to swapgate6, both disclosed: the
envelope, and the corpus — batches 1–2 fixed **51 verified defects in
these very targets**, disproportionately the single-source-of-truth class
that carried v3's swapgate6 margin (duplication findings were 16 of its
42). Fixing the corpus consumed the doctrine's favorite prey; the gap
compressing afterward is what you would predict, and the incumbent's own
count fell 29→27 while v3's fell 42→34. The strict-better claim remains
attached to its original banked measurement; the standing claim across
all measurements is **v3 ≥ ancestor everywhere measured** (defect-finding
twice, authoring once), strictly better once.

## Envelope savings: mostly did not materialize — kept opt-in

Projected from the COSTS.md microbenchmark: ~25–30% per leg. Observed:
v3 leg $7.81 vs swapgate6's $8.30 (~6%), incumbent $6.59 vs a ~$7.40
swapgate3-era leg (~11%) — and both deltas are confounded by the corpus
change (fewer findings → different verify volume). Suspected mechanism:
the prompt-cache TTL (~5 min) expires between probe calls, because each
target's verify batch takes minutes — the microbenchmark ran back-to-back
calls and real legs do not. `--doctrine-system` stays opt-in; the shape is
recorded either way and `compare` refuses cross-shape pairs.

## Costs

incumbent $6.59 + v3 $7.81 = **$14.40**. Both runs `verify` clean at
banking. These two runs are the baselines of record for same-shape gates.
