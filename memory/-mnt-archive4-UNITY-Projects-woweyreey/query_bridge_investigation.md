---
name: JS EntityQuery Bridge Investigation
description: Deep debugging of why EntityQuery in JsQueryBridge returns 0 for game components when called from P/Invoke callbacks. Key findings and workaround.
type: project
---

## Root Cause: EntityQuery created inside P/Invoke callbacks is broken in Unity 6 DOTS

When `_nativeQuery(...)` is called from JS (via QuickJS P/Invoke callback → C# `JsQueryBridge.Query`),
`EntityManager.CreateEntityQuery(desc)` returns an EntityQuery that never matches any archetypes.
This affects ALL component queries, not just game components.

**Why:** The system runner caches the first EntityQuery created for each component combination.
On the first call (before any entities exist), the query is created inside the P/Invoke callback.
Due to a Unity 6 DOTS context issue, this query is permanently broken — it never finds entities even after they're created.

**Workaround implemented:** `FlushPendingQueries` — when the callback first encounters a component combination,
it records it as "pending" and returns empty. On the next frame, `JsSystemRunner.OnUpdate` calls
`FlushPendingQueries(EntityManager)` which creates the query from the system context (outside P/Invoke).
Additionally, ALL cached queries are recreated from system context every frame via `GetEntityQueryDesc() + Dispose + CreateEntityQuery`.

**Current status:** The query now finds entities. But `setAll` (batch writeback) doesn't persist changes.
Per-entity `set()` API DOES work. The batch path reads correctly (`getAll`) but the writeback via `setAll` silently fails.

**Why:** Unknown. The benchmark's `BatchIterateReadWrite` uses the same batch API with BenchComp components and works.
Likely cause: the `ComponentLookup<T>` used by `setAll` is obtained during `UpdateAllLookups` from `state.GetComponentLookup<T>()`.
This lookup might have a safety handle that's invalidated when used from P/Invoke.
The per-entity `set()` works because it writes directly via `s_lookup.Data[entity] = comp` which bypasses batch array operations.

**How to apply:** When investigating further, focus on:
1. Whether `setAll` is actually called (add logging in generated code via source generator)
2. Whether the Float32Array passed to `setAll` has the modified values
3. Whether `s_lookup.Data[entity] = comp` inside `setAll` actually writes
4. Compare the ComponentLookup safety handles between batch and per-entity paths
