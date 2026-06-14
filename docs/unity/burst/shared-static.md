# `SharedStatic<T>` — sharing mutable state across the Burst boundary

The only sanctioned way to read or write a static field from inside a `[BurstCompile]` method.

## Why plain static fields don't work

Burst-compiled native code does not have access to managed static fields — they live in the CLR heap, the native code can't see them. A plain `static int Counter = 0;` referenced from inside a Burst job triggers a Burst compile error.

`SharedStatic<T>` is a hash-keyed slab of native memory the runtime allocates eagerly at type-init time. Both managed code and Burst-compiled code can read and write it through the same pointer.

## Declaring one

```csharp
internal struct MyCounterContext { }   // identity type — its FQN is the lookup key

private static readonly SharedStatic<int> Counter =
    SharedStatic<int>.GetOrCreate<MyCounterContext>();

public static void Increment() {
    Counter.Data++;          // Counter.Data is `ref int` — the slot lives in native memory
}
```

Cited at `Runtime/SharedStatic.cs:50`.

The convention is to declare a private context type next to the field, naming what the slot represents. `Type.AssemblyQualifiedName` of the context type is hashed (FNV-1a 64-bit, `Runtime/BurstRuntime.cs:44`) to derive the slot identity.

## Two-key form

For per-instance storage, use the two-context form:

```csharp
internal struct PerCloudPresetCounterContext { }

// One slot per (CloudPreset) — keyed by both context types.
public static SharedStatic<int> GetCounter<TPreset>() where TPreset : struct =>
    SharedStatic<int>.GetOrCreate<PerCloudPresetCounterContext, TPreset>();
```

Cited at `Runtime/SharedStatic.cs:65`. Two-key form derives the slot identity from `(hash(TContext), hash(TSubContext))`.

## Reading & writing

```csharp
public ref int Data         { get; }     // line 28 — ref into the native slab
public void*   UnsafeDataPointer { get; } // line 39 — raw pointer
```

`Data` is a `ref` getter — every access dereferences the pointer afresh. To use it inside a Burst job, capture the slot once and share via `unsafe`:

```csharp
[BurstCompile]
struct MyJob : IJob {
    [NativeDisableUnsafePtrRestriction] public unsafe int* CounterPtr;
    public void Execute() {
        Interlocked.Increment(ref UnsafeUtility.AsRef<int>(CounterPtr));
    }
}

// Schedule:
unsafe {
    new MyJob { CounterPtr = (int*)Counter.UnsafeDataPointer }.Schedule().Complete();
}
```

For the simple "read/write a single struct" case, just access `Counter.Data` directly inside the job — Burst inlines the property getter.

## The size-mismatch gotcha

`SharedStatic<T>` slots are keyed by `(TContext, TSubContext)` hashes only. If two assemblies use the **same context type** with **different `T`** sizes, the second `GetOrCreate` raises a runtime error: "size mismatch on shared static".

Resolution: the keyed identity must encode both the context types and the storage type. In practice this means giving each `SharedStatic<T>` a unique private context type:

```csharp
// Bad — both share Bucket as the context:
internal struct Bucket { }
SharedStatic<int>     A = SharedStatic<int>.GetOrCreate<Bucket>();
SharedStatic<float4>  B = SharedStatic<float4>.GetOrCreate<Bucket>();   // RUNTIME ERROR

// Good:
internal struct ABucket { }
internal struct BBucket { }
SharedStatic<int>    A = SharedStatic<int>.GetOrCreate<ABucket>();
SharedStatic<float4> B = SharedStatic<float4>.GetOrCreate<BBucket>();
```

## Lifetime

`SharedStatic<T>` slots persist for the **lifetime of the application / domain reload**. There is no `Dispose`. On editor domain reload (script recompile), the slabs are reset.

## Used internally by job reflection-data

Look at `IJobExtensions.JobStruct<T>` (cited `UnityEngine.CoreModule.decompiled.cs:2286`):

```csharp
internal static readonly BurstLike.SharedStatic<IntPtr> jobReflectionData =
    BurstLike.SharedStatic<IntPtr>.GetOrCreate<JobStruct<T>>();
```

Every job extension for `IJob` / `IJobFor` / `IJobParallelFor` / `IJobParallelForBatch` uses a `SharedStatic<IntPtr>` to hold the reflection-data pointer the native scheduler needs. The context type is the producer struct itself (`JobStruct<T>` — generic over the job type), so each distinct job type gets its own slot.

This is why `[RegisterGenericJobType]` exists for generic jobs: closed types get auto-registered by codegen, but `MyJob<MyParam>` for a runtime-known `MyParam` needs explicit registration so the slot pre-allocates at startup, before the Burst-compiled scheduler tries to read it.

## Constructor variants

```csharp
SharedStatic<T>.GetOrCreate<TContext>(uint alignment = 0)                                  // line 50
SharedStatic<T>.GetOrCreate<TContext, TSubContext>(uint alignment = 0)                      // line 65
SharedStatic<T>.GetOrCreateUnsafe(uint alignment, long hashCode, long subHashCode)         // line 85
SharedStatic<T>.GetOrCreatePartiallyUnsafeWithHashCode<TSubContext>(uint, long)            // line 101
SharedStatic<T>.GetOrCreatePartiallyUnsafeWithSubHashCode<TContext>(uint, long)            // line 117
SharedStatic<T>.GetOrCreate(Type contextType, uint alignment = 0)                          // line 133 (managed-only)
SharedStatic<T>.GetOrCreate(Type contextType, Type subContextType, uint alignment = 0)     // line 148 (managed-only)
```

Default alignment is **16 bytes** (line 76). Override only if you need wider SIMD alignment or padding for `JobsUtility.CacheLineSize` (=64) per-thread layout.

The `GetOrCreate(Type)` overloads (lines 133, 148) are **managed-only** — they cannot be called from inside a `[BurstCompile]` method (reflection). Use them at startup from C#, then read the resulting `SharedStatic<T>` from Burst.

## Source citations

| Symbol                                                   | File                              |
|----------------------------------------------------------|-----------------------------------|
| `SharedStatic<T>` struct                                 | `Runtime/SharedStatic.cs:15`      |
| `Data` (ref getter)                                      | `Runtime/SharedStatic.cs:28`      |
| `UnsafeDataPointer`                                      | `Runtime/SharedStatic.cs:39`      |
| `GetOrCreate<TContext>(uint)`                            | `Runtime/SharedStatic.cs:50`      |
| `GetOrCreate<TContext, TSubContext>(uint)`               | `Runtime/SharedStatic.cs:65`      |
| Default alignment 16                                     | `Runtime/SharedStatic.cs:76`      |
| Hash function (FNV-1a 64-bit)                            | `Runtime/BurstRuntime.cs:44`      |
| Use in IJob reflection data                              | `UnityEngine.CoreModule.decompiled.cs:2290` |
