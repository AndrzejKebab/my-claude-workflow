# Unity.Burst local reference (com.unity.burst@1.8.x / Unity 6.3)

Canonical local reference for "what does this Burst attribute / API actually do" and "how do I make this code Burst-compile". Anchored to:

- **`com.unity.burst@6bb9aca3ef38`** at `Library/PackageCache/com.unity.burst@6bb9aca3ef38/`. Source-shipped: every public type lives in `Runtime/`, with sub-namespaces in `Runtime/CompilerServices/` and `Runtime/Intrinsics/`.

All `file:line` citations refer to that root verbatim. The `Runtime/` prefix is omitted in cites for brevity.

## Documents

- [`attributes.md`](attributes.md) — `[BurstCompile]`, its full property surface (`FloatMode`, `FloatPrecision`, `OptimizeFor`, `CompileSynchronously`, `Debug`, `DisableSafetyChecks`, `DisableDirectCall`), how it propagates to nested types and merges with assembly-level attributes. Plus `[NoAlias]`, `[BurstDiscard]`, `[BurstCompile(typeof(Foo))]` for static methods.

- [`compilation-context.md`](compilation-context.md) — what compiles in Burst (HPC# subset). The "entry-point only" rule (only the [BurstCompile]'d struct needs the attribute; helpers auto-compile from Burst context). When return-by-value structs are fine and when they aren't. Static methods → direct calls via the IL post-processor.

- [`function-pointers.md`](function-pointers.md) — `FunctionPointer<T>`, `BurstCompiler.CompileFunctionPointer<T>`, the delegate constraints (non-generic, non-multicast, static, `[UnmanagedFunctionPointer(Cdecl)]`). The `.Invoke` re-creation cost and the canonical caching pattern.

- [`shared-static.md`](shared-static.md) — `SharedStatic<T>.GetOrCreate<TContext>()` for reading shared state across Burst and managed boundaries. The hash-based identity, alignment, and the `Type.AssemblyQualifiedName` keying. Plus the size-mismatch gotcha.

- [`compiler-services.md`](compiler-services.md) — `CompilerServices/` namespace: `Hint.Likely/Unlikely/Assume`, `Loop.ExpectVectorized`, `Aliasing.ExpectAliased/NotAliased`, `Constant.IsConstantExpression`, `[SkipLocalsInit]`, `[AssumeRange]`, `[IgnoreWarning]`. When each is load-bearing.

- [`intrinsics.md`](intrinsics.md) — `Intrinsics/` namespaces (`X86.*`, `Arm.Neon.*`), the `IsXyzSupported` runtime-guard pattern, vector types `v64` / `v128` / `v256`. How the support guards branch out at compile-time on non-matching ISAs.

- [`verification.md`](verification.md) — confirming Burst actually compiled. Inspector window, console error filter, `BurstCompilerOptions.EnableBurstCompileSynchronously` for forcing sync compile in tests, the `unity-cli console --filter error` recipe.

- [`empirical-examples.md`](empirical-examples.md) — every `[BurstCompile]` in this project, bucketed by how it's parameterised. Default attribute, FloatMode-tweaked, struct-level vs method-level, with `FunctionPointer` patterns called out.

## Reading order for "is this code Burst-compatible?"

1. [`compilation-context.md`](compilation-context.md) — the HPC# subset and what's allowed in Execute.
2. [`attributes.md`](attributes.md) — pick the right attribute parameters (FloatMode/Precision matter for determinism vs throughput).
3. [`compiler-services.md`](compiler-services.md) — apply hints if you need to nudge the optimizer.
4. [`verification.md`](verification.md) — confirm compilation actually happened.

## What this docset deliberately does NOT cover

- The Burst compiler's IR / LLVM lowering — we treat Burst as a black box that takes HPC# in and produces native code out.
- Editor-side Burst Inspector internals (`Editor/` folder under `com.unity.burst`). Use it via the menu; we don't drive it programmatically.
- `Unity.Burst.CodeGen` (the IL post-processor). Internal-only; users never reference its types.
- AOT / standalone-build burst settings. Project ship config only — see Unity Manual.
