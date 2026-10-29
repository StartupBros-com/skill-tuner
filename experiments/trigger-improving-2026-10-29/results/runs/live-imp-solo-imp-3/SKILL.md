---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory.

## Release

1. `shipit check`. Exit code is 0 even when the manifest is missing, so read the output: `no manifest` on stderr means failure. Stop and tell the human.
2. `shipit release --target staging --dry-run`, then the same without `--dry-run`.
3. Repeat for prod: dry run first, then `shipit release --target prod`.

Release notes are optional JSON, exactly `{"items":[{"id":"T-1420","text":"Fix login redirect"}]}`. A bare array, a `notes` key, or extra keys inside an item are rejected.

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

Run `shipit check` before every release, because a manifest that fails validation has caused a prod outage.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`.
3. `shipit status` again; confirm the previous id is now ACTIVE.
4. `shipit check`.
5. Tell the human which release is now active and which was rolled back.

If rollback fails, rerun it with `--retries 5`. Put the failed release id in the notes of the next release.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only for a release the human named, and add `--yes` only after they confirm.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

`shipit <command> --help` shows per-command usage. Read each command's output before choosing the next one.
