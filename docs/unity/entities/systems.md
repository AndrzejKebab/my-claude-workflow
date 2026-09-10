# Systems — `ISystem`, `SystemState`, and the Burst `OnUpdate` boundary

Engine `file:line` citations refer to the installed `com.unity.entities` package under `Library/PackageCache/com.unity.entities@<version>/Unity.Entities/`. Verify line numbers against the version used by the current project.

## `ISystem` (unmanaged) vs `SystemBase` (managed)

A system is one of two kinds. `ISystem` is an interface (`ISystem.cs:11`) implemented by an unmanaged `partial struct`; `SystemBase` is an abstract managed class. The three lifecycle methods on `ISystem` each take the system's backing state by reference — `void OnCreate(ref SystemState state)` (`ISystem.cs:24`), `void OnUpdate(ref SystemState state)` (`ISystem.cs:65`), `void OnDestroy(ref SystemState state)` (`ISystem.cs:36`) — all three with default empty bodies, so a system implements only the ones it needs. `SystemBase` instead exposes parameterless `OnCreate()`/`OnUpdate()`/`OnDestroy()` overrides and reaches its state through instance members.

`ISystem` is the Burst-oriented form. The reason is structural: an `ISystem` is an unmanaged struct, so its methods can carry `[BurstCompile]` and the system updates through a Burst-compiled function pointer (`SystemBaseDelegates.Function` at `ISystem.cs:80` is the `Cdecl` delegate the compilation pipeline uses for that). A `SystemBase` is a managed object and cannot be Burst-compiled. Prefer unmanaged `ISystem` structs for hot per-tick work; use `SystemBase` or a non-Burst system when managed access is genuinely required.

A `SystemBase` is still useful when the system must touch managed objects. Alternatively, an `ISystem` can use `SystemAPI.ManagedAPI.GetComponent<…>(state.SystemHandle)` as a managed escape hatch, but such a system cannot Burst-compile that code path.

## `[BurstCompile]` placement: the type AND each method

A Burst `ISystem` carries `[BurstCompile]` in two places, and both are required:

- on the `partial struct` declaration itself, and
- on each of `OnCreate`, `OnUpdate`, `OnDestroy` that it implements.

The attribute on the type alone does not Burst-compile the lifecycle methods, and an attribute on a method whose type lacks it does not compile either — the compilation pipeline matches the pair. The full form places `[BurstCompile]` on the struct and again on each implemented lifecycle method that should compile with Burst.

A system whose `OnUpdate` must call managed code omits `[BurstCompile]` and runs on the main thread; it may still schedule Burst jobs for HPC#-compatible work. This is the decision a system author makes first — Burst the system if its `OnUpdate` is HPC#-clean; leave it managed if it must reach a managed API — and it is per-system, not per-package.

## `ref SystemState`

`SystemState` is the system's backing state, passed by reference into every lifecycle method; an `ISystem` struct holds only its own fields and reaches everything else through it. The members an `OnUpdate` reaches for:

- `state.Dependency` — `public JobHandle Dependency { get; set; }` (`SystemState.cs:406`). The input/output job-dependency handle; see the chaining section below.
- `state.EntityManager` — `public EntityManager EntityManager` (`SystemState.cs:220`). The handle for structural changes and singleton creation done on the main thread.
- `state.World` / `state.WorldUnmanaged` — `public World World` (`SystemState.cs:227`) and `public WorldUnmanaged WorldUnmanaged` (`SystemState.cs:233`). `WorldUnmanaged` is the Burst-callable one and is what an ECB singleton's `CreateCommandBuffer(WorldUnmanaged)` wants.
- `state.GetComponentLookup<T>(bool isReadOnly = false)` — `public ComponentLookup<T> GetComponentLookup<T>(...)` (`SystemState.cs:1030`). Creates a lookup cached on the system; call it once in `OnCreate`, then `lookup.Update(ref state)` at the top of each `OnUpdate` before use.
- `state.GetEntityTypeHandle()` — `public EntityTypeHandle GetEntityTypeHandle()` (`SystemState.cs:1013`). For `IJobChunk` scheduling.
- `state.RequireForUpdate<T>()` (`SystemState.cs:1164`) and `state.RequireForUpdate(EntityQuery query)` (`SystemState.cs:1138`) — gate `OnUpdate` so it only runs when the required component/query is non-empty. Call these in `OnCreate`; a system may gate on both a query and a required singleton.

