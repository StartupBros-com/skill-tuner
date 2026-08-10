---
name: metrics-digest
description: Builds the Monday metrics email from the analytics CLI — pulls signups/activation/churn, compares to the prior week, flags moves over 10%. Use when asked to build, generate, or send the metrics digest or Monday metrics email.
---

Produces the fixed-format Monday email from `an4`. Follow the four steps in order; each one's output feeds the next.

## 1. Pull both weeks

Run:

```
an4 query --metric signups,activation,churn --last 7d --json
```

Then run the same query shifted back one week (via `an4`'s date-range flags) to get the prior-week baseline. Done when you hold two JSON payloads — current and prior — each nominally covering signups, activation, and churn.

## 2. Reconcile against the three metrics

For each of signups, activation, churn, look it up in both payloads:

- **Present in both** — compute `pct_change = (current - prior) / prior`. Flag it if `|pct_change| > 10%`.
- **Missing from either payload** — do not drop the row and do not compute a delta for it. Carry it into rendering as an explicit gap (see step 4). It cannot be flagged — there is nothing to compare.

Done when every one of the three metrics is classified as computed-and-flagged, computed-and-not-flagged, or missing.

## 3. Assign sections

Fixed mapping, not inferred from the data:

- **Growth** — signups
- **Engagement** — activation, churn
- **Flags** — every metric flagged in step 2, restated with prior value, current value, and signed percent change

## 4. Render the template

Plain text, no markdown, exactly these sections, in this order:

```
Subject: Metrics week of <date>

Growth
signups: <value> (<+/-pct>% vs prior week)

Engagement
activation: <value> (<+/-pct>% vs prior week)
churn: <value> (<+/-pct>% vs prior week)

Flags
<metric> moved <+/-pct>%: <prior value> -> <current value>
```

For a missing metric, write its line as `<metric>: no data returned by CLI` in its assigned Growth/Engagement section — never omit the row.

If no metric was flagged, the Flags section reads exactly `None over ±10%`.

`<date>` is the first day of the current 7-day window, formatted `YYYY-MM-DD`.