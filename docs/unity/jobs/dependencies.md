# Dependencies and `JobHandle`

How a `JobHandle` flows through the scheduler, when work actually starts, and the multi-job patterns that get this right.

## What `Schedule*` returns

Every `Schedule*` extension returns a `JobHandle` (`UnityEngine.CoreModule.decompiled.cs:2526`):

```csharp
public struct JobHandle : IEquatable<JobHandle> {
    internal ulong jobGroup;          // identity; 0 == no-op handle
    internal int   version;
    internal int   debugVersion;
    internal IntPtr debugInfo;
}
```

A `default(JobHandle)` has `jobGroup == 0`. **`Complete()` on a default handle is a no-op** by design — the implementation early-outs (line 2545):

```csharp
public void Complete() {
    if (jobGroup != 0) ScheduleBatchedJobsAndComplete(ref this);
}
```

This means a defensive `someHandle.Complete()` after a code path that may or may not have scheduled anything is safe — it costs only the branch.

## "Scheduled" ≠ "running"

`Schedule*` enqueues the job into the scheduler. **Nothing actually starts running** until one of the following:

1. Unity's main loop calls `JobHandle.ScheduleBatchedJobs()` at one of its sync points (e.g. between `Update` phases, before render, frame end). Reference: `UnityEngine.CoreModule.decompiled.cs:2585`.
2. You call `handle.Complete()` (which internally calls `ScheduleBatchedJobsAndComplete`).
3. You query `handle.IsCompleted` (which calls `ScheduleBatchedJobsAndIsCompleted`, line 2540).
4. You call `JobHandle.CombineDependencies(...)` and then sync on the result.

**Implication**: a job you scheduled but never flushed and never completed can sit dormant until Unity's next sync point. For frame-local work (compute → consume in the same frame) this is fine because Unity flushes between phases. For cross-frame work, **call `JobHandle.ScheduleBatchedJobs()` explicitly** to give the scheduler permission to start now.

## `Complete` patterns

```csharp
// Pattern A: schedule and immediately wait — main thread blocks until done.
job.Schedule(arrayLength, batchCount).Complete();

// Pattern B: schedule, do other work, then sync.
JobHandle h = job.Schedule(arrayLength, batchCount, prev);
DoUnrelatedMainThreadWork();
h.Complete();

// Pattern C: schedule and let downstream depend on it (no sync this frame).
JobHandle h = job.Schedule(arrayLength, batchCount, prev);
return h;
```

`Complete` is the **only** point where the safety system releases the writer/reader holds on the `NativeContainer`s the job declared. Reading `[WriteOnly]` outputs from the main thread before `Complete` triggers `InvalidOperationException` in development builds.

## `IsCompleted` is non-blocking

```csharp
if (h.IsCompleted) {
    h.Complete();              // still required to release safety handles
    ConsumeOutput();
}
```

`IsCompleted` returns false until the worker thread actually finishes. After it returns true, you **still need to call `Complete()`** to drain the safety system — `IsCompleted` only inspects the runtime state, it does not release container handles.

## `CompleteAll` for fan-in

```csharp
JobHandle a = jobA.Schedule(prev);
JobHandle b = jobB.Schedule(prev);
JobHandle.CompleteAll(ref a, ref b);
// a and b are reset to default(JobHandle) after the call.
```

Cited at `UnityEngine.CoreModule.decompiled.cs:2553`. There are stack-allocated overloads for 2 / 3 handles (lines 2553, 2563) and a `NativeArray<JobHandle>` overload (line 2575) for arbitrary fan-in. **The non-array overloads zero the input handles** after completion (line 2559–2561). The array overload does not.

## `CombineDependencies` for graph fan-in/fan-out

When job D depends on the output of jobs A, B, C:

```csharp
JobHandle a = jobA.Schedule(prev);
JobHandle b = jobB.Schedule(prev);
JobHandle c = jobC.Schedule(prev);
JobHandle abc = JobHandle.CombineDependencies(a, b, c);
JobHandle d = jobD.Schedule(abc);
```

