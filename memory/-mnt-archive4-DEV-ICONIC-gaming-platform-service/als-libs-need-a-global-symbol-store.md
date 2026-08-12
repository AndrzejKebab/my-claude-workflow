---
name: als-libs-need-a-global-symbol-store
description: "A workspace lib holding AsyncLocalStorage must key it off Symbol.for — injectWorkspacePackages makes hard copies, so a module-level `new` is two stores"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4825f98f-e566-436a-a288-8c230c252aaa
  modified: 2026-08-10T22:37:26.946Z
---

`pnpm-workspace.yaml` sets `injectWorkspacePackages: true`. A workspace library reached *through
another* library (`@gps/failure-injection` via `@gps/http-client`, which every service depends on)
is installed as a **hard copy** under its own `.pnpm` path, not a symlink to `libs/`. Two copies are
two module instances, so a module-level `const storage = new AsyncLocalStorage()` becomes two
stores: the service's plugin arms one, the http client reads the other and finds nothing.

Key the store off the cross-instance registry instead:

```ts
const CHANNEL = Symbol.for("@gps/failure-injection#channel")
const host = globalThis as { [CHANNEL]?: AsyncLocalStorage<T> }
host[CHANNEL] ??= new AsyncLocalStorage<T>()
const storage = host[CHANNEL]
```

**The injected copy is also a snapshot of `dist/` taken at install time.** Rebuilding `libs/<x>/dist`
does not update it, and `pnpm install` says "Already up to date". To refresh:
`pnpm turbo run build && rm node_modules/.pnpm-workspace-state-v1.json && pnpm install`, then restart
the stack's containers. Related: [[injected-workspace-libs-need-a-rebuilt-node-modules]].

**Why:** the failure is silent and tier-shaped — every in-process test stayed green while the
`x-failure` header quietly stopped crossing the hop, and only the integration tier could see it.

**How to apply:** any new shared lib carrying request-scoped state through `AsyncLocalStorage` gets
the `Symbol.for` store and a test that imports a second module instance (`import("../src/x.ts?copy")`)
and asserts they share it.
