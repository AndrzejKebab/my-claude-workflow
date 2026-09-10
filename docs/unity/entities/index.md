# Unity.Entities — Burst ISystem / ECS systems

Canonical local reference for "what does this `ISystem` / `IJobEntity` / `EntityCommandBuffer` API actually do", "how do I chain dependencies across an ECS system", and "how do I write, order, and schedule Burst-compiled systems". Read it for writing, ordering, and scheduling Burst `ISystem`s.

## Package root and version

- Use the installed **`com.unity.entities`** package at `Library/PackageCache/com.unity.entities@<version>/`. Source-shipped sub-assemblies of interest:
  - `Unity.Entities/` — core: `ISystem`, `SystemBase`, `EntityManager`, `EntityCommandBuffer`, `IJobEntity`, `IJobChunk`, `EntityQuery`.
  - `Unity.Entities.Hybrid/Baking/` — `IBaker`, `Baker<TAuthoring>`, baking systems.
  - `Unity.Transforms/` — `LocalTransform`, `LocalToWorld`, `Parent`, `Child`, `TransformSystemGroup`.
  - `Unity.Scenes/` — sub-scene loading (out of scope for this docset).

Verify all `file:line` citations against the package version installed in the current Unity project.

## Documents

### Writing and ordering systems

- [`systems.md`](systems.md) — **start here for Burst systems**. `ISystem` (unmanaged) vs `SystemBase` (managed) and why ISystem is the Burst form; `[BurstCompile]` placement on the type and on `OnCreate`/`OnUpdate`/`OnDestroy`; the `ref SystemState` parameter; which `SystemAPI` members are usable inside a Burst `OnUpdate` and the fact that they are all source-generated; `state.Dependency` chaining; scheduling `IJobEntity`/`IJobChunk` from a system; the boundary of what is Burst-legal in `OnUpdate`.

- [`system-types.md`](system-types.md) — `ISystem` (struct, Burst-friendly) vs `SystemBase` (class, managed). Lifecycle: `OnCreate` / `OnUpdate` / `OnDestroy` / `OnStartRunning` / `OnStopRunning`. `[UpdateInGroup]` / `[UpdateBefore]` / `[UpdateAfter]`. The standard groups: `InitializationSystemGroup` / `SimulationSystemGroup` / `PresentationSystemGroup`. The "tag the struct AND tag every lifecycle method" Burst pattern.

- [`system-groups.md`](system-groups.md) — `ComponentSystemGroup`; the ordering attributes `[UpdateInGroup]`, `[UpdateBefore]`/`[UpdateAfter]`, `[CreateAfter]`/`[CreateBefore]`; defining a custom group; the standard groups (Initialization / Simulation / Presentation), the fixed-step group, and their built-in `EntityCommandBufferSystem`s; explicit ordering edges as the binding idiom over implicit creation-order dependence.

### Querying, jobs, and mutations

- [`query-and-iteration.md`](query-and-iteration.md) — `EntityQuery` (`state.GetEntityQuery`, `SystemAPI.QueryBuilder`), `SystemAPI.Query<T1,T2,...>` codegen iteration, **`IJobEntity` schedule overloads** (the Entities-side equivalent of [`docs/unity/jobs/scheduling-overloads.md`](../jobs/scheduling-overloads.md) — covers all the parameter names), `IJobChunk` for chunk-level access, `[WithAll]` / `[WithAny]` / `[WithNone]` / `[WithChangeFilter]`, the `[EntityIndexInQuery]` family.

- [`jobs-on-systems.md`](jobs-on-systems.md) — `state.Dependency` chaining. The "you must `state.Dependency = job.Schedule(state.Dependency)` after every schedule" rule. `[BurstCompile]` on `ISystem` plus `[BurstCompile]` on each method. Implicit vs explicit dependency tracking on `SystemBase` vs `ISystem`. Why `IJobChunk` does not auto-track.

- [`entity-mutations.md`](entity-mutations.md) — `EntityManager` (immediate, structural-change-on-every-call) vs `EntityCommandBuffer` (deferred, parallel-safe via `AsParallelWriter`). The standard `EntityCommandBufferSystem`s (`Begin`/`EndInitialization`, `Begin`/`EndSimulation`, `Begin`/`EndPresentation`). When each is the right insertion point.

- [`command-buffers-singletons.md`](command-buffers-singletons.md) — `EntityCommandBuffer` Burst-compatible usage and `EntityCommandBuffer.ParallelWriter`; obtaining an ECB from the standard ECB-system singletons; structural-change patterns; singletons (`GetSingleton`/`SetSingleton`/`TryGetSingleton`/`CreateSingleton`); holding a native-collection-bearing struct (a chunk pool) on a singleton component so a Burst system can reach it; blob assets in one paragraph.

### Baking, transforms, and advanced idioms

