# Scheduling overloads — the named-argument cheat sheet

Every `Schedule` / `ScheduleParallel` / `Run` overload exposed by Unity's job system, with the **exact parameter names** the compiler accepts. Use this page before writing any named-argument call.

## TL;DR — the wrong-named-argument trap

```csharp
// WRONG — does not compile against any Schedule overload in any job interface.
job.Schedule(VoxelsPerTile, batchSize: 64).Complete();
```

`batchSize` is **not** a public parameter name. It is the internal field `JobRanges.BatchSize` (`UnityEngine.CoreModule.decompiled.cs:2775`) populated by the native scheduler. The accepted names depend on the job interface:

| Interface              | Parallel-mode parameter (after `arrayLength`)   |
|------------------------|-------------------------------------------------|
| `IJobParallelFor`      | `innerloopBatchCount`                           |
| `IJobFor.ScheduleParallel` | `innerloopBatchCount`                       |
| `IJobParallelForBatch` | `indicesPerJobCount`                            |
| `IJobParallelForDefer` | `innerloopBatchCount`                           |
| `IJobParallelForTransform` | `minIndicesPerJobCount`                     |

If you cannot remember which one applies, **omit the named argument** and let the compiler bind positionally — the names diverge by interface but the position of the batch-size parameter is always slot 2 (zero-indexed: `arrayLength`, then batch count).

## `IJob` (`UnityEngine.CoreModule.decompiled.cs:2273`)

```csharp
public interface IJob { void Execute(); }
```

Dispatch model: one task, runs on a single worker thread. No iteration, no batching.

`IJobExtensions` (`UnityEngine.CoreModule.decompiled.cs:2283`):

```csharp
public static JobHandle Schedule<T>(this T jobData, JobHandle dependsOn = default) where T : struct, IJob;        // line 2320
public static void      Run<T>     (this T jobData)                                where T : struct, IJob;        // line 2326
public static JobHandle ScheduleByRef<T>(this ref T jobData, JobHandle dependsOn = default) where T : struct, IJob; // line 2332
public static void      RunByRef<T>     (this ref T jobData)                                where T : struct, IJob; // line 2338
```

- **Named arg**: `dependsOn` (only). All other variants take no parameters.
- **ScheduleMode**: `Schedule`/`ScheduleByRef` → `ScheduleMode.Single`. `Run`/`RunByRef` → `ScheduleMode.Run` (executes synchronously on the calling thread).
- **ByRef vs by-value**: `ScheduleByRef` takes the job by `ref` to avoid copying very large job structs. Behaviour is otherwise identical.

## `IJobFor` (`UnityEngine.CoreModule.decompiled.cs:2345`)

```csharp
public interface IJobFor { void Execute(int index); }
```

Dispatch model: indexed for-loop with two distinct schedules. `Schedule` runs all indices sequentially on one worker (ordered). `ScheduleParallel` runs in work-stealing batches across worker threads (unordered).

`IJobForExtensions` (`UnityEngine.CoreModule.decompiled.cs:2356`):

```csharp
public static JobHandle Schedule<T>        (this T jobData, int arrayLength,                            JobHandle dependency) where T : struct, IJobFor; // line 2403
public static JobHandle ScheduleParallel<T>(this T jobData, int arrayLength, int innerloopBatchCount,   JobHandle dependency) where T : struct, IJobFor; // line 2409
public static void      Run<T>             (this T jobData, int arrayLength)                                                   where T : struct, IJobFor; // line 2415
public static JobHandle ScheduleByRef<T>        (this ref T jobData, int arrayLength,                          JobHandle dependency) where T : struct, IJobFor; // line 2421
public static JobHandle ScheduleParallelByRef<T>(this ref T jobData, int arrayLength, int innerloopBatchCount, JobHandle dependency) where T : struct, IJobFor; // line 2427
public static void      RunByRef<T>             (this ref T jobData, int arrayLength)                                                 where T : struct, IJobFor; // line 2433
```

- **`Schedule` (no `Parallel`) is sequential.** It internally calls `JobsUtility.ScheduleParallelFor(ref parameters, arrayLength, arrayLength)` — i.e. one giant batch — and uses `ScheduleMode.Single`. The job runs on **one** worker, in index order.
- **`ScheduleParallel` is the parallel one.** Uses `ScheduleMode.Batched` (which is now the same value as `Parallel` — see ScheduleMode note below).
- **No `dependency` default.** Unlike `IJob.Schedule`, `IJobFor.Schedule` and `ScheduleParallel` require the dependency explicitly. Pass `default` if there is none.
- **Named arg**: `dependency` (note: singular, not `dependsOn` like `IJob`/`IJobParallelFor`/`IJobParallelForBatch`). The naming is inconsistent across interfaces — verify against the table below before passing by name.

