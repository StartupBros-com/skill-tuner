---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. Commands: `check`, `release`, `rollback`, `status`, `purge`. It reads the version from `shipit.yaml` in the current directory, so run it from the project root.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing; it then prints `no manifest` on stderr. Treat that line as a failure, not a pass. Do not rely on the exit code.
- Do a dry run (`--dry-run`) before any prod release. It prints the plan and publishes nothing.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check` (see the rule above on `no manifest`).
2. Staging first: `shipit release --target staging`.
3. Prod dry run: `shipit release --target prod --dry-run`, then `shipit release --target prod`.

The flag is `--target`, not `--env`. Release notes are optional JSON via `--notes-json`:

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

If a release fails:

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` returns that target to its previous release.
3. `shipit status` again; confirm the previous id is now active.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. If the rollback itself fails because of a remote error, rerun it with `--retries 5`.
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

Dry runs ignore `--retries`.

Background: in March 2026 an unchecked, invalid manifest went to prod and caused a forty-minute outage; that is why the check rule exists.