- [`baking.md`](baking.md) — `IBaker` / `Baker<TAuthoring>`. `GetEntity(TransformUsageFlags)`, `AddComponent`, `DependsOn`. The component types: `IComponentData`, `ISharedComponentData`, `IBufferElementData`, `IEnableableComponent`, `ICleanupComponentData`. `TransformUsageFlags` (None / Renderable / Dynamic / WorldSpace / NonUniformScale).

- [`transforms-and-hierarchy.md`](transforms-and-hierarchy.md) — `LocalTransform` (Position/Rotation/Scale), `LocalToWorld` (read-only matrix updated by `LocalToWorldSystem`), `Parent`, `Child` (cleanup buffer), `PreviousParent`. `TransformSystemGroup` ordering and when LocalToWorld is fresh.

- [`burst-isystem-patterns.md`](burst-isystem-patterns.md) — the Burst-`ISystem` patterns a Burst-throughout engine leans on: the unmanaged-generic-struct seam (`void Op<T>(in T impl) where T : unmanaged, I...`) as the Burst substitute for a managed interface, the entry-point-only `[BurstCompile]` rule applied to system methods, and the failure modes that pass EditMode and break at AOT. *(written by a sibling agent)*

- [`latios-idioms.md`](latios-idioms.md) — idioms drawn from the Latios Framework and regarded DOTS packages for structuring a large system graph. *(written by a sibling agent)*

## Reading order for "I am writing a new Burst ISystem"

1. [`systems.md`](systems.md) / [`system-types.md`](system-types.md) — the `ISystem` shell, `[BurstCompile]` placement, the `ref SystemState` surface, and what `SystemAPI` you may call inside Burst; pick `ISystem` (default) or `SystemBase` (only if you need managed types in `OnUpdate`).
2. [`query-and-iteration.md`](query-and-iteration.md) — pick `IJobEntity` (default) or `IJobChunk` (when you need chunk metadata or the enabled-mask).
3. [`system-groups.md`](system-groups.md) — pick the group it lives in and the explicit `[UpdateBefore]`/`[UpdateAfter]` edges that fix its order.
4. [`jobs-on-systems.md`](jobs-on-systems.md) — wire `state.Dependency` correctly.
5. [`command-buffers-singletons.md`](command-buffers-singletons.md) / [`entity-mutations.md`](entity-mutations.md) — if it makes structural changes (create/destroy/add/remove), the ECB pattern; if it reads or publishes shared state, the singleton pattern.
6. [`burst-isystem-patterns.md`](burst-isystem-patterns.md) — apply the unmanaged-generic seam where a behavior must be swappable on the Burst path, and confirm the `[BurstCompile]` surface against the entry-point-only rule.

## Reading order for the "deferred mutation" pattern

1. [`entity-mutations.md`](entity-mutations.md) §"EntityCommandBuffer".
2. Pick the right `EntityCommandBufferSystem` based on when you want playback (start-of-frame? after simulation? before render?).

## What this docset deliberately does NOT cover

- **Aspects** (`IAspect`, generated property accessors) — newer pattern, not yet adopted. Add when needed.
- **Sub-scenes** and the streaming pipeline — see `Unity.Scenes/`. Covered separately if/when a project starts using them.
- **Netcode for Entities**, **Physics** — separate packages, separate docsets.
- **Entity-aware job *scheduling overloads*** (the `IJobChunk`/`IJobEntity` `Schedule*` parameter tables) beyond what a system's `OnUpdate` needs — the plain Unity.Jobs overload tables are in [`../jobs/`](../jobs/index.md); the entity-job interfaces themselves are covered in [`systems.md`](systems.md) and [`query-and-iteration.md`](query-and-iteration.md).
- **Legacy `Entities.ForEach` / `Job.WithCode` / `JobComponentSystem`** — deprecated in 1.x, superseded by `ISystem` + `SystemAPI.Query`; mentioned in `query-and-iteration.md` only as a "do not write new code in this style" note.
- **Burst attribute internals** (`FloatMode`, `FunctionPointer<T>`, intrinsics) — see [`../burst/`](../burst/index.md). This docset only states where `[BurstCompile]` goes on a system.
- **`com.unity.entities.graphics` / Hybrid Renderer** internals — NSprites sprite rendering is cited as an example but not documented as engine canon.
- **Baking deep internals beyond [`baking.md`](baking.md)** — for the asset-serialization rules that decide whether a baker's authoring `MonoBehaviour` resolves at all, see [`../authoring/`](../authoring/index.md).

## Version note

The captures span entities `1.x` (Unity 6.3) and `6.5.0` (editor `6000.6.0a6`). Every signature was read from the cited package's source; where a member could not be verified against the installed source it is flagged inline. Entities 6.5 is a higher minor than the `6000.0` baseline; the broader version-drift caveat is in [`../index.md`](../index.md) "What is NOT covered here".
