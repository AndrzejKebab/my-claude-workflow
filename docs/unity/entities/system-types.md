# `ISystem` vs `SystemBase` — picking a system shape

## The decision

- **`ISystem`** — default. A `partial struct` implementing the interface. Burst-compatible end-to-end. Cannot hold managed reference fields. Use for everything new.
- **`SystemBase`** — fall-back. A managed `partial class`. Holds managed fields, allows the deprecated `Entities.ForEach` lambda (codegen). **Don't write new ones**; migrate existing ones to `ISystem` opportunistically.

A common project convention is to prefer `ISystem` for unmanaged, performance-sensitive systems.

## `ISystem` interface

```csharp
public interface ISystem {
    void OnCreate (ref SystemState state);    // Unity.Entities/ISystem.cs:24
    void OnUpdate (ref SystemState state);    // Unity.Entities/ISystem.cs:39
    void OnDestroy(ref SystemState state);    // Unity.Entities/ISystem.cs:35
}

// Optional:
public interface ISystemStartStop {
    void OnStartRunning(ref SystemState state); // line 101
    void OnStopRunning (ref SystemState state); // line 115
}
```

Citations: `Unity.Entities/ISystem.cs`.

### Lifecycle

1. `OnCreate` — once, at world initialisation. Cache queries, register required components, initialise `SharedStatic` slots.
2. `OnStartRunning` — fires before the first `OnUpdate`, and again any time the system resumes after being skipped (e.g. `RequireForUpdate<T>` query went from empty to non-empty).
3. `OnUpdate` — per frame (or per tick of the containing `ComponentSystemGroup`).
4. `OnStopRunning` — symmetric to `OnStartRunning`. Fires when the system stops being invoked (queries return empty, `state.Enabled = false`, etc.).
5. `OnDestroy` — at world teardown (editor: play-mode exit, script reload).

### Skipping `OnUpdate` when no entities match

`ISystem` skips `OnUpdate` if **none of the queries created via `state.GetEntityQuery(...)` (or `SystemAPI.QueryBuilder`) match any entity** — unless you opt out:

- `[RequireMatchingQueriesForUpdateAttribute]` on the system struct **enables** the skip behaviour (this is the default starting in 1.x — but the attribute makes it explicit).
- `state.RequireForUpdate<T>()` or `state.RequireForUpdate(query)` from `OnCreate` lets you require a specific component/query **on top of** any auto-detected ones. If the requirement is unmet, `OnUpdate` is skipped.

Cited at `Unity.Entities/ISystem.cs:39, 65`.

## `SystemBase` (for reference)

```csharp
public abstract partial class SystemBase : ComponentSystemBase {
    public  JobHandle Dependency { get; set; }   // SystemBase.cs:151
    protected sealed override void OnUpdate();   // managed
    // ...
}
```

Cited at `Unity.Entities/SystemBase.cs:150–151`. Same lifecycle methods as `ISystem`, but they're called on the main thread of the **managed** runtime — Burst-friendly only if you're careful to not touch managed types in them.

`SystemBase.Dependency` is the **implicit-dependency property** — the legacy `Entities.ForEach` codegen reads/writes it transparently, chaining jobs without you having to thread `state.Dependency` manually. `ISystem` has no equivalent; you write the chain by hand (see [`jobs-on-systems.md`](jobs-on-systems.md)).

## `[BurstCompile]` on `ISystem`

The required pattern:

```csharp
[BurstCompile]                       // 1) on the struct
partial struct MySystem : ISystem {
    [BurstCompile]                   // 2) on each lifecycle method you implement
    public void OnCreate(ref SystemState state) { ... }

    [BurstCompile]
    public void OnUpdate(ref SystemState state) { ... }

    [BurstCompile]
    public void OnDestroy(ref SystemState state) { ... }
}
```

**Both layers are required.** The struct attribute marks the type as Burst-compilable; the per-method attribute is needed because `ISystem` lifecycle methods are dispatched via interface call from `ComponentSystemGroup`, and the IL post-processor needs the explicit attribute to rewrite the call site to a direct native call.

In the current project, verify this pattern against a representative Burst-compiled `ISystem` and its lifecycle methods.

## System groups

Three standard `ComponentSystemGroup`s execute in this order each frame:

