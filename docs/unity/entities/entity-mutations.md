# Entity mutations — `EntityManager` vs `EntityCommandBuffer`

When to mutate entities synchronously through `EntityManager` vs deferring through `EntityCommandBuffer`.

## What "structural change" means

Adding or removing a component, creating or destroying an entity, or changing a `ISharedComponentData` value all change an entity's **archetype** — the set of components defining its memory layout. The runtime moves the entity to a new chunk, possibly creating a new archetype.

Structural changes:
- **Force a job-system sync point.** All currently-running jobs are completed before the mutation.
- **Invalidate any in-flight queries / arrays / refs.** Existing `RefRW<T>` and `NativeArray<T>` from `chunk.GetNativeArray(...)` are unsafe to read after the mutation.

`EntityManager.SetComponentData<T>(entity, value)` is **not** a structural change — it overwrites the existing slot. No sync.

## `EntityManager` — synchronous, main thread

```csharp
public void OnUpdate(ref SystemState state) {
    var em = state.EntityManager;
    var e = em.CreateEntity(typeof(Position), typeof(Velocity));
    em.SetComponentData(e, new Position { Value = float3.zero });
    em.SetComponentData(e, new Velocity { Value = math.up() });
    em.AddComponent<Active>(e);     // structural change — syncs jobs
    em.DestroyEntity(e);            // structural change — syncs jobs
}
```

Key methods (all `[StructuralChangeMethod]`-attributed where applicable):

| Method                                                              | Structural change? |
|---------------------------------------------------------------------|--------------------|
| `CreateEntity()` / `CreateEntity(EntityArchetype)` / `CreateEntity(params ComponentType[])` | yes |
| `Instantiate(Entity)`                                               | yes                |
| `DestroyEntity(Entity)` / `DestroyEntity(NativeArray<Entity>)` / `DestroyEntity(EntityQuery)` | yes |
| `AddComponent<T>(Entity)` / `AddComponent(Entity, ComponentType)` / `AddComponent<T>(EntityQuery)` | yes |
| `RemoveComponent<T>(Entity)` / `RemoveComponent(Entity, ComponentType)` | yes            |
| `SetComponentData<T>(Entity, T)`                                    | **no**             |
| `GetComponentData<T>(Entity)`                                       | **no**             |
| `SetComponentEnabled<T>(Entity, bool)` (for `IEnableableComponent`) | **no**             |

Cited at `Unity.Entities/EntityManager.cs:1579, 1644, 2053, 2188, 27–100`.

### When `EntityManager` is the right pick

- One-off setup in `OnCreate` (system creates singleton entities, etc.).
- Editor / authoring-time mutations that won't run from a job.
- Single mutation per frame where the sync cost is negligible (e.g. responding to a UI button).

### When it's wrong

- Mutating from inside an `IJobEntity` / `IJobChunk` `Execute` — `EntityManager` is **not job-safe**, the job system will refuse it (or in release builds, race).
- Mutating tens or hundreds of entities per frame — each call is a sync point. Use `EntityCommandBuffer` instead.

## `EntityCommandBuffer` — deferred

```csharp
[BurstCompile]
public void OnUpdate(ref SystemState state) {
    var ecbSingleton = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>();
    var ecb = ecbSingleton.CreateCommandBuffer(state.WorldUnmanaged);

    foreach (var (transform, entity) in
             SystemAPI.Query<RefRO<LocalTransform>>().WithEntityAccess()) {
        if (transform.ValueRO.Position.y < -100f)
            ecb.DestroyEntity(entity);   // QUEUED, not executed yet
    }
    // No sync here. ecb plays back when EndSimulationECBSystem.OnUpdate runs.
}
```

`EntityCommandBuffer` records mutations into a flat buffer. Playback happens later, on the main thread, at a controlled point in the frame.

### Standard `EntityCommandBufferSystem`s

Each pre-defined `EntityCommandBufferSystem` has a `Singleton` component you fetch via `SystemAPI.GetSingleton<...>` to get an ECB:

| System                                            | When it plays back                            |
|---------------------------------------------------|-----------------------------------------------|
| `BeginInitializationEntityCommandBufferSystem`    | Start of `InitializationSystemGroup`          |
| `EndInitializationEntityCommandBufferSystem`      | End of `InitializationSystemGroup`            |
| `BeginSimulationEntityCommandBufferSystem`        | Start of `SimulationSystemGroup`              |
| `EndSimulationEntityCommandBufferSystem`          | End of `SimulationSystemGroup`                |
| `BeginPresentationEntityCommandBufferSystem`      | Start of `PresentationSystemGroup`            |
| `EndPresentationEntityCommandBufferSystem`        | End of `PresentationSystemGroup`              |
| `EndSimulationEntityCommandBufferSystem` (most common) | After all simulation systems finish      |

