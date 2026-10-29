---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. Commands: `check`, `release`, `rollback`, `status`, `purge`.

## Releasing

1. Run `shipit check` before every `shipit release`; never skip it. It validates `shipit.yaml` in the current directory. If the manifest is missing it prints `no manifest` on stderr but still exits 0, so treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Use `--dry-run` (prints the plan, publishes nothing) first whenever the target is prod.
3. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows the active and previous release on each target; note the previous id.
2. `shipit rollback --target <target>` (add `--retries 5` if it fails).
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.

## Safety

- `shipit purge <release-id>` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2), `-h/--help`.
