---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`) and keeps the previous release for rollback. Run `shipit <command> --help` for options. The version comes from `shipit.yaml` in the current directory.

## Releasing

1. `shipit check` before every `shipit release`. It exits 0 even when the manifest is missing, printing `no manifest` on stderr: treat that line as a failure.
2. Release to staging, then prod: `shipit release --target staging`, then `--target prod`. Add `--dry-run` first for prod; it prints the plan without publishing.
3. Notes go in `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape (bare array, `notes` key, extra item keys) is rejected.

Read each command's output before choosing the next.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`, then `shipit status` to confirm the previous id is now active.
3. Tell the human which release is active and which was rolled back.

## Purge

`shipit purge <release-id> --yes` irreversibly deletes a release's artifacts from the remote store. Run it only for a release the human names, and only after they confirm.
