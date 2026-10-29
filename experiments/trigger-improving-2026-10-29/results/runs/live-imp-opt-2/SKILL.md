---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory.

Commands: `check`, `release`, `rollback`, `status`, `purge`. Run `shipit <command> --help` for details.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that as a failure. Read the output, not just the exit code.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. `shipit release --target staging`, then `shipit release --target prod`. The flag is `--target`, not `--env`.
3. For prod, first run with `--dry-run` (prints the plan, publishes nothing) and review it.

Release notes are optional JSON, exactly this shape (a bare array, a `notes` key, or extra keys in an item are rejected with exit 2):

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

## Rollback

If a release fails:

1. `shipit status`: shows ACTIVE and PREVIOUS release id per target.
2. `shipit rollback --target <target>`. If it fails, retry with `--retries 5`.
3. `shipit status` again to confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`.
