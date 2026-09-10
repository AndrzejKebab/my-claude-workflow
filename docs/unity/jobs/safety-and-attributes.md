# NativeContainer attributes and safety relaxations

Each attribute relaxes a specific check on the `AtomicSafetyHandle` of a `NativeContainer` field of a job. The **failure mode you accept** when adding the attribute is the dual of the check it relaxes — name it before reaching for the attribute.

## Default state: full safety

Without any attribute, a `NativeContainer` field on a job is assumed read-write. The safety system enforces:

1. **Container disposal**: the container must outlive the job (or be flagged `[DeallocateOnJobCompletion]`).
2. **Reader/writer mutex**: at most one writer, or any number of readers, across all jobs sharing the container.
3. **ParallelFor index range**: in an `IJobParallelFor`/`IJobParallelForBatch`, the job may only access indices in its assigned range. Cross-range access trips at runtime.
4. **Main-thread exclusion**: the main thread cannot read/write the container while a job has it scheduled.

The relaxation attributes peel off these checks one-at-a-time.

## `[ReadOnly]`

```csharp
[BurstCompile]
struct CountJob : IJobParallelFor {
    [ReadOnly] public NativeArray<float> Input;     // read-only, parallel-safe
    [WriteOnly] public NativeArray<int>  Output;
    public void Execute(int i) => Output[i] = (int)Input[i];
}
```

- The container behaves as a shared-readers handle — multiple parallel jobs can all read it concurrently.
- Forbids writes inside `Execute`. Compile-time error in Burst, runtime error in mono.
- **Failure mode if misused**: silent — a write you intended that the compiler missed (e.g. through an unsafe pointer) corrupts state with no diagnostic.
- Use whenever the job logically reads but does not write. Cheap, no downside.

## `[WriteOnly]`

```csharp
[WriteOnly] public NativeArray<float> Output;
```

- Permits writes, forbids reads. Useful when you don't want to accidentally read uninitialised output.
- The safety handle is a write-only handle: another job cannot read the same container in parallel.
- **Failure mode if misused**: same as `[ReadOnly]` — silent corruption on accidental reads through unsafe pointers.

## `[NativeDisableParallelForRestriction]`

```csharp
[NativeDisableParallelForRestriction] public NativeArray<float> Output;
```

- Removes the index-range check. Job may write any index, not only those in its assigned `[startIndex, endIndex)` range.
- Parallel jobs **may now race** on the same index — you take responsibility for ensuring index ownership (e.g. by deriving the write index from data outside the parallel-for range).
- **Failure mode**: data race + UB. Tooling cannot warn you; the compiler trusts your annotation.
- Common legitimate use: per-batch reduction outputs in `IJobParallelForBatch` where each batch writes a single output slot indexed by `startIndex / batchSize`.

## `[NativeDisableContainerSafetyRestriction]`

```csharp
[NativeDisableContainerSafetyRestriction] public NativeArray<float> SharedScratch;
```

- Disables **all** AtomicSafetyHandle checks for this field. Equivalent to "I promise I know what I'm doing".
- Multiple parallel jobs can write the same container at the same indices. Multiple jobs with conflicting reader/writer claims can co-schedule.
- **Failure mode**: full UB. Don't use this unless you have an external invariant guaranteeing safety (e.g. batch-disjoint writes through pointer arithmetic that the safety system can't see).

## `[NativeDisableUnsafePtrRestriction]`

```csharp
[NativeDisableUnsafePtrRestriction] public IntPtr NativePointer;
```

- Permits a job to hold a raw `IntPtr` / `void*` that the safety system would otherwise refuse to capture.
- Used when you must pass a non-`NativeContainer` pointer (e.g. a UnityEngine native handle) into Burst.
- **Failure mode**: the pointer must remain valid for the job's full lifetime. Unity does not check.

## `[DeallocateOnJobCompletion]`

```csharp
[DeallocateOnJobCompletion] public NativeArray<float> Temp;
```

