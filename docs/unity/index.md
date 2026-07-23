# `docs/unity/` — model-aware Unity API canon

Local references for "what does this Unity API actually do, in this version, on this project's setup". Each subdocset:

- Cites engine sources by `file:line` (verified on disk, not recalled from training).
- Documents one Unity subsystem at the depth needed to write or modify code without guessing.
- Includes an `empirical-examples.md` page surveying existing call sites.
- Has an `index.md` that lists the topical pages and a "reading order for X" recipe.

This canon is the shared, project-agnostic home in the workflow repo, merged from copies that had diverged across several sibling Unity projects. The engine `file:line` citations and the `empirical-examples.md` surveys point at the source trees of the projects they were captured against, not at any one consuming project. The API content is the engine's and is project-agnostic; treat the citations as engine-API provenance, and re-survey against a consuming project's own call sites when you need a project-local example. Where two captures of the same page diverged, the merged page keeps both surveys. The version caveat is in "What is NOT covered here" below.

## Subdocsets

- [`rendergraph/`](rendergraph/index.md) — Unity 6.3 / URP 17.5 RenderGraph.
  Builder API (`IBaseRenderGraphBuilder`, `IRasterRenderGraphBuilder`,
  `IComputeRenderGraphBuilder`, `IUnsafeRenderGraphBuilder`), pass-type
  restrictions, global-state propagation, depth-target selection,
  camera-state isolation, samplers, shadow-sampling-from-compute,
  shader-globals-vs-compute-kernel binding, empirical examples. Also:
  Surface Cache GI's scene-discovery mechanism and its integration gap
  with GPU-driven/indirect-draw geometry (`surface-cache-gi.md`), and the
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

- [`entities/`](entities/index.md) — Unity.Entities / DOTS on entities 1.x / 6.5.0, the engine canon for a Burst-compiled DOTS falling-sand engine (`is.zori.pixelworld`) and its sibling ECS packages, with systems as `[BurstCompile] ISystem`. Pages: `systems.md` and `system-types.md` (`ISystem` vs `SystemBase`, lifecycle, `[BurstCompile]` placement, `ref SystemState`, the source-generated `SystemAPI` surface usable inside Burst, `state.Dependency` chaining, scheduling `IJobEntity`/`IJobChunk`), `system-groups.md` (`ComponentSystemGroup`, the `[UpdateInGroup]`/`[UpdateBefore]`/`[UpdateAfter]`/`[CreateAfter]` edges, the standard + fixed-step groups and their ECB systems), `query-and-iteration.md` (`EntityQuery`, `SystemAPI.Query`, `IJobEntity` schedule overloads, `IJobChunk`, the `[WithAll]`/`[WithAny]`/`[WithNone]` family), `jobs-on-systems.md` (`state.Dependency` chaining rules), `entity-mutations.md` and `command-buffers-singletons.md` (`EntityManager` vs `EntityCommandBuffer` + `ParallelWriter`, the standard ECB-system singletons, the native-collection-bearing struct on a singleton component), `baking.md` (`Baker<TAuthoring>`, `TransformUsageFlags`, the component-type taxonomy), `transforms-and-hierarchy.md` (`LocalTransform`/`LocalToWorld`/`Parent`/`Child`, `TransformSystemGroup`), `burst-isystem-patterns.md`, `latios-idioms.md`, and `empirical-examples.md`.

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

1. **PackageCache source** — direct Read of `Library/PackageCache/com.unity.<pkg>@<hash>/...`.
2. **Editor BuiltInPackages** — `Editor/Data/Resources/PackageManager/BuiltInPackages/com.unity.render-pipelines.{core,universal}/...`.
3. **Rider DecompilerCache** — `~/.config/JetBrains/Rider*/resharper-host/DecompilerCache/decompiler/...`. Free if Rider has navigated there.
4. **SharpTools MCP** (`mcp__sharptools__*`) — Roslyn workspace + ILSpy-based decompile fallback. Use `SharpTool_LoadSolution` then `SharpTool_ViewDefinition` / `SharpTool_SearchDefinitions`.
5. **`ilspycmd`** — `dotnet tool install -g ilspycmd` (run from `/tmp` to dodge multi-csproj). Bulk decompile any DLL.

Full recipe in [`jobs/decompilation-workflow.md`](jobs/decompilation-workflow.md).

## What is NOT covered here

- **Version drift, and which way it runs.** This canon was captured against a *higher* engine than `mara`'s declared `6000.0` baseline (the source project sat on URP 17.5 / Unity 6000.4, while `mara` resolves URP 17.6 against an installed `6000.6.0a6` editor). The drift therefore reverses from the usual "watch for newer APIs": watch instead for an API the docs reference that the engine `mara` actually runs may not expose, and verify every signature in doubt against `mara`'s installed editor rather than against the doc. The RenderGraph subdocset is the most exposed, since URP RenderGraph signatures move between minors.
- Unity.Entities / DOTS **is** covered — `mara` hosts the `is.zori.pixelworld` DOTS engine and several sibling ECS packages, so the `entities/` subdocset is a real reference (Burst `ISystem`, system groups, command buffers, singletons). The entity-side *baking/authoring* path and the DLL-only entity-job scheduling tables are the deliberately omitted parts (see that subdocset's "does NOT cover").
- Unity Manual prose / ScriptReference guides — consult the Manual for `mara`'s installed version, treat it as often stale, and cross-check against the source.
- HDRP-specific API. `mara` uses URP exclusively.
- Game-design specifics and project architecture — those live in `docs/` at the repository root (for example `docs/rc2d-jfa-assessment.md`) and in the orchestration journals under `docs/orchestrate/`.
- General programming style — see project `CLAUDE.md` § "C# codestyle".
