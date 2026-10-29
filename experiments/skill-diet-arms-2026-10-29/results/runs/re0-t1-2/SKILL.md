---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. The version comes from `shipit.yaml` in the current directory.

## Releasing

1. Run `shipit check` before every `shipit release`; never skip it. It exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` to print the plan without publishing; always do so first for prod.
3. Release notes travel as JSON: `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

If a release fails:

1. Run `shipit status` and note the previous release id in the PREVIOUS column for the target.
2. Run `shipit rollback --target <target>`. If it fails, rerun with `--retries 5`.
3. Run `shipit status` to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back, and file the failed release id in the next release's notes.

## Safety

- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and only after they confirm.
- Read each command's output before deciding the next command.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2), `-h/--help`.