Cited at `UnityEngine.CoreModule.decompiled.cs:2606` (2-arg) / 2618 (3-arg) / 2623 (`NativeArray<JobHandle>`) / 2628 (`NativeSlice<JobHandle>`). For more than 3 dependencies, allocate a `NativeArray<JobHandle>(Allocator.Temp)`.

`CombineDependencies` does **not** schedule a barrier job — it returns a "logical handle" the scheduler treats as "depends on all of these". No runtime cost beyond the `NativeArray` allocation if you used the array overload.

## Multi-job system pattern (one MonoBehaviour / system)

```csharp
class FoobarSystem : MonoBehaviour {
    JobHandle _frameDeps;

    void Update() {
        // Chain jobs through _frameDeps.
        _frameDeps = jobA.Schedule(_frameDeps);
        _frameDeps = jobB.Schedule(_frameDeps);
        _frameDeps = jobC.Schedule(_frameDeps);
        // Optionally:
        JobHandle.ScheduleBatchedJobs();
    }

    void LateUpdate() {
        _frameDeps.Complete();   // hard sync at end of frame
        ConsumeOutput();
    }

    void OnDestroy() {
        _frameDeps.Complete();   // never tear down with jobs in flight
    }
}
```

In `ISystem` (Unity.Entities) the equivalent state is `state.Dependency` — see [`docs/unity/entities/jobs-on-systems.md`](../entities/jobs-on-systems.md) and [`docs/unity/entities/systems.md`](../entities/systems.md).

## When a `JobHandle` is invalid

- After `Complete()` returns. The handle is "done" — calling `Complete()` again is safe (no-op via the `jobGroup != 0` short-circuit, but the underlying `jobGroup` may be non-zero from before; rely on Unity's internal version-check, not the surface API). Best practice: zero it (`h = default;`) after `Complete`.
- After `CompleteAll(ref h, ...)` on a non-array overload — handle is zeroed.
- After Unity's frame-end safety check pass on dev builds, where any handle still in flight gets logged.

## `JobHandle.ScheduleBatchedJobs` vs `Complete` cost

| Call                                                | Cost                                   |
|------------------------------------------------------|----------------------------------------|
| `JobHandle.ScheduleBatchedJobs()`                    | Flushes pending schedules; non-blocking. ~µs. |
| `handle.IsCompleted`                                 | Flush + atomic read of completion flag. ~µs. |
| `handle.Complete()` on completed work                | Flush + drain safety handles. ~µs.    |
| `handle.Complete()` on in-flight work                | Blocks calling thread until done. As long as the job. |
| `JobHandle.CombineDependencies(a, b, c)`             | Allocates a 3-handle internal record. ns–µs. |

## The "scheduled, never flushed" footgun

```csharp
// A side-effect-only job. Schedule, walk away, and... never sync.
new SideEffectJob { Buffer = buf }.Schedule();
// Frame ends. Buffer's safety handle still says "writer in flight".
// Next frame's main-thread access to `buf` raises InvalidOperationException
// (development build) or undefined behaviour (release).
```

If a job writes a `NativeContainer` you also touch from the main thread, you **must** sync before the next main-thread read. The compiler does not enforce this; the safety system catches it in dev builds, prod builds silently corrupt.

## Source citations

| Symbol                               | File                                                       |
|--------------------------------------|------------------------------------------------------------|
| `JobHandle` struct                   | `UnityEngine.CoreModule.decompiled.cs:2526`                |
| `JobHandle.Complete()`               | `UnityEngine.CoreModule.decompiled.cs:2545`                |
| `JobHandle.IsCompleted`              | `UnityEngine.CoreModule.decompiled.cs:2540`                |
| `JobHandle.ScheduleBatchedJobs()`    | `UnityEngine.CoreModule.decompiled.cs:2585`                |
| `JobHandle.CompleteAll(ref, ref)`    | `UnityEngine.CoreModule.decompiled.cs:2553`                |
| `JobHandle.CompleteAll(NativeArray)` | `UnityEngine.CoreModule.decompiled.cs:2575`                |
| `JobHandle.CombineDependencies`      | `UnityEngine.CoreModule.decompiled.cs:2606`/2618/2623/2628 |
