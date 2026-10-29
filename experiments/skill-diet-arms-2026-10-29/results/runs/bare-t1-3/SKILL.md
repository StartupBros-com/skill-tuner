---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback.

## Commands

- `shipit check`: validates `shipit.yaml` in the current directory. With no manifest it prints `no manifest` on stderr but still exits 0; treat that as a failure.
- `shipit release --target <staging|prod> [--notes-json <json>] [--dry-run]`: publishes. `--dry-run` prints the plan without publishing.
- `shipit status`: shows the active and previous release on each target.
- `shipit rollback --target <staging|prod>`
- `shipit purge <release-id> --yes`: see Rules.

Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).

## Releasing

1. Run `shipit check` and confirm it passes (a prior prod release with an unvalidated manifest caused an outage).
2. Release to staging first, then prod. Use `--dry-run` first when the target is prod.
3. Notes shape is exactly `{"items":[{"id":"T-1420","text":"Fix login redirect"}]}`; a bare array, a `notes` key, or extra keys in an item are rejected.

## Rules

- Never skip `shipit check` before `shipit release`.
- `shipit purge` irreversibly deletes a release's artifacts from the remote store. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before choosing the next one.

## Rollback

1. `shipit status`; note the previous release id.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the next release's notes.
