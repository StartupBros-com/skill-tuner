---
name: shipit
description: Release builds with the shipit CLI. Use when releasing or promoting a build to staging or prod, checking a release manifest, or rolling back a shipit deployment.
---

# shipit

Publishes the current build to a target (`staging` or `prod`) and keeps the previous release for rollback. Options: `shipit <command> --help`.

- **Check first.** Run `shipit check` before every `shipit release`. It exits 0 even when `shipit.yaml` is missing, printing `no manifest`; treat that as a failure.
- **Staging, then prod.** `shipit release --target staging`, then `--target prod`. Run `--dry-run` first for prod.
- **Notes** go in `--notes-json` in the exact shape shown by `shipit release --help`.
- **Purge is irreversible.** Run `shipit purge <release-id>` only for a release the human names, and pass `--yes` only after they confirm.
- **Rollback.** `shipit status` shows ACTIVE and PREVIOUS per target; run `shipit rollback --target <target>`, run `shipit status` to confirm the previous id is active, and tell the human what is now active.
