---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory.

## Releasing

1. Run `shipit check` before every `shipit release`. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Add `--dry-run` to print the plan without publishing; do so whenever the target is prod, then release for real.
4. Notes travel as JSON, exactly `{"items":[{"id":"T-1420","text":"Fix login redirect"}]}` via `--notes-json`. A bare array, a `notes` key, or extra keys inside an item are rejected.

## Rules

- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Rollback

1. `shipit status` shows the active and previous release per target; note the previous id.
2. `shipit rollback --target <target>`; if it fails, rerun with `--retries 5`.
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the next release's notes.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
