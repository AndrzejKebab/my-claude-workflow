# RenderGraph local reference (Unity 6.3 / URP 17.5)

Canonical local reference for how RenderGraph passes work in URP. Inspect the Render Pipeline sources installed with the active Editor under `F:\Unity Editors\<version>\Editor\Data\Resources\PackageManager\BuiltInPackages\com.unity.render-pipelines.{core,universal}` or, when resolved as project packages, under `Library/PackageCache/com.unity.render-pipelines.*@<version>`.

All file:line citations refer to those two roots verbatim. Every line citation has been verified against source.

## Documents

- [`builder-api.md`](builder-api.md) — full reference for `IBaseRenderGraphBuilder`, `IComputeRenderGraphBuilder`, `IRasterRenderGraphBuilder`, `IUnsafeRenderGraphBuilder`. Every method (signature, XML doc, builder type, caller responsibility, project examples). Use this when you need to look up "what does X do, and what is the caller responsible for".

- [`pass-types.md`](pass-types.md) — `AddRasterRenderPass` vs `AddComputePass` vs `AddUnsafePass`. Restrictions per type, when to use each, what kind of `cmd` you get. Use when picking the right pass type.

- [`global-state.md`](global-state.md) — how URP-published globals (`cmd.SetGlobalTexture`, `cmd.SetGlobalMatrixArray`, etc.) reach your custom passes. Covers `UseGlobalTexture` vs `UseAllGlobalTextures` vs `AllowGlobalStateModification`, the host-side `Shader.SetGlobal*` vs CommandBuffer-side `cmd.SetGlobal*` distinction, and the exact list of globals issued by `MainLightShadowCasterPass`. Read this first when something "isn't reaching the kernel".

- [`texture-resources.md`](texture-resources.md) — the texture-resource creation/lifetime taxonomy: `CreateTransientTexture` (single-pass scratch) vs `RenderGraph.CreateTexture` (graph/frame-scoped, pooled, the kind you publish as a global) vs `ImportTexture(RTHandle)` (external, persistent across frames). States that `CreateSharedTexture` is removed in this version, and documents the rule a transient must never be published as a global — the cross-pass validation that throws "A transient resource should only be used in a single pass" every frame. Read alongside `global-state.md` when deciding which resource to publish.

- [`shader-globals-and-compute.md`](shader-globals-and-compute.md) — why `Shader.SetGlobal*` / `cmd.SetGlobal*` reach raster shaders and the Blitter but not compute kernels, and the `SetCompute*Param` family a dispatch reads instead. Covers the per-dispatch binding requirement for declared buffers/textures, compute keywords vs `Shader.EnableKeyword`, and the backend-dependent `cbuffer` exception. Read alongside `global-state.md` when a value "reaches the raster path but reads as zero in compute".

- [`shadow-sampling-from-compute.md`](shadow-sampling-from-compute.md) — focused recipe for "I want to sample URP cascade shadows from a compute pass on Vulkan". Walks `Shadows.hlsl` line by line, identifies the implicit-LOD trap on the screen-space branch, and gives the exact builder calls + compute bindings the receiving pass must declare for `_MainLightShadowmapTexture`, `sampler_LinearClampCompare`, `_MainLightWorldToShadow[5]`, `_CascadeShadowSplitSpheres0..3`, `_CascadeShadowSplitSphereRadii`, `_MainLightShadowParams`, `_MainLightShadowmapSize`, `_MainLightShadowOffset0/1`. Use when fixing the cascade-shadow-from-compute failure.

- [`depth-targets.md`](depth-targets.md) — `activeDepthTexture` vs `cameraDepth` vs `cameraDepthTexture`. Which one URP's prepass writes (and when), why `cameraDepthTexture` flips between depth-format and `R32_SFloat` based on `useDepthPriming`, and the format-detection pattern a custom feature uses to land its writes in the same texture URP itself wrote into. Use when authoring a custom depth prepass / depth-only draw.

- [`camera-state-isolation.md`](camera-state-isolation.md) — restoring camera matrices after a raster pass mutates V/P/VP (cascade rendering, atlas blits). What `cmd.SetViewProjectionMatrices` does and does NOT update, why the inverses leak, and URP's "wrap state-mutating pass with sibling `SetupRenderGraphCameraProperties` RG pass" pattern. Use whenever a custom feature calls `cmd.SetViewProjectionMatrices` on a non-camera matrix.

- [`samplers.md`](samplers.md) — how samplers reach compute kernels. URP's `GlobalSamplers.hlsl` declares `sampler_LinearClamp` etc. inline; `sampler_LinearClampCompare` is an inline-name-encoded `SamplerComparisonState` declared in `Shadows.hlsl`. Documents the rule, the redeclaration-collision pitfall (`feedback_urp_sampler_linearclamp_collision.md`), and how comparison samplers wire up across DX/Vulkan via `SAMPLE_TEXTURE2D_SHADOW` macro expansion to `SampleCmpLevelZero`.

- [`empirical-examples.md`](empirical-examples.md) — reusable RenderGraph patterns for compute passes reading URP globals, raster passes publishing textures, transient and history resources, Hi-Z generation, and resource declarations.

- [`surface-cache-gi.md`](surface-cache-gi.md) — Unity's realtime Surface Cache GI renderer feature: geometry discovery, `GeometryPool` ingestion, Meta-pass requirements, and an integration checklist for GPU-driven voxel or heightfield renderers.

- [`resource-attributes.md`](resource-attributes.md) — the attribute/class vocabulary for organizing a `ScriptableRendererFeature`'s own shader/material/compute dependencies as versioned, categorized Editor assets: `[ResourcePath]` + `IRenderPipelineGraphicsSettings`, `[SupportedOnRenderPipeline]`, `[Categorization.CategoryInfo]` + `[HideInInspector]`, `[DisallowMultipleRendererFeature]`, the `Handle<T>`/`HandleSet<T>` strongly-typed-handle idiom, `ObjectDispatcher` for incremental scene-object change tracking, and the cached-`ShaderIDs` pattern.

- [`unity-docs-fetched.md`](unity-docs-fetched.md) — curated extracts from `docs.unity3d.com/6000.3` Manual + ScriptReference for the RenderGraph API surface. Many of the ScriptReference URLs return 404 against the 6.3 doc tree; the Core RP package `17.0` ScriptReference (`docs.unity3d.com/Packages/com.unity.render-pipelines.core@17.0/api/...`) is the working source for method signatures and is what is captured here. Use when you need an externally citable signature.

## Reading order for the cascade-shadow-from-compute bug

1. `shadow-sampling-from-compute.md` (problem statement and exact fix list)
2. `global-state.md` (why some globals reach compute and others do not)
3. `builder-api.md` for the methods the fix calls (`UseGlobalTexture`, `AllowGlobalStateModification`, `UseTexture`)
4. `empirical-examples.md` for canon mirroring (e.g. `VolumetricFogPass.cs:1143`, URP `MainLightShadowCasterPass.cs:482-505`)

## What this docset deliberately does NOT cover

- HDRP-specific RG patterns. URP 17.5 only.
- The legacy `AddRenderPass` API (deprecated in 6.x in favor of the typed Add{Raster,Compute,Unsafe}Pass split — see `RenderGraph.cs:1528`).
- 2D Renderer passes under `Runtime/2D/Rendergraph/` (project does not use the 2D renderer).
