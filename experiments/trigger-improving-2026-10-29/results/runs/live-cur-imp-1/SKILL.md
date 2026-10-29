---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` from the current directory.

## Rules

- Run `shipit check` before every `shipit release`; never skip it. A prod release once went out with an invalid manifest and caused a 40-minute outage.
- `shipit check` exits 0 even when the manifest is missing, and prints `no manifest` on stderr. Treat that line as a failure, not a pass; don't rely on the exit code.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check` (run from the directory containing `shipit.yaml`).
2. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`. The flag is `--target`, not `--env`.
3. For prod, first run with `--dry-run`, which prints the plan without publishing, then run for real.
4. Release notes are passed with `--notes-json`:
   `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`
   The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

If a release fails:

1. `shipit status` to see the active and previous release on each target; note the previous release id.
2. `shipit rollback --target <staging|prod>`. If it fails, rerun with `--retries 5`.
3. `shipit status` again and confirm the previous id is now active.
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

Dry runs ignore `--retries`. Command-specific options: `release` takes `--target`, `--notes-json`, `--dry-run`; `rollback` takes `--target`; `purge` takes `<release-id>` and `--yes`. `shipit <command> --help` shows details.
