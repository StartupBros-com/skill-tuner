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

1. Run `shipit check` immediately before each `shipit release`, staging and prod alike. Proceed only when that run exited 0 and printed no `no manifest` line on stderr (a missing manifest exits 0 but is a failure). A check from earlier in the session, or on a different target, does not count: run it again.
2. Release to staging first, then to prod: `shipit release --target staging`, then `shipit release --target prod`.
3. Release notes travel as JSON: `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Checking

`shipit check` validates the manifest; see Releasing step 1 for how to read its result.

Use a dry run whenever the target is prod.

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

## History

Twice a release went to prod with a broken manifest because `shipit check` was not run first: in March 2026 (a forty-minute outage) and again in October 2026 (`shipit release --target prod` straight away). Releasing step 1 comes from those incidents. Earlier, in January, the team moved from a Makefile to shipit, which is why some older docs still mention `make deploy`.

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
