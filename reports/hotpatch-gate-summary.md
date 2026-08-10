# Hot-patch gate: an ungated production doctrine edit, measured and reverted

A new rule appeared directly in the live `writing-for-agents` copy on
2026-08-10 — "Never summarize the workflow in the pointer" — added outside
the gate flow. Plausible, well-written, aimed at a real failure mode. This
is precisely the class of edit the project exists to gate, so it became the
first live run of the sequential gate under the system-prompt envelope,
against the fresh `rebank-sys-v3` baseline on the same 15 targets.

## Verdict: regression confirmed — reverted

25 confirmed vs v3's 34. Mean **−0.600/doc**, 95% CI **[−1.18, −0.02]** —
the interval excludes zero; fixed-n verdict *inconclusive with regression
confirmed* at δ = 1.0, which fails the land bar. Document record 2 won /
8 lost / 5 tied. The sequential rule never crossed (the effect sits near
the margin), so the full leg ran: the gate spends when the answer is
close, which is the honest direction. $7.02.

This is v3.1's lesson repeated at one-rule scale: a single sensible-looking
addition measurably dilutes the doctrine's yield. Two for two now — every
expert-endorsed doctrine addition this project has gated was refused by the
measurement.

Per the standing convention (the gate decides; refused reverts), the rule
comes out of the live and dotfiles copies and moves to the ledger as
refused-at-gate. It remains a candidate for a future rewrite — refusal is
about this wording's measured effect, not the intent behind it.
