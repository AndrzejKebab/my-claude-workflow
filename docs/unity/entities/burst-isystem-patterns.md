# Burst-ISystem patterns for a Burst-oriented DOTS engine

This page collects copyable patterns for keeping the core simulation inside `[BurstCompile]` jobs and `[BurstCompile] ISystem` structs, without managed collections on hot runtime paths. Each pattern states what it is and the failure it prevents. The Burst-compiler mechanics each pattern uses — the entry-point-only rule, `FunctionPointer<T>`, and `SharedStatic<T>` — live in [`../burst/`](../burst/index.md). System organization is covered in [`systems.md`](systems.md), [`system-groups.md`](system-groups.md), and [`command-buffers-singletons.md`](command-buffers-singletons.md).

## Every system is an unmanaged `ISystem`, `[BurstCompile]` on the type and the lifecycle methods

A system on a per-tick hot path is an unmanaged `partial struct : ISystem` with `[BurstCompile]` on the type and on each of `OnCreate`, `OnUpdate`, and `OnDestroy`. The attribute on the type carries the compile settings to every nested entry point — including the system's own scheduled jobs — but each lifecycle method still needs its own attribute, because the system struct is a managed-callable type and only the explicitly-tagged methods become Burst entry points.

`KinematicCharacterPhysicsSolveSystem2D` is a representative shape: `[BurstCompile]` on the struct, on `OnCreate`, `OnDestroy`, and `OnUpdate`, and on the nested `KinematicCharacterPhysicsSolveJob`. The whole solve is HPC#-clean, so `OnUpdate` schedules the job and the job Bursts and parallelizes.

The failure this prevents: a `SystemBase` (managed) system, or an `ISystem` whose `OnUpdate` touches managed code, forces per-tick work onto the managed runtime. Reserve managed systems for work that genuinely needs managed APIs, such as authoring bridges or editor tooling.

The necessary exception is a system whose API surface is itself managed. A physics integration may use an `ISystem` deliberately **without** `[BurstCompile]` because its body or shape calls are managed instance methods on the main thread. The struct can still hold only blittable state and schedule Burst jobs; it forgoes Burst because the work it drives is managed, not because the struct could not be unmanaged.

## Native collections only — no `System.Collections.Generic`

State that survives across a tick, and every container a job touches, is a `Unity.Collections` native container (`NativeArray`, `NativeList`, `NativeHashMap`, `NativeHashSet`, `UnsafeList`, …) or an unmanaged generic struct over those. No `List<T>`, `Dictionary<K,V>`, or managed array appears on any runtime path (`01-context.md` § "Burst compatibility": "No managed collections anywhere in runtime").

A system holds its cross-tick container as a native field and disposes it in `OnDestroy`: `PhysicsWorld2DSystem` keeps `NativeHashMap<uint4, CachedBodyTemplate> m_Templates`, allocates it `Allocator.Persistent` on first use, and disposes it in `OnDestroy` (`PhysicsWorld2DSystem.cs:46,829-830,48-54`). Per-tick scratch is `Allocator.Temp` and disposed within the same `OnUpdate` (`:903,925`).

The failure this prevents: a managed collection in a `[BurstCompile]` region is a reference type, which HPC# forbids ([`../burst/compilation-context.md`](../burst/compilation-context.md) § "HPC# — the allowed subset"). It is flagged at Burst-compile time, not C# compile time, so it passes a plain compile and surfaces only when the job actually compiles for Burst.

## The unmanaged-struct-generic seam — the Burst substitute for a managed interface

Where behavior must be swappable on a Burst path — a chunk seeder, a mesher policy, a sink, a character-movement processor — express it as a `struct` implementing an interface and consume it through a generic method constrained `where T : unmanaged, IFoo`. Burst monomorphizes the call: it compiles one specialized copy of the method per concrete `T`, and the interface call inside becomes a direct call to that struct's method with no boxing and no virtual dispatch.

