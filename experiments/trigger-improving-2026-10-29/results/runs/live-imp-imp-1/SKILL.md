---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` from the current directory, so run it from the project root.

## Rules

- Run `shipit check` before every `shipit release`; never skip it. (A prod release with an invalid manifest caused a forty-minute outage in March 2026.)
- `shipit check` exits 0 even when the manifest is missing; it just prints `no manifest`. Treat that output as a failure, not a pass.
- Dry-run (`--dry-run`) every prod release first, and read the plan before the real run.
- `shipit purge` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. `shipit release --target staging`
3. `shipit release --target prod --dry-run`, then `shipit release --target prod`

Release notes are optional and travel as JSON via `--notes-json`:

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

If a release fails:

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target; note the previous id.
2. `shipit rollback --target <target>`. If it fails, rerun with `--retries 5`.
3. `shipit status` again; confirm the previous id is now active.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. Put the failed release id in the notes of the next release.

## Options

```
shipit check
shipit release --target <staging|prod> [--notes-json <json>] [--dry-run]
shipit rollback --target <staging|prod>
shipit status
shipit purge <release-id> --yes

Global options:
  --verbose             Print each step as it runs
  --quiet               Print only errors
  --no-color            Disable colored output
  --timeout <seconds>   Give up on a remote call after this long (default 60)
  --retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`.
