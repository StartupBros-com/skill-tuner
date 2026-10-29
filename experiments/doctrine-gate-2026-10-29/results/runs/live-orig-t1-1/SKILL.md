---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory.

## Releasing

1. Run `shipit check` before every `shipit release`; never skip it. It exits 0 even when the manifest is missing, but prints `no manifest` on stderr. Treat that as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Always add `--dry-run` (prints the plan, publishes nothing) before a prod release.
4. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys in an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`, then `shipit status` to confirm the previous id is now active.
3. Tell the human which release is active and which was rolled back.
4. If rollback fails, retry with `--retries 5`.

## Purge

`shipit purge <release-id> --yes` permanently deletes a release's artifacts from the remote store. Run it only when the human names the release, and pass `--yes` only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2), `-h/--help`.

Read each command's output before choosing the next command.
