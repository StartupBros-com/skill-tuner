---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` in the current directory, so run it from the project root.

## Rules

- Run `shipit check` before every `shipit release`; never skip it.
- `shipit check` exits 0 even when the manifest is missing, and prints `no manifest` on stderr. Treat that line as a failure: do not release.
- Release to staging first, then prod.
- Dry-run (`--dry-run`) every prod release first, and read the plan before the real run.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and add `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Releasing

1. `shipit check`
2. `shipit release --target staging`
3. `shipit release --target prod --dry-run`, then `shipit release --target prod`

The flag is `--target`; `--env` is not accepted.

Release notes are JSON passed with `--notes-json`:

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

The shape is exactly `{"items":[{"id":"...","text":"..."}]}`. A bare array, a `notes` key, or extra keys in an item are rejected (exit 2).

## Rollback

If a release fails:

1. `shipit status` to see the active and previous release on each target; note the previous release id.
2. `shipit rollback --target <staging|prod>`
3. `shipit status` again and confirm the previous id is now active.
4. `shipit check` to confirm the manifest still validates.
5. If the rollback itself fails, rerun with `--retries 5`.
6. Tell the human which release is now active and which was rolled back, and put the failed release id in the notes of the next release.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

## Background

In March 2026 a release went to prod with a manifest that failed validation and caused a forty-minute outage because nobody ran the check. Older docs may mention `make deploy`; the team moved to shipit from a Makefile in January.
