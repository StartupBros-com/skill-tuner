---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. Run `shipit <command> --help` for exact options.

## Releasing

1. Run `shipit check` before every `shipit release`.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` first for prod; it prints the plan without publishing.
3. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Checking

`shipit check` validates `shipit.yaml` in the current directory. With no manifest it prints `no manifest` on stderr and still exits 0; treat that line as a failure, not a pass.

## Rules

- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before choosing the next command.

## Rollback

1. Run `shipit status` to see the active and previous release on each target.
2. Run `shipit rollback --target <target>`; if it fails, retry with `--retries 5`.
3. Run `shipit status` and confirm the previous release is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the next release's notes.

Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).
