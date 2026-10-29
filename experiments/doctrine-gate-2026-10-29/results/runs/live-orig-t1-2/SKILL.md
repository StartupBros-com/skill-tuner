---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback.

## Rules

- Run `shipit check` before every `shipit release`; never skip it. A prod release once went out with an invalid manifest and caused a forty-minute outage.
- `shipit check` exits 0 even when `shipit.yaml` is missing, printing `no manifest` on stderr. Treat that line as a failure, not a pass.
- Use `--dry-run` on `shipit release` (prints the plan, publishes nothing) whenever the target is prod.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. `shipit release --target staging`, then `shipit release --target prod`.

Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape must be exactly this; a bare array, a `notes` key, or extra keys in an item are rejected.

## Rollback

1. `shipit status` shows the active and previous release on each target; note the previous id.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2, for failed remote calls), `-h/--help`. Dry runs ignore `--retries`.
