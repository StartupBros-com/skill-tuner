---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory. `shipit <command> --help` lists a command's options.

## Releasing

1. `shipit check` before every `shipit release`. It exits 0 even when the manifest is missing, printing `no manifest` on stderr: treat that line as a failure.
2. Release to staging, then prod: `shipit release --target staging`, then `shipit release --target prod`. Add `--dry-run` first for prod; it prints the plan and publishes nothing.
3. Notes go in `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape (bare array, `notes` key, extra keys in an item) is rejected with exit 2.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`; if it fails, rerun with `--retries 5`.
3. `shipit status` again to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back, and put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only for a release the human named, and pass `--yes` only after they confirm.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2; ignored by dry runs).
