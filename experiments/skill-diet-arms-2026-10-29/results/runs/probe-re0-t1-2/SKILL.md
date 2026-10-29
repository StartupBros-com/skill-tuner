---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads the version from `shipit.yaml` in the current directory.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure.
- Release to staging first, then prod. Always use `--dry-run` first for prod.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Commands

```
shipit check
shipit release --target <staging|prod> [--notes-json <json>] [--dry-run]
shipit rollback --target <staging|prod>
shipit status
shipit purge <release-id> --yes
```

Notes JSON must be exactly `{"items":[{"id":"T-1420","text":"Fix login redirect"}]}`; a bare array, a `notes` key, or extra keys in an item are rejected.

Global options: `--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2).

## Rollback

1. `shipit status`; note the previous release id.
2. `shipit rollback --target <target>` (if it fails, retry with `--retries 5`).
3. `shipit status` to confirm the previous id is active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.
