---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory.

## Commands

- `shipit check`: validate the manifest. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that as a failure.
- `shipit release --target <staging|prod> [--notes-json <json>] [--dry-run]`: publish. `--dry-run` prints the plan without publishing.
- `shipit rollback --target <staging|prod>`
- `shipit status`: shows TARGET, ACTIVE and PREVIOUS release ids.
- `shipit purge <release-id> --yes`: irreversible.

Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- Release to staging first, then prod. Do a `--dry-run` first when the target is prod.
- `shipit purge` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Release notes

Notes are JSON of exactly this shape: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. A bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status`; note the previous release id for the target.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.
