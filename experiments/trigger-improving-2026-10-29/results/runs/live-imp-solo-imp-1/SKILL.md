---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. Run `shipit <command> --help` for a command's options.

## Release

1. Run `shipit check`. It exits 0 even when `shipit.yaml` is missing, printing `no manifest` on stderr, so read the output: `no manifest` means the check failed, so stop and tell the human.
2. Run `shipit release --target staging --dry-run` and confirm the plan names the right target.
3. Run `shipit release --target staging`.
4. Repeat steps 1-3 for `--target prod`. Always dry-run prod first.

Release notes are optional JSON: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":..., "text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` returns that target to its PREVIOUS release.
3. `shipit status` again; confirm the old PREVIOUS id is now ACTIVE.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. If the rollback fails, rerun it with `--retries 5`. Put the failed release id in the next release's notes.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only for a release the human named, and add `--yes` only after they confirm.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`.
