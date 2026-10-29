---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. The version is read from `shipit.yaml` in the current directory.

## Releasing

1. Run `shipit check` before every `shipit release`; never skip it. It exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`.
3. Always preview prod with `shipit release --target prod --dry-run` (prints the plan, publishes nothing).
4. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys in an item are rejected.

Read each command's output before choosing the next command.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` returns the target to its PREVIOUS release.
3. Run `shipit status` again to confirm the previous id is now active, and `shipit check`.
4. Tell the human which release is now active and which was rolled back. If rollback fails, retry with `--retries 5`.
5. Put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2; ignored by dry runs).
