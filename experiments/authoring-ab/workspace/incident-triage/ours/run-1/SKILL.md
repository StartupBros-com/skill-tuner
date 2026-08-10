---
name: incident-triage
description: Triage a fired production alert — acknowledge, classify severity by user impact, pull the last deploy, check the four golden dashboards, then roll back or escalate. Use when a PagerDuty alert fires for a production service.
---

# Incident Triage

## Live-log

Every step below ends with a live-log: post the result to `#incident-<id>` the moment that step finishes, before starting the next one. A step is not done until its action *and* its live-log post both exist. The channel's log is the incident record — if a decision isn't in it, it didn't happen as far as anyone reading the channel later can tell.

## 1. Acknowledge

Run `pd ack <id>`.

Live-log: "Acknowledged `<id>`."

Done when the command exits 0 and the post is in the channel.

## 2. Classify severity

Classify by user impact on checkout, not by the internal severity of whatever broke:

- **SEV1** — checkout is down for any user.
- **SEV2** — checkout is degraded: works but slower, partial, or erroring for some users.
- **SEV3** — cosmetic, no functional impact on checkout.

Live-log the severity and one sentence describing the impact observed.

Done when the channel has a severity that matches exactly one of the three definitions above, with no hedge ("maybe SEV1/SEV2").

## 3. Pull the last deploy

Run `deployctl last` for the affected service.

Live-log the deploy SHA and its timestamp.

Done when you have the deploy timestamp in hand, whether or not it turns out to be implicated.

## 4. Check the four golden dashboards

Links: `runbooks/dashboards.md`.

Live-log one line per dashboard: nominal, or anomalous with what you saw.

Done when all four have a log line, not just three plus a skim of the fourth.

## 5. Roll back or escalate

Compare the alert's start time to the deploy timestamp from step 3.

- **Alert start ≤ 30 minutes after the deploy** — roll back that deploy via `deployctl`. Confirm the exact rollback invocation with `deployctl --help` if unsure. Live-log that rollback is running.
- **Alert start > 30 minutes after the deploy, or no deploy in the lookback window** — escalate to the service owner listed in `.github/CODEOWNERS` for the affected path. Live-log who was paged and when.

The 30-minute window is measured strictly: `alert_start − deploy_timestamp ≤ 30min`. A value on the line rounds to "within."

Done when either the rollback is confirmed running, or the paged owner has acknowledged the escalation in the channel.

## Exit condition

Triage is complete when `#incident-<id>` reads, in order with no gaps, as: ack → severity → last deploy → four dashboard lines → rollback-or-escalation decision. If a reader could not reconstruct the triage from the channel alone, it isn't done yet.