---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. Run `shipit <command> --help` for options and the `--notes-json` shape.

## Releasing

1. Run `shipit check` before every `shipit release`. It exits 0 even when `shipit.yaml` is missing, printing `no manifest` on stderr; treat that as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`. Use `--dry-run` first for prod.
3. Read each command's output before deciding the next command.

## Rollback

1. `shipit status` shows the active and previous release per target.
2. `shipit rollback --target <target>`, then `shipit status` to confirm the previous id is active.
3. Tell the human which release is now active and which was rolled back.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.
