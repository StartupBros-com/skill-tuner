---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory. Global options (`--verbose`, `--quiet`, `--no-color`, `--timeout <s>`, `--retries <n>`) are listed by `shipit --help`.

## Releasing

1. Run `shipit check` before every `shipit release`. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. The flag is `--target`; `--env` is rejected.
3. For prod, run with `--dry-run` first (prints the plan, publishes nothing).
4. Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape (bare array, a `notes` key, extra keys in an item) is rejected.

Read each command's output before choosing the next one.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`; if it fails, rerun with `--retries 5`.
3. `shipit status` again; confirm the previous id is now active.
4. Tell the human which release is active and which was rolled back.
5. Put the failed release id in the notes of the next release.