1. **`InitializationSystemGroup`** — early-frame setup. Hosts `BeginInitializationEntityCommandBufferSystem` (OrderFirst) and `EndInitializationEntityCommandBufferSystem` (OrderLast). Cited `Unity.Entities/DefaultWorld.cs:8–77`.
2. **`SimulationSystemGroup`** — main game logic. **Default group** if you don't specify `[UpdateInGroup]`. Hosts `BeginSimulationECBSystem` and `EndSimulationECBSystem`.
3. **`PresentationSystemGroup`** — render-side / presentation logic. Hosts `BeginPresentationECBSystem` and `EndPresentationECBSystem`.

### Ordering attributes

- **`[UpdateInGroup(typeof(MyGroup))]`** — places the system in `MyGroup`. Optional `OrderFirst = true` / `OrderLast = true` move it to the start/end of the group's local sort order. Cited `Unity.Entities/ScriptBehaviourUpdateOrder.cs:143–174`.
- **`[UpdateBefore(typeof(OtherSystem))]`** — order constraint within the same group. Cited `Unity.Entities/ScriptBehaviourUpdateOrder.cs:22–42`.
- **`[UpdateAfter(typeof(OtherSystem))]`** — symmetric. Cited `Unity.Entities/ScriptBehaviourUpdateOrder.cs:50–70`.

### Sorting

Each `ComponentSystemGroup` topologically sorts its members from the constraint graph. Sort runs at world-creation time and again on any structural change to the group (system added/removed). Set `EnableSystemSorting = false` on a group to lock the order to declaration order — useful for performance-critical groups where you want zero re-sort cost.

Cited `Unity.Entities/ComponentSystemGroup.cs:36–80`.

## Querying state from `OnCreate` / `OnUpdate`

```csharp
[BurstCompile]
public void OnCreate(ref SystemState state) {
    state.RequireForUpdate<MyComponent>();
    _query = SystemAPI.QueryBuilder().WithAll<Position, Velocity>().Build(ref state);
}

[BurstCompile]
public void OnUpdate(ref SystemState state) {
    foreach (var (pos, vel) in SystemAPI.Query<RefRW<Position>, RefRO<Velocity>>()) {
        pos.ValueRW.Value += vel.ValueRO.Value * SystemAPI.Time.DeltaTime;
    }
}
```

`SystemAPI` is a Roslyn-generated facade that lowers to `state.*` calls during code generation. It can only be used inside `ISystem` / `SystemBase` methods (the codegen scans for the syntactic pattern).

Key `SystemAPI` accessors:
- `SystemAPI.Query<...>()` — codegen iteration.
- `SystemAPI.QueryBuilder()` — fluent EntityQuery construction.
- `SystemAPI.Time` — per-system time delta (can be sub-stepped).
- `SystemAPI.GetSingleton<T>()` / `SystemAPI.GetSingletonRW<T>()` — read or read-write the single component of type `T`.
- `SystemAPI.HasSingleton<T>()`.

See [`query-and-iteration.md`](query-and-iteration.md) for the full Query API.

## Source citations

| Symbol                                       | File                                                       |
|----------------------------------------------|------------------------------------------------------------|
| `ISystem` interface                          | `Unity.Entities/ISystem.cs:11–116`                         |
| `ISystemStartStop`                           | `Unity.Entities/ISystem.cs:101, 115`                       |
| `SystemBase` class                           | `Unity.Entities/SystemBase.cs:32–303`                      |
| `SystemBase.Dependency`                      | `Unity.Entities/SystemBase.cs:150–151`                     |
| `ComponentSystemGroup`                       | `Unity.Entities/ComponentSystemGroup.cs:36–80`             |
| Standard groups                              | `Unity.Entities/DefaultWorld.cs:8–148`                     |
| `[UpdateInGroup]`                            | `Unity.Entities/ScriptBehaviourUpdateOrder.cs:143–174`     |
| `[UpdateBefore]` / `[UpdateAfter]`           | `Unity.Entities/ScriptBehaviourUpdateOrder.cs:22–42, 50–70`|
| Project example: ISystem + Burst pattern     | A representative Burst-compiled `ISystem` in the current project's `Assets/` or owned packages |
