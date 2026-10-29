---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` in the current directory, so run it from the project root.

## Rules

- Run `shipit check` before every `shipit release`; never skip it. (A prod release once went out with an invalid manifest and caused a 40-minute outage.)
- `shipit check` exits 0 even when the manifest is missing; it prints `no manifest` on stderr. Treat that as a failure, not a pass.
- `shipit purge <release-id> --yes` permanently deletes a release's artifacts from the remote store. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. Dry run first, always for prod: `shipit release --target prod --dry-run` prints the plan and publishes nothing.
3. Release to staging, then to prod: `shipit release --target staging`, then `shipit release --target prod`.

The flag is `--target`, not `--env`.

Release notes are optional JSON, in exactly this shape (a bare array, a `notes` key, or extra keys inside an item are rejected):

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

## Rollback

If a release fails:

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <staging|prod>`
3. `shipit status` again; confirm the previous id is now active.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. If the rollback itself fails, rerun it with `--retries 5`.
7. Include the failed release id in the notes of the next release.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`.
