---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. It reads `shipit.yaml` in the current directory. Run `shipit <command> --help` for exact flags.

## Releasing

1. Run `shipit check`. A pass prints no `no manifest` line. `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr, so read the output and treat that line as a failure; stop and tell the human.
2. Preview with `shipit release --target <target> --dry-run`. Always do this for prod.
3. Release to staging, then to prod: `shipit release --target staging`, then `shipit release --target prod`. The flag is `--target`; `--env` does not exist.
4. Run `shipit status` and confirm the new release id is ACTIVE on that target.

Check before every release, because an unvalidated manifest once took prod down.

### Release notes

Pass notes with `--notes-json`, in exactly this shape:

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

A bare array, a `notes` key, or extra keys inside an item are rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` returns that target to its PREVIOUS release.
3. `shipit status` again; confirm the old PREVIOUS id is now ACTIVE.
4. `shipit check` to confirm the manifest still validates.
5. Tell the human which release is now active and which was rolled back.
6. If the rollback fails, rerun it with `--retries 5`.
7. Put the failed release id in the notes of the next release.

## Purge

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only for a release the human names, and add `--yes` only after they confirm.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

`--dry-run` ignores `--retries`.
