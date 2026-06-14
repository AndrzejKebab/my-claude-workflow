# Burst attributes

The full surface area of `[BurstCompile]` and adjacent attributes. Every property name and default cited from `Runtime/BurstCompileAttribute.cs`.

## `[BurstCompile]`

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Struct
              | AttributeTargets.Assembly, AllowMultiple = false, Inherited = false)]
public class BurstCompileAttribute : Attribute {
    public BurstCompileAttribute() { }                                                 // line 212
    public BurstCompileAttribute(FloatPrecision floatPrecision, FloatMode floatMode);   // line 230
    public FloatMode      FloatMode      { get; set; } = FloatMode.Default;             // line 118
    public FloatPrecision FloatPrecision { get; set; } = FloatPrecision.Standard;       // line 127
    public bool CompileSynchronously     { get; set; } = false;                         // line 135
    public bool Debug                    { get; set; } = false;                         // line 151
    public bool DisableSafetyChecks      { get; set; } = false;                         // line 167
    public bool DisableDirectCall        { get; set; } = false;                         // line 184
    public OptimizeFor OptimizeFor       { get; set; } = OptimizeFor.Default;           // line 196
}
```

Citation: `Runtime/BurstCompileAttribute.cs`.

### Targets

- **Struct / Class**: marks the type as containing Burst-compilable code. Required on a job struct (`[BurstCompile] struct MyJob : IJobParallelFor { ... }`). Propagates to nested static methods on the type.
- **Method**: marks a static method for direct-call IL post-processing (the IL post-processor rewrites managed call sites to call the Burst native function pointer directly). Requires the method to be `static`.
- **Assembly**: `[assembly: BurstCompile(FloatMode = FloatMode.Fast)]` sets defaults for every nested `[BurstCompile]` in the assembly. Method-level attributes override.

### `FloatMode` (`Runtime/BurstCompileAttribute.cs`)

- `Default` — Unity-decided. Currently maps to `Strict`-like behaviour but is not contractually so.
- `Strict` — IEEE-strict. No reordering of FP ops, no fused-multiply-add unless explicitly written, no `x * 0.0 = 0.0` simplifications. Slowest, most predictable.
- `Deterministic` — Strict + cross-platform/compiler determinism. Required if two builds must produce bitwise-identical FP results.
- `Fast` — Reorder, FMA, `x * 0.0 = 0.0`, contract `(a+b)*c = a*c + b*c`. Allows vectorisation of more loops. Use when you don't care about NaN/Inf semantics or sub-ulp differences.

Per-method override:
```csharp
[BurstCompile(FloatMode = FloatMode.Fast)]
struct VectorMathJob : IJobParallelFor { ... }
```

### `FloatPrecision`

- `Standard` — float32 / float64 as written.
- `Low` / `Medium` / `High` — affect built-in `math.sin`/`cos`/`exp`/`log`/etc. precision: `Low` permits faster approximations with up to a few ulps of error.

`Low` only affects Unity.Mathematics intrinsics (the builtin trig/transcendental table); plain `+`, `*`, `sqrt` are unchanged.

### `CompileSynchronously`

- Default `false` — Burst compiles asynchronously. The first call to a job runs the **managed fallback** while Burst compiles in the background; subsequent calls run native.
- `true` — first call blocks until Burst finishes. Use in tests where you want to be sure native code is what's measured. **Do not use in shipping** (multi-second hitch on first invocation).

### `Debug`

- `true` — disables all optimizations, emits full debug info, allows attaching a native debugger.
- Order-of-magnitude perf penalty. Use only when stepping through Burst output in a debugger.

### `DisableSafetyChecks` / `DisableDirectCall`

- `DisableSafetyChecks` — drops AtomicSafetyHandle checks, NativeContainer index bounds, etc. **inside the Burst-compiled job**. The global "Force On" setting in `BurstCompilerOptions.ForceEnableBurstSafetyChecks` overrides this.
- `DisableDirectCall` — for static `[BurstCompile]` methods. Disables the IL post-processor's "rewrite call site to native" pass. Caller dispatches through the managed delegate fallback. Useful when you want the method available as both a managed function and a Burst function pointer.

### `OptimizeFor`

```csharp
public enum OptimizeFor { Default, Performance, Size, FastCompilation, Balanced }
```

- `Default` — Unity-decided per build target.
- `Performance` — full LLVM `-O3`. Maximum runtime speed, highest compile time.
- `Size` — `-Os`. Smaller code, slightly slower at runtime.
- `FastCompilation` — `-O1` or below. Fastest Burst compile time, slowest runtime. Useful in iteration-heavy editor flows.
- `Balanced` — middle ground.

## Attribute merging

Assembly-level `[BurstCompile]` attributes serve as **defaults**; type-/method-level attributes **override individual properties**, not the whole attribute. Internal merge function is `BurstCompilerOptions.MergeAttributes` (cited `Runtime/BurstCompilerOptions.cs:519`).

Example:
```csharp
// Assembly:
[assembly: BurstCompile(FloatMode = FloatMode.Fast)]

