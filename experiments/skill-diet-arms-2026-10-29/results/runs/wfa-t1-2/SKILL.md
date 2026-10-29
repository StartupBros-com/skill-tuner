---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads the version from `shipit.yaml` in the current directory. Run `shipit <command> --help` for options.

## Releasing

1. `shipit check` before every `shipit release`; a prod release with an unchecked manifest caused a forty-minute outage. `check` exits 0 when the manifest is missing and prints `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` first for prod; it prints the plan and publishes nothing.
3. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly this; a bare array, a `notes` key, or extra keys inside an item are rejected.

Read each command's output before choosing the next.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`.
3. `shipit status` again; confirm the previous id is now active.
4. Tell the human which release is active and which was rolled back.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only for a release the human names, and pass `--yes` only after they confirm.
