# `docs/unity/` — Unity API reference

Local references for "what does this Unity API actually do in the current project and Editor version?" Each subdocset:

- Cites engine sources by `file:line` (verified on disk, not recalled from training).
- Documents one Unity subsystem at the depth needed to write or modify code without guessing.
- Uses focused examples or empirical notes where they add reusable guidance.
- Has an `index.md` that lists the topical pages and practical reading orders.

This is the shared, project-neutral home for Unity guidance in the workflow repository. Treat `file:line` citations as navigation aids, not permanent identifiers: package hashes and source lines change between Unity versions. Verify exact APIs against the packages and Editor used by the current project.

## Subdocsets

- [`rendergraph/`](rendergraph/index.md) — Unity 6+ URP RenderGraph.
  Builder API (`IBaseRenderGraphBuilder`, `IRasterRenderGraphBuilder`,
  `IComputeRenderGraphBuilder`, `IUnsafeRenderGraphBuilder`), pass-type
  restrictions, global-state propagation, depth-target selection,
  camera-state isolation, samplers, shadow-sampling-from-compute,
  shader-globals-vs-compute-kernel binding, and reusable examples. Also:
  Surface Cache GI's scene-discovery mechanism and integration constraints
  for GPU-driven/indirect-draw geometry (`surface-cache-gi.md`), and the
  `[ResourcePath]`/`IRenderPipelineGraphicsSettings`/`ObjectDispatcher`
  family of SRP resource-organization idioms (`resource-attributes.md`).

- [`jobs/`](jobs/index.md) — Unity.Jobs (`IJob`, `IJobFor`, `IJobParallelFor`,
  `IJobParallelForBatch`, `IJobParallelForDefer`, `IJobParallelForTransform`,
  `IJobFilter`). The full `Schedule*` overload table with the exact named
  arguments per interface (`innerloopBatchCount` vs `indicesPerJobCount` vs
  `dependsOn` vs `dependency`). `JobHandle`, `CombineDependencies`, safety
  attributes (`[ReadOnly]`, `[WriteOnly]`, `[NativeDisable*]`,
  `[DeallocateOnJobCompletion]`). Decompilation workflow.

- [`burst/`](burst/index.md) — Unity.Burst. `[BurstCompile]` attribute surface
  (`FloatMode`, `FloatPrecision`, `OptimizeFor`, `CompileSynchronously`,
  `Debug`, `DisableSafetyChecks`, `DisableDirectCall`). HPC# subset and the
  entry-point-only rule. `FunctionPointer<T>`, `SharedStatic<T>`,
  `CompilerServices` hints (`Hint.Likely`, `Aliasing.ExpectNotAliased`,
  `Constant.IsConstantExpression`, `[AssumeRange]`, `[SkipLocalsInit]`).
  Intrinsics with `IsXyzSupported` runtime guards. Verification.

- [`authoring/`](authoring/index.md) — the serialization rules that decide whether a scene / prefab / SubScene can resolve a script at all, plus the package-sample lifecycle that ships those assets. The one-`MonoBehaviour`-per-correctly-named-file rule and why `fileID: 11500000` binds only the file-name-matching type (a second `MonoBehaviour`/`ScriptableObject` in the same file is unreferenceable); the corollary for programmatic (`-executeMethod`) scene/prefab builders; the missing-script symptom and the YAML-level confirmation. And the sample workflow: `Samples~/` is tilde-ignored delivery (no compile, no import), the `Assets/Samples/…` import is the working copy you develop and test in, publishing back to `Samples~/` happens when ready, re-import/publish is additive (stale files linger), and publishing must preserve `.cs.meta` GUIDs or a consumer's import gets the same missing scripts. As binding as the jobs/burst entries: read it before authoring any `MonoBehaviour`/`ScriptableObject`, building a scene programmatically, or developing/publishing a package sample, because the defects it prevents show nothing at C# compile time and only surface when the asset is imported — by this project or by a consumer of the sample.

