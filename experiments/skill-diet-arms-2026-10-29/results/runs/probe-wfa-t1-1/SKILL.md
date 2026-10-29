---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

shipit publishes the current build to a target (`staging` or `prod`) and keeps the previous release on each target for rollback. The version comes from `shipit.yaml` in the current directory. Run `shipit <command> --help` for options.

## Rules

- Run `shipit check` before every `shipit release`.
- `shipit check` exits 0 even when the manifest is missing, printing `no manifest` on stderr. Treat that line as a failure.
- Release to staging first, then prod. Dry-run (`--dry-run`) every prod release first; it prints the plan and publishes nothing.
- `shipit purge <release-id> --yes` deletes a release's artifacts from the remote store, irreversibly. Run it only when the human names the release, and pass `--yes` only after they confirm.
- Read each command's output before choosing the next command.

## Releasing

```
shipit check
shipit release --target staging
shipit release --target prod --dry-run
shipit release --target prod
```

Release notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Exactly this shape; anything else is rejected (exit 2).

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`.
3. `shipit status` again: the previous id should now be active. Then `shipit check`.
4. Tell the human which release is active and which was rolled back.
5. If the rollback fails, rerun with `--retries 5`.
6. Put the failed release id in the next release's notes.

## Global options

`--verbose`, `--quiet`, `--no-color`, `--timeout <seconds>` (default 60), `--retries <n>` (default 2, ignored by dry runs).
