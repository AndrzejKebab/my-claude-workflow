# Picking the right job interface

Decision tree: pick the interface that matches **what `Execute` is called with**, then [`scheduling-overloads.md`](scheduling-overloads.md) tells you the named arguments.

## Decision tree

1. **Single one-shot work item** (no iteration) → `IJob`. `Execute()` runs once on a worker thread.
2. **Indexed for-loop, ordered, sequential**, must run in index order on a single worker → `IJobFor` + `Schedule` (no `Parallel`). E.g. building a prefix-sum array.
3. **Indexed for-loop, parallel work-stealing, no ordering required** →
   - **Per-index work** (each `Execute(int index)` operates on one element) → `IJobParallelFor` (or `IJobFor.ScheduleParallel`).
   - **Per-batch work** (each `Execute(int startIndex, int count)` loops internally over `count` elements — useful when you want stack state shared across the batch, e.g. accumulators, pre-computed batch transforms, sub-array views) → `IJobParallelForBatch`.
4. **Iteration count not known until a previous job finishes** (e.g. parallel-for over the populated entries of a `NativeList<T>` written by a producer job) → `IJobParallelForDefer`.
5. **Per-Transform work**, parallel, with `TransformAccess` access to `Transform.localPosition`/`localRotation`/`localScale` → `IJobParallelForTransform`.
6. **"Select-where" filter** producing a `NativeList<int>` of indices that pass a predicate → `IJobFilter`.
7. **ECS-aware iteration over chunks** (Unity.Entities) → `IJobChunk` or `IJobEntity`. See [`docs/unity/entities/`](../entities/).

## `IJob` — one task

```csharp
[BurstCompile]
struct CountingJob : IJob {
    [ReadOnly]  public NativeArray<int> Input;
    [WriteOnly] public NativeArray<int> Sum;
    public void Execute() {
        int s = 0;
        for (int i = 0; i < Input.Length; i++) s += Input[i];
        Sum[0] = s;
    }
}

new CountingJob { Input = a, Sum = sum }.Schedule(prevHandle).Complete();
```

Use when the whole task is sequential or fits comfortably on one worker. Frees a thread, no batching overhead.

Project example: `OctreeBuilder.cs:49` (`is.zori.volumetrics`) — `job.Schedule().Complete();` for a CPU octree build.

## `IJobFor` — sequential indexed for-loop

```csharp
[BurstCompile]
struct PrefixSumJob : IJobFor {
    public NativeArray<int> Data;
    public void Execute(int i) {
        if (i > 0) Data[i] += Data[i - 1];   // depends on previous index — must be sequential
    }
}

new PrefixSumJob { Data = a }.Schedule(arrayLength: a.Length, dependency: prev);
```

`IJobFor.Schedule` differs from `IJobParallelFor.Schedule` — it's **single-threaded with index ordering**. Use only when index `i` reads results written at index `i-1` (or similar dependency).

If you also want a parallel version of the same job struct, the same `IJobFor` type can be scheduled with `ScheduleParallel(arrayLength, innerloopBatchCount, dependency)`. This is the polymorphic two-mode pattern that distinguishes `IJobFor` from `IJobParallelFor`.

## `IJobParallelFor` — parallel per-index

```csharp
[BurstCompile]
struct VoxelTileFillJob : IJobParallelFor {
    [ReadOnly]  public int3 TileWorldCoord;
    [WriteOnly] public NativeArray<float> DensityOut;
    public void Execute(int voxelIndex) {
        // independent work per voxel
        DensityOut[voxelIndex] = ComputeDensity(voxelIndex);
    }
}

new VoxelTileFillJob { ... }.Schedule(arrayLength: VoxelsPerTile, innerloopBatchCount: 64).Complete();
```

The default. Use when each index's work is independent.

`innerloopBatchCount` heuristics: Unity divides `arrayLength` into chunks of size `innerloopBatchCount` and dispatches them across workers. Too small → scheduling overhead dominates. Too large → poor load balance. Typical values: 32–128 for cheap per-index work, 1–16 for expensive per-index work, 1 for very heterogeneous workloads. **Match to roughly one worker's worth of work per chunk** (~10–100 µs).

Project example: `VoxelTileFiller.cs:54` (`is.zori.volumetrics`) — `job.Schedule(VoxelsPerTile, 64).Complete();` (positional). With `VoxelsPerTile = 16³ = 4096` and `innerloopBatchCount = 64` → 64 batches of 64 voxels, comfortably more than the worker count.

## `IJobParallelForBatch` — parallel per-batch

```csharp
[BurstCompile]
struct AccumulateBatchJob : IJobParallelForBatch {
    [ReadOnly]  public NativeArray<float> Input;
    [NativeDisableParallelForRestriction] public NativeArray<float> PerBatchSum;
    public void Execute(int startIndex, int count) {
        float s = 0;
        for (int i = startIndex; i < startIndex + count; i++) s += Input[i];
        PerBatchSum[startIndex / count] = s;
    }
}

new AccumulateBatchJob { ... }.ScheduleParallel(
    arrayLength: input.Length,
    indicesPerJobCount: 256,
    dependsOn: prev
);
```

