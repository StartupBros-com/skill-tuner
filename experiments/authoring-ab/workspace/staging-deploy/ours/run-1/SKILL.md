---
name: staging-deploy
description: Deploy to staging — test, build, push the image, migrate the staging DB, deploy, and smoke-check. Use when the task is deploying to staging.
---

Deploy to staging by running these steps in order. Stop and report if any step fails; do not proceed to the next step on top of a failure.

1. Capture the SHA once and reuse it for every later step: `SHA=$(git rev-parse --short HEAD)`. The same value tags the image in step 4 and verifies the deploy in step 7.
2. Test: `pnpm test`. All tests must pass — a non-zero exit code stops the deploy here.
3. Build: `pnpm build`. Must exit 0.
4. Push the image: `make docker-push TAG=staging-$SHA`.
5. Migrate the staging DB: `pnpm db:migrate:staging`. The `.env` file also holds the prod DB URL — confirm the command targets staging before running it; never run a migration command against the prod URL.
6. Deploy: `make deploy-staging`.
7. Smoke-check: `curl -s -o /dev/null -w '%{http_code}' https://staging.acme.dev/healthz` must return `200`, and the sha reported by the deployed service must equal `$SHA`. Both conditions must hold — a 200 with a stale sha is not a successful deploy.

## If the smoke-check fails

Run `make rollback-staging` immediately, then report the failure.