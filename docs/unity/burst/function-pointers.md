# Function pointers — `FunctionPointer<T>` and `BurstCompiler.CompileFunctionPointer<T>`

Calling a Burst-compiled function from another Burst-compiled function (or from managed code) without going through the managed delegate dispatcher.

## When you need them

- **Polymorphism inside Burst.** A job kernel that picks one of N implementations at scheduling time. Plain virtual dispatch is forbidden in HPC#. Function pointers fit the gap: pre-compile each implementation and pass the chosen `FunctionPointer<T>` into the job.
- **Calling Burst from managed.** Static `[BurstCompile]` methods automatically get the direct-call treatment via the IL post-processor; for cases where you want to **store** a Burst pointer (e.g. into a `NativeArray<FunctionPointer<T>>` or a callback table), you build it explicitly.
- **Calling C from Burst, or Burst from C.** Native plugins exposed as P/Invoke with `[UnmanagedFunctionPointer(Cdecl)]` work the same way once obtained.

## The full pattern

```csharp
using AOT;
using System.Runtime.InteropServices;
using Unity.Burst;

// 1. Delegate type — must satisfy:
//    - non-generic
//    - non-multicast (single-cast)
//    - matches a static method (no captured this)
//    - tagged [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
delegate float DensityFn(float3 p);

// 2. Static methods that match — each tagged with the delegate type.
//    [MonoPInvokeCallback] is required when called from native code on IL2CPP.
[BurstCompile(typeof(DensityFn))]
[MonoPInvokeCallback(typeof(DensityFn))]
static float SphereDensity(float3 p) {
    return math.length(p) - 1.0f;
}

[BurstCompile(typeof(DensityFn))]
[MonoPInvokeCallback(typeof(DensityFn))]
static float TorusDensity(float3 p) {
    var q = new float2(math.length(p.xz) - 0.7f, p.y);
    return math.length(q) - 0.3f;
}

// 3. Compile to function pointers — typically once at startup.
static readonly FunctionPointer<DensityFn> SpherePtr =
    BurstCompiler.CompileFunctionPointer<DensityFn>(SphereDensity);
static readonly FunctionPointer<DensityFn> TorusPtr =
    BurstCompiler.CompileFunctionPointer<DensityFn>(TorusDensity);

// 4. Pass into a job:
[BurstCompile]
struct RaymarchJob : IJobParallelFor {
    public FunctionPointer<DensityFn> Density;
    [WriteOnly] public NativeArray<float> Output;

    public void Execute(int i) {
        var p = IndexToPos(i);
        Output[i] = Density.Invoke(p);   // call through the function pointer
    }
}

// Schedule:
new RaymarchJob { Density = SpherePtr, Output = buf }.Schedule(N, 64).Complete();
```

Cited at `Runtime/BurstCompiler.cs:321` (`CompileFunctionPointer<T>`).

## `FunctionPointer<T>` struct

```csharp
public readonly struct FunctionPointer<T> {
    public FunctionPointer(IntPtr ptr);                   // line 38
    public IntPtr Value    { get; }                        // line 46 — raw native pointer
    public T      Invoke   { get; }                        // line 63 — DELEGATE INSTANCE, not a method
    public bool   IsCreated { get; }                       // line 75 — _ptr != IntPtr.Zero
}
```

Cited at `Runtime/FunctionPointer.cs`.

The crucial subtlety: **`.Invoke` is a property that returns a `T` (the delegate instance), not a method**. Each access creates a fresh `Marshal.GetDelegateForFunctionPointer<T>` allocation:

```csharp
// Line 68 inside the property getter:
get => Marshal.GetDelegateForFunctionPointer<T>(_ptr);
```

So this:

```csharp
for (int i = 0; i < n; i++)
    fp.Invoke(i);     // allocates a delegate every iteration
```

is much slower than this:

```csharp
var invoke = fp.Invoke;   // cache the delegate once
for (int i = 0; i < n; i++)
    invoke(i);
```

**Inside Burst-compiled code**, the optimizer collapses the property access to a direct call so the caching doesn't matter — but only inside Burst. From managed code, **always cache `.Invoke`** before a hot loop.

## Delegate constraints

`BurstCompiler.CompileFunctionPointer<T>(T method)` (`Runtime/BurstCompiler.cs:321`) requires:

1. `T` is a delegate type marked `[UnmanagedFunctionPointer(CallingConvention.Cdecl)]`.
2. The delegate is **non-generic** (`Func<int, int>` won't work; declare a concrete type).
3. The delegate is **non-multicast** (single-cast — the result of `+=` on multiple methods is not allowed).
4. `method` resolves to a `static` method (no captured `this`, no closure).
5. The static method is tagged `[BurstCompile(typeof(T))]` so Burst knows which delegate signature it implements.
6. `[MonoPInvokeCallback(typeof(T))]` is **required for IL2CPP builds** — without it, the native pointer points at a stub that throws on call.

The implementation pins the managed fallback delegate via `GCHandle.Alloc` so it isn't collected while the function pointer is alive.

## When to skip `FunctionPointer<T>`

If you have N implementations and the choice is **fixed at compile time per-job**, generics + a struct-typed dispatcher is faster than function pointers — the optimizer can inline:

```csharp
interface IDensityFn { float Invoke(float3 p); }

struct SphereFn : IDensityFn { public float Invoke(float3 p) => math.length(p) - 1.0f; }
struct TorusFn  : IDensityFn { public float Invoke(float3 p) => /* ... */; }

[BurstCompile]
struct RaymarchJob<TDensity> : IJobParallelFor where TDensity : struct, IDensityFn {
    public TDensity Density;
    public NativeArray<float> Output;
    public void Execute(int i) => Output[i] = Density.Invoke(IndexToPos(i));
}

// Schedule (the type parameter must be registered with [RegisterGenericJobType]):
new RaymarchJob<SphereFn> { Density = default, Output = buf }.Schedule(N, 64).Complete();
```

Trade-off: each `<T>` instantiation Burst-compiles separately (more compile time, more cache footprint). Use `FunctionPointer<T>` when the set of implementations is open-ended or registered at runtime; use generic specialisation when it's a closed set known at code-write time.

## Source citations

| Symbol                                  | File                                          |
|-----------------------------------------|-----------------------------------------------|
| `FunctionPointer<T>` struct             | `Runtime/FunctionPointer.cs:27`               |
| `FunctionPointer<T>(IntPtr)`            | `Runtime/FunctionPointer.cs:38`               |
| `FunctionPointer<T>.Value`              | `Runtime/FunctionPointer.cs:46`               |
| `FunctionPointer<T>.Invoke` (property)  | `Runtime/FunctionPointer.cs:63` (impl line 68: `Marshal.GetDelegateForFunctionPointer<T>`) |
| `FunctionPointer<T>.IsCreated`          | `Runtime/FunctionPointer.cs:75`               |
| `BurstCompiler.CompileFunctionPointer<T>` | `Runtime/BurstCompiler.cs:321`              |
| `BurstCompiler.SetExecutionMode`        | `Runtime/BurstCompiler.cs:147`                |
| `BurstCompiler.GetExecutionMode`        | `Runtime/BurstCompiler.cs:155`                |
