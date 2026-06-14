# Unity.Jobs local reference (Unity 6.3 / Collections 2.x)

Canonical local reference for "what does this Schedule overload actually accept" and "which job interface fits this work". Anchored to:

- **`UnityEngine.CoreModule.dll`** at `/home/midori/Unity/Hub/Editor/6000.3.14f1/Editor/Data/Managed/UnityEngine/UnityEngine.CoreModule.dll`. The core `Unity.Jobs` namespace (`IJob`, `IJobFor`, `IJobParallelFor`, `JobHandle`, `JobsUtility`) lives in this DLL — there is no `Library/PackageCache/com.unity.jobs` entry (the package was rolled into the engine in 2023).
- **`com.unity.collections@12999e356c23`** at `Library/PackageCache/com.unity.collections@12999e356c23/Unity.Collections/Jobs/`. Hosts the extra job interfaces shipped as source: `IJobParallelForBatch`, `IJobParallelForDefer`, `IJobFilter`, `RegisterGenericJobTypeAttribute`.
- **`com.unity.entities@8b72e8a7d7d1`** at `Library/PackageCache/com.unity.entities@8b72e8a7d7d1/Unity.Entities/IJobChunk.cs` etc. Adds entity-aware job interfaces (`IJobChunk`, `IJobEntity` — covered in `docs/unity/entities/`).

DLL-only types are cited via `ilspycmd` decompilation captured at `/tmp/unity-decompile/CoreModule/UnityEngine.CoreModule.decompiled.cs` (line numbers stable for that decompile; see [`decompilation-workflow.md`](decompilation-workflow.md) for how to refresh). Source-package types are cited at their PackageCache `file:line` directly. Every cited line has been verified against the source.

## Documents

- [`scheduling-overloads.md`](scheduling-overloads.md) — **start here**. The exact overload table for every job interface. Names every parameter (`arrayLength`, `innerloopBatchCount`, `indicesPerJobCount`, `dependsOn`, `dependency`) verbatim, lists ByRef variants, and explains the `ScheduleMode.Single` / `ScheduleMode.Parallel` / `ScheduleMode.Run` mapping. Use this when you would otherwise guess at named arguments.

- [`job-types.md`](job-types.md) — picking between `IJob`, `IJobFor`, `IJobParallelFor`, `IJobParallelForBatch`, `IJobParallelForTransform`, `IJobParallelForDefer`, `IJobFilter`. Each entry: `Execute` signature, dispatch model, when to choose it over the others, characteristic gotcha.

- [`dependencies.md`](dependencies.md) — `JobHandle`, `Complete`, `IsCompleted`, `CompleteAll`, `CombineDependencies`, `JobHandle.ScheduleBatchedJobs`. The "scheduled but not flushed" trap, why `Complete` on a `default(JobHandle)` is a no-op, and how to fan-out/fan-in N jobs through a single output handle.

- [`safety-and-attributes.md`](safety-and-attributes.md) — `[ReadOnly]` / `[WriteOnly]` / `[NativeDisableParallelForRestriction]` / `[NativeDisableContainerSafetyRestriction]` / `[DeallocateOnJobCompletion]`. Which attribute relaxes which AtomicSafetyHandle check, and the failure modes you trade for the perf.

- [`empirical-examples.md`](empirical-examples.md) — survey of every `Schedule`/`ScheduleParallel` call in this project's packages (`is.zori.volumetrics`, `is.zori.atmospherics`, `is.zori.heightfields`, `com.api-haus.steamdeck-deploy`) plus a sampling of canonical Unity package usage (Entities, Collections, Mathematics). Bucketed by interface. Use as a copy-from canon: "find the closest existing call site and mirror its overload + named-arg style".

- [`decompilation-workflow.md`](decompilation-workflow.md) — how to find the truth when you don't trust an LLM-written job call. Tier 1: PackageCache (source). Tier 2: Rider DecompilerCache (`~/.config/JetBrains/Rider*/resharper-host/DecompilerCache/decompiler/...` — fastest, but only populates on Rider visit). Tier 3: `ilspycmd` (bulk decompile any DLL). Includes the `dotnet tool install -g ilspycmd` install recipe and the right invocation for Unity engine modules.

## Reading order for the "wrong named argument" bug

The bug `job.Schedule(VoxelsPerTile, batchSize: 64).Complete();` does not compile against any of `IJob*Extensions.Schedule`. Diagnosis path:

1. [`scheduling-overloads.md`](scheduling-overloads.md) §"Named arguments cheat sheet" — the canonical parameter is `innerloopBatchCount` (IJobParallelFor / IJobFor.ScheduleParallel) or `indicesPerJobCount` (IJobParallelForBatch). `batchSize` is the **internal** field name on `Unity.Jobs.LowLevel.Unsafe.JobRanges.BatchSize` (`UnityEngine.CoreModule.decompiled.cs:2775`), not a public parameter — easy mistranscription.
2. [`job-types.md`](job-types.md) — confirm whether the work is per-index (`IJobParallelFor`) or per-batch (`IJobParallelForBatch`). The two have different parameter names; picking the right interface settles the named-arg question.
3. [`empirical-examples.md`](empirical-examples.md) — find a sibling call in the same package and mirror its parameter style.

## What this docset deliberately does NOT cover

- `Unity.Entities`-side jobs (`IJobChunk`, `IJobEntity`) — see [`docs/unity/entities/`](../entities/).
- The legacy `JobComponentSystem` and `Entities.ForEach` codegen (deprecated in Entities 1.x in favour of `ISystem` + `SystemAPI.Query`). A consuming project's DOTS engine uses the modern `ISystem` path — for entity systems and the entity-aware jobs they schedule, see [`docs/unity/entities/system-types.md`](../entities/system-types.md) and [`../entities/`](../entities/index.md).
- Burst-specific concerns (`[BurstCompile]`, intrinsics, `FunctionPointer<T>`) — see [`docs/unity/burst/`](../burst/).
- `JobsUtility.JobScheduleParameters` direct construction. The `Unity.Jobs.LowLevel.Unsafe` API is shown in `scheduling-overloads.md` only because every public `Schedule*` extension forwards to it; do not call it directly from project code.
