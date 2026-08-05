---
name: JS hot reload TypeError bug (FIXED)
description: "TypeError: not a function" after system reload — was caused by stale QuickJS module cache. Fixed 2026-03-16 with versioned filenames.
type: project
---

**Fixed 2026-03-16.** Root causes and fixes:

1. **Stale module cache:** `JsSystemRunner.ReloadSystem` called `LoadSystem` which guarded with `HasScript()` — the old module namespace was found, skipping re-evaluation. Fix: `ReloadSystem` now calls `m_Vm.ReloadScript()` directly.

2. **QuickJS module dedup:** Re-evaluating the same filename appends a second entry but `import` resolves to the first (old) one. Fix: `JsRuntimeManager.ReloadScript` appends `?v=N` to filenames, creating unique cache keys. `JsModuleLoader.Normalize` and `ReadFile` strip the version suffix for filesystem resolution.

3. **One-shot TypeScript compilation:** `TscCompiler` ran only on domain reload. Originally fixed with `TscWatchService` (persistent `tsc --watch`), later replaced by synchronous `TscCompiler` invocations — no background watcher process.

**Verified by:** E2E stress tests in `UnityJS.Entities.EditModeTests` (EditMode, uses EnterPlayMode/ExitPlayMode) covering sequential mutations, concurrent mutations, rapid burst, and syntax error recovery.
