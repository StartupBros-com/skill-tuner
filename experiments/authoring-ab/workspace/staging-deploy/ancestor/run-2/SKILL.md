---
name: staging-deploy
description: Deploying, shipping, or pushing the app to staging. Use whenever asked to deploy, ship, or push to staging.
---

Deploy the current commit to staging: test, build, push, migrate, deploy, smoke-check.

## Steps

1. Run the test suite: `pnpm test`. Done when it exits 0 — do not proceed past a failure.
2. Build: `pnpm build`. Done when the build exits 0.
3. Push the image: `make docker-push TAG=staging-<git-sha>`, using the current commit's short sha. Done when the push completes and that tag appears in the registry output. Keep the sha — step 6 checks against it.
4. Migrate: `pnpm db:migrate:staging`. **Never run a migrate command against the prod URL** — it sits in the same `.env` as the staging URL, so confirm you're invoking the `:staging` script and not passing a URL by hand. Done when the migration output reports success against the staging DB.
5. Deploy: `make deploy-staging`. Done when the command exits 0.
6. Smoke-check: request `https://staging.acme.dev/healthz` and confirm it returns 200 *and* reports the sha pushed in step 3. Both must match — a 200 with a stale sha is not done.

## Rollback

If step 6 fails, or staging misbehaves after deploy, run `make rollback-staging`.