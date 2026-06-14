# `Unity.Burst.CompilerServices` — hints, intrinsics, attributes

The contents of `Runtime/CompilerServices/` — knobs that nudge the optimizer or assert invariants Burst can use.

## `Hint` — branch prediction & assumptions

```csharp
public static class Hint {
    public static bool Likely(bool condition);
    public static bool Unlikely(bool condition);
    public static void Assume(bool condition);
}
```

- `Hint.Likely(c)` / `Hint.Unlikely(c)` — pass-through that returns `c`, but tells Burst's branch-weight heuristic which side is the hot path. Affects `if`/`while` codegen (preferred fall-through, branch hint metadata to LLVM).
- `Hint.Assume(c)` — declares `c` is true at this point. Burst can use it for invariant-based optimization (eliminating bounds checks, removing dominated branches). **Wrong assumption = miscompile.** No runtime check.

Use sparingly. Hot inner-loop branches are the only place where `Likely`/`Unlikely` measurably help.

## `Loop` — vectorisation guards (experimental)

```csharp
public static class Loop {
    public static void ExpectVectorized();
    public static void ExpectNotVectorized();
}
```

- `Loop.ExpectVectorized()` placed inside a `for` loop — **fails the Burst compile** with a diagnostic if the loop wasn't auto-vectorised. Used to guard "this kernel must SIMD-ise".
- `Loop.ExpectNotVectorized()` — opposite. Used to assert a known-non-vectorisable loop stayed scalar.

Both require defining `UNITY_BURST_EXPERIMENTAL_LOOP_INTRINSICS` in the project (Player Settings → Scripting Define Symbols). Off by default.

## `Aliasing` — pointer disjointness assertions

```csharp
public static class Aliasing {
    public static void ExpectAliased(void* a, void* b);
    public static void ExpectAliased<A, B>(in A a, in B b);
    public static void ExpectNotAliased(void* a, void* b);
    public static void ExpectNotAliased<A, B>(in A a, in B b);
}
```

Burst-compile-time assertions. `ExpectNotAliased(a, b)` triggers a compile error if Burst's alias analysis thinks `a` and `b` could overlap. Used to guard a kernel that **requires** non-aliasing (e.g. one that you also tagged `[NoAlias]`).

Combine with `[NoAlias]` to make the contract bidirectional: the attribute tells Burst "trust me", the `ExpectNotAliased` asserts "and verify".

## `Constant.IsConstantExpression`

```csharp
public static class Constant {
    public static bool IsConstantExpression<T>(T t);
    public static unsafe bool IsConstantExpression(void* t);
}
```

Returns `true` (at Burst compile time) if `t` is a known compile-time constant. Used to gate specialisation:

```csharp
[BurstCompile]
static float Pow(float x, int n) {
    if (Constant.IsConstantExpression(n)) {
        // n is known at compile time — unroll.
        return n switch {
            0 => 1f, 1 => x, 2 => x * x, 3 => x * x * x,
            _ => SlowPow(x, n)
        };
    }
    return SlowPow(x, n);
}
```

## `[SkipLocalsInit]` — skip zero-init of stack locals

```csharp
[SkipLocalsInit]
static void Kernel() {
    Span<float> tmp = stackalloc float[64];   // not zeroed
    // ... fill tmp before reading
}
```

Saves the zero-fill of stackalloc'd buffers in hot kernels. **Wrong use = read uninitialised stack memory.** Project rule: only on functions that immediately and unconditionally write every byte of every stack local before reading.

## `[AssumeRange(min, max)]`

```csharp
[BurstCompile]
static int LookupSafe([AssumeRange(0, 1023)] int index, NativeArray<int> table) {
    return table[index];   // bounds check eliminated — Burst trusts the range
}
```

Available as `[AssumeRange(long, long)]` and `[AssumeRange(ulong, ulong)]`. Closed interval `[min, max]`. Used to communicate value-range invariants the C# type system can't express.

## `[IgnoreWarning(int warningId)]`

Suppress a specific Burst diagnostic on a single method. Use only when you've confirmed the warning is a false positive — Burst's diagnostics catch real bugs.

## `[Spmd]` (experimental)

```csharp
[Spmd] static void ProcessLane(...) { ... }
```

Marks a method to be compiled as **SPMD** (Single Program Multiple Data — like an ISPC kernel). Calls to it are auto-vectorised across SIMD lanes. Requires `UNITY_BURST_EXPERIMENTAL_SPMD_ATTRIBUTE`. Off by default.

## When each is load-bearing

| API                                | Use when…                                                              |
|------------------------------------|------------------------------------------------------------------------|
| `Hint.Likely / Unlikely`           | Hot inner-loop branch with a known >90% bias.                          |
| `Hint.Assume`                      | Range or pointer-disjointness assertion the compiler can't infer.      |
| `Loop.ExpectVectorized`            | Kernel performance regresses if vectorisation breaks. CI guard.        |
| `Aliasing.ExpectNotAliased`        | Pair with `[NoAlias]` to verify the assumption.                        |
| `Constant.IsConstantExpression`    | Specialise for compile-time-constant arguments.                        |
| `[SkipLocalsInit]`                 | Stack buffer fully written before any read.                            |
| `[AssumeRange]`                    | Eliminate bounds-check on indexed access with known clamp.             |
| `[IgnoreWarning]`                  | Confirmed false-positive diagnostic. Comment with reasoning.           |

## Source citations

`Runtime/CompilerServices/` directory (file paths inferred — confirm with `SharpTool_ViewDefinition` or `find /mnt/archive4/UNITY/Projects/woweyreey/Library/PackageCache/com.unity.burst@*/Runtime/CompilerServices -name '*.cs'`):

- `HintAttribute.cs` — `Hint.Likely/Unlikely/Assume`
- `LoopAttributes.cs` — `Loop.ExpectVectorized/ExpectNotVectorized`
- `AliasingAttribute.cs` — `Aliasing.ExpectAliased/NotAliased`
- `ConstantAttribute.cs` — `Constant.IsConstantExpression`
- `SkipLocalsInitAttribute.cs`
- `AssumeRangeAttribute.cs`
- `IgnoreWarningAttribute.cs`
- `SpmdAttribute.cs`
