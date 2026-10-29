---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, inspecting release status, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` in the current directory.

## Rules

- Run `shipit check` before every `shipit release`; never skip it. A prod release once went out with an invalid manifest and caused a forty-minute outage.
- `shipit check` exits 0 even when the manifest is missing; it prints `no manifest` on stderr. Treat that line as a failure, not a pass.
- `shipit purge` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. `shipit release --target staging --dry-run`, then without `--dry-run`. (`--dry-run` prints the plan and publishes nothing.)
3. Repeat for prod: always dry-run first, then `shipit release --target prod`.

The flag is `--target`; there is no `--env`.

Release notes are optional JSON: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Status and rollback

`shipit status` prints a table of TARGET, ACTIVE and PREVIOUS release ids.

If a release fails:

1. `shipit status` to see the active and previous release on each target.
2. `shipit rollback --target <staging|prod>` (returns that target to its PREVIOUS release).
3. `shipit status` again; confirm the previous id is now active.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. If the rollback itself fails, retry with `--retries 5`.
7. Put the failed release id in the notes of the next release.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
-h, --help            Show help for shipit or for a command
```

Older docs may mention `make deploy`; that was replaced by shipit.
