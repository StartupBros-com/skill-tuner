---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory.

Commands: `check`, `release`, `rollback`, `status`, `purge`. Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2), `-h/--help`.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure.
- `shipit purge <release-id> --yes` irreversibly deletes a release's artifacts from the remote store. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Use `--dry-run` (prints the plan, publishes nothing) first, always for prod.
3. Notes are optional JSON: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape must be exactly this; a bare array, a `notes` key, or extra keys in an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` again to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.
