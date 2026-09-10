# Empirical examples — Burst-`ISystem` call sites

A survey of Burst-`ISystem` and ECS systems from several Unity packages, with `file:line`, to copy from. The examples cover a 2D physics binding (`Packages/<physics-package>`), a kinematic character controller (`Packages/<character-controller-package>`), and the NSprites sprite renderer (`Packages/NSprites`). Paths are relative to a Unity project root.

Find the closest call site to your task and mirror its shape — the `[BurstCompile]` placement, the group + ordering edges, the job-scheduling form, and the ECB/singleton usage.

## How each system declares `[BurstCompile] ISystem`

Two distinct postures appear, and which one a system takes is decided by whether its `OnUpdate` must call a managed API.

**Fully Burst** — `[BurstCompile]` on the struct and on every lifecycle method. The character controller's solve system is the reference:

- `Packages/<character-controller-package>/Runtime/Systems/KinematicCharacterPhysicsSolveSystem2D.cs:44` — `[BurstCompile]` on the `partial struct … : ISystem`, repeated on `OnCreate` (`:59`), `OnDestroy` (`:84`), `OnUpdate` (`:87`).
- Same posture in `StoreKinematicCharacterBodyPropertiesSystem2D.cs:28,33,43,46`, `KinematicCharacterDeferredImpulsesSystem2D.cs:41,46,55,58`.

**Non-Burst by necessity** — no `[BurstCompile]` at all, because `OnUpdate` calls managed `Unity.U2D.Physics` instance methods on the main thread. The entire physics2d fixed-step pipeline is this:

- `Packages/<physics-package>/Runtime/Systems/PhysicsWorld2DSystem.cs:37` — `public partial struct PhysicsWorld2DSystem : ISystem` with no attribute; the XML documents why (`:20-24`): the world/body calls are managed and main-thread.
- Same for `PhysicsBody2DCleanupSystem.cs:43`, `PhysicsJoint2DCreationSystem.cs:40`, `PhysicsBody2DWriteBackSystem.cs:32`. The package note states it package-wide (`Packages/<physics-package>/Documentation~/runtime-systems.md:3`).

**Non-Burst holding a managed object** — an `ISystem` struct that stores a managed object on its own system entity via the managed API. NSprites:

- `Packages/NSprites/Rendering/Systems/SpriteRenderingSystem.cs:13` — `public partial struct SpriteRenderingSystem : ISystem`, holding a managed `RenderArchetypeStorage` reached with `SystemAPI.ManagedAPI.GetComponent<RenderArchetypeStorage>(state.SystemHandle)` (`:33`) — the managed escape hatch, not Burst-legal.

## How each organizes into groups with explicit ordering

The physics2d package defines a custom public group and pins a five-system order inside it with explicit edges (no creation-order reliance):

- `Packages/<physics-package>/Runtime/Systems/Physics2DSimulationSystemGroup.cs:14-15` — `[UpdateInGroup(typeof(FixedStepSimulationSystemGroup))] public partial class Physics2DSimulationSystemGroup : ComponentSystemGroup { }`.
- All five members carry `[UpdateInGroup(typeof(Physics2DSimulationSystemGroup))]`; the edges: `PhysicsBody2DCleanupSystem.cs:41-42` (`[UpdateBefore(PhysicsWorld2DSystem)]`), `PhysicsJoint2DCreationSystem.cs:38-39` (`[UpdateBefore(PhysicsWorld2DSystem)]`), `PhysicsBody2DWriteBackSystem.cs:30-31` (`[UpdateAfter(PhysicsWorld2DSystem)]`). Resolved order: `Cleanup → JointCreation → World step → JointBreak → WriteBack` (`…/runtime-systems.md:75-82`).

The character controller orders against the physics *group*, not its internal systems, and chains its own three systems with explicit edges:

- `KinematicCharacterPhysicsSolveSystem2D.cs:41-43` — `[UpdateInGroup(typeof(FixedStepSimulationSystemGroup))]`, `[UpdateAfter(typeof(StoreKinematicCharacterBodyPropertiesSystem2D))]`, `[UpdateBefore(typeof(KinematicCharacterDeferredImpulsesSystem2D))]`.
- `StoreKinematicCharacterBodyPropertiesSystem2D.cs:26-27` and `StoreDynamicBodyDataSystem2D.cs:36-38` both `[UpdateAfter(typeof(Physics2DSimulationSystemGroup))]` so they read the just-stepped world. Note the dependency direction documented at `StoreKinematicCharacterBodyPropertiesSystem2D.cs:22-24`: the store system holds no forward reference to the solve type; the solve system references the store type, so the snapshot-before-solve edge is the solve system's to declare.

NSprites lands in the standard presentation group: `SpriteRenderingSystem.cs:11-12` — `[WorldSystemFilter(Default | Editor)] [UpdateInGroup(typeof(PresentationSystemGroup))]`.

## How each schedules jobs

**`IJobEntity` with an explicit query** — `ScheduleParallel(query, state.Dependency)`, query built in `OnCreate` to include every component the `Execute` touches:

