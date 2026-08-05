---
name: Read DOTS docs first (jobs / burst / entities)
description: Companion to feedback_read_rendergraph_docs_first.md — directs the agent to docs/unity/jobs/, docs/unity/burst/, docs/unity/entities/ before writing any Schedule call, [BurstCompile] type, or ISystem.
type: feedback
originSessionId: 28f3c936-6d15-4761-82ea-8f370aeade9b
---
**READ FIRST** for any DOTS work:

- `docs/unity/jobs/` — the Unity.Jobs canon. `scheduling-overloads.md` has the full overload table with the exact named-argument names per interface (`innerloopBatchCount` for IJobParallelFor / IJobFor.ScheduleParallel; `indicesPerJobCount` for IJobParallelForBatch; `dependsOn` vs `dependency` inconsistency between interfaces). `decompilation-workflow.md` has the SharpTools MCP / Rider DecompilerCache / `ilspycmd` recipe for verifying signatures.
- `docs/unity/burst/` — `[BurstCompile]` property surface, the entry-point-only rule, FunctionPointer<T> caching pattern, SharedStatic<T>, intrinsics with IsXyzSupported guards.
- `docs/unity/entities/` — `ISystem` vs `SystemBase`, `IJobEntity` schedule overloads (the entities-side answer to docs/unity/jobs/scheduling-overloads.md), `state.Dependency` chaining contract, EntityCommandBuffer playback timing.

**Why:** Sub-agents have shipped wrong code from guessed parameter names — the canonical example is `job.Schedule(N, batchSize: 64)` (no such named arg on any IJobParallelFor*Schedule overload; correct names are `innerloopBatchCount` and `indicesPerJobCount`). The docsets cite engine source by `file:line` so the agent doesn't have to guess.

**How to apply:** Before writing or modifying any DOTS code (any Schedule/ScheduleParallel/Run call, any [BurstCompile]'d type, any ISystem/IJobEntity/IJobChunk), open the matching docset and verify the exact API. The empirical-examples.md page in each docset surveys this project's existing call sites — copy the closest sibling rather than recalling from training data.

`docs/unity/jobs/decompilation-workflow.md` documents the canonical fallback chain (PackageCache → Editor BuiltInPackages → Rider DecompilerCache → SharpTools MCP → `ilspycmd`) when a signature isn't already on disk as source.
