---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory. Run `shipit <command> --help` for exact flags.

## Releasing

1. Run `shipit check`. A missing manifest still exits 0 but prints `no manifest` on stderr; that line means the check failed, so stop and tell the human.
2. Preview with `shipit release --target <target> --dry-run`. Always do this for prod.
3. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`.
4. Read each command's output before running the next.

Release notes go in `--notes-json`, shaped exactly `{"items":[{"id":"T-1420","text":"Fix login redirect"}]}`. Use no bare array, no `notes` key, and no extra keys inside an item.

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

## Rollback

1. `shipit status` shows the active and previous release per target; note the previous id.
2. `shipit rollback --target <target>`. If it fails, rerun with `--retries 5`.
3. `shipit status` again: the previous id must now be active.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. Put the failed release id in the notes of the next release.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only for a release the human named, and only after they confirm that release id.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```
