---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback.

## Releasing

1. `shipit check` first, every time. It validates `shipit.yaml` in the current directory. With no manifest it prints `no manifest` on stderr yet exits 0: treat that as a failure.
2. Release to staging, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` to print the plan without publishing; always dry-run prod first.
3. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Exactly that shape; a bare array, a `notes` key, or extra keys in an item are rejected.

Read each command's output before choosing the next one.

## Rollback

1. `shipit status` shows the active and previous release on each target.
2. `shipit rollback --target <target>`. If it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous release is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back, and put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` irreversibly deletes a release's artifacts from the remote store. Run it only for a release the human named, and pass `--yes` only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