- `KinematicCharacterPhysicsSolveSystem2D.cs:105` — `state.Dependency = job.ScheduleParallel(_characterQuery, state.Dependency)`. The query is built at `:66-74` with the inline comment recording the "query must contain all Execute components" failure; the job is the nested `[BurstCompile] [WithAll(typeof(Simulate))] partial struct KinematicCharacterPhysicsSolveJob : IJobEntity` (`:113-208`) carrying `[ReadOnly] ComponentLookup<>` and value fields.

**`IJobEntity` with no query, using the system auto-dependency** — `.ScheduleParallel()` / `.Schedule()` with no arguments; the generator uses the system's `Dependency` as both input and output:

- `StoreKinematicCharacterBodyPropertiesSystem2D.cs:49-50` — `job.ScheduleParallel();` (`StoreKinematicCharacterBodyPropertiesJob`, `:57-69`).
- `KinematicCharacterDeferredImpulsesSystem2D.cs:61-67` — `job.Schedule();`, the job built with three lookups obtained from source-generated `SystemAPI`: `GetComponentLookup<…>(false)`, `GetComponentLookup<…>(true)`, `GetBufferLookup<PhysicsBody2DCommand>(false)` (`:63-65`), then read inside `Execute` (`:90-127`).

**`IJobParallelFor` scheduled from a non-Burst system** — the physics2d write-back is a managed system scheduling one Burst job:

- `PhysicsBody2DWriteBackSystem.cs:74-81` — builds the job from three field-cached `ComponentLookup<>`s (created in `OnCreate` at `:34-42`, refreshed with `.Update(ref state)` at `:69-73`), then `job.Schedule(count, 64, state.Dependency)`. The job `BatchTransformToLocalToWorldJob` is `[BurstCompile] … : IJobParallelFor` with `[ReadOnly]`/`[NativeDisableParallelForRestriction]` lookup fields (`…/BatchTransformToLocalToWorldJob.cs:38-51`) — the package's only `[BurstCompile]` entry point.
- The dispose chain off the result handle, then write-back: `PhysicsBody2DWriteBackSystem.cs:84-87` — `handle = array.Dispose(handle)` three times, `state.Dependency = handle`.

**Fan-out then combine** — NSprites schedules one job per render archetype and combines:

- `SpriteRenderingSystem.cs:49-58` — handles collected into a `NativeArray<JobHandle>`, then `state.Dependency = JobHandle.CombineDependencies(renderArchetypeHandles)`.

## How each uses ECBs and singletons

**Inline `Allocator.Temp` ECB, played back the same frame** — when the structural changes must be live immediately:

- `PhysicsWorld2DSystem.cs:957` — `new EntityCommandBuffer(Allocator.Temp)`; records `ecb.AddComponent(entity, new PhysicsBody2D { … })` and the cleanup/smoothing adds during the body-creation loop (`:185-211`); `ecb.Playback(state.EntityManager); ecb.Dispose()` at `:1048-1049`.
- Same shape in `PhysicsJoint2DCreationSystem.cs:95,133,137-138`.

**`EntityManager` whole-query structural change** — no ECB needed for a query-wide change:

- `PhysicsBody2DCleanupSystem.cs:57` — `state.EntityManager.RemoveComponent<PhysicsBody2DCleanup>(_ghostQuery)`.

**Collect-then-apply** — accumulate into a `NativeList<Entity>`, apply after the iterator closes:

- `StoreDynamicBodyDataSystem2D.cs:58-77` — `NativeList<Entity> toAdd`, filled in a `SystemAPI.Query` foreach, then `state.EntityManager.AddComponent<StoredDynamicBodyData2D>(toAdd[i])` in a second loop; the XML notes this defers to `EndSimulationEntityCommandBufferSystem` for the structural change (`:28-30`).

**Singletons** — lazy create, read, mutate, write back; the duplicate-throws contract:

- `PhysicsWorld2DSystem.cs:794-807` — `state.EntityManager.CreateSingleton(new PhysicsWorldSingleton2D { world = … })`, then `AddBuffer<…>` the three event streams to the singleton entity (`GetSingletonEntity<PhysicsWorldSingleton2D>()` at `:798`), then `GetSingleton<…>()` to read it back.
- `PhysicsWorld2DSystem.cs:788-790` — `SystemAPI.TryGetSingleton<PhysicsWorld2DConfig>(out var cfg)` used to enforce the single-config rule: more than one config makes `TryGetSingleton` throw, surfacing the violation loudly.
- `PhysicsWorld2DSystem.cs:809-813,945-947` — the read-modify-`SetSingleton` cycle for the world handle and the fixed-step-time singleton.
- `KinematicCharacterPhysicsSolveSystem2D.cs:77,90` — `state.RequireForUpdate<PhysicsWorldSingleton2D>()` in `OnCreate`, then `SystemAPI.GetSingleton<PhysicsWorldSingleton2D>().world` inside the Burst `OnUpdate` (a singleton read crossing into a `[BurstCompile]` method, legal because `SystemAPI` is source-generated).

**Native handle on a singleton entity** — the per-world shared structure every system reaches through the singleton (the small-scale form of the chunk-pool-on-a-singleton pattern in [`command-buffers-singletons.md`](command-buffers-singletons.md)):

