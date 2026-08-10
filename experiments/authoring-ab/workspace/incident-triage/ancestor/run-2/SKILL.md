---
name: incident-triage
description: Use when first-responding to a production alert or PagerDuty page — acknowledging, classifying severity, and deciding rollback vs escalation.
---

# Incident Triage

Narrate every action to the incident channel the moment you take it, not batched at the end — acknowledgment, severity, dashboard status, decision. A responder reading the channel should be able to follow the triage live, without asking you anything. Each step below ends with a narrate action; do it as part of the step, not afterward.

## 1. Acknowledge

Run `pd ack <id>`.

Narrate: post the acknowledgment to the incident channel.

Done when PagerDuty shows the alert as acknowledged.

## 2. Classify severity

- **SEV1** — checkout is down; no user can complete a purchase.
- **SEV2** — degraded; checkout completes, but slower, partially, or with errors on non-critical paths.
- **SEV3** — cosmetic; no functional impact on checkout.

Narrate: post the severity and the one-line reason behind it.

Done when a severity is assigned and posted.

## 3. Pull the last deploy

Run `deployctl last` for the affected service. Record the deploy id, timestamp, and author.

Narrate: post the deploy id, timestamp, and author.

Done when the deploy record is in the channel.

## 4. Check the four golden dashboards

Links are in `runbooks/dashboards.md`. Check all four.

Narrate: post each dashboard's status — normal or anomalous — as you check it.

Done when all four have a posted status.

## 5. Decide: rollback or escalate

Compare the alert's start time to the deploy timestamp from step 3.

- Alert started **within 30 minutes** of the deploy → rollback (step 6a).
- Otherwise → escalate (step 6b).

Narrate: post the decision and the time delta that drove it.

### 6a. Rollback

Run `deployctl rollback <id>` on the deploy from step 3.

Narrate: rollback triggered.

Recheck the four dashboards. Narrate: recovered, or still anomalous.

If still anomalous after rollback, go to step 6b — a bad rollback is still an incident.

### 6b. Escalate

Look up the owning team for the affected service in `.github/CODEOWNERS`.

Page the owner.

Narrate: escalated to `<owner>`, with the reason from step 5.

Done when the owner has acknowledged.