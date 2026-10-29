---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads the version from `shipit.yaml` in the current directory, so run it from the project root.

## Releasing

1. `shipit check` before every `shipit release`; never skip it. A release once went to prod with an invalid manifest and caused a 40-minute outage.
2. `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure, not a pass.
3. Dry run first, always for prod: `shipit release --target prod --dry-run` prints the plan and publishes nothing.
4. Release to staging, then prod: `shipit release --target staging`, then `shipit release --target prod`. The flag is `--target`, not `--env`.
5. Release notes are optional JSON: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly that; a bare array, a `notes` key, or extra keys in an item are rejected (exit 2).

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <staging|prod>`. If it fails, retry with `--retries 5`.
3. `shipit status` again; confirm the previous id is now active. Run `shipit check` too.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Purge (destructive)

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`. Read each command's output before choosing the next command.
