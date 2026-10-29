---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads the version from `shipit.yaml` in the current directory. Run `shipit <command> --help` for options.

## Releasing

1. Run `shipit check` before every `shipit release`. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`.
3. Add `--dry-run` to print the plan without publishing; always dry-run prod first.
4. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2). Dry runs ignore `--retries`.
