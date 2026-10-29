---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target and keeps the previous release on each target so it can be rolled back. This skill covers the day-to-day commands; the full option list is at the end.

## Before you start

Versions follow semantic versioning: a version number has the form MAJOR.MINOR.PATCH, where you increment MAJOR when you make incompatible API changes, MINOR when you add functionality in a backwards-compatible manner, and PATCH when you make backwards-compatible bug fixes. shipit reads the version from `shipit.yaml` in the current directory.

A dry run prints the plan without publishing anything.

## Releasing

1. Run `shipit check` and read its output. Proceed only when it exits 0 and prints no `no manifest` line; otherwise fix the manifest and run it again. Every `shipit release` to any target, dry run or not, is preceded by a passing check in the same working directory state.
2. Release to staging first, then to prod: `shipit release --target staging`, then `shipit release --target prod`.
3. Release notes travel as JSON: `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Checking

`shipit check` validates the manifest. It exits 0 when the manifest is missing and prints `no manifest` on stderr; treat that line as a failure, not a pass. Re-run it after any edit to `shipit.yaml`.

Dry-run (`--dry-run`) every prod release before the real one.

## Rules

- `shipit purge` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and pass `--yes` only after they confirm.
- Read each command's output before deciding the next command.

## Rollback

If a release fails:

1. Run `shipit status` to see the active release on each target.
2. Note the previous release id in the PREVIOUS column.
3. Run `shipit rollback --target <target>`.
4. Run `shipit status` again and confirm the previous id is now active.
5. Run `shipit check` to confirm the manifest still validates.
6. Tell the human which release is now active and which was rolled back.
7. If the rollback itself fails, run it again with `--retries 5`.
8. File the failed release id in the notes of the next release.

## Options

```
Global options:
  --verbose             Print each step as it runs
  --quiet               Print only errors
  --no-color            Disable colored output
  --timeout <seconds>   Give up on a remote call after this long (default 60)
  --retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`.
