---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. The version comes from `shipit.yaml` in the current directory.

Commands: `check`, `release`, `rollback`, `status`, `purge`. Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).

## Releasing

1. Always run `shipit check` before `shipit release`. It exits 0 even when `shipit.yaml` is missing, printing `no manifest` on stderr; treat that as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Use `--dry-run` (prints the plan, publishes nothing) first, always for prod.
3. Notes: `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":...,"text":...}]}`; a bare array, a `notes` key, or extra keys in an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. Run `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.

Read each command's output before choosing the next command.
