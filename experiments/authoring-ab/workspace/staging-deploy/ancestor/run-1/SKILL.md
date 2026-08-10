---
name: staging-deploy
description: Deploy-to-staging procedure — test, build, push image, migrate, deploy, smoke-check. Use when asked to deploy, ship, or push to staging.
---

Deploys the current branch to staging. Run every step in order; do not skip ahead on a hunch that an earlier step would pass.

## Steps

1. **Capture the sha.** `SHA=$(git rev-parse --short HEAD)`. Reuse this value for the image tag and the final sha check — a mismatch between them is how a stale image passes review.
2. **Test.** `pnpm test`. Done when the suite exits 0. A failure here stops the deploy — do not proceed to build.
3. **Build.** `pnpm build`. Done when the build exits 0.
4. **Push the image.** `make docker-push TAG=staging-$SHA`. Done when the push reports success for that tag.
5. **Migrate staging.** `pnpm db:migrate:staging`. The staging and prod database URLs live in the same `.env` — before running, confirm the command and its resolved URL target staging, never prod. Running a migration against the prod URL is not reversible by this skill's rollback step.
6. **Deploy.** `make deploy-staging`. Done when the command exits 0.
7. **Smoke-check.** `curl -s -o /dev/null -w '%{http_code}' https://staging.acme.dev/healthz` returns `200`, and the sha reported by the deployed service matches `$SHA`. Both conditions must hold — a 200 with a mismatched sha means the old build is still serving traffic.

## If the smoke check fails

Run `make rollback-staging`, then re-check `/healthz` and its sha against the pre-deploy sha before reporting the deploy as resolved.