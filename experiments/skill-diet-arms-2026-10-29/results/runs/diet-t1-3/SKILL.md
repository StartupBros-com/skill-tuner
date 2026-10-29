---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`) and keeps the previous release for rollback. Run `shipit <command> --help` for flags.

## Releasing

1. `shipit check` before every release. It exits 0 even when `shipit.yaml` is missing, printing `no manifest`; treat that as a failure.
2. Release to staging, then prod: `shipit release --target staging`, then `--target prod`. Use `--dry-run` first for prod.
3. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Exactly this shape; anything else is rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release per target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is active, then tell the human which release is active and which was rolled back.

## Purge

`shipit purge <release-id>` irreversibly deletes artifacts from the remote store. Run it only for a release the human named, and pass `--yes` only after they confirm.