## `SystemAPI` inside a Burst `OnUpdate` — all of it is source-generated

`SystemAPI` is a `static class` (`SystemAPI.cs:16`) whose methods are the convenient entry points to queries, components, time, and singletons from inside a system. The load-bearing fact about it: **every `SystemAPI` member is source-generated, not a real method call.** Each declaration in the source has a body that throws — `=> throw Internal.InternalCompilerInterface.ThrowCodeGenException()` — and the source generator rewrites each call site against the enclosing system into cached direct access (`SystemAPI.cs:29` for `QueryBuilder`, `:42` for `Query<T1>`, and so on for every member). The consequence for a system author is two rules:

- A `SystemAPI` call only works lexically inside a system's own `OnCreate`/`OnUpdate`/`OnDestroy` (or inside an `IJobEntity.Execute`). It cannot be factored out into a `static` helper that takes no system context — the generator has nothing to bind against there, and the call hits the throwing stub at runtime.
- Because the rewrite produces direct, cached, blittable access, the calls are Burst-legal — for example, a `[BurstCompile] OnUpdate` can call `SystemAPI.GetSingleton<…>()` and `SystemAPI.Time`.

The members usable inside a Burst `OnUpdate`, with their declaration lines:

| Member | Declaration | Use |
|--------|-------------|-----|
| `SystemAPI.Query<T1,…>()` | `SystemAPI.cs:42` (and the multi-arg overloads following) | Iterate matching entities; combine with `.WithAll<>`/`.WithNone<>`/`.WithEntityAccess()`. |
| `SystemAPI.QueryBuilder()` | `SystemAPI.cs:29` | Fluent `EntityQuery` construction, materialized in `OnCreate`. |
| `SystemAPI.GetSingleton<T>()` | `SystemAPI.cs:558` | Read a singleton component by value. |
| `SystemAPI.TryGetSingleton<T>(out T)` | `SystemAPI.cs:569` | Read a singleton if present; throws if more than one matches. |
| `SystemAPI.SetSingleton<T>(T)` | `SystemAPI.cs:608` | Write a singleton component. |
| `SystemAPI.GetSingletonEntity<T>()` | `SystemAPI.cs:619` | The entity carrying a singleton. |
| `SystemAPI.GetSingletonBuffer<T>(bool isReadOnly = false)` | `SystemAPI.cs:642` | A singleton `DynamicBuffer`. |
| `SystemAPI.GetComponentLookup<T>(bool isReadOnly = false)` | `SystemAPI.cs:179` | A `ComponentLookup<T>` (the generator caches and auto-updates it). |
| `SystemAPI.GetBufferLookup<T>(bool isReadOnly = false)` | `SystemAPI.cs:450` | A `BufferLookup<T>`. |
| `SystemAPI.HasComponent<T>(Entity)` | `SystemAPI.cs:313` | Component presence test. |
| `SystemAPI.GetComponent<T>(Entity)` | `SystemAPI.cs:203` | Read a component by value. |
| `SystemAPI.GetComponentRW<T>(Entity)` | `SystemAPI.cs:249` | A read-write reference to a component. |
| `SystemAPI.Time` | `SystemAPI.cs:162` (`ref readonly TimeData`) | The world's `TimeData`; `.DeltaTime`, `.ElapsedTime`. |

`SystemAPI.ManagedAPI.GetComponent<T>` is the managed escape hatch and is **not** Burst-legal.

Note the `GetComponentLookup` distinction. The source-generated `SystemAPI.GetComponentLookup<T>` caches and auto-updates the lookup; the explicit `state.GetComponentLookup<T>` (`SystemState.cs:1030`) returns a lookup you store as a system field and must refresh yourself with `lookup.Update(ref state)` each update before reading it.

## `state.Dependency` chaining

`OnUpdate` runs on the main thread but its job-scheduled work runs deferred. The contract is the `state.Dependency` handle: the system reads it as the incoming dependency when it schedules a job, and writes the scheduled job's handle back into it so the next system (and the structural-change sync point) waits on this system's jobs. The pattern is read-then-write:

- Schedule with `state.Dependency` as the `dependsOn` argument, then assign the result back: `state.Dependency = job.ScheduleParallel(query, state.Dependency)`.
- When intermediate disposals chain off the same handle, thread them through each `array.Dispose(handle)` call and write the final handle back to `state.Dependency`.
- A system that fans out several jobs combines their handles before writing back: `state.Dependency = JobHandle.CombineDependencies(handles)`.

