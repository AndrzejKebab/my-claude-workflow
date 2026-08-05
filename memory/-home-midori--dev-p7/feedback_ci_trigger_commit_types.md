---
name: CI rebuilds only on feat/fix commits
description: In P7 service repos, only feat: and fix: commit types trigger a new CI rebuild/release — other types (ci, chore, docs, test, refactor) do not advance the pipeline.
type: feedback
originSessionId: 955c4723-6c10-4910-8513-321fb0ac44e0
---
When committing to a P7 service repo that uses semantic-release (game-api confirmed; likely all services with `"release": "semantic-release"` in package.json), only `feat:` and `fix:` commit types trigger a CI rebuild and new release. Other conventional-commit types — `ci:`, `chore:`, `docs:`, `test:`, `refactor:`, `style:`, `perf:`, `build:`, `revert:` — will pass lint and commit successfully but **will not** trigger a rebuild of the deployed artifact.

**Why:** user flagged this after I committed a `ci/values.env.yaml` change to game-api with `ci(values): ...` — the CI pipeline did not pick it up for rebuild. Infra-looking changes (CI placeholders, helm values, env plumbing) must still be labeled `feat:` or `fix:` if you want the deployed pod to receive them on the next release cycle.

**How to apply:**
- If a commit introduces a change that must reach deployed pods (e.g. adding env-var placeholders to `ci/values.env.yaml`, wiring new config through helm), use `feat:` or `fix:` even if the work is infra-flavored.
- Prefer **`fix:` for small changes** — patching missing env keys, correcting a config placeholder, small plumbing repairs. These bump the patch version.
- Reserve **`feat:`** for genuinely new capability — new endpoints, new features, schema additions. These bump the minor version.
- When uncertain, lean toward `fix:` — over-reaching with `feat:` inflates the minor version unnecessarily.
- Test/doc/chore commits that do not need a release (integration tests that run in CI but don't ship, internal docs) can keep their `test:` / `docs:` / `chore:` type — no rebuild is desired.