Pick this over `IJobParallelFor` when:
- You want **one buffer per batch** (e.g. write per-batch reductions; write to a sub-array via `NativeArray.GetSubArray(startIndex, count)`).
- You want **stack-local state shared across the batch** (accumulators, pre-computed common transform, etc.).

Note `IJobParallelForBatch` is in `com.unity.collections` (source-shipped), not the engine. Reference path: `Library/PackageCache/com.unity.collections@.../Unity.Collections/Jobs/IJobParallelForBatch.cs:18`.

## `IJobParallelForDefer` — defer length to job-start time

When the producer of the work is itself a job:

```csharp
NativeList<int> indices = ...;
JobHandle producer = new ProduceIndicesJob { Output = indices }.Schedule();

// Consumer schedules WITHOUT knowing indices.Length — Unity reads it at job-start.
JobHandle consumer = new ConsumeJob { Indices = indices.AsDeferredJobArray() }
    .Schedule(indices, innerloopBatchCount: 32, dependsOn: producer);
```

Cited at `Library/PackageCache/com.unity.collections@.../Unity.Collections/Jobs/IJobParallelForDefer.cs`. Without `Defer` you'd have to `producer.Complete()` on the main thread to read `indices.Length` before scheduling `consumer`, breaking the job graph.

## `IJobParallelForTransform` — parallel per-Transform

```csharp
[BurstCompile]
struct MoveTransformsJob : IJobParallelForTransform {
    public float3 Delta;
    public void Execute(int index, TransformAccess transform) {
        transform.localPosition += Delta;
    }
}

TransformAccessArray transforms = ...;  // Unity.Jobs.TransformAccessArray
new MoveTransformsJob { Delta = ... }.Schedule(transforms, dependsOn: prev);
```

The job-system batches transforms by hierarchy (children of the same parent must serialise their writes). For read-only access, use `ScheduleReadOnly(transforms, batchSize: 32, dependsOn: prev)` — this is the **only** scheduling overload anywhere that uses the public name `batchSize`.

## `IJobFilter` — predicate filter

```csharp
[BurstCompile]
struct VisibleFilter : IJobFilter {
    [ReadOnly] public NativeArray<float3> Positions;
    public float CullDistance;
    public bool Execute(int index) => math.length(Positions[index]) < CullDistance;
}

NativeList<int> kept = new(Allocator.TempJob);
new VisibleFilter { Positions = ps, CullDistance = 50 }
    .ScheduleAppend(kept, arrayLength: ps.Length, batchSize: 64, dependsOn: prev);
```

Cited at `Library/PackageCache/com.unity.collections@.../Unity.Collections/Jobs/IJobFilter.cs`. The `Schedule*` overloads append matching indices to the output `NativeList<int>`.

## When to scaffold a custom job interface

The `[JobProducerType(typeof(MyExecutor<>))]` attribute (cited `UnityEngine.CoreModule.decompiled.cs:2754`) lets you author **your own** job interface that the job system recognises. The producer type provides a `static Execute(ref T, IntPtr, IntPtr, ref JobRanges, int)` matching the same signature `IJobParallelForExtensions.ParallelForJobStruct<T>` uses.

Almost no project code needs this — it's how `Unity.Collections` ships `IJobParallelForBatch` / `IJobFilter` etc. Exceptions: writing a low-level scheduling primitive (e.g. `IJobParallelForChunkBlock` for spatial-locality sweeps). If you find yourself wanting one, **first check** `Unity.Collections.Jobs/` and `Unity.Entities/IJobChunk.cs` — odds are an existing producer fits.

## Quick chooser table

| What `Execute` looks like                    | Interface                       | Schedule shape                                                    |
|----------------------------------------------|---------------------------------|-------------------------------------------------------------------|
| `void Execute()`                             | `IJob`                          | `Schedule(dependsOn: prev)`                                       |
| `void Execute(int i)` — sequential           | `IJobFor`                       | `Schedule(arrayLength, dependency)`                               |
| `void Execute(int i)` — parallel             | `IJobFor` or `IJobParallelFor`  | `ScheduleParallel(arrayLength, innerloopBatchCount, dependency)` <br> `Schedule(arrayLength, innerloopBatchCount, dependsOn)` |
| `void Execute(int start, int count)`         | `IJobParallelForBatch`          | `ScheduleParallel(arrayLength, indicesPerJobCount, dependsOn)`    |
| `void Execute(int i, TransformAccess t)`     | `IJobParallelForTransform`      | `Schedule(transforms, dependsOn)` <br> `ScheduleReadOnly(transforms, batchSize, dependsOn)` |
| `bool Execute(int i)` — predicate            | `IJobFilter`                    | `ScheduleAppend(list, arrayLength, batchSize, dependsOn)`         |
| length comes from a `NativeList<T>`          | `IJobParallelForDefer`          | `Schedule(list, innerloopBatchCount, dependsOn)`                  |
