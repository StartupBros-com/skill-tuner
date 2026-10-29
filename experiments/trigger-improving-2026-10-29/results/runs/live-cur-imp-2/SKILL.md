---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target so it can be rolled back. It reads `shipit.yaml` from the current directory, so run it from the project root.

## Releasing

1. Run `shipit check`. Do this before every `shipit release`, never skip it.
2. Preview with `shipit release --target <target> --dry-run`, which prints the plan and publishes nothing. Always do this for prod.
3. Release to staging first, then prod: `shipit release --target staging`, then `shipit release --target prod`.

Release notes are optional JSON, shaped exactly `{"items":[{"id":"<ticket>","text":"<summary>"}]}`; a bare array, a `notes` key, or extra keys inside an item are rejected:

```
shipit release --target prod --notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'
```

## Checking

`shipit check` validates `shipit.yaml`. If the file is missing it prints `no manifest` on stderr but still exits 0 (verified), so the exit code is not enough: treat `no manifest` as a failure, and make sure you are in the right directory. A March 2026 prod outage came from releasing a manifest that failed validation.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>` returns the target to its previous release.
3. Run `shipit status` again and confirm the previous id is now active, then `shipit check`.
4. Tell the human which release is now active and which was rolled back.
5. If the rollback fails, retry with `--retries 5`, and report the failure.
6. Put the failed release id in the notes of the next release.

## Purge (irreversible)

`shipit purge <release-id> --yes` deletes a release's artifacts from the remote store and cannot be undone. Run it only when the human names the release to purge, and add `--yes` only after they confirm.

## Global options

```
--verbose             Print each step as it runs
--quiet               Print only errors
--no-color            Disable colored output
--timeout <seconds>   Give up on a remote call after this long (default 60)
--retries <n>         Retry failed remote calls this many times (default 2)
```

Dry runs ignore `--retries`. Read each command's output before choosing the next command.