- `PhysicsWorldSingleton2D` carries the `PhysicsWorld` handle; three `DynamicBuffer<…>` event streams ride the same singleton entity and are cleared/refilled each step (`PhysicsWorld2DSystem.cs:798-806,834-839`).

## Field-cached `ComponentLookup` vs source-generated

Two ways to get a lookup appear in the surveyed code:

- **Explicit, field-cached** — `state.GetComponentLookup<T>(isReadOnly)` stored as a system field in `OnCreate`, refreshed with `.Update(ref state)` each `OnUpdate` before use. `PhysicsBody2DWriteBackSystem.cs:34-42` (create) and `:69-73` (update); `KinematicCharacterPhysicsSolveSystem2D.cs:81` (create) and `:92` (update).
- **Source-generated** — `SystemAPI.GetComponentLookup<T>(isReadOnly)` / `SystemAPI.GetBufferLookup<T>(isReadOnly)`, obtained inline in `OnUpdate`; the generator caches and auto-updates it. `KinematicCharacterDeferredImpulsesSystem2D.cs:63-65`; `PhysicsWorld2DSystem.cs:870,904,939`.

---

# Empirical examples — minimal Entities usage (`SlimeLatticeSyncSystem`)

A second survey covers every `: ISystem`, `: IJobEntity`, `: IJobChunk`, `EntityCommandBuffer`, and `Baker<>` in a small Unity project. It documents the minimal single-system ECS shape; the package survey above is the richer multi-package reference. Use either as a copy-from reference.

Generated by:
```bash
rg -n ': ISystem\b|: IJobEntity\b|: IJobChunk\b|EntityCommandBuffer|: Baker<' \
    Assets Packages
  | grep -E '\.cs:[0-9]+:' | grep -v '\.meta:'
```

## `ISystem` declarations

| Call site                                                                  | Pattern                                                  |
|----------------------------------------------------------------------------|----------------------------------------------------------|
| `SlimeLatticeSyncSystem.cs:7`         | `[BurstCompile] partial struct SlimeLatticeSyncSystem : ISystem` |

This is the only active `ISystem` in that project at time of writing. Other ECS systems (`AppSettingsBridgeSystem`, `GIRendererTweaksSyncSystem`) exist as commented-out scaffolding for future systems following the same pattern.

## `IJobEntity` declarations

| Call site                                                                  | Pattern                                                  |
|----------------------------------------------------------------------------|----------------------------------------------------------|
| `SlimeLatticeSyncSystem.cs:23`        | `[BurstCompile] partial struct SlimeLatticeJob : IJobEntity` |

## `IJobChunk` declarations

No active `IJobChunk` jobs in that project. The volumetrics, atmospherics, and heightfields packages all use plain `IJob` / `IJobParallelFor` (see [`docs/unity/jobs/empirical-examples.md`](../jobs/empirical-examples.md)) rather than ECS-aware variants — they operate on `NativeArray<T>` directly without entity context.

## `EntityCommandBuffer` usage

No `EntityCommandBuffer` usage appeared in the surveyed ECS code. The `SlimeLatticeSyncSystem` only reads `LocalTransform` and writes managed Unity-side state, so no entity mutations happen at runtime.

## `Baker<TAuthoring>` declarations

No active baker patterns appeared in the surveyed ECS code. That example uses runtime-spawned entities (for example, via `EntityManager.CreateEntity` from MonoBehaviour bridges) rather than authored sub-scenes.

## The reference pattern: `SlimeLatticeSyncSystem.cs`

```csharp
// Lines 7–21: ISystem with full Burst tagging.
[BurstCompile]
partial struct SlimeLatticeSyncSystem : ISystem {
    [BurstCompile] public void OnCreate(ref SystemState state) { ... }
    [BurstCompile] public void OnUpdate(ref SystemState state) {
        new SlimeLatticeJob { ... }.ScheduleParallel();   // implicit state.Dependency
    }
    [BurstCompile] public void OnDestroy(ref SystemState state) { ... }
}

// Lines 23–82: IJobEntity nested job.
[BurstCompile]
partial struct SlimeLatticeJob : IJobEntity {
    public void Execute(ref Position p, in Velocity v) { ... }
}
```

This is the canonical minimal pattern for new ECS work. Mirror this structure for any new `ISystem` + `IJobEntity` system:

1. `[BurstCompile]` on the system struct.
2. `partial struct ... : ISystem`.
3. `[BurstCompile]` on every implemented lifecycle method (`OnCreate` / `OnUpdate` / `OnDestroy` at minimum).
4. Schedule jobs via implicit `ScheduleParallel()` (no args) when state.Dependency chaining is the only dependency, or `ScheduleParallel(state.Dependency)` + `state.Dependency = ...` for explicit chaining.
5. Nested `IJobEntity` job tagged `[BurstCompile] partial struct ... : IJobEntity`.

## How to refresh this survey

```bash
rg -n ': ISystem\b|: IJobEntity\b|: IJobChunk\b|EntityCommandBuffer|: Baker<' \
    Assets Packages
```

When new ECS code lands, slot it into the right bucket above.
