# Workload-balancing examples for `IJobParallelFor`

`IJobParallelFor.Schedule` uses this shape:

```csharp
Schedule(int arrayLength, int innerloopBatchCount, JobHandle dependsOn = default)
```

`innerloopBatchCount` is a workload-balancing choice, not a fixed project
convention. Smaller batches improve work stealing when iteration costs vary;
larger batches reduce scheduling overhead when iteration costs are uniform.

## Uniform voxel work: moderate batches

```csharp
job.Schedule(arrayLength: 16 * 16 * 16, innerloopBatchCount: 64);
```

For a `16³ = 4096` voxel tile, batch size `64` creates 64 batches of 64
voxels. If each voxel performs similar work, such as FBM sampling plus SDF
combination, a moderate batch keeps scheduling overhead low while leaving
enough batches for workers to share.

## Heterogeneous region work: batch size 1

```csharp
job.Schedule(arrayLength: regionCount, innerloopBatchCount: 1);
```

Region costs may vary sharply: one region can be empty while another produces
a dense mesh. Batch size `1` lets the work-stealing scheduler distribute each
region independently. The additional scheduling overhead is acceptable when
the work per non-empty region dominates that overhead.

## Practical rule

- Start with `32–128` for cheap, uniform per-index work.
- Start with `1–16` for expensive or uneven work.
- Use `1` when each index is coarse and highly unpredictable.
- Profile representative worlds on target hardware; total iteration count,
  worker count, and cost variance all affect the best value.

See [`job-types.md`](job-types.md) for choosing the job interface and
[`scheduling-overloads.md`](scheduling-overloads.md) for exact parameter names.
