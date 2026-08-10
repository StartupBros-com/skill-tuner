---
name: incident-triage
description: First-response playbook for a live PagerDuty alert on a production service — acknowledge, classify severity, pull the last deploy, check the four golden dashboards, then roll back or escalate. Use when a PagerDuty alert fires.
---

# Incident Triage

Work the five steps below in order. After each one, post what you did and what you found to the incident channel before starting the next — a channel updated after the fact is a reconstruction, not a record. This applies to all five steps; it isn't restated under each one.

## 1. Acknowledge

Run `pd ack <id>` for the alert. Confirm it exits 0 before continuing — an unacknowledged alert keeps paging.

## 2. Classify severity

Judge by user impact, not by what looks broken in logs:

- **SEV1** — checkout is down; no user can complete a purchase.
- **SEV2** — checkout is degraded; it works but is slow or erroring for some users.
- **SEV3** — cosmetic; no user-facing functional impact.

Post the severity with the one observation that justifies it (a failed checkout, an error-rate graph, a screenshot) — the level alone isn't enough.

## 3. Pull the last deploy

Run `deployctl last <service>` for the affected service. Record the deploy id and its timestamp — both are needed in step 5.

## 4. Check the four golden dashboards

Open the four dashboards linked in `runbooks/dashboards.md` and check each against its normal range for this kind of alert; call out any that's outside it. The links live there, not here, because they change more often than this file does.

## 5. Roll back or escalate

Compare the deploy timestamp from step 3 to the alert's start time.

- **Deploy landed within 30 minutes before the alert started** → roll back: `deployctl rollback <deploy-id>`. Confirm the rollback finishes and the golden dashboards recover before closing this step.
- **Otherwise** → escalate: find the owning team for the affected service's path in `.github/CODEOWNERS` and page that team directly.