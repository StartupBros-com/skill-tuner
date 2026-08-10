---
name: migration-review
description: Reviewing a database migration PR — new or changed migration files, ALTER/CREATE/DROP statements, up and down migrations, data backfills. Produces a pass/fail verdict with cited lines.
---

# Migration review

Walk every DDL/DML statement in the diff against the five checks below, in order. Each check resolves to PASS, FAIL, or N/A — N/A means no statement in the diff triggers the check, and is not the same as PASS. A FAIL must cite the exact `file:line` of the offending statement. Overall verdict is FAIL if any check FAILs; otherwise PASS. Emit the verdict as one line per check plus an overall line, in this format:

```
[PASS|FAIL|N/A] <check name> — <file:line or reason>
...
OVERALL: [PASS|FAIL]
```

A table counts as **hot** for checks 2 and 3 if the PR description says so, if it already carries an index, or if its name suggests high-traffic production data (users, orders, sessions, events, and similar core-domain tables). When traffic can't be determined, treat the table as hot — the cost of an unnecessary CONCURRENTLY or a stricter default check is near zero; the cost of missing a lock on a real hot table is an outage.

## Checks

### 1. Destructive ops need a two-phase plan
DROP TABLE, DROP COLUMN, RENAME COLUMN, and RENAME TABLE may not land in the same PR as the last application reference to that column or table, unless the PR description or linked history shows a phase-one migration (stopped writes/reads, dual-write, or code deploy removing the reference) already merged and live. FAIL cites the DROP/RENAME line; note in the reason whether phase one is missing entirely or merely undocumented.

### 2. New columns on hot tables must not lock
ADD COLUMN on a hot table FAILs if it carries a volatile DEFAULT — one that calls a function (`now()`, `gen_random_uuid()`, `nextval`, etc.) rather than a literal constant — unless the migration is explicitly guarded to run only on Postgres 11+, where such an ADD COLUMN no longer rewrites the table. No guard present means assume the older, locking semantics and FAIL.

### 3. Every index on a big table needs CONCURRENTLY
CREATE INDEX / DROP INDEX on a hot table FAILs if it omits `CONCURRENTLY`. If `CONCURRENTLY` is present, also confirm the statement runs outside a transaction block (migration tool configured to skip wrapping it — e.g. `disable_ddl_transaction!`, an Alembic autocommit block) — `CONCURRENTLY` inside a transaction fails at apply time, so treat a missing skip-transaction config as FAIL too.

### 4. Down-migration must round-trip the up
Trace the up migration's net effect on the schema, then trace the down. The down FAILs unless it reverses every change the up made — not merely "runs without erroring." A down that's a no-op, drops the wrong column, or omits reversing one of several up changes is a FAIL. A missing down migration is a FAIL, not N/A.

### 5. Backfill is a separate batched job
Any statement that writes or rewrites existing rows — `UPDATE ... SET`, `INSERT ... SELECT` against an existing table — FAILs if it appears in the schema migration itself rather than a separate batched, rate-limited job (background job or script using cursor/LIMIT-OFFSET batching). A single-row or fixed-handful `INSERT`/`UPDATE` (seed data, a config row) is not a backfill and does not trigger this check.