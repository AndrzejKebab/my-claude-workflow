# Verifying Burst actually compiled

How to know whether your `[BurstCompile]` attribute is doing what you think it is.

## The four states a Burst job can be in

1. **Native, hot** — Burst-compiled, called at least once, running native code.
2. **Managed fallback, compiling in background** — first call after a recompile. Job runs in the C# scaffold while Burst compiles asynchronously.
3. **Managed fallback, compile failed** — the source had non-HPC# code. Job permanently runs in mono. **Logs an error to the Unity console** with the line number of the offending construct.
4. **Disabled by global** — `BurstCompiler.Options.EnableBurstCompilation = false` (e.g. via `--burst-disable-compilation` CLI arg or `UNITY_BURST_DISABLE_COMPILATION` env var). Everything runs managed, no errors.

## Confirm via the Unity console

Project canon (`docs/CLAUDE.md` § "unity-cli console"):

```bash
unity-cli console --filter error --lines 5
```

Burst compile errors emit to the standard Unity console with messages like:

```
Burst error BC1019: An exception was thrown by the Cecil ResolveType — likely a managed reference in HPC# code at MyJob.Execute (line 42).
```

If `unity-cli console --filter error` is empty after a recompile, no Burst errors fired. If you see Burst-prefixed errors, fix them — Burst won't silently degrade to managed unless you opted out.

## Confirm via the Burst Inspector

Window → Analysis → Burst Inspector. Pick the job from the left panel. The right panel shows three tabs:

1. **Branches** — list of all `[BurstCompile]` entry points Burst sees.
2. **Disassembly** — native assembly Burst produced for the selected target. Empty = not compiled. Non-empty = compiled.
3. **Targets** — pick `x86_64_sse4`, `x86_64_avx2`, `arm64_neon`, etc. to see per-target output.

If a job appears in Branches but Disassembly is empty, the job pre-compiled with errors. Switch to the **Console** tab and filter to "Burst" to see why.

## Force sync compile in tests

```csharp
[BurstCompile(CompileSynchronously = true)]
struct PerfRegressionGuardJob : IJobParallelFor { ... }
```

The first call to `Schedule` blocks the calling thread until Burst finishes. Use this in performance tests where you measure the job and don't want the first measurement to capture managed-fallback cost.

**Do not use in shipping** — first invocation hitches multi-seconds.

## Force sync compile globally (editor flag)

`Edit → Preferences → Jobs → Burst Compile Synchronously` toggles `BurstCompilerOptions.EnableBurstCompileSynchronously` (cited `Runtime/BurstCompilerOptions.cs:316`). Forces every job to compile before its first use. Massive editor compile-time penalty; useful when you want **deterministic test runs** to never hit the managed fallback.

## Disable Burst entirely

`Jobs → Burst → Enable Compilation` (toggle) flips `BurstCompilerOptions.EnableBurstCompilation` (cited `Runtime/BurstCompilerOptions.cs:262`). Everything runs managed. Use to A/B test "is Burst the bottleneck or my algorithm?".

CLI: `--burst-disable-compilation` flag to the editor / player. Env: `UNITY_BURST_DISABLE_COMPILATION=1`.

## Force safety checks ON globally

`BurstCompilerOptions.ForceEnableBurstSafetyChecks = true` (cited `Runtime/BurstCompilerOptions.cs:357`) overrides the per-job `[BurstCompile(DisableSafetyChecks = true)]`. Use when you have a job-level `DisableSafetyChecks` and want to verify it's still correct.

## Recompile-after-edit checklist

After editing a `[BurstCompile]` source file:

```bash
unity-recompile                                       # focus + refresh + sleep 30 + console-error tail
unity-cli console --filter error --lines 5            # double-check no Burst errors
```

`unity-recompile` is the project-canonical wrapper (project `CLAUDE.md` § "Recompile Protocol"); it handles focus, deferred init, and the post-recompile freeze. Always use it — never raw `unity-cli editor refresh`.

## When `[BurstCompile]` produces no native code silently

If a job has `[BurstCompile]` but **runs in managed mode with no error**, common causes:

1. **`BurstCompiler.Options.EnableBurstCompilation == false`** — toggled off via menu, env var, or CLI flag. Re-enable.
2. **The job's reflection data wasn't registered.** For closed types, codegen handles this automatically. For generic jobs (`MyJob<MyParam>` for runtime-known `MyParam`), you must add `[assembly: RegisterGenericJobType(typeof(MyJob<MyParam>))]` in the assembly. Without it, the `SharedStatic<IntPtr> jobReflectionData` slot remains `IntPtr.Zero`, and `JobsUtility.Schedule` falls back to managed.
3. **The job is an inner type of a generic** without `[RegisterGenericJobType]`. Same fix.

Diagnosis: in Burst Inspector, search for the job name. If absent → reflection-data not registered. If present but Disassembly empty → look at console errors.

## Source citations

| Setting / API                                | File                                          |
|----------------------------------------------|-----------------------------------------------|
| `BurstCompilerOptions.EnableBurstCompilation` | `Runtime/BurstCompilerOptions.cs:262`        |
| `BurstCompilerOptions.EnableBurstCompileSynchronously` | `Runtime/BurstCompilerOptions.cs:316` |
| `BurstCompilerOptions.EnableBurstSafetyChecks` | `Runtime/BurstCompilerOptions.cs:333`       |
| `BurstCompilerOptions.ForceEnableBurstSafetyChecks` | `Runtime/BurstCompilerOptions.cs:357`  |
| `BurstCompilerOptions.EnableBurstDebug`      | `Runtime/BurstCompilerOptions.cs:375`         |
| `[RegisterGenericJobType]`                   | `Library/PackageCache/com.unity.collections@.../Unity.Collections/Jobs/RegisterGenericJobTypeAttribute.cs` |
| Project recompile wrapper                    | `~/_dev/my-claude-workflow/bin/unity-recompile` |
| Project console-error recipe                 | `unity-cli console --filter error --lines 5` (CLAUDE.md) |
