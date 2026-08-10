---
name: staging-deploy
description: Deploying, shipping, or pushing code to staging — runs tests, build, image push, staging migration, deploy, and smoke-check in order, with the safeguard that keeps migrations off prod.
---

Deploy to staging by running this sequence in order. Each step depends on the one before it succeeding — do not skip or reorder.

1. **Test** — `pnpm test`. Done when the command exits 0. A failing suite stops the deploy here.
2. **Build** — `pnpm build`. Done when the command exits 0.
3. **Push image** — `make docker-push TAG=staging-<git-sha>`, where `<git-sha>` is the current commit's short SHA (`git rev-parse --short HEAD`). Done when the push exits 0. Note the tag — step 6 checks against it.
4. **Migrate** — `pnpm db:migrate:staging`. Target the staging DB only: the `.env` file holds the staging and prod URLs side by side, so confirm the command is reading the staging one before running it. Done when the migration exits 0.
5. **Deploy** — `make deploy-staging`. Done when the command exits 0.
6. **Smoke-check** — request `https://staging.acme.dev/healthz` and confirm both: the response is `200`, and its reported sha matches the `<git-sha>` from step 3. Done only when both hold — a `200` alone is not enough.

If the smoke-check fails, roll back immediately: `make rollback-staging`. Do not patch forward on a failed staging deploy.