---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. Run `shipit <command> --help` for options.

## Releasing

1. Run `shipit check` before every `shipit release`. It validates `shipit.yaml` in the current directory. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`.
3. Run `shipit release --target prod --dry-run` first; it prints the plan without publishing.
4. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":...,"text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

Read each command's output before choosing the next command.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only when the human names the release, and pass `--yes` only after they confirm.

## Rollback

1. `shipit status` shows the active and previous release on each target.
2. `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
