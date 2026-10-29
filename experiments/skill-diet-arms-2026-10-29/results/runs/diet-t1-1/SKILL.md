---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`) and keeps the previous release for rollback. Run `shipit <command> --help` for options.

## Releasing

1. `shipit check` before every release. It exits 0 even when the manifest is missing and prints `no manifest`; treat that as a failure.
2. Staging first, then prod: `shipit release --target staging`, then `--target prod`. Add `--dry-run` first for prod.
3. Notes: `--notes-json '{"items":[{"id":"T-1420","text":"Fix login redirect"}]}'` (other shapes are rejected).

## Rollback

`shipit status` (the PREVIOUS column is what rollback restores), then `shipit rollback --target <target>`, then `shipit status` to confirm. Tell the human which release is now active and which was rolled back.

## Safety

- `shipit purge <release-id> --yes` permanently deletes a release's artifacts. Run it only for a release the human names, and add `--yes` only after they confirm.
- Read each command's output before choosing the next command.
