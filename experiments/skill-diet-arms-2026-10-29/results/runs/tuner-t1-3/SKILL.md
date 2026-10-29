---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads the version from `shipit.yaml` in the current directory. Run `shipit <command> --help` for options.

## Releasing

1. Run `shipit check` before every `shipit release`. It validates `shipit.yaml`. When the manifest is missing it exits 0 and prints `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` to print the plan without publishing; always dry-run prod first.
3. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys inside an item are rejected.

Read each command's output before choosing the next command.

## Rollback

1. `shipit status` lists ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` returns the target to its PREVIOUS release.
3. Run `shipit status` and confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. If the rollback fails, retry with `--retries 5`.
6. Put the failed release id in the notes of the next release.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only for a release the human names, and pass `--yes` only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
