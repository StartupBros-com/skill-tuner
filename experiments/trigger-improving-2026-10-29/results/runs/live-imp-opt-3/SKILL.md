---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads the version from `shipit.yaml` in the current directory.

## Releasing

1. Run `shipit check`. It exits 0 even when the manifest is missing, printing `no manifest` on stderr; treat that line as a failure.
2. Run `shipit release --target staging --dry-run` and read the plan. Repeat with `--target prod` before the prod release.
3. Release to staging, then to prod: `shipit release --target staging`, then `shipit release --target prod`. Skipping `check` ships an invalid manifest to prod.
4. Release notes travel as JSON: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

Read each command's output before choosing the next command.

## Rollback

1. Run `shipit status`; the PREVIOUS column holds the release id each target returns to.
2. Run `shipit rollback --target <target>`. If it fails, rerun with `--retries 5`.
3. Run `shipit status` and confirm the previous id is now active, then run `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. Put the failed release id in the notes of the next release.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only for a release the human names, and only after they confirm.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`.
