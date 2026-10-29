---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads the version from `shipit.yaml` in the current directory.

## Releasing

1. Run `shipit check` before every `shipit release`. It exits 0 even when the manifest is missing, printing `no manifest`; treat that as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` to print the plan without publishing; do so whenever the target is prod.
3. Release notes use exactly `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. A bare array, a `notes` key, or extra keys inside an item are rejected.

## Rules

- Never skip `shipit check` before a release; a prod release with an invalid manifest once caused a forty-minute outage.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back, and list the failed release id in the next release's notes.

## Global options

`--verbose`, `--quiet` (errors only), `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
