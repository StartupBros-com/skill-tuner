# What a run costs, and what actually reduces it

Measured on `claude-sonnet-5` through `claude -p`, CLI 2.1.224, 2026-08-08.
Numbers are from real gate runs and controlled probes, not estimates.

## Where the money goes

A 16-document probe at `verify_trials: 3` (`swapgate4-probe-ablated`, 192
calls, **$8.07**):

| | calls | mean | total | share |
| --- | --- | --- | --- | --- |
| probe (doctrine + target inline) | 16 | $0.2755 | $4.41 | 55% |
| verify (target + one finding) | 176 | $0.0208 | $3.66 | 45% |

## Caching already pays for the skeptic panel

`verify_trials: 3` sends the *same* prompt three times, and the repeats hit
prompt cache:

| verify trial | mean cost |
| --- | --- |
| 1 (cold) | $0.03401 |
| 2 (identical prompt) | $0.01386 |
| 3 (identical prompt) | $0.01422 |

**59% cheaper after the first.** A three-skeptic panel costs about 1.8× a
single skeptic, not 3×. Raising `verify_trials` is far cheaper than its call
count suggests, and that is the one lever here with no methodological cost.

## What does *not* work: partial-prefix caching

Claude Code's cache breakpoint sits after the whole user message, so two
calls sharing a long prefix but differing at the end get no reuse. Measured
with a fixed ~10 KB prefix and a varying one-line suffix:

| call | cache_create | cache_read | cost |
| --- | --- | --- | --- |
| 1 | 11536 | 0 | $0.06216 |
| 2 (same prefix, new suffix) | 3173 | 8362 | $0.01447 |
| 3 (same prefix, new suffix) | 3174 | 8362 | $0.01449 |

The 8362 read tokens are Claude Code's own system prompt. Our content is
cache-*written* every call and never read. So the doctrine, constant across
all 16 probe calls, buys nothing where it currently sits.

## What would work: the doctrine as a system prompt

Moving the constant doctrine into `--append-system-prompt` makes it part of
the cached prefix. Same three calls, varying targets:

| shape | call 1 | calls 2–3 |
| --- | --- | --- |
| doctrine inline (today) | $0.01795 | $0.01795 |
| doctrine in `--append-system-prompt` | $0.07281 | **$0.00672** |

Break-even is about **6 calls**; past that the system-prompt shape wins, and
it read 11,595 cached tokens per call instead of 0.

## Why neither optimization is switched on

Both of these — and the Batch API's flat 50%, which needs a direct-API
adapter and drops Claude Code's system prompt entirely — **change the prompt
envelope**. The model reads a doctrine in a system prompt differently from
one in a user message. A run made under a new envelope is not comparable to a
baseline made under the old one, so adopting either invalidates every banked
baseline and costs a re-measure (~$7.50 a leg) to regain a valid comparison.

That is a fine price to pay once, at a deliberate boundary. It is not a fine
price to pay in the middle of a gate, where it would confound the exact
difference being measured.

**Rule: adopt envelope-changing optimizations at a re-baseline boundary,
never mid-experiment.** `compare` already refuses runs with different model
pins for this reason; an adapter-shape field belongs in the same check.

## What to do meanwhile

- Keep `verify_trials: 3`. Caching makes the panel nearly free and it is the
  difference between a verdict and a coin flip.
- Re-use banked baselines instead of re-measuring: `tune.py verify` tells you
  whether one is still valid, and one leg costs half of two.
- When a single input drifts, `tune.py compare --exclude <substring>` drops it
  from both sides rather than forcing a full re-baseline.
- Size the target set from `n_to_resolve`, not from habit. More documents than
  the question needs is the most common way to overspend here.
