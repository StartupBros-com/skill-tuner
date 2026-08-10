---
name: metrics-digest
description: Build the Monday metrics email from the analytics CLI's signups, activation, and churn numbers — pull last week and the prior week, flag any metric that moved more than 10%, and render the fixed template. Use when compiling the Monday metrics email.
---

## Pull the numbers

Run the analytics CLI for the reporting week and the week before it:

```
an4 query --metric signups,activation,churn --last 7d --json
```

For the prior week, check `an4 query --help` for the correct offset/date-range flag rather than guessing one — CLI flags drift and a wrong guess produces a silently wrong comparison. Run the equivalent query for the 7 days immediately before the reporting week.

Parse both JSON outputs before doing any comparison.

## Handle missing or zero-baseline metrics

The three metrics are signups, activation, churn. For each one, check both weeks' output before computing anything:

- **Metric absent from either week's JSON**: do not compute a change and do not drop the row. Write it as `<metric>: not available in analytics output` in its section.
- **Prior week value is 0 and current week value is nonzero**: percent change is undefined, not zero. Write the row as `<metric>: <current value> (up from 0)` instead of a percentage, and treat it as flagged.

## Compute change and flag movers

For every metric with a real value in both weeks:

```
pct_change = (current - prior) / prior * 100
```

A metric is flagged when `abs(pct_change) > 10`. This is the only threshold — do not round it or treat 10.0 as a pass.

## Render the email

Plain text only — no `#`, `*`, `-`, backticks, or other markdown syntax anywhere in the output.

```
Subject: Metrics week of <YYYY-MM-DD of the reporting week's start date>

Growth
signups: <value>, <+/-X%> vs prior week

Engagement
activation: <value>, <+/-X%> vs prior week
churn: <value>, <+/-X%> vs prior week

Flags
<one line per flagged metric, e.g. "signups moved +14% vs prior week">
<or, if none qualify: "No metrics moved more than 10% this week.">
```

Every metric row uses the missing-data or zero-baseline wording above in place of a percentage when those cases apply, in whichever section (Growth or Engagement) it normally belongs to.

## Done when

- Subject line reads exactly `Metrics week of <date>` with the real start date substituted.
- All three metrics — signups, activation, churn — appear exactly once each, in Growth or Engagement, either with a value and percent change or with the explicit missing/zero-baseline wording. None are silently dropped.
- Flags lists every metric with `abs(pct_change) > 10`, or the exact no-movers sentence if none qualify.
- The rendered output contains zero markdown characters — reread it once and confirm before sending.