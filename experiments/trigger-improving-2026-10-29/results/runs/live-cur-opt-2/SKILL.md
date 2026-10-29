---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads the version from `shipit.yaml` in the current directory, so run it from the project root.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure, not a pass. (A prod release once went out with an invalid manifest and caused a 40-minute outage.)
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. For prod, preview first: `shipit release --target prod --dry-run` (prints the plan, publishes nothing).
3. Release to staging, then prod: `shipit release --target staging`, then `shipit release --target prod`.

The flag is `--target`, not `--env`.

Release notes are optional and passed as JSON:
`shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`
The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <staging|prod>`. If it fails, retry with `--retries 5`.
3. `shipit status` again; confirm the previous id is now active.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. Put the failed release id in the notes of the next release.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
-h, --help            Show help for shipit or a command
```

Dry runs ignore `--retries`.
