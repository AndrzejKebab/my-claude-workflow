---
name: Always run pnpm test before pushing
description: Must run pnpm test and verify it passes before every git push — never push untested code
type: feedback
---

Always run `pnpm test` in the service directory and verify it passes BEFORE pushing to remote. Never push code that hasn't been tested.

**Why:** Pushed code that failed lint (`_loggerOpts` unused variable) to player-api and game-api, causing deployment failures. The destructuring fix for Fastify's `logger`/`loggerInstance` conflict also wasn't pushed for game-api, causing a crash in production.

**How to apply:** Before every `git push`, run `pnpm test` in the affected service. If tests fail, fix the issue, commit, then push. Also verify the diff against `origin/master` to confirm all intended changes are included.
