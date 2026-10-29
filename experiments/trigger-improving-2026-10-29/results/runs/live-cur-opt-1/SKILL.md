---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` in the current directory.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure, not a pass.
- Release to staging first, then prod. Dry-run (`--dry-run`) before any prod release.
- `shipit purge` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before choosing the next command.

## Releasing

```
shipit check
shipit release --target staging --dry-run
shipit release --target staging
shipit release --target prod --dry-run
shipit release --target prod
```

The flag is `--target`, not `--env`.

Release notes are optional JSON: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`. If it fails, retry with `--retries 5`.
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
```

Dry runs ignore `--retries`.

## Why check matters

In March 2026 a release went to prod with a manifest that failed validation, causing a forty-minute outage because nobody ran the check.
