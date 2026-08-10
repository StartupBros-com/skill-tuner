---
name: incident-triage
description: First-response triage for a production alert. Use when paged for an incident — acknowledge, classify severity, check the last deploy and golden dashboards, then roll back or escalate to the owner.
---

Runbook for the first response to a production page. Every step ends with a **narrate**: post what you just found or did to the incident channel the moment it happens. The channel is the incident's timeline, built live — not reconstructed afterward.

## 1. Acknowledge

`pd ack <incident-id>`

Narrate: "Acked `<id>`."

Done when PagerDuty shows you as the acknowledging responder.

## 2. Classify severity

Severity follows user impact, not error volume or gut feel:

| Severity | Impact |
|---|---|
| SEV1 | checkout is down |
| SEV2 | checkout is degraded — slow, partial, or intermittently erroring |
| SEV3 | cosmetic — no checkout impact |

Narrate the SEV and the one concrete symptom behind it.

Done when the posted SEV is backed by a specific user-facing symptom, not an impression.

## 3. Pull the last deploy

`deployctl last`

Narrate the deploy id, service, and timestamp.

Done when you have a deploy timestamp to compare against the alert's start time in step 5.

## 4. Check the golden dashboards

Links in runbooks/dashboards.md. Check all four and narrate one line per dashboard — including "nothing unusual" where that's true.

Done when all four have been checked and narrated.

## 5. Roll back or escalate

Compare the alert's start time to the deploy timestamp from step 3.

- **Within 30 minutes of the deploy** → roll back. Narrate the rollback command and its result.
- **Otherwise** → escalate to the service owner for the affected path in `.github/CODEOWNERS`. Narrate who you paged and why (deploy too old, or no recent deploy to implicate).

Done when the rollback has completed and been narrated, or the owner has been paged and the page confirmed.