---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory. Commands: `check`, `release`, `rollback`, `status`, `purge`; `shipit <command> --help` lists each one's options.

## Releasing

1. Run `shipit check` before every `shipit release`; never skip it. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` (prints the plan, publishes nothing) whenever the target is prod, and read the plan before the real run.
3. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys inside an item are rejected.

Read each command's output before deciding the next command.

## Rollback

1. `shipit status` shows the active and previous release on each target; note the previous id.
2. `shipit rollback --target <target>`. If it fails, rerun with `--retries 5`.
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
