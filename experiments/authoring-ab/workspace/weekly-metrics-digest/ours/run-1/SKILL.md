---
name: metrics-digest
description: Monday metrics email — pulls signups, activation, and churn from the analytics CLI, diffs against the prior week, flags moves over 10%, renders the fixed template. Use when asked for the weekly metrics email or metrics digest.
---

Builds the Monday metrics email: two data pulls, a diff, a flag pass, and a fixed plain-text render. Follow the steps in order — the template at the end depends on values computed in the ones before it.

## 1. Pull current and prior week

Current week:

```
an4 query --metric signups,activation,churn --last 7d --json
```

Prior week: same command shape, shifted back one more week. Run `an4 query --help` to find the exact date-range flag (`--since`/`--until`, `--offset`, or similar) rather than guessing one — it varies by CLI version and guessing risks silently querying the wrong window.

Done when you hold two JSON payloads, each covering a distinct 7-day window, prior immediately preceding current.

## 2. Diff

For each of signups, activation, churn present in *both* payloads:

```
change_pct = (current - prior) / prior * 100
```

## 3. Handle missing metrics

If a metric is absent from either week's JSON — not zero, actually absent — do not compute a change and do not drop the row. Write it into its template line as `no data returned by an4 for <metric>` in place of the value. Every row for signups, activation, and churn appears in the final email regardless of what the CLI returned.

## 4. Flag

Any metric with `|change_pct| > 10` goes in the Flags section, direction included (e.g. `churn +14% week-over-week`). Metrics that moved 10% or less, and metrics with missing data, do not appear in Flags.

## 5. Render

Fixed template, plain text only — sentences and `label: value` lines, no markdown syntax (no `#`, `*`, `-`, backticks). Section membership is fixed regardless of that week's numbers:

- **Growth**: signups, churn
- **Engagement**: activation
- **Flags**: metrics from step 4, or the line `None` if the list is empty

```
Subject: Metrics week of <Monday date of the current window, YYYY-MM-DD>

Growth
signups: <current> (prior week: <prior>, change: <+/-x%>)
churn: <current> (prior week: <prior>, change: <+/-x%>)

Engagement
activation: <current> (prior week: <prior>, change: <+/-x%>)

Flags
<metric>: <+/-x%> week-over-week
```

Rows with missing data replace the `(prior week: ..., change: ...)` portion with `no data returned by an4 for <metric>` and are still listed under their fixed section (Growth or Engagement) — never Flags, since a change percentage was never computed.