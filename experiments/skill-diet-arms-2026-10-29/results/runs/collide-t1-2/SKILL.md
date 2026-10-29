---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build (version from `shipit.yaml` in the current directory) to a target and keeps the previous release on each target for rollback. Run `shipit <command> --help` for options.

## Releasing

1. Run `shipit check` before every `shipit release`; never skip it. It exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`. Use `--dry-run` first for prod.
3. Notes go in `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape is rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`, then `shipit status` to confirm the previous id is now active.
3. Tell the human which release is active and which was rolled back.

## Safety

- `shipit purge <release-id> --yes` permanently deletes a release's artifacts. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before choosing the next command.
