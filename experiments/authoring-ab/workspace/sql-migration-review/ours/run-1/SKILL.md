---
name: migration-review
description: Produces a pass/fail gate for a database migration PR — destructive ops, hot-table column locking, index concurrency, down-migration reversal, and backfill placement, each finding cited to a line. Use when reviewing, auditing, or approving a schema migration diff.
---

Apply the five checks below to every migration file in the PR, statement by statement. The output is a pass/fail verdict per check plus one overall gate, and every finding — pass or fail — traces to a file:line in the diff.

## Steps

1. List every migration file changed in the PR, and every DDL/DML statement inside each, one line per statement.
2. Run each of the five checks against every statement. A check with no matching statement in the migration passes trivially — record N/A, no citation needed.
3. For any check that fails, quote the offending statement's file:line and the reason.
4. Emit the verdict block below. The gate is FAIL if any check fails; PASS only when all five are PASS or N/A.

## The five checks

### 1. Destructive ops need a two-phase plan
Trigger: `DROP TABLE`, `DROP COLUMN`, `ALTER TABLE ... RENAME`, or `RENAME COLUMN`.
Pass when the drop or rename lands in a later migration, after an earlier one that already stopped writing to the old name — with a deploy expected between the two. A migration that renames or drops the same object it's still being written to fails, with no exception for "nothing reads this column anymore" asserted but not shown.
Fail: cite the DROP/RENAME line and note that no prior migration in the PR deprecates the target first.

### 2. New columns on hot tables need non-locking defaults
Trigger: `ADD COLUMN` on a table you can identify as hot — flagged in the migration's own comments or PR description, or carrying an index that implies high-traffic access. If you cannot determine traffic, treat the table as hot.
Pass when the added column has no `DEFAULT`, the default is a constant on Postgres 11+ (metadata-only, no rewrite), or the default is populated afterward by a separate batched job per check 5 rather than inline in `ADD COLUMN`.
Fail: cite the `ADD COLUMN ... DEFAULT` line where the default is volatile (`now()`, a sequence, any function call), or where the target Postgres predates 11 and a non-null default is used — both rewrite the full table under a lock.

### 3. Every index on a big table must use CONCURRENTLY
Trigger: `CREATE INDEX` or `CREATE UNIQUE INDEX` on a table not created earlier in this same migration.
Pass when the statement includes `CONCURRENTLY`, and the migration tool's transaction wrapping doesn't put it inside a transaction block alongside other DDL — `CONCURRENTLY` cannot run inside a transaction, and most migration tools wrap the whole file in one by default.
Fail: cite the `CREATE INDEX` line missing `CONCURRENTLY`, or cite the config/line showing the migration runs in an implicit transaction that would make it error or get silently dropped.

### 4. Down-migrations must actually reverse the up
Trigger: any migration file with a down/rollback section.
Pass when every up statement has a down statement that fully inverts it — an added column is removed, a dropped column's exact prior type and constraints are restored, a rename is renamed back, a created index is dropped. Read both halves side by side.
Fail: cite the up statement with no matching inverse in the down, or the down statement whose effect only partially undoes its up counterpart — including a down section that is present but empty, a no-op, or a comment-only stub.

### 5. Backfills belong in a separate batched job
Trigger: any statement writing to existing rows — `UPDATE`, `INSERT ... SELECT`, or a default-population loop — whose row count isn't bounded by the migration itself.
Pass when the migration contains no such statement, and any backfill is instead referenced as a separate batched job: a script, worker task, or follow-up ticket linked in the PR.
Fail: cite the `UPDATE`/backfill line running inside the schema migration itself, regardless of current table size — an unbatched write inside a schema migration locks rows or bloats WAL even on a table that's small today.

## Verdict format

```
## Migration Review: <gate PASS|FAIL>

1. Destructive ops / two-phase plan: PASS|FAIL|N/A — <file:line or reason>
2. Hot-table column defaults: PASS|FAIL|N/A — <file:line or reason>
3. CONCURRENTLY on indexes: PASS|FAIL|N/A — <file:line or reason>
4. Down-migration reversal: PASS|FAIL|N/A — <file:line or reason>
5. Backfill separated from schema migration: PASS|FAIL|N/A — <file:line or reason>
```

A FAIL line with no file:line citation is itself a defect in the review — find the line before emitting it, don't assert the failure impressionistically.