// Method gets FloatMode = Fast (from assembly) AND FloatPrecision = Low (own value):
[BurstCompile(FloatPrecision = FloatPrecision.Low)]
static void Kernel() { }
```

## `[NoAlias]`

```csharp
[AttributeUsage(AttributeTargets.Parameter | AttributeTargets.Field
              | AttributeTargets.Struct    | AttributeTargets.ReturnValue)]
public class NoAliasAttribute : Attribute { }
```

Cited `Runtime/NoAliasAttribute.cs:8`.

Tells Burst the marked pointer / field / struct does not alias other pointers visible in the function. Enables aggressive load-store reordering and SIMD vectorisation. **Wrong annotation = silent wrong code** — Burst will hoist/reorder loads under the assumption you gave it.

Use sparingly. A correct application: a kernel that takes two `NativeArray<float>*`s and is called only from sites where the arrays are different. Mark both with `[NoAlias]` and Burst can vectorise the load/store pairs.

## `[BurstDiscard]`

Marks a method whose body is **stripped from Burst-compiled output** but kept in managed/mono. Use for `Debug.Log` calls, profiler markers, or any other managed-only API you call from inside a `[BurstCompile]` method.

```csharp
[BurstDiscard]
static void LogIfManaged(string msg) {
    UnityEngine.Debug.Log(msg);    // never executed when called from Burst context
}
```

When called from a Burst-compiled function, the call is replaced by a no-op. When called from managed/mono, the body runs normally. Used internally by `IJobExtensions.JobStruct<T>.Initialize` (`UnityEngine.CoreModule.decompiled.cs:2293`) to stash reflection data without entering Burst.

`BurstDiscardAttribute` is not in the public Burst Runtime/ folder — it's defined in `UnityEngine.CoreModule.dll`. Reference it as `using Unity.Burst;` in code; `SharpTool_ViewDefinition Unity.Burst.BurstDiscardAttribute` to inspect.

## `[BurstCompile(typeof(MyDelegate))]`

The single-arg form of `[BurstCompile]` tagging a static method as **the implementation of a delegate type**, used with `BurstCompiler.CompileFunctionPointer<T>`:

```csharp
[BurstCompile(typeof(MyCallback))]
static int MyImpl(int x) => x * 2;

delegate int MyCallback(int x);

var fp = BurstCompiler.CompileFunctionPointer<MyCallback>(MyImpl);
int result = fp.Invoke(21);
```

See [`function-pointers.md`](function-pointers.md) for the full pattern.

## Source citations

| Attribute / property             | File                                        |
|----------------------------------|---------------------------------------------|
| `BurstCompileAttribute`          | `Runtime/BurstCompileAttribute.cs:212+`     |
| `FloatMode`                      | `Runtime/BurstCompileAttribute.cs:118`      |
| `FloatPrecision`                 | `Runtime/BurstCompileAttribute.cs:127`      |
| `CompileSynchronously`           | `Runtime/BurstCompileAttribute.cs:135`      |
| `Debug`                          | `Runtime/BurstCompileAttribute.cs:151`      |
| `DisableSafetyChecks`            | `Runtime/BurstCompileAttribute.cs:167`      |
| `DisableDirectCall`              | `Runtime/BurstCompileAttribute.cs:184`      |
| `OptimizeFor`                    | `Runtime/BurstCompileAttribute.cs:196`      |
| `NoAliasAttribute`               | `Runtime/NoAliasAttribute.cs:8`             |
| Attribute merge logic            | `Runtime/BurstCompilerOptions.cs:519`       |
| `BurstDiscardAttribute`          | `UnityEngine.CoreModule.dll` (decompile)    |