Never `Complete()` `state.Dependency` mid-`OnUpdate` unless the system genuinely needs the results on the main thread that frame — completing forces a sync point and discards the parallelism. The `CombineDependencies` and `JobHandle` semantics themselves are in [`../jobs/dependencies.md`](../jobs/dependencies.md).

## Scheduling `IJobEntity` / `IJobChunk` from a system

`IJobChunk` is a real interface — `public interface IJobChunk` (`IJobChunk.cs:43`) — with one method, `void Execute(in ArchetypeChunk chunk, int unfilteredChunkIndex, bool useEnabledMask, in v128 chunkEnabledMask)` (`IJobChunk.cs:70`). Its scheduling extensions are real methods: `Schedule<T>(this T jobData, EntityQuery query, JobHandle dependsOn)` (`IJobChunk.cs:128`) and `ScheduleParallel<T>(this T jobData, EntityQuery query, JobHandle dependsOn)` (`IJobChunk.cs:175`). Inside the `Execute` you read component arrays off the chunk through `ComponentTypeHandle<T>` fields the system fills before scheduling.

`IJobEntity` is the lower-boilerplate per-entity form. `public interface IJobEntity {}` is an empty marker (`IJobEntity.cs:27`); the job carries a user-defined `void Execute(...)` whose parameters (`ref`/`in` components, `DynamicBuffer<>`s, `Entity`) declare what it touches. A source generator reads that `Execute` signature and generates a backing `IJobChunk` plus the real scheduling code (`IJobEntity.cs:14-17`). Like `SystemAPI`, the `Schedule`/`ScheduleParallel` extension methods in the source are throwing stubs the generator replaces — `Schedule<T>(this T jobData, JobHandle dependsOn) where T : unmanaged, IJobEntity => throw …ThrowCodeGenException()` (`IJobEntity.cs:296`), and the `EntityQuery`-taking overloads at `:328`/`:345`. The author writes `job.ScheduleParallel(query, state.Dependency)` and the generator binds it.

Two facts that bite when writing an `IJobEntity`:

- The `EntityQuery` passed to `ScheduleParallel` **must contain every component the `Execute` accesses**, or scheduling throws "the query must (at the very minimum) contain all the components required for …Execute()".
- An `IJobEntity` is a `partial struct` (the generator completes it) and must be `unmanaged`. A `[WithAll(typeof(T))]` attribute on the job struct adds a query constraint the `Execute` parameters do not express — for example, a simulation tag.

A typical worked `IJobEntity` has `[BurstCompile]` on the partial struct, `[ReadOnly] ComponentLookup<>` and plain value fields, and an `Execute` taking the entity plus its `ref`/`in` components and buffers.

## The Burst-legal boundary in `OnUpdate`

What may appear inside a `[BurstCompile] OnUpdate`:

- The source-generated `SystemAPI` members above (they lower to direct access).
- HPC# arithmetic and `Unity.Mathematics` math (`using static Unity.Mathematics.math`).
- `Unity.Collections` native containers — `NativeArray`, `NativeList`, `NativeHashMap`, `NativeHashSet`, `UnsafeList` — and unmanaged generic structs over `unmanaged` type parameters.
- Scheduling jobs (`job.ScheduleParallel(...)`), reading/writing `state.Dependency`.
- `state.EntityManager` structural-change calls and `EntityCommandBuffer` recording (the ECB type is itself `[BurstCompile]`, `EntityCommandBuffer.cs:85-86`).

What may **not**:

- Managed objects, `System.Collections.Generic` (`List<T>`, `Dictionary<K,V>`), managed arrays, `string` formatting, and reflection.
- A managed-interface virtual call inside the Burst region — a compile/AOT failure; the substitute is the unmanaged-generic-struct seam detailed in [`burst-isystem-patterns.md`](burst-isystem-patterns.md).
- `SystemAPI.ManagedAPI.*`, and any managed-API instance method.

The entry-point-only rule applies here exactly as in [`../burst/compilation-context.md`](../burst/compilation-context.md): only the system type and its lifecycle methods (and the job types) carry `[BurstCompile]`; the `static` helpers they call into compile automatically from the Burst context and must not carry the attribute themselves. A `[BurstCompile]` on a helper that is never an entry point passes EditMode and breaks only at AOT build — the documented failure that this rule exists to prevent.
