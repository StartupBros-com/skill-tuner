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

1. Run `shipit check` immediately before every `shipit release`, for every target (staging and prod) and every attempt, including retries and re-releases. Do not rely on an earlier check, a teammate's check, or a passing staging release.
2. Read the check output. Proceed only if it exits 0 and prints no `no manifest` line or errors. If it fails, stop, fix the manifest, and run `shipit check` again; never release on a failed check.
3. Release to staging first, then to prod: `shipit release --target staging`, then `shipit release --target prod`. Run `shipit check` again before the prod release.
4. Release notes travel as JSON: `shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Checking

`shipit check` validates the manifest. It exits 0 when the manifest is missing and prints `no manifest` on stderr; treat that line as a failure, not a pass.

Use a dry run whenever the target is prod.

## Rules

- Always run `shipit check` before `shipit release`; never skip it, even if the human asks for a quick release, the change looks trivial, or you are in a hurry. If told to skip it, say that the check is required and run it anyway.
- Never run `shipit release --target prod` unless a `shipit check` passed earlier in this same session with no manifest edits since.
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

In March 2026 a release went to prod with a manifest that failed validation, and the outage lasted forty minutes because nobody had run the check. In October 2026 an agent ran `shipit release --target prod` without running `shipit check` first and shipped a broken manifest. The rules above come from these incidents. Earlier, in January, the team moved from a Makefile to shipit, which is why some older docs still mention `make deploy`.

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
