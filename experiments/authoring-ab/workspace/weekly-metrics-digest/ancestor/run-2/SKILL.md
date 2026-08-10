---
name: metrics-digest
description: Building the Monday metrics email — pulling last week's signups/activation/churn from the analytics CLI, diffing against the prior week, and flagging swings over 10%. Use when asked to draft, generate, or send this week's metrics email/digest.
---

Builds the Monday metrics email from the analytics CLI. Three metrics only: `signups`, `activation`, `churn`.

## 1. Pull both weeks

Run the current week:

```
an4 query --metric signups,activation,churn --last 7d --json
```

Then pull the 7 days immediately before that window. If you don't already know the flag for an offset window, run `an4 query --help` rather than guessing one — don't invent a flag.

Done when you hold two JSON blobs, current and prior, each covering a distinct 7-day window with no gap or overlap between them.

## 2. Compute deltas

For each of the three metrics, `pct_change = (current - prior) / prior * 100`.

A metric can be **missing** from either blob's output. Missing is not zero — carry it as its own state, not a number. Done when every one of the three metrics has one of: a numeric `pct_change`, or a missing-in-current / missing-in-prior marker. No metric is silently dropped.

## 3. Flag

A metric flags if `abs(pct_change) > 10`, or if it's missing from either window (a missing metric is always a flag — there's no percentage to threshold).

## 4. Render

Subject: `Metrics week of <date>` — `<date>` is the Monday that starts the current week's window, `YYYY-MM-DD`.

Plain text, no markdown, three sections in this order:

```
Metrics week of <date>

Growth
  Signups: <value> (<+/-X%> vs prior week)

Engagement
  Activation: <value> (<+/-X%> vs prior week)
  Churn: <value> (<+/-X%> vs prior week)

Flags
  <one line per flagged metric, or "None" if nothing crossed 10%>
```

Section mapping is fixed: Growth holds signups; Engagement holds activation and churn.

Every metric gets a row in its section even when missing — write the row as:

```
  Signups: no data returned by an4 for this window
```

— never drop the line. A missing metric's Flags line reads `Signups: no data` rather than a percentage.

Done when the email has exactly three sections, all three metrics appear exactly once each across Growth/Engagement, and Flags lists every metric that crossed 10% or was missing — "None" only if that set is empty.