# Unity.Jobs local reference

Canonical local reference for "what does this Schedule overload actually accept" and "which job interface fits this work". Anchored to:

- **`UnityEngine.CoreModule.dll`** under the installed Unity Editor's `Editor/Data/Managed/UnityEngine/` directory. The core `Unity.Jobs` namespace (`IJob`, `IJobFor`, `IJobParallelFor`, `JobHandle`, `JobsUtility`) lives in this DLL — there is no `Library/PackageCache/com.unity.jobs` entry.
- **Installed `com.unity.collections` package** at `Library/PackageCache/com.unity.collections@<version>/Unity.Collections/Jobs/`. Hosts extra job interfaces shipped as source: `IJobParallelForBatch`, `IJobParallelForDefer`, `IJobFilter`, and `RegisterGenericJobTypeAttribute`.
- **Installed `com.unity.entities` package** at `Library/PackageCache/com.unity.entities@<version>/Unity.Entities/`. Adds entity-aware job interfaces (`IJobChunk`, `IJobEntity` — covered in `docs/unity/entities/`).

DLL-only types can be inspected with `ilspycmd`; see [`decompilation-workflow.md`](decompilation-workflow.md) for how to produce a local decompilation. Source-package types can be inspected directly in `Library/PackageCache`. Verify cited lines against the package and Editor versions used by the current project.

## Documents

- [`scheduling-overloads.md`](scheduling-overloads.md) — **start here**. The exact overload table for every job interface. Names every parameter (`arrayLength`, `innerloopBatchCount`, `indicesPerJobCount`, `dependsOn`, `dependency`) verbatim, lists ByRef variants, and explains the `ScheduleMode.Single` / `ScheduleMode.Parallel` / `ScheduleMode.Run` mapping. Use this when you would otherwise guess at named arguments.

- [`job-types.md`](job-types.md) — picking between `IJob`, `IJobFor`, `IJobParallelFor`, `IJobParallelForBatch`, `IJobParallelForTransform`, `IJobParallelForDefer`, `IJobFilter`. Each entry: `Execute` signature, dispatch model, when to choose it over the others, characteristic gotcha.

- [`dependencies.md`](dependencies.md) — `JobHandle`, `Complete`, `IsCompleted`, `CompleteAll`, `CombineDependencies`, `JobHandle.ScheduleBatchedJobs`. The "scheduled but not flushed" trap, why `Complete` on a `default(JobHandle)` is a no-op, and how to fan-out/fan-in N jobs through a single output handle.

- [`safety-and-attributes.md`](safety-and-attributes.md) — `[ReadOnly]` / `[WriteOnly]` / `[NativeDisableParallelForRestriction]` / `[NativeDisableContainerSafetyRestriction]` / `[DeallocateOnJobCompletion]`. Which attribute relaxes which AtomicSafetyHandle check, and the failure modes you trade for the perf.

- [`empirical-examples.md`](empirical-examples.md) — workload-balancing examples for `IJobParallelFor`: moderate batches for uniform voxel work and batch size `1` for heterogeneous region work.

- [`decompilation-workflow.md`](decompilation-workflow.md) — how to verify a job API against source or decompiled assemblies: PackageCache first, IDE decompiler second, and `ilspycmd` for bulk inspection.

## Reading order for the "wrong named argument" bug

The bug `job.Schedule(VoxelsPerTile, batchSize: 64).Complete();` does not compile against any of `IJob*Extensions.Schedule`. Diagnosis path:

1. [`scheduling-overloads.md`](scheduling-overloads.md) §"Named arguments cheat sheet" — the canonical parameter is `innerloopBatchCount` (IJobParallelFor / IJobFor.ScheduleParallel) or `indicesPerJobCount` (IJobParallelForBatch). `batchSize` is the **internal** field name on `Unity.Jobs.LowLevel.Unsafe.JobRanges.BatchSize` (`UnityEngine.CoreModule.decompiled.cs:2775`), not a public parameter — easy mistranscription.
2. [`job-types.md`](job-types.md) — confirm whether the work is per-index (`IJobParallelFor`) or per-batch (`IJobParallelForBatch`). The two have different parameter names; picking the right interface settles the named-arg question.
3. [`empirical-examples.md`](empirical-examples.md) — choose an initial batch size based on workload cost and variance, then profile it.

## What this docset deliberately does NOT cover

- `Unity.Entities`-side jobs (`IJobChunk`, `IJobEntity`) — see [`docs/unity/entities/`](../entities/).
- The legacy `JobComponentSystem` and `Entities.ForEach` codegen (deprecated in Entities 1.x in favour of `ISystem` + `SystemAPI.Query`). A consuming project's DOTS engine uses the modern `ISystem` path — for entity systems and the entity-aware jobs they schedule, see [`docs/unity/entities/system-types.md`](../entities/system-types.md) and [`../entities/`](../entities/index.md).
- Burst-specific concerns (`[BurstCompile]`, intrinsics, `FunctionPointer<T>`) — see [`docs/unity/burst/`](../burst/).
- `JobsUtility.JobScheduleParameters` direct construction. The `Unity.Jobs.LowLevel.Unsafe` API is shown in `scheduling-overloads.md` only because every public `Schedule*` extension forwards to it; do not call it directly from project code.
