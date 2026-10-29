---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory. Run `shipit <command> --help` for options.

## Releasing

1. `shipit check` before every `shipit release`, never skipped. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that as a failure. (A prod release with an unvalidated manifest once caused a forty-minute outage.)
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Add `--dry-run` to print the plan without publishing; do this for every prod release.
4. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Exactly that shape; a bare array, a `notes` key, or extra keys in an item are rejected (exit 2).

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back, and put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only when the human names the release, and pass `--yes` only after they confirm.
