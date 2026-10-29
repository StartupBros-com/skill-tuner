---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` from the current directory.

## Commands

- `shipit check`: validate the manifest. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that as a failure.
- `shipit release --target <staging|prod> [--notes-json <json>] [--dry-run]`: publish. `--dry-run` prints the plan without publishing.
- `shipit status`: show the active and previous release on each target.
- `shipit rollback --target <staging|prod>`: return a target to its previous release.
- `shipit purge <release-id> --yes`: delete a release's artifacts from the remote store. Irreversible.

Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2; ignored by dry runs).

## Rules

- Run `shipit check` before every `shipit release`, and read its output (including stderr).
- Release to staging first, then prod. Dry-run first when the target is prod.
- Notes JSON must be exactly `{"items":[{"id":"T-1420","text":"Fix login redirect"}]}`. A bare array, a `notes` key, or extra keys in an item are rejected.
- Run `shipit purge` only when the human names the release to purge, and pass `--yes` only after they confirm.

## Rollback

1. `shipit status`; note the previous release id for the failed target.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the next release's notes.
