---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. Run `shipit <command> --help` for options, including the `--notes-json` shape.

## Releasing

1. Run `shipit check` before every `shipit release`. It exits 0 even when `shipit.yaml` is missing, printing `no manifest` on stderr; treat that as a failure.
2. Release to staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Use `--dry-run` first when the target is prod.

## Safety

- `shipit purge` irreversibly deletes a release's artifacts from the remote store. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before choosing the next command.

## Rollback

1. `shipit status`; note the PREVIOUS release id for the target.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` again to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.
