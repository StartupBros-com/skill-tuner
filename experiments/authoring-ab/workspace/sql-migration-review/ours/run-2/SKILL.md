---
name: migration-review
description: Pass/fail gate for reviewing database migration PRs — checks destructive DROP/RENAME for a two-phase plan, locking column defaults on hot tables, non-concurrent indexes on big tables, down-migrations that mirror the up, and backfills embedded in the schema change. Use when reviewing a migration file or schema-change PR before merge.
---

This is a gate: read the migration diff, run all five checks below against it, and emit a PASS/FAIL verdict per check with a cited line for every violation. A check with no matching pattern in the diff is PASS by default — say so, don't skip it silently.

## The five checks

### 1. Destructive ops carry a two-phase plan
A `DROP COLUMN`, `DROP TABLE`, or `RENAME COLUMN`/`RENAME TABLE` is only safe once nothing still reads or writes the old name. FAIL any destructive statement unless the PR shows the deprecation already happened: a prior migration that stopped writes to the column/table, application code in the same PR that no longer references it, or a linked ticket confirming a phase-one migration already shipped. A destructive statement with no such evidence is a FAIL regardless of how trivial the column looks.

### 2. New columns on hot tables get a non-locking default
`ADD COLUMN ... DEFAULT <constant literal>` is metadata-only on Postgres 11+ and safe. Anything else — `now()`, `gen_random_uuid()`, a subquery, any volatile or STABLE function — forces a full-table rewrite under `ACCESS EXCLUSIVE` on every Postgres version, hot table or not. FAIL any `ADD COLUMN` on a hot table whose default isn't a constant literal. Treat a table as hot unless the PR or schema comments state it's low-traffic; when unsure, treat it as hot.

### 3. Every index on a big table is CONCURRENTLY
FAIL any `CREATE INDEX` or `CREATE UNIQUE INDEX` on a big table that omits `CONCURRENTLY`. Also FAIL a `CONCURRENTLY` index built inside a migration the tooling wraps in a transaction — Postgres rejects `CREATE INDEX CONCURRENTLY` inside a transaction block, so that statement needs its transaction wrapper disabled. Same default as check 2: unsure means treat the table as big.

### 4. The down-migration mirrors the up
For every statement in the up-migration, find its inverse in the down-migration, in reverse order, and confirm it actually restores the prior state — not just runs without erroring. A `down` that drops the column the `up` added is a mirror; a `down` that's empty, drops the wrong column, or can't reverse an operation at all (a backfilled value, a destructive `DROP` from check 1) is a FAIL. Cite the up/down line pair for each mismatch.

### 5. Backfills live outside the schema migration
Any `UPDATE`, `INSERT ... SELECT`, or other data-touching statement that isn't setting a fixed default belongs in a standalone, batched, throttled job — not the schema migration. FAIL any data-migration statement found inside the migration file itself, regardless of row count; cite the line.

## Output

One line per check: `<check name> — PASS|FAIL — <file:line or "no match"> — <one-sentence reason>`. Then an overall verdict: FAIL if any check FAILed, PASS only if all five PASSed. Don't summarize past that — the table is the review.