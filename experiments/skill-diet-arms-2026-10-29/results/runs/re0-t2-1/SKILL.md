---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target and keeps the previous release on each target so it can be rolled back. This skill covers the day-to-day commands; the full option list is at the end.

## Before you start

Versions follow semantic versioning (MAJOR.MINOR.PATCH), and shipit reads the version from `shipit.yaml` in the current directory.

`--dry-run` prints the plan without publishing anything.

## Releasing

1. Run `shipit check` and confirm it passes. This is required before every `shipit release`, staging and prod alike, and again after any change to `shipit.yaml`. Releases have shipped broken manifests to prod when it was skipped.
2. Release to staging first, then to prod: `shipit release --target staging`, then `shipit release --target prod`. Use `--dry-run` first whenever the target is prod.
3. Release notes travel as JSON: `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Checking

`shipit check` validates the manifest. It exits 0 even when the manifest is missing, printing `no manifest`; treat that line as a failure, not a pass, so judge the result by its output rather than its exit code. Do not release until the check passes.

## Rules

- Never run `shipit release` without a passing `shipit check` in the same session, even under time pressure or for a small change.
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
