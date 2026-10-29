---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`) and keeps the previous release for rollback. Run `shipit --help` and `shipit <command> --help` for options.

## Releasing

1. `shipit check` before every `shipit release`. A missing `shipit.yaml` exits 0 but prints `no manifest` on stderr: treat that as a failure.
2. Staging first, then prod: `shipit release --target staging`, then `--target prod`.
3. Use `--dry-run` first when the target is prod.
4. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'`. Any other shape is rejected.

## Rollback

1. `shipit status` shows ACTIVE and PREVIOUS release ids per target.
2. `shipit rollback --target <target>`.
3. `shipit status` again; confirm the previous id is now active.
4. Tell the human which release is active and which was rolled back.

## Safety

- `shipit purge <release-id> --yes` permanently deletes a release's artifacts. Run it only for a release the human names, and add `--yes` only after they confirm.
- Read each command's output before choosing the next command.
