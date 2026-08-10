---
name: migration-review
description: Checklist for reviewing a database migration PR before merge — destructive ops, hot-table locking, index creation, down-migration correctness, backfills. Use when reviewing, approving, or auditing a migration/schema-change PR.
---

Produce a single verdict: **PASS** only if every applicable rule below passes; otherwise **FAIL**. For each rule, cite `file:line` for every violation found, or mark **N/A** if the rule doesn't apply to this diff (e.g., no indexes touched). Do not summarize in prose only — the review is the checklist, filled in.

## Process

1. Read every changed file in the migration diff before judging any single statement — a `DROP` in one file can be the second half of an `expand/contract` pair started in another.
2. List every schema-changing statement (`CREATE`, `ALTER`, `DROP`, `RENAME`) and every data-touching statement (`UPDATE`, `INSERT ... SELECT`, ORM backfill code), each tagged with the table it targets.
3. Determine which targeted tables are **hot** — actively written in production, not a table created earlier in the same migration. Use PR description, table name conventions, or ask if genuinely ambiguous; don't assume small/cold by default.
4. Apply each rule below to every statement it covers.
5. Emit the verdict.

## Rules

**Destructive ops need expand/contract.** Any `DROP COLUMN`, `DROP TABLE`, `RENAME COLUMN`, or `RENAME TABLE` is a contract step. FAIL unless the PR shows the matching expand step already shipped — application code stopped reading/writing the object in a prior, separate deploy — or the object is demonstrably never-used (no expand step needed). A drop/rename with no expand evidence and no separate follow-up plan is always a FAIL, regardless of how small the table looks.

**Hot-table column additions must not rewrite.** `ADD COLUMN ... DEFAULT` on a hot table:
- Volatile default (`now()`, `random()`, `nextval()`, a subquery) — always forces a full table rewrite under lock, on every Postgres version. FAIL.
- Constant default — rewrite-free (metadata-only) on Postgres 11+; still rewrites pre-11. Check the target Postgres version (migration tool config, CI image, explicit comment). FAIL if version is unconfirmed or <11.
- Either failure mode is fixed the same way: add the column nullable with no default, backfill in batches (see backfill rule), then add the default/`NOT NULL` in a follow-up step.

**Indexes on big tables must be CONCURRENTLY.** Any `CREATE INDEX` (or unique constraint backed by an index) on a big table without `CONCURRENTLY` takes a lock that blocks writes — FAIL. Also check the inverse failure: `CONCURRENTLY` cannot run inside a transaction, so if the migration tool wraps migrations in a transaction by default, confirm it's disabled for this file (e.g., `disable_ddl_transaction!`, `atomic = False`). `CONCURRENTLY` present but still transaction-wrapped is a FAIL — it will error, not just lock.

**Down-migrations must actually reverse the up.** For every up step, the down must undo it against the same object. FAIL if: the down is missing or a no-op stub, the down targets a different object than the up created, or the down claims to reverse an op that destroyed data (a `DROP COLUMN` can't be undone by re-adding an empty column) without an explicit comment acknowledging the data loss is accepted and irreversible.

**Backfills don't live in the schema migration.** Any statement that writes existing rows (`UPDATE`, `INSERT ... SELECT`, an ORM loop over all records) belongs in a separate, batched, out-of-band job — not the DDL migration. FAIL if such a statement appears in the migration file, or exists as a script but runs unbatched (no chunking/pagination) over a hot table.