## `IJobParallelFor` (`UnityEngine.CoreModule.decompiled.cs:2440`)

```csharp
public interface IJobParallelFor { void Execute(int index); }
```

Dispatch model: indexed work-stealing loop, parallel by default. Cannot be scheduled sequentially (use `IJobFor.Schedule` for that).

`IJobParallelForExtensions` (`UnityEngine.CoreModule.decompiled.cs:2451`):

```csharp
public static JobHandle Schedule<T>     (this T jobData,     int arrayLength, int innerloopBatchCount, JobHandle dependsOn = default) where T : struct, IJobParallelFor; // line 2498
public static void      Run<T>          (this T jobData,     int arrayLength)                                                          where T : struct, IJobParallelFor; // line 2504
public static JobHandle ScheduleByRef<T>(this ref T jobData, int arrayLength, int innerloopBatchCount, JobHandle dependsOn = default) where T : struct, IJobParallelFor; // line 2510
public static void      RunByRef<T>     (this ref T jobData, int arrayLength)                                                          where T : struct, IJobParallelFor; // line 2516
```

- **Named args**: `innerloopBatchCount`, `dependsOn`.
- `Schedule` is the only scheduling variant — there is no `ScheduleParallel` (parallel is the only mode).
- `dependsOn` defaults to `default(JobHandle)` (here it is named differently from `IJobFor`'s `dependency`).
- Calling `.Run(arrayLength)` synchronously executes all indices on the calling thread, ignoring `innerloopBatchCount`.

## `IJobParallelForBatch` (`com.unity.collections@.../Unity.Collections/Jobs/IJobParallelForBatch.cs:18`)

```csharp
public interface IJobParallelForBatch { void Execute(int startIndex, int count); }
```

Dispatch model: like `IJobParallelFor`, but `Execute` is called once per **batch**, with the start index and count, not per index. Lets you keep per-batch state on the stack (e.g. a `NativeArray.GetSubArray(startIndex, count)`).

`IJobParallelForBatchExtensions` (`IJobParallelForBatch.cs:31`):

```csharp
public static JobHandle Schedule<T>            (this T jobData,     int arrayLength, int indicesPerJobCount, JobHandle dependsOn = default) where T : struct, IJobParallelForBatch; // line  98
public static JobHandle ScheduleByRef<T>       (this ref T jobData, int arrayLength, int indicesPerJobCount, JobHandle dependsOn = default) where T : struct, IJobParallelForBatch; // line 117
public static JobHandle ScheduleParallel<T>    (this T jobData,     int arrayLength, int indicesPerJobCount, JobHandle dependsOn = default) where T : struct, IJobParallelForBatch; // line 135
public static JobHandle ScheduleParallelByRef<T>(this ref T jobData, int arrayLength, int indicesPerJobCount, JobHandle dependsOn = default) where T : struct, IJobParallelForBatch; // line 154
public static JobHandle ScheduleBatch<T>       (this T jobData,     int arrayLength, int indicesPerJobCount, JobHandle dependsOn = default) where T : struct, IJobParallelForBatch; // line 172  (alias for ScheduleParallel)
public static JobHandle ScheduleBatchByRef<T>  (this ref T jobData, int arrayLength, int indicesPerJobCount, JobHandle dependsOn = default) where T : struct, IJobParallelForBatch; // line 190  (alias for ScheduleParallelByRef)
public static void      Run<T>                 (this T jobData,     int arrayLength, int indicesPerJobCount)                                where T : struct, IJobParallelForBatch; // line 206  (indicesPerJobCount IGNORED — main thread)
public static void      RunByRef<T>            (this ref T jobData, int arrayLength, int indicesPerJobCount)                                where T : struct, IJobParallelForBatch; // line 220
public static void      RunBatch<T>            (this T jobData,     int arrayLength)                                                         where T : struct, IJobParallelForBatch; // line 235
public static void      RunBatchByRef<T>       (this ref T jobData, int arrayLength)                                                         where T : struct, IJobParallelForBatch; // line 247
```

- **Named args**: `indicesPerJobCount`, `dependsOn`. **Not** `batchSize`.
- **`Schedule` is sequential** (`ScheduleMode.Single`); **`ScheduleParallel` / `ScheduleBatch` are parallel** (`ScheduleMode.Parallel`). This mirrors `IJobFor` rather than `IJobParallelFor`.
- `ScheduleBatch` / `ScheduleBatchByRef` are pure aliases for `ScheduleParallel` / `ScheduleParallelByRef` (line 175 / 193 just forwards).
- `Run` and `RunByRef` accept `indicesPerJobCount` but ignore it (XML doc, line 201: "This argument is ignored when using .Run()") — the main thread loops over the whole range as a single batch.

## `IJobParallelForDefer` (`com.unity.collections@.../Unity.Collections/Jobs/IJobParallelForDefer.cs`)

Like `IJobParallelFor`, but the iteration count is read from a `NativeList<T>.Length` or `int*` at job start time rather than baked in at schedule time. Use when the producer of the work-list is itself a job whose final length you don't know until completion.

Named arg: `innerloopBatchCount`. Dependency parameter is `dependsOn` (default).

## `IJobParallelForTransform` (`UnityEngine.CoreModule.decompiled.cs:117534`)

```csharp
public interface IJobParallelForTransform { void Execute(int index, TransformAccess transform); }
```

Dispatch model: parallel iteration over a `TransformAccessArray`. Each `Execute` gets a `TransformAccess` you can read/write `localPosition` etc. through.

`IJobParallelForTransformExtensions` (`UnityEngine.CoreModule.decompiled.cs:117546`):

```csharp
public static JobHandle Schedule<T>(this T jobData, TransformAccessArray transforms,                                                  JobHandle dependsOn = default) where T : struct, IJobParallelForTransform;
public static JobHandle Schedule<T>(this T jobData, TransformAccessArray transforms, IntPtr minIndicesPerJobCount /* see note */,     JobHandle dependsOn = default) where T : struct, IJobParallelForTransform;
public static JobHandle ScheduleReadOnly<T>(this T jobData, TransformAccessArray transforms, int batchSize, JobHandle dependsOn = default) where T : struct, IJobParallelForTransform;
```

- This is the **only** Schedule overload that uses the public name `batchSize` — and it is on `ScheduleReadOnly` specifically, where the transforms are read-only and Unity is free to dispatch any batch size you choose. The plain `Schedule` overloads use `minIndicesPerJobCount` (write-mode requires Unity to choose batches that respect `Transform`/parent-hierarchy locking).
- **Do not generalise**. The `batchSize` name is exclusive to `ScheduleReadOnly` on this single interface. Other interfaces use `innerloopBatchCount` / `indicesPerJobCount`.

## `IJobFilter` (`com.unity.collections@.../Unity.Collections/Jobs/IJobFilter.cs`)

```csharp
public interface IJobFilter { bool Execute(int index); }
```

Dispatch model: append-only filter. Indices for which `Execute` returns `true` are written into an output `NativeList<int>`. Helper for "select-where" patterns. See `IJobFilter.cs` for the `ScheduleAppend` / `ScheduleFilter` extensions.

## Named arguments cheat sheet

```csharp
// IJob
job.Schedule(dependsOn: prev);
job.Run();

// IJobFor — sequential
job.Schedule(arrayLength: N, dependency: prev);
// IJobFor — parallel
job.ScheduleParallel(arrayLength: N, innerloopBatchCount: 64, dependency: prev);

// IJobParallelFor (only schedule mode is parallel)
job.Schedule(arrayLength: N, innerloopBatchCount: 64, dependsOn: prev);

// IJobParallelForBatch — sequential
job.Schedule(arrayLength: N, indicesPerJobCount: 64, dependsOn: prev);
// IJobParallelForBatch — parallel
job.ScheduleParallel(arrayLength: N, indicesPerJobCount: 64, dependsOn: prev);

// IJobParallelForTransform
job.Schedule(transforms);                                         // 1-arg
job.Schedule(transforms, dependsOn: prev);
job.ScheduleReadOnly(transforms, batchSize: 64, dependsOn: prev); // ONLY place batchSize is correct

// IJobParallelForDefer
job.Schedule(deferredArray, innerloopBatchCount: 64, dependsOn: prev);
```

Note the **inconsistent dependency name**: `IJob`/`IJobParallelFor`/`IJobParallelForBatch` use `dependsOn`; `IJobFor` uses `dependency` (no `s`). Verify per call.

## `ScheduleMode` enum (`UnityEngine.CoreModule.decompiled.cs:2789`)

```csharp
public enum ScheduleMode {
    Run = 0,                                            // synchronous, calling thread
    [Obsolete("Batched is obsolete, use Parallel ...")] Batched = 1,
    Parallel = 1,                                       // multi-worker, work-stealing
    Single = 2,                                         // one worker, ordered
}
```

`Batched` and `Parallel` share the underlying value `1` and are interchangeable at runtime. Job-extension code in `UnityEngine.CoreModule` still uses the obsolete `ScheduleMode.Batched` token internally (e.g. `IJobForExtensions.ScheduleParallel` line 2411, `IJobParallelForExtensions.Schedule` line 2500) — this is the canonical engine code, not a project mistake. New code should pass `ScheduleMode.Parallel` if it constructs `JobsUtility.JobScheduleParameters` directly.

## `JobsUtility` constants (`UnityEngine.CoreModule.decompiled.cs:2829`)

- `JobsUtility.MaxJobThreadCount = 128` (line 2877). Maximum number of worker slots the system can ever expose; size of `[NativeSetThreadIndex]`-tagged arrays.
- `JobsUtility.CacheLineSize = 64` (line 2882). Padding constant for `[NativeDisableParallelForRestriction]` arrays where you want one slot per worker without false-sharing — pad each slot to `CacheLineSize` bytes.
- `JobsUtility.JobWorkerCount` / `JobWorkerMaximumCount` (line 2932 / 2942). Runtime worker-thread count (set by Unity at startup, can be lowered with `JobsUtility.JobWorkerCount = N`).
- `JobsUtility.IsExecutingJob` (line 2889). `true` when the current call stack is inside a worker — useful for guards like "do not allocate temp NativeArrays from inside a job".

## Why `Schedule` returns a `JobHandle` you must complete

A `Schedule*` call **does not run the job** — it enqueues it. Three things matter:

1. **Flushing**: nothing actually starts until `JobHandle.ScheduleBatchedJobs()` is called or you sync on a handle (`Complete`, `IsCompleted`, `CombineDependencies`-then-sync). Unity's main-loop calls `ScheduleBatchedJobs` at well-defined points (frame end, before `Update`, etc.). Manually scheduling and never syncing within a frame can leave jobs unflushed across frame boundaries.
2. **Completion**: `handle.Complete()` blocks the calling thread until the job is done. **`default(JobHandle).Complete()` is a no-op** by design (`JobHandle.Complete` line 2545: `if (jobGroup != 0) ScheduleBatchedJobsAndComplete(...)`).
3. **Safety handles**: until `Complete` returns, every `NativeContainer` the job declared as a dependency is in "scheduled, do not touch from main thread" state. Reading from the main thread before `Complete` triggers the safety system (in development builds) or undefined behaviour (release).

See [`dependencies.md`](dependencies.md) for `CombineDependencies`, `CompleteAll`, and the multi-job graph patterns.

## Source citations

| Symbol                                | File                                                                                                              |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| `IJob`                                | `UnityEngine.CoreModule.decompiled.cs:2273` (also Rider cache `c18aa02f.../IJobExtensions.cs`)                    |
| `IJobExtensions`                      | `UnityEngine.CoreModule.decompiled.cs:2283`                                                                       |
| `IJobFor`                             | `UnityEngine.CoreModule.decompiled.cs:2345`                                                                       |
| `IJobForExtensions`                   | `UnityEngine.CoreModule.decompiled.cs:2356` (also Rider cache `01e3965e.../IJobForExtensions.cs`)                 |
| `IJobParallelFor`                     | `UnityEngine.CoreModule.decompiled.cs:2440`                                                                       |
| `IJobParallelForExtensions`           | `UnityEngine.CoreModule.decompiled.cs:2451`                                                                       |
| `IJobParallelForBatch` + extensions   | `Library/PackageCache/com.unity.collections@12999e356c23/Unity.Collections/Jobs/IJobParallelForBatch.cs:18,31`    |
| `IJobParallelForDefer` + extensions   | `Library/PackageCache/com.unity.collections@12999e356c23/Unity.Collections/Jobs/IJobParallelForDefer.cs`           |
| `IJobFilter` + extensions             | `Library/PackageCache/com.unity.collections@12999e356c23/Unity.Collections/Jobs/IJobFilter.cs`                    |
| `IJobParallelForTransform`            | `UnityEngine.CoreModule.decompiled.cs:117534`                                                                     |
| `IJobParallelForTransformExtensions`  | `UnityEngine.CoreModule.decompiled.cs:117546`                                                                     |
| `JobHandle`                           | `UnityEngine.CoreModule.decompiled.cs:2526`                                                                       |
| `JobHandle.Complete`                  | `UnityEngine.CoreModule.decompiled.cs:2545`                                                                       |
| `ScheduleMode`                        | `UnityEngine.CoreModule.decompiled.cs:2789`                                                                       |
| `JobRanges` (incl. internal `BatchSize` field) | `UnityEngine.CoreModule.decompiled.cs:2773`                                                              |
| `JobsUtility`                         | `UnityEngine.CoreModule.decompiled.cs:2829`                                                                       |
| `JobProducerTypeAttribute`            | `UnityEngine.CoreModule.decompiled.cs:2754`                                                                       |