- [`entities/`](entities/index.md) — Unity.Entities / DOTS guidance for Burst-oriented simulation, including voxel games. Pages cover `ISystem` vs `SystemBase`, lifecycle and `[BurstCompile]` placement, source-generated `SystemAPI`, job dependency chaining, explicit system groups and ordering, `EntityQuery`, `IJobEntity`/`IJobChunk`, entity mutations and command buffers, singleton-owned native state, baking, transforms and hierarchy, Burst-system patterns, and relevant Latios idioms.

## When to read each

| You are about to…                                           | Read first                              |
|-------------------------------------------------------------|-----------------------------------------|
| Author a `MonoBehaviour` / `ScriptableObject`, or build a scene/prefab programmatically | [`authoring/monobehaviour-files.md`](authoring/monobehaviour-files.md) |
| Develop, test, or publish a package sample (`Samples~/` ↔ `Assets/Samples/…`) | [`authoring/package-samples.md`](authoring/package-samples.md) |
| Write or modify a `ScriptableRendererFeature` / RG pass     | [`rendergraph/`](rendergraph/index.md)  |
| Give a `ScriptableRendererFeature` its own shaders/materials as versioned Editor assets | [`rendergraph/resource-attributes.md`](rendergraph/resource-attributes.md) |
| Make custom/procedural geometry participate in (or understand why it's invisible to) Surface Cache GI | [`rendergraph/surface-cache-gi.md`](rendergraph/surface-cache-gi.md) |
| Write `job.Schedule(...)`, `job.ScheduleParallel(...)`      | [`jobs/scheduling-overloads.md`](jobs/scheduling-overloads.md) |
| Tag a struct or method `[BurstCompile]`                     | [`burst/attributes.md`](burst/attributes.md) and [`burst/compilation-context.md`](burst/compilation-context.md) |
| Write or order an `ISystem` / `ComponentSystemGroup`        | [`entities/systems.md`](entities/systems.md) and [`entities/system-groups.md`](entities/system-groups.md) |
| Write an `ISystem`, `IJobEntity`, or `IJobChunk`            | [`entities/system-types.md`](entities/system-types.md) and [`entities/jobs-on-systems.md`](entities/jobs-on-systems.md) |
| Query / iterate entities, schedule entity jobs              | [`entities/query-and-iteration.md`](entities/query-and-iteration.md) |
| Write a `Baker<TAuthoring>` or work with transforms         | [`entities/baking.md`](entities/baking.md) and [`entities/transforms-and-hierarchy.md`](entities/transforms-and-hierarchy.md) |
| Use an `EntityCommandBuffer` or a singleton from a system   | [`entities/command-buffers-singletons.md`](entities/command-buffers-singletons.md) and [`entities/entity-mutations.md`](entities/entity-mutations.md) |
| Verify a Unity API signature you don't trust                | [`jobs/decompilation-workflow.md`](jobs/decompilation-workflow.md) |

## Decompilation tooling (shared across the docsets)

The DOTS / engine-module APIs live partly as source under `Library/PackageCache/com.unity.*/` and partly as compiled DLLs under `Editor/Data/Managed/UnityEngine/`. The full canonical lookup chain:

1. **PackageCache source** — read `Library/PackageCache/com.unity.<pkg>@<version>/...`.
2. **Editor BuiltInPackages** — `Editor/Data/Resources/PackageManager/BuiltInPackages/com.unity.render-pipelines.{core,universal}/...`.
3. **Rider or another IDE decompiler** — navigate to the declaration in the referenced assembly.
4. **`ilspycmd`** — `dotnet tool install --global ilspycmd`; use it for searchable local decompilation.

Full recipe in [`jobs/decompilation-workflow.md`](jobs/decompilation-workflow.md).

## What is NOT covered here

- **Version guarantees.** These docs span multiple Unity 6 and package versions. RenderGraph is particularly sensitive to minor-version changes, so verify signatures against the active project before editing production code.
- Full Unity Manual or ScriptReference coverage. Use the documentation matching the installed Editor, then cross-check exact signatures against local source.
- HDRP-specific APIs; the RenderGraph material here is URP-oriented unless stated otherwise.
- Project-specific game architecture and design decisions. Keep those in the consuming project's own documentation.
- General C# style conventions. Keep those in shared agent instructions or the consuming project's contributor guidance.
