---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking the release manifest, or rolling back a deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. Run `shipit <command> --help` for exact flags.

## Release

1. `shipit check` in the directory holding `shipit.yaml`. Stdout/stderr `no manifest` means failure even though the exit code is 0; stop and tell the human.
2. `shipit release --target staging --dry-run`, read the plan, then run it without `--dry-run`.
3. Repeat step 2 for `--target prod`. Always dry-run prod first.

The flag is `--target`; `--env` does not exist.

Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. The shape is exactly `{"items":[{"id":...,"text":...}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`.
3. `shipit status` again; confirm the old PREVIOUS id is now ACTIVE.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is active and which was rolled back. If rollback fails, retry with `--retries 5`, and mention the failed release id in the next release's notes.

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

Read each command's output before choosing the next command.