- Disposes the container on the job's `Execute` returning (or `Complete` returning, for a parallel-for).
- Saves a manual `.Dispose()` call when the container is genuinely scoped to a single job.
- **Failure mode**: container is unusable after `Complete` returns. Multi-job pipelines that try to chain access to the same container break.
- Modern alternative: pass `Allocator.TempJob` (auto-released after a few frames) or `Allocator.Persistent` + explicit `Dispose`.

## `[NativeContainerSupportsDeallocateOnJobCompletion]` / `[NativeContainerIsAtomicWriteOnly]` / etc.

These appear on the **container type definition** (e.g. `NativeArray<T>`, `NativeQueue<T>`) and tell the safety system what relaxations the container itself supports. As a project consumer you do not write these. They show up when reading the source of `Unity.Collections` types.

## Relaxation matrix

| Attribute on field                          | Disposal | RW mutex | PFor range | Main-thread exclusion |
|----------------------------------------------|----------|----------|-------------|------------------------|
| (none)                                       | ✓        | ✓        | ✓           | ✓                      |
| `[ReadOnly]`                                 | ✓        | shared-readers | ✓     | ✓                      |
| `[WriteOnly]`                                | ✓        | exclusive-writer | ✓ | ✓                      |
| `[NativeDisableParallelForRestriction]`      | ✓        | ✓        | **off**     | ✓                      |
| `[NativeDisableContainerSafetyRestriction]`  | ✓        | **off**  | **off**     | **off**                |
| `[NativeDisableUnsafePtrRestriction]`        | n/a (raw pointer) | n/a | n/a | n/a                    |
| `[DeallocateOnJobCompletion]`                | auto-dispose | ✓     | ✓           | ✓                      |

## Examples

- A voxel-filling `IJobParallelFor` can mark every input container `[ReadOnly]` and every output `NativeArray` `[WriteOnly]`. This is the clean default shape.
- A per-region decode can schedule with `job.Schedule(slotCount, 1)`. If each `Execute(int slotIndex)` writes a distinct sub-array, the normal parallel-for index restriction remains valid without `[NativeDisableParallelForRestriction]`.

Search the project with:

```powershell
rg -n "NativeDisableParallelForRestriction|NativeDisableContainerSafetyRestriction|DeallocateOnJobCompletion" Assets Packages
```

to find every relaxation site and audit its rationale.

## When a relaxation is the right call

- Per-batch output slot in `IJobParallelForBatch` where `Execute(start, count)` writes `output[start / batchSize]` → `[NativeDisableParallelForRestriction]` (provably disjoint).
- Per-thread accumulator array sized `JobsUtility.MaxJobThreadCount` (= 128, `UnityEngine.CoreModule.decompiled.cs:2877`) addressed by `[NativeSetThreadIndex] int _threadIndex` → `[NativeDisableParallelForRestriction]` (per-worker disjoint by construction).
- Holding a UnityEngine native handle in a Burst job → `[NativeDisableUnsafePtrRestriction]` (the safety system has no model for it).

If the rationale is "the test passes", the rationale is wrong. Move the offending attribute up the stack until you can name a structural property guaranteeing safety.

## Source citations

| Symbol                                         | File                                                                                                                |
|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `[NativeContainer]`, `[ReadOnly]`, `[WriteOnly]` | `Library/PackageCache/com.unity.collections@.../Unity.Collections/...` (inspect package source directly; see [`decompilation-workflow.md`](decompilation-workflow.md)) |
| `[DeallocateOnJobCompletion]`                  | `UnityEngine.CoreModule.decompiled.cs` (search `class DeallocateOnJobCompletion`)                                   |
| `[NativeDisableParallelForRestriction]`        | `UnityEngine.CoreModule.decompiled.cs` (Unity.Collections.LowLevel.Unsafe namespace)                                |
| `JobsUtility.MaxJobThreadCount = 128`          | `UnityEngine.CoreModule.decompiled.cs:2877`                                                                         |
| `JobsUtility.CacheLineSize = 64`               | `UnityEngine.CoreModule.decompiled.cs:2882`                                                                         |
