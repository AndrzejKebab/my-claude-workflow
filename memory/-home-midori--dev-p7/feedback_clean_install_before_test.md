---
name: Clean install before testing
description: Always run pnpm install --frozen-lockfile after resetting lockfiles to avoid stale node_modules
type: feedback
---

After resetting pnpm-lock.yaml with git checkout, ALWAYS run `pnpm install --frozen-lockfile` (or `rm -rf node_modules && pnpm install --frozen-lockfile`) before running tests. Otherwise node_modules retains packages from the previous install and tests pass locally but fail in CI.

**Why:** We shipped a broken adapter MR because stale node_modules had a newer library version with different type signatures. CI does a clean install and got the real published types, which didn't have the fields our code referenced.

**How to apply:** Any time you reset or modify pnpm-lock.yaml or package.json, re-sync node_modules before testing. Prefer `--frozen-lockfile` to match CI behavior.
