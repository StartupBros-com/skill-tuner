---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`), keeping the previous release on each target for rollback. Reads `shipit.yaml` in the current directory.

## Releasing

1. `shipit check` before every `shipit release`. With no `shipit.yaml` it prints `no manifest` on stderr but exits 0: treat that as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Add `--dry-run` to print the plan without publishing; do so before any prod release.
4. Notes go in `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape (bare array, other keys, extra item keys) is rejected with exit 2.

## Rollback

1. `shipit status` shows the active and previous release per target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is active and which was rolled back; put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` deletes the release's artifacts from the remote store, irreversibly. Run it only for a release the human names, and only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2; dry runs ignore it).
