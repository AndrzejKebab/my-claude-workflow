# `EntityQuery`, `SystemAPI.Query`, `IJobEntity`, `IJobChunk`

The four iteration shapes ECS supports, in increasing order of control. Pick the shape that matches what you actually need.

## 1. `SystemAPI.Query<...>()` — main-thread codegen iteration

```csharp
foreach (var (transform, velocity) in
         SystemAPI.Query<RefRW<LocalTransform>, RefRO<Velocity>>()
                  .WithAll<Active>()
                  .WithChangeFilter<Velocity>()) {
    transform.ValueRW.Position += velocity.ValueRO.Value * dt;
}
```

- Roslyn-generated codegen. Lowers to a tight `IJobChunk`-equivalent loop on the main thread.
- **No worker threads, no Burst** — runs in the calling system's `OnUpdate`.
- Use for cheap per-entity work where job overhead would dominate.
- The `Ref{RW,RO}<T>` wrappers are the sanctioned read-only / read-write tokens.

Modifiers (chain before the `foreach`):
- `.WithAll<C1, C2>()` / `.WithAny<C1, C2>()` / `.WithNone<C1>()` / `.WithAbsent<C1>()` — query composition.
- `.WithChangeFilter<C>()` — only iterate chunks where `C` changed since this system's last update.
- `.WithSharedComponentFilter(value)` — restrict to chunks with that shared-component value.
- `.WithEntityAccess()` — yields the `Entity` handle as an extra tuple element.

## 2. `IJobEntity` — codegen-to-`IJobChunk`, parallel-friendly

```csharp
[BurstCompile]
partial struct AdvanceJob : IJobEntity {
    public float Dt;
    public void Execute(ref LocalTransform t, in Velocity v) {
        t.Position += v.Value * Dt;
    }
}
```

- Codegen emits an `IJobChunk` wrapper that calls `Execute` once per matching entity.
- The Roslyn analyser infers the query from the `Execute` parameter list (one of each component type → `WithAll`).
- `ref` parameters → write access. `in` parameters → read-only access.

### `IJobEntity` schedule overloads

```csharp
// Schedule (sequential, single worker), implicit query, implicit dependency:
new AdvanceJob { Dt = dt }.Schedule();
new AdvanceJob { Dt = dt }.ScheduleByRef();

// Schedule with explicit dependency:
new AdvanceJob { Dt = dt }.Schedule(state.Dependency);
new AdvanceJob { Dt = dt }.ScheduleByRef(state.Dependency);

// Schedule on a specific query:
new AdvanceJob { Dt = dt }.Schedule(myQuery);
new AdvanceJob { Dt = dt }.Schedule(myQuery, state.Dependency);

// Parallel variants — same shape, replace Schedule with ScheduleParallel:
new AdvanceJob { Dt = dt }.ScheduleParallel();
new AdvanceJob { Dt = dt }.ScheduleParallel(state.Dependency);
new AdvanceJob { Dt = dt }.ScheduleParallel(myQuery);
new AdvanceJob { Dt = dt }.ScheduleParallel(myQuery, state.Dependency);
new AdvanceJob { Dt = dt }.ScheduleParallelByRef();
new AdvanceJob { Dt = dt }.ScheduleParallelByRef(state.Dependency);
// ... etc.

// Synchronous (main thread, completes deps):
new AdvanceJob { Dt = dt }.Run();
new AdvanceJob { Dt = dt }.Run(myQuery);
```

**Named arguments — there are none.** All `IJobEntity` Schedule overloads use positional arguments. `query` and `dependsOn` are the parameter names but the convention is to pass positionally because the codegen-generated extension method names are stable enough that ambiguity does not arise.

The codegen-generated `IJobEntityExtensions` class is **synthesized at compile time** under `Library/Bee/...` — it doesn't appear in the package source. To inspect, use SharpTools `SharpTool_ViewDefinition Unity.Entities.IJobEntityExtensions.Schedule` or build the project and decompile the `Assembly-CSharp.dll` it produces.

Cited at `Library/PackageCache/com.unity.entities@8b72e8a7d7d1/Unity.Entities/IJobEntity.cs:11–544` (interface declaration + codegen contract).

### `IJobEntity` parameter attributes

The `Execute` method can take more than just component refs. The codegen recognises:

```csharp
public void Execute(
    [EntityIndexInQuery]  int   queryIndex,    // packed index across all chunks  — expensive
    [EntityIndexInChunk]  int   chunkIndex,    // 0..127 within the current chunk — cheap
    [ChunkIndexInQuery]   int   chunkIdx,      // chunk index — cheap, deterministic sort key
    Entity entity,                              // the entity handle itself
    ref MyComponent c1,                         // read-write
    in  ReadOnlyComponent c2,                   // read-only
    EnabledRefRW<MyEnableable> enabled          // read-write to enable-state of an IEnableableComponent
)
```

Project canon: prefer `[ChunkIndexInQuery]` over `[EntityIndexInQuery]` when you only need a deterministic sort key (e.g. for `EntityCommandBuffer.ParallelWriter`'s `sortKey`) — chunk indices are O(chunks) to compute, query indices are O(entities).

### `IJobEntity` struct-level attributes

```csharp
[WithAll(typeof(Active))]
[WithChangeFilter(typeof(Velocity))]
partial struct AdvanceJob : IJobEntity { ... }
```

- `[WithAll(typeof(C1), typeof(C2))]` — required-all.
- `[WithAny(typeof(C1), typeof(C2))]` — at-least-one.
- `[WithNone(typeof(C1))]` — required-absent.
- `[WithAbsent(typeof(C1))]` — synonym for `WithNone`.
- `[WithDisabled(typeof(C1))]` — only entities where the `IEnableableComponent` is disabled.
- `[WithPresent(typeof(C1))]` — include the component regardless of enabled state.
- `[WithChangeFilter(typeof(C1))]` — only chunks where `C1` changed.
- `[WithOptions(EntityQueryOptions.IgnoreComponentEnabledState)]` — query-option override.

These layer on top of the parameter-inferred `WithAll`. If `Execute` takes `ref Position`, the query implicitly requires `Position`.

### Optional chunk callbacks via `IJobEntityChunkBeginEnd`

```csharp
partial struct MyJob : IJobEntity, IJobEntityChunkBeginEnd {
    public bool OnChunkBegin(in ArchetypeChunk chunk, int unfilteredChunkIndex,
                              bool useEnabledMask, in v128 chunkEnabledMask) {
        return chunk.Count > 0;   // return false to skip the chunk entirely
    }
    public void OnChunkEnd(in ArchetypeChunk chunk, int unfilteredChunkIndex,
                            bool useEnabledMask, in v128 chunkEnabledMask, bool chunkWasExecuted) { }
    public void Execute(ref Position p) { ... }
}
```

Use when per-chunk setup/teardown is needed (e.g. compute a chunk-wide constant before processing entities).

## 3. `IJobChunk` — full chunk-level control

```csharp
[BurstCompile]
struct ChunkJob : IJobChunk {
    public ComponentTypeHandle<Position>     PositionTH;
    [ReadOnly] public ComponentTypeHandle<Velocity> VelocityTH;
    public float Dt;

    public void Execute(in ArchetypeChunk chunk, int unfilteredChunkIndex,
                         bool useEnabledMask, in v128 chunkEnabledMask) {
        var positions = chunk.GetNativeArray(ref PositionTH);
        var velocities = chunk.GetNativeArray(ref VelocityTH);
        var enumerator = new ChunkEntityEnumerator(useEnabledMask, chunkEnabledMask, chunk.Count);
        while (enumerator.NextEntityIndex(out int i)) {
            positions[i] = new Position { Value = positions[i].Value + velocities[i].Value * Dt };
        }
    }
}

// Schedule:
state.Dependency = new ChunkJob {
    PositionTH = state.GetComponentTypeHandle<Position>(false),
    VelocityTH = state.GetComponentTypeHandle<Velocity>(true),
    Dt = SystemAPI.Time.DeltaTime,
}.ScheduleParallel(myQuery, state.Dependency);
```

Cited at `Unity.Entities/IJobChunk.cs:43–231`.

### `IJobChunk` schedule overloads

```csharp
public static JobHandle Schedule        <T>(this T jobData,     EntityQuery query, JobHandle dependsOn) where T : struct, IJobChunk;
public static JobHandle ScheduleByRef   <T>(this ref T jobData, EntityQuery query, JobHandle dependsOn);
public static JobHandle ScheduleParallel<T>(this T jobData,     EntityQuery query, JobHandle dependsOn);
public static JobHandle ScheduleParallelByRef<T>(this ref T jobData, EntityQuery query, JobHandle dependsOn);
public static void      Run            <T>(this T jobData,     EntityQuery query);
public static void      RunByRef       <T>(this ref T jobData, EntityQuery query);
```

**Named args**: `query`, `dependsOn`. Both are required for `Schedule*` (no defaults); only `query` for `Run*`.

### `chunkEnabledMask` and `ChunkEntityEnumerator`

`IJobChunk.Execute` receives a `v128` bitmask (from `Unity.Burst.Intrinsics`) where bit N indicates entity N in the chunk is enabled-and-matches. `useEnabledMask` is `true` if the query has any `IEnableableComponent` filter. Iterate via:

```csharp
var enumerator = new ChunkEntityEnumerator(useEnabledMask, chunkEnabledMask, chunk.Count);
while (enumerator.NextEntityIndex(out int i)) { /* ... */ }
```

If `useEnabledMask == false`, all `chunk.Count` entities match — the mask is undefined.

## 4. `EntityQuery` directly

When you need to query entity counts, gather entity arrays manually, or set filters that the codegen patterns don't expose:

```csharp
[BurstCompile]
public void OnCreate(ref SystemState state) {
    _activeEnemies = state.GetEntityQuery(
        ComponentType.ReadOnly<EnemyTag>(),
        ComponentType.ReadWrite<Position>()
    );
}

[BurstCompile]
public void OnUpdate(ref SystemState state) {
    int count = _activeEnemies.CalculateEntityCount();
    var entities = _activeEnemies.ToEntityArray(Allocator.TempJob);
    // ... use entities ...
    entities.Dispose();
}
```

Key methods:
- `CalculateEntityCount()` / `IsEmpty` / `IsEmptyIgnoreFilter`.
- `ToEntityArray(Allocator)`, `ToComponentDataArray<T>(Allocator)`.
- `SetChangedVersionFilter(ComponentType type)` — restrict to changed chunks.
- `SetSharedComponentFilter<T>(T value)` — restrict by shared-component value.
- `GetSingletonEntity<T>()`, `GetSingleton<T>()`, `HasSingleton<T>()`.

`EntityQuery` is created via `state.GetEntityQuery(...)` (legacy) or `SystemAPI.QueryBuilder().Build(ref state)` (preferred fluent API).

## When to pick which

| Need                                                  | Pick                                       |
|-------------------------------------------------------|--------------------------------------------|
| Cheap per-entity work, main thread is fine            | `SystemAPI.Query<...>` foreach             |
| Per-entity work, want Burst + parallel                | `IJobEntity` + `ScheduleParallel`          |
| Need the `ArchetypeChunk` itself (e.g. `chunk.GetSharedComponent<T>`) | `IJobChunk`         |
| Need enabled-mask access without `IJobEntityChunkBeginEnd`            | `IJobChunk`         |
| Just counting entities, gathering arrays              | `EntityQuery` direct                       |
| Singleton read/write                                  | `SystemAPI.GetSingleton<T>` / `GetSingletonRW<T>` |

## Legacy: `Entities.ForEach` / `Job.WithCode`

```csharp
// SystemBase only. Deprecated in 1.x.
Entities
    .WithAll<Active>()
    .ForEach((ref LocalTransform t, in Velocity v) => {
        t.Position += v.Value * dt;
    })
    .ScheduleParallel();
```

**Do not write new code in this style.** Migrate to `IJobEntity`. The lambda capture pipeline behind `Entities.ForEach` is heavier (Roslyn-rewrites the lambda into an inner job struct), the API is `SystemBase`-only, and it has known footguns with managed captures.

## Source citations

| Symbol                                       | File                                                  |
|----------------------------------------------|-------------------------------------------------------|
| `IJobEntity` interface + codegen contract    | `Unity.Entities/IJobEntity.cs:11–544`                 |
| `IJobChunk`                                  | `Unity.Entities/IJobChunk.cs:43–231`                  |
| `ChunkEntityEnumerator`                      | `Unity.Entities/IJobChunk.cs` (search "ChunkEntityEnumerator") |
| `EntityQuery` API                            | `Unity.Entities/EntityQuery.cs`                       |
| `SystemAPI.Query` codegen contract           | `Unity.Entities/SystemAPI.cs` + codegen              |
| Project example: ISystem + IJobEntity        | A representative `ISystem` and `IJobEntity` pair in the current project |
