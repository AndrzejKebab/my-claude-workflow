# Compilation context — the HPC# subset and the entry-point rule

What actually compiles in Burst, and which methods need `[BurstCompile]`.

## HPC# — the allowed subset

Burst compiles a subset of C# called HPC# (High-Performance C#). The contract:

**Allowed**:
- Value types: `struct`, primitives, `enum`, fixed-size arrays.
- Generics, including generic struct constraints.
- `unsafe` code, `void*`, `T*`, pointer arithmetic.
- `Unity.Mathematics` (`float3`, `float4x4`, `math.*` etc.).
- `Unity.Collections` Native containers used through their types' published APIs.
- Function pointers via `FunctionPointer<T>`.
- Static fields if marked via `SharedStatic<T>` (see [`shared-static.md`](shared-static.md)).
- `throw` statements (Burst lowers to a managed-exception trap that ends the job).
- `string` literals via `BurstString` and `Debug.Log` if all arguments are constants (newer Burst versions).

**Forbidden**:
- Reference types (`class`, `string`-as-runtime-value beyond literals, arrays of managed types).
- Boxing / unboxing.
- Reflection (`typeof().GetMethod`, etc.).
- LINQ, `IEnumerable<T>`, `yield`, `async`/`await`.
- `try`/`catch`/`finally`.
- Plain managed `static` mutable fields (use `SharedStatic<T>`).
- Calling managed-only APIs (the job system arranges for `IJob*` extension methods and the like to enter Burst at the boundary; everything called from inside the entry point must be HPC#).

Non-HPC# code in a `[BurstCompile]` method is flagged at Burst-compile time, **not** C# compile time. You discover violations either via the Burst Inspector (Window → Analysis → Burst Inspector) or via the console after a job runs. See [`verification.md`](verification.md).

## The entry-point rule

**Default rule:** apply `[BurstCompile]` to **entry points**; helpers reached
from those entry points compile in the same Burst context.

An entry point is a type the job system calls into:

```csharp
// Entry point:
[BurstCompile]
public struct DensityFillJob : IJobParallelFor {
    public void Execute(int i) {
        var n = Fbm3(uvw, seed);     // helper — NO [BurstCompile] needed
        DensityOut[i] = ApplyMask(n);
    }

    // No attribute. Auto-Bursted because it's reached from a Burst entry point.
    static float Fbm3(float3 p, int seed) { ... }
    static float ApplyMask(float n) { ... }
}
```

**Why the rule matters**: redundantly tagging helpers with `[BurstCompile]` makes
them direct-call-eligible (the IL post-processor rewrites managed call sites to
call the native function pointer directly), which is fine. But it also publishes
them as separate Burst entry points. Prefer one entry point per logical job and
let private helpers auto-compile unless a managed caller needs a direct call.

## Helpers can return structs by value

A non-obvious HPC# property: **helpers reached from a Burst entry point can return any HPC# struct by value**, not only primitives. The `Smin` helper in `VoxelTileFiller.cs:194` returns `float`; the same job could equally return `float3` or `int4`:

```csharp
static float3 ComputeNormal(float3 p) {
    return math.normalize(p - Center);   // returning float3 by value — fine.
}
```

This makes it safe to write small helper functions that take and return
Unity.Mathematics types without falling back to ref-out parameters.

## Static methods + direct call

A static method tagged `[BurstCompile]` outside a job struct gets the **direct-call** treatment: the IL post-processor rewrites every managed call site to call the native function pointer directly, bypassing the managed delegate.

```csharp
public static class VoxelMath {
    [BurstCompile]
    public static float DistanceToSurface(float3 p) { ... }
}

// Caller — managed code:
float d = VoxelMath.DistanceToSurface(p);   // post-processor rewrites to direct native call
```

This is the **right pattern for shared utility functions** that are called from both Burst jobs and the main thread. Without `[BurstCompile]` on the static, callers from the main thread go through plain managed code (correct but slow); with it, they trampoline into the Burst-compiled version.

To opt out (e.g. you want both a managed and a Burst version available): `[BurstCompile(DisableDirectCall = true)]`.

## What `[BurstCompile]` on a class actually means

```csharp
[BurstCompile]
internal class MyRenderPass : ScriptableRenderPass { ... }
```

Cited example pattern: `Packages/com.dim0v.radiance-cascades-2d/Runtime/Passes/PrepareAnalyticalLightsPass.cs:17` (third-party reference).

This **does not Burst-compile the class itself** — classes are reference types and cannot live in HPC#. It marks every nested static method (and every nested job struct's `Execute`) with the same `[BurstCompile]` settings. Equivalent to writing the attribute on each entry point, but compact.

## Recompilation rules

- Editing a `.cs` file with `[BurstCompile]` triggers a full Burst recompile of the affected jobs on the next domain reload (`unity-recompile`).
- The first call to a `[BurstCompile]` job after recompile runs **managed** while Burst compiles in the background, then switches to native on the next call. To force sync, use `[BurstCompile(CompileSynchronously = true)]`.
- Burst caches per-target builds at `Library/BurstCache/`. Wiping that folder forces a full recompile.

## Source citations

| Topic                                            | Reference                                                              |
|--------------------------------------------------|------------------------------------------------------------------------|
| HPC# subset, attribute targets                   | `Runtime/BurstCompileAttribute.cs`                                     |
| Direct-call IL post-processor mechanism          | `Unity.Burst.CodeGen/` (internal — black-box for users)                |
| Entry-point and helper pattern                   | The `DensityFillJob` example above; verify against current Burst Inspector output. |
