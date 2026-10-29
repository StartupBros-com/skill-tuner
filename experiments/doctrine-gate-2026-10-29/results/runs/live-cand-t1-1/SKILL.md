---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`), keeping the previous release on each target for rollback. Run `shipit <command> --help` for options.

## Releasing

1. `shipit check` before every release. With no `shipit.yaml` it prints `no manifest` on stderr but exits 0; treat that as a failure.
2. Release to staging, then prod: `shipit release --target staging`, then `shipit release --target prod`. Use `--dry-run` first for prod; it prints the plan and publishes nothing.
3. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape (bare array, other top-level key, extra keys in an item) is rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`.
3. `shipit status` again; confirm the previous id is now active.
4. Tell the human which release is active and which was rolled back.

## Purge

`shipit purge <release-id> --yes` irreversibly deletes a release's artifacts from the remote store. Run it only for a release the human names, and add `--yes` only after they confirm.
