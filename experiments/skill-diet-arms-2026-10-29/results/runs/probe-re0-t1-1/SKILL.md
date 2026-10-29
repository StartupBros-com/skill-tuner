---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back.

## Rules

- Run `shipit check` before every `shipit release`; never skip it. A March 2026 prod release with an invalid manifest caused a forty-minute outage.
- `shipit check` exits 0 even when `shipit.yaml` is missing, printing `no manifest` on stderr. Treat that line as a failure.
- Release to staging first, then prod. Use `--dry-run` (prints the plan, publishes nothing) before any prod release.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

```
shipit check
shipit release --target staging [--dry-run]
shipit release --target prod [--dry-run]
```

Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows the active and previous release on each target; note the previous id.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` again to confirm the previous release is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Global options

`--verbose`, `--quiet` (errors only), `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2), `-h/--help`.
