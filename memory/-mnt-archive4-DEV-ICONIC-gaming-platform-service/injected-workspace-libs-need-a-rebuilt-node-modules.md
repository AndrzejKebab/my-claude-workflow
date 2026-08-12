---
name: injected-workspace-libs-need-a-rebuilt-node-modules
description: "A fresh worktree fails every suite with ERR_MODULE_NOT_FOUND on a @gps lib's dist; only rebuilding node_modules repairs it"
metadata: 
  node_type: memory
  type: project
  originSessionId: f6c0487d-7e3a-4620-80e4-44de59385fb9
  modified: 2026-08-11T19:44:57.330Z
---

`pnpm-workspace.yaml` sets `injectWorkspacePackages: true`, so a `workspace:` library is **hard-copied**
into `node_modules/.pnpm/@gps+<lib>@file+libs+<lib>/` at install time. A worktree installed before its
libs were built carries a copy with `src/` and no `dist/`, and every suite that imports it dies with
`ERR_MODULE_NOT_FOUND … /dist/index.mjs` — observed taking all 20 `test:games` files down at once, and
reading exactly like a broken branch.

**Why:** absence of `dist` in the injected copy, while `libs/<lib>/dist` on disk is fine. Check with
`ls node_modules/.pnpm/@gps+*@file+libs+*/node_modules/@gps/*/dist`.

**How to apply:** try `pnpm turbo run build --force` first — turbo reports a *cache hit* for a lib
whose `dist` is absent and restores nothing, so an ordinary `pnpm turbo run build` says "18
successful" over missing output; `--force` rebuilds and writes it, and that alone repaired a whole
worktree (all local, unit and integration tiers) in seconds. Watch for the second layer: an injected
copy can also be missing a *transitive* `@gps` dep's dist, which `cp -r libs/<lib>/dist <injected>/`
patches directly.

When the injected copies themselves are stale rather than merely unbuilt, nothing short of a
reinstall helps: `pnpm install`, `pnpm install --force`, deleting the injected directories, and
removing `node_modules/.modules.yaml` all answer "Already up to date" — the lockfile check
short-circuits before re-injection. Then the fix is
`rm -rf node_modules apps/*/node_modules libs/*/node_modules configs/*/node_modules tests/*/node_modules`
then `pnpm install` (~seconds, everything is in the store). Build first if `libs/*/dist` is also
missing, because injection copies whatever is there at install time.

**Checking out an older tree makes them stale every time** — a history rewrite, a `git bisect`, a
`reset --hard` back to an earlier commit. `turbo build` rewrites `libs/<lib>/dist`, but nothing
rewrites the injected copy, so the app resolves the *newer* build against *older* source. Observed:
squashing this branch, launcher-service refused to boot with
`FST_ERR_SCH_SERIALIZATION_BUILD … response schemas should be nested under a valid status code`,
because a route named `EErrorCode.ROUND_NOT_PLAYABLE` that the injected `@gps/common-errors` no
longer had, so `statusOf` returned `undefined` and keyed a schema by it. It reads as a defect in the
commit under test and is not one.

Once node_modules is sound, the cheap repair per checkout is `turbo build` then copy each
`libs/<lib>/dist` over `node_modules/.pnpm/@gps+<lib>@file+libs+<lib>/node_modules/@gps/<lib>/dist`
— seconds, and it is exactly what injection does. Reserve the full reinstall for a broken tree.

Same shape as [[stale-worktree-brokers]]: an artefact older than the thing that describes it,
invisible until an unrelated red. Related: [[no-local-typecheck-gate]].