Where behavior must be swappable on a Burst path, express it as a `struct` implementing an interface and consume it generically (`void Op<T>(in T impl) where T : unmanaged, I...`) so Burst monomorphizes the call with no boxing — the standard DOTS substitute for dynamic dispatch.

### Before — a managed interface, an AOT failure

```csharp
public interface ISeeder { Cell Sample(int2 worldCell); }

// Stored as a managed reference, called virtually inside the job:
ISeeder seeder;                                    // reference type — boxed
[BurstCompile]
struct SeedChunkJob : IJob {
    public ISeeder Seeder;                         // managed field in a Burst struct
    public void Execute() => cell = Seeder.Sample(p);  // virtual call
}
```

The `ISeeder` field is a reference type, and the `Seeder.Sample(p)` call is a virtual dispatch through it. Both are forbidden in HPC#; the job fails to Burst-compile. EditMode and a plain managed run can mask it, and AOT build is where it breaks.

### After — a generic over an unmanaged struct, monomorphized and zero-alloc

```csharp
public interface ISeeder { Cell Sample(int2 worldCell); }

public struct SdfSeeder : ISeeder {                // a value type
    public float radius;
    public Cell Sample(int2 worldCell) { ... }     // no allocation, no boxing
}

[BurstCompile]
struct SeedChunkJob<T> : IJob where T : unmanaged, ISeeder {
    public T Seeder;                               // stored by value, blittable
    public void Execute() => cell = Seeder.Sample(p);  // monomorphized → direct call
}
```

`SeedChunkJob<SdfSeeder>` compiles to one specialized job in which `Seeder.Sample` is a direct, inlinable call. Swapping the seeder is choosing a different `T`; no runtime cost separates the swappable design from a hand-written specialized one.

A representative character-controller seam is `PhysicsUpdate<T, C>(...) where T : unmanaged, IKinematicCharacterProcessor<C> where C : unmanaged`. The processor interface declares the solve callbacks; a default processor struct implements them and is passed by `in` into the generic solve from inside the job's `Execute`. Consumers customize the solve with their own unmanaged processor struct — dynamic-dispatch ergonomics without a managed interface on the Burst path.

A generic Burst job benefits from `[GenerateTestsForBurstCompatibility(GenericTypeArguments = …)]`, which pins the concrete instantiations a Burst-compatibility test should exercise — for example, a generic `CellSurface<T>` instantiated with a concrete voxel-cell type.

## `FunctionPointer<T>` — only for a genuinely runtime-dynamic seam

`FunctionPointer<T>` is the seam for a choice not known at compile time: the set of behaviors is open, or selected from data at runtime, so monomorphizing over a closed set of `T` is impossible. It carries a real per-`Invoke` cost and a strict delegate contract (non-generic, non-multicast, `static`, `[UnmanagedFunctionPointer(CallingConvention.Cdecl)]`); the canonical caching pattern and that contract are in [`../burst/function-pointers.md`](../burst/function-pointers.md).

Prefer the generic struct seam (above) whenever the set of implementations is closed and known at compile time — which is the common case for this engine's seams (a fixed roster of seeders, meshers, material rules). The generic monomorphizes to a direct call with no indirection; `FunctionPointer<T>` keeps an indirect call and re-creates a callable each `Invoke` unless cached. Reach for the function pointer only when the genericity cannot close: behavior chosen from loaded content, a user-extensible registry resolved at runtime, a callback handed across an API boundary that cannot be made generic.

The failure this prevents runs both ways. A managed `delegate` or `Action` on a Burst path is a reference type and does not compile. A `FunctionPointer<T>` reached for where a generic struct would do pays an avoidable indirect-call cost on a per-tick hot path and loses inlining the monomorphized form would have given.

## Hash-based determinism, not stateful RNG

A voxel simulation can use a stateless integer hash that is a pure function of `(seed, tick, x, y, z)`. Identical inputs yield identical output on every thread and every run, which makes the world reproducible and parallel simulation lock-free: there is no stored RNG or shared mutable state. A `1/N` event test can use a bounded hash conversion; a directional bias can use selected hash bits; per-tick grid jitter can derive from the tick and spatial key.