Cited `Unity.Entities/DefaultWorld.cs:8–148`.

Pick by **when you need the mutation visible**:
- Want it visible to the next system this frame? → `Begin*` of the appropriate group.
- Happy to wait until the end? → `End*`.
- Most "spawn / destroy" patterns: `EndSimulationECBSystem.Singleton`.

### `AsParallelWriter` for jobs

Inside an `IJobEntity` / `IJobChunk` `Execute`, you cannot use the plain `EntityCommandBuffer` (it's main-thread-only). Instead, get a `EntityCommandBuffer.ParallelWriter` and pass it as a job field:

```csharp
[BurstCompile]
partial struct DestroyOldJob : IJobEntity {
    public EntityCommandBuffer.ParallelWriter Ecb;
    public float CullY;

    public void Execute([ChunkIndexInQuery] int sortKey, Entity entity, in LocalTransform t) {
        if (t.Position.y < CullY)
            Ecb.DestroyEntity(sortKey, entity);
    }
}

// In OnUpdate:
var ecbSingleton = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>();
var ecb = ecbSingleton.CreateCommandBuffer(state.WorldUnmanaged);
state.Dependency = new DestroyOldJob {
    Ecb = ecb.AsParallelWriter(),
    CullY = -100f,
}.ScheduleParallel(state.Dependency);
```

**Every `ParallelWriter` mutation method takes a `sortKey: int` first parameter.** This determines the playback order — playback is deterministic given the same sort keys, even across parallel writers. **`[ChunkIndexInQuery]` is the canonical source for the sort key** (see [`query-and-iteration.md`](query-and-iteration.md) §"`IJobEntity` parameter attributes").

### Key ECB methods

`EntityCommandBuffer` methods mirror `EntityManager` but defer execution:

```csharp
ecb.CreateEntity(EntityArchetype archetype) -> Entity;     // pseudo-entity placeholder
ecb.Instantiate(Entity src) -> Entity;
ecb.DestroyEntity(Entity entity);
ecb.AddComponent<T>(Entity entity);
ecb.AddComponent<T>(Entity entity, T component);
ecb.SetComponent<T>(Entity entity, T component);
ecb.RemoveComponent<T>(Entity entity);
ecb.SetEnabled(Entity entity, bool enabled);
ecb.AppendToBuffer<T>(Entity entity, T element);
```

The `Entity` returned by `CreateEntity` / `Instantiate` is a **placeholder** — it points at the deferred-creation slot. Subsequent `ecb.SetComponent(placeholder, ...)` calls in the same buffer resolve to the real entity at playback time.

### Manual ECB lifetime

If you need fine-grained control (not using a standard `EntityCommandBufferSystem`):

```csharp
var ecb = new EntityCommandBuffer(Allocator.TempJob);

// ... record commands, possibly via .AsParallelWriter() into jobs ...

state.Dependency.Complete();   // ensure all writers finished
ecb.Playback(state.EntityManager);
ecb.Dispose();
```

Project canon: avoid manual lifetime management when a standard `EndSimulationECBSystem.Singleton` would do.

## Quick decision flow

```
Need to mutate entities from inside a parallel job?
├── Yes → ECB.AsParallelWriter() + sortKey from [ChunkIndexInQuery]
└── No  → Mutating one or two entities, sync OK?
         ├── Yes → state.EntityManager directly
         └── No  → ECB from EndSimulationECBSystem.Singleton (or appropriate group)
```

## Source citations

| Symbol                                       | File                                                  |
|----------------------------------------------|-------------------------------------------------------|
| `EntityManager` overview                     | `Unity.Entities/EntityManager.cs:27–100`              |
| `EntityManager.AddComponent<T>`              | `Unity.Entities/EntityManager.cs:1644`                |
| `EntityManager.RemoveComponent<T>`           | `Unity.Entities/EntityManager.cs:2188`                |
| `EntityCommandBuffer`                        | `Unity.Entities/EntityCommandBuffer.cs`               |
| Default ECB systems                          | `Unity.Entities/DefaultWorld.cs:8–148`                |
| `EntityCommandBuffer.ParallelWriter`         | `Unity.Entities/EntityCommandBuffer.cs` (search `struct ParallelWriter`) |
