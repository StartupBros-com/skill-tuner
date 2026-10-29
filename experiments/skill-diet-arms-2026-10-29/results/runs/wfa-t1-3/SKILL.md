---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads the version from `shipit.yaml` in the current directory. Run `shipit <command> --help` for options.

## Releasing

1. `shipit check` before every `shipit release`. It exits 0 with `no manifest` on stderr when `shipit.yaml` is missing; treat that as a failure. (A release once went to prod with an invalid manifest and caused a forty-minute outage.)
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Run `shipit release --target prod --dry-run` first; it prints the plan without publishing.
4. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. This shape only; a bare array, a `notes` key, or extra keys in an item are rejected.

Read each command's output before choosing the next.

## Rollback

1. `shipit status` shows the active and previous release per target; note the previous id.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` again to confirm the previous id is active.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` irreversibly deletes a release's artifacts from the remote store. Run it only for a release the human names, and add `--yes` only after they confirm.