These are Burst helpers, not entry points — they carry no `[BurstCompile]` and auto-compile when reached from a Burst job, which is what lets `JitterOffset` return `int2` by value (the entry-point-only rule, [`../burst/compilation-context.md`](../burst/compilation-context.md) § "The entry-point rule"). The static methods are also direct-call-eligible when called from the main thread.

The failure this prevents: a stateful RNG (a `Unity.Mathematics.Random` field mutated per draw) carried into a parallel job is per-thread mutable state — the same world cell draws a different value depending on which thread and in which order it ran, breaking determinism, and a shared mutable RNG is a data race. The hash has no state to share, so the parallel checkerboard schedule needs no synchronization around it. Latios's deterministic `Rng`/`RngSequence` ([`latios-idioms.md`](latios-idioms.md)) is the per-job-index variant of the same stateless-hash idea, relevant where a job index is the natural key rather than a world coordinate.

## Holding a native-collection-bearing world struct reachable from a Burst system

A chunk pool — a `struct` owning many native containers (per-chunk cell buffers, dirty rects, residency state) — is reached from a Burst system as an unmanaged value made addressable through ECS, not as a managed object field on the system. The two reachable shapes are a singleton component holding the (blittable, native-container-bearing) struct, retrieved through `SystemAPI.GetSingleton`/`GetSingletonRW` and read inside a Burst `OnUpdate`; or, in the Latios idiom, a collection component associated with an entity ([`latios-idioms.md`](latios-idioms.md) § "Collection components"). The mechanics — singleton creation, the `RW` access for in-place mutation, the buffer-on-singleton-entity pattern for per-frame event streams — are in [`command-buffers-singletons.md`](command-buffers-singletons.md). `PhysicsWorld2DSystem` shows the singleton-holding-native-state shape: `PhysicsWorldSingleton2D` carries the `PhysicsWorld` handle, with the system's `NativeHashMap` template store held as a system field disposed in `OnDestroy` (`PhysicsWorld2DSystem.cs:790-813,46`).

The constraint that decides the shape: a `CellSurface<T>` (or any native container) passed by value into a job copies the header — the pointer and the dimensions — but aliases the same buffer, which is exactly what makes in-job mutations visible to the caller; such a by-value copy is a non-owning view and must never `Dispose()`, or it double-frees the owner's buffer (`CellSurface.cs:29-34`). The pool struct therefore has exactly one owner that disposes it; every system that reaches it holds a non-owning view.

The failure this prevents: a managed class pool stored as a system field cannot be touched from a `[BurstCompile] OnUpdate` (it is a reference type), and a native container disposed by both the owner and a passed-by-value copy is a use-after-free that a plain compile never catches.

## Source citations

| Topic | Reference |
|-------|-----------|
| Burst requirement and no-managed-collections rule | The patterns and failure descriptions above |
| Unmanaged `ISystem`, `[BurstCompile]` on type + lifecycle + nested job | A representative Burst-compiled system in the current project |
| Non-Burst `ISystem` for a managed engine API | A representative managed integration system in the current project |
| Generic-struct seam — solve chain, processor interface, default processor | The `ISeeder` and character-controller examples above |
| `[GenerateTestsForBurstCompatibility]` on a generic native struct | A generic `CellSurface<T>` test instantiated with the project's cell type |
| Hash-based determinism | A stateless `(seed,tick,x,y,z)` hash implementation in the current project |
| Non-owning by-value view of a native container; single-owner disposal | The current project's native-container ownership tests |
| Entry-point-only rule, HPC# subset, `FunctionPointer<T>`, `SharedStatic<T>` | [`../burst/compilation-context.md`](../burst/compilation-context.md), [`../burst/function-pointers.md`](../burst/function-pointers.md), [`../burst/shared-static.md`](../burst/shared-static.md) |
