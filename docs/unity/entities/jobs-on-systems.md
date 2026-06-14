# Jobs on `ISystem` — `state.Dependency` and `[BurstCompile]` integration

The single most-frequently-broken contract in Entities code. Read this before scheduling anything from inside `OnUpdate`.

## The `state.Dependency` contract

`SystemState.Dependency` (a `JobHandle`) represents the cumulative dependency chain of every job this system has scheduled this frame. **You are responsible** for reading it before scheduling and writing it after — `ISystem` does **no** auto-tracking.

```csharp
[BurstCompile]
public void OnUpdate(ref SystemState state) {
    // Schedule first job — depends on whatever was already in flight.
    state.Dependency = new JobA { ... }.Schedule(state.Dependency);

    // Schedule second job — depends on first.
    state.Dependency = new JobB { ... }.Schedule(state.Dependency);

    // Schedule third job (parallel) — depends on second.
    state.Dependency = new JobC { ... }.ScheduleParallel(state.Dependency);
}
```

The pattern is:
```
state.Dependency = job.Schedule(state.Dependency);
```
or for parallel:
```
state.Dependency = job.ScheduleParallel(state.Dependency);
```

Forgetting either side breaks correctness:

- **Forget the read**: jobs scheduled this frame race jobs scheduled in a previous system.
- **Forget the write**: subsequent systems don't see your jobs as dependencies and may run in parallel with them, racing on shared `NativeContainer`s.

## `IJobEntity`'s implicit-dependency overloads

`IJobEntity` codegen generates Schedule overloads that accept and return `state.Dependency` implicitly:

```csharp
new MyJob { ... }.ScheduleParallel();              // implicit  state.Dependency
new MyJob { ... }.ScheduleParallel(myQuery);       // implicit  state.Dependency
new MyJob { ... }.ScheduleParallel(state.Dependency);   // explicit
```

The implicit overloads **read and write `state.Dependency` automatically**. Cited example: `Assets/_Project/Scripts/ECS/Systems/SlimeLatticeSyncSystem.cs:21` — `}.ScheduleParallel();` with no arguments.

This is the **only** Schedule API across all of Unity's job interfaces that auto-tracks dependencies. Plain `IJob` / `IJobFor` / `IJobParallelFor` / `IJobChunk` all require manual `state.Dependency = ...` chaining.

## `IJobChunk` requires manual chaining

```csharp
[BurstCompile]
public void OnUpdate(ref SystemState state) {
    state.Dependency = new ChunkJob {
        PositionTH = state.GetComponentTypeHandle<Position>(false),
        VelocityTH = state.GetComponentTypeHandle<Velocity>(true),
        Dt = SystemAPI.Time.DeltaTime,
    }.ScheduleParallel(myQuery, state.Dependency);
}
```

There is no zero-arg overload. Always pass `state.Dependency` and assign back.

## `[BurstCompile]` on `ISystem`

Both layers required:

```csharp
[BurstCompile]                       // 1) struct
partial struct MySystem : ISystem {
    [BurstCompile]                   // 2) every implemented lifecycle method
    public void OnCreate(ref SystemState state) { ... }

    [BurstCompile]
    public void OnUpdate(ref SystemState state) { ... }

    [BurstCompile]
    public void OnDestroy(ref SystemState state) { ... }
}
```

Without the per-method attribute, the method runs in managed mode even though the struct is "Burst-compilable". The per-method attribute tells the IL post-processor to rewrite the interface-dispatched call site to a native-direct call.

If `OnUpdate` is the only Burst-compiled method, it can call **non-Burst-compiled** `OnCreate` / `OnDestroy` without issue (those run on the main thread anyway).

## `[BurstCompile]` on the nested job

Same pattern as any `IJob*` — tag the struct only:

```csharp
[BurstCompile]
partial struct MyEntityJob : IJobEntity {
    public float Dt;
    public void Execute(ref Position p, in Velocity v) { p.Value += v.Value * Dt; }
}
```

Helpers reachable from `Execute` auto-Bursted (project canon `feedback_burst_entrypoints_only.md`).

## `state.GetComponentTypeHandle<T>` — caching strategy

For `IJobChunk` jobs, you must hand the job a `ComponentTypeHandle<T>` per accessed type. There are two ways:

**1. Per-call (common, works fine):**
```csharp
[BurstCompile]
public void OnUpdate(ref SystemState state) {
    state.Dependency = new MyJob {
        PositionTH = state.GetComponentTypeHandle<Position>(false),
        VelocityTH = state.GetComponentTypeHandle<Velocity>(true),
    }.ScheduleParallel(myQuery, state.Dependency);
}
```

**2. Cached (slightly faster, more boilerplate):**
```csharp
ComponentTypeHandle<Position> _positionTH;
ComponentTypeHandle<Velocity> _velocityTH;

[BurstCompile]
public void OnCreate(ref SystemState state) {
    _positionTH = state.GetComponentTypeHandle<Position>(false);
    _velocityTH = state.GetComponentTypeHandle<Velocity>(true);
}

[BurstCompile]
public void OnUpdate(ref SystemState state) {
    _positionTH.Update(ref state);   // refresh frame-local data
    _velocityTH.Update(ref state);
    state.Dependency = new MyJob {
        PositionTH = _positionTH,
        VelocityTH = _velocityTH,
    }.ScheduleParallel(myQuery, state.Dependency);
}
```

Cached form requires the `.Update(ref state)` call every frame to refresh the type handle's frame-local epoch. Forgetting `.Update` causes silently-stale change-filter behaviour.

For most systems the per-call form is fine — `GetComponentTypeHandle<T>` is cheap.

## Anti-patterns

### Forgetting to assign back to `state.Dependency`

```csharp
// WRONG — schedule's handle is dropped on the floor.
new MyJob { ... }.Schedule(state.Dependency);
```

The next system sees `state.Dependency` unchanged from before this call. If `MyJob` writes a `NativeContainer` that another system reads, that system races with `MyJob`.

### Reading `state.Dependency` then **forgetting to thread it through**

```csharp
// WRONG — JobB doesn't depend on JobA.
JobHandle a = new JobA { ... }.Schedule(state.Dependency);
state.Dependency = new JobB { ... }.Schedule(state.Dependency);   // doesn't see `a`
```

Use `JobHandle.CombineDependencies(a, state.Dependency)` if you need a fork-join, or thread serially:

```csharp
state.Dependency = new JobA { ... }.Schedule(state.Dependency);
state.Dependency = new JobB { ... }.Schedule(state.Dependency);
```

### Calling `state.Dependency.Complete()` mid-OnUpdate

This forces a sync inside the system, defeating the parallelism between this system and downstream systems. Almost always wrong.

The legitimate uses:
- You need to read a job result on the main thread to decide what to do next.
- You're about to call a structural-change `EntityManager` method.

In both cases, prefer ECB-deferred patterns (see [`entity-mutations.md`](entity-mutations.md)) over forcing a sync.

## `SystemBase`'s implicit `Dependency`

`SystemBase.Dependency` is read/written transparently by `Entities.ForEach` and `Job.WithCode` codegen. If you're maintaining a `SystemBase`, **don't manually thread `Dependency` through `Schedule(Dependency)`** — the codegen does it for you. Doing both double-chains the dependency and may deadlock.

Migration path: when converting a `SystemBase` to `ISystem`, every `Entities.ForEach(...).ScheduleParallel()` becomes either:

- `state.Dependency = new MyEntityJob { ... }.ScheduleParallel(state.Dependency);`, or
- `new MyEntityJob { ... }.ScheduleParallel();` (implicit form).

## Source citations

| Symbol                                       | File                                                       |
|----------------------------------------------|------------------------------------------------------------|
| `SystemState.Dependency`                     | `Unity.Entities/SystemState.cs` (search "Dependency")      |
| `SystemBase.Dependency`                      | `Unity.Entities/SystemBase.cs:150–151`                     |
| `IJobEntity` codegen contract                | `Unity.Entities/IJobEntity.cs:11–544`                      |
| `IJobChunk` schedule overloads               | `Unity.Entities/IJobChunk.cs:43–231`                       |
| `ComponentTypeHandle<T>`                     | `Unity.Entities/ComponentTypeHandle.cs`                    |
| Project example: implicit ScheduleParallel  | `Assets/_Project/Scripts/ECS/Systems/SlimeLatticeSyncSystem.cs:21` |
| Project example: per-method [BurstCompile]  | `Assets/_Project/Scripts/ECS/Systems/SlimeLatticeSyncSystem.cs:11,15,19` |
