# The context ledger

What the August 2026 campaign's 96 verified fixes did to context cost,
measured from the four dotfiles PRs that carried them (base vs merge
commit, byte-exact, $0). Published per the claims-discipline rule:
whichever way it lands.

## Always-loaded context (SKILL.md files)

The number that matters — SKILL.md text is charged to the context budget
every time its skill fires:

| batch | PR | SKILL.md files | net bytes |
|---|---|---|---|
| 1 | dotfiles#289 | 15 | −2,255 |
| 2 | dotfiles#296 | 12 | −98 |
| 3 | dotfiles#316 | 13 | −2,376 |
| 4 | dotfiles#321 | 6 | −1,360 |
| **total** | | | **−6,089 (~1.5k tokens)** |

Every batch reduced it. Against the corpus's 458KB of always-loaded skill
text (41 skills at measurement time, 2026-08-11) that is −1.3% — modest,
stated as such. The per-skill numbers are
lumpier: the batches deleted duplication and sediment from the specific
files that had it, not evenly.

## Total bytes tell a different (also true) story

Counting *all* skill-directory markdown, batch 1 is **+5,360 bytes** and
the campaign nets **+1,922**. The difference is demotion, not bloat:
batch 1 moved implementation patterns out of always-loaded SKILL.md text
into on-demand reference files (`references/*.md`), which cost nothing
until an agent actually reaches for them. An earlier draft of this
analysis used the total and concluded the campaign grew the corpus; the
always-loaded/on-demand split is the accounting that matches how context
is actually charged. Both numbers stay published so nobody has to trust
the framing.

## What certifies the "same behavior" half

A context reduction is only free if behavior held. The receipts:

- `configs/endtask-suite/` first run: all three invasively-tuned skills
  **not_worse** on 7 hard cases each (δ = 0.10 pass-rate).
- The curl easy-case A/B: exact tie.
- 16 description prunes landed at measured routing parity; 4 refused.
- Re-probes to the instrument's floor after each batch.

The accurate headline the campaign earns: **96 defects fixed and ~1.5k
tokens of always-loaded context removed, at certified behavioral parity —
with 8KB of reference material demoted to pay-on-use.** Not "obviously
better"; measurably not-worse for measurably less, which is the claim the
receipts support.
