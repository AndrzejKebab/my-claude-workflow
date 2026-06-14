# Pass types

Three constructors on `RenderGraph` produce three distinct builder interfaces, each with a different command-buffer flavour and a different set of restrictions.

| Pass type | Builder interface | Render-func context | `cmd` type | Native render pass | Auto state setup | Auto-allow global state |
| --- | --- | --- | --- | --- | --- | --- |
| `AddRasterRenderPass` | `IRasterRenderGraphBuilder` | `RasterGraphContext` | `RasterCommandBuffer` | yes (mergeable) | yes (RT bind, viewport, etc.) | no |
| `AddComputePass` | `IComputeRenderGraphBuilder` | `ComputeGraphContext` | `ComputeCommandBuffer` | n/a | n/a | no |
| `AddUnsafePass` | `IUnsafeRenderGraphBuilder` | `UnsafeGraphContext` | `CommandBuffer` (full, via `CommandBufferHelpers.GetNativeCommandBuffer`) | serialized out | no | yes (`RenderGraph.cs:1505`) |

Source: `RenderGraph.cs:1338-1516`.

---

## AddRasterRenderPass

`RenderGraph.cs:1350-1391`. Use for any pass whose work is rasterization — vertex/fragment shaders writing to render targets.

Restrictions enforced by `RasterCommandBuffer`:
- No compute dispatch.
- No `cmd.SetRenderTarget` (the graph binds the attachments declared by `SetRenderAttachment*`).
- No copy commands.
- Effectively a draw-call API only.

Required builder calls:
- At least one `SetRenderAttachment` or `SetRenderAttachmentDepth`. The pass's MRT layout is fixed by these calls.
- `SetRenderFunc<PassData>(BaseRenderFunc<PassData, RasterGraphContext>)`.

Mergeable: the native render-pass compiler can merge consecutive raster passes that share render targets and tile-fit on mobile. This is the **only** pass type that can be merged.

XR friendly: `EnableFoveatedRasterization` only meaningful here (and the post-process raster passes).

Project examples:
- `Packages/is.zori.atmospherics/Runtime/VolumetricClouds/VolumetricCloudsPass.cs:522` — fullscreen blit raymarch, single MRT (lighting + depth).
- `Packages/is.zori.atmospherics/Runtime/DistantShadows/CloudShadowSource.cs:612,713,748,776` — bake/temporal/blur chain, all raster.
- `Packages/is.zori.atmospherics/Runtime/DistantShadows/Heightfields/HeightfieldShadowSource.cs:356,379,434,468,568` — bake → temporal → blurH → blurV → fold.
- URP `MainLightShadowCasterPass.cs:482` — `using (var builder = graph.AddRasterRenderPass<PassData>(passName, out var passData, profilingSampler))` — shadow-caster draws the cascades into a depth attachment.

## AddComputePass

`RenderGraph.cs:1405-1446`. Use for compute-shader work that operates on textures/buffers without rasterization.

Restrictions enforced by `ComputeCommandBuffer`:
- No draw calls.
- No `SetRenderTarget` (no concept of one).
- Compute and copy commands only.

Required builder calls:
- `SetRenderFunc<PassData>(BaseRenderFunc<PassData, ComputeGraphContext>)`.
- `UseTexture(handle, ReadWrite)` for every UAV.
- `UseBuffer(handle, ReadWrite)` for every RW buffer.

Crucial caveat — does NOT auto-allow global state modification. If your compute kernel relies on globals previously published by other passes (e.g. URP shadow globals), the receiver needs:
- `UseTexture(mainShadowTexture, Read)` or `UseGlobalTexture(_MainLightShadowmapID, Read)` to schedule after the producer.
- For non-texture globals (matrix arrays, vectors), nothing automatic. The producer needs `AllowGlobalStateModification(true)` to keep its `cmd.SetGlobal*` calls in order, and on Vulkan the consumer needs to mirror the values into per-dispatch `SetComputeMatrixParam` / `SetComputeVectorParam` (see [global-state.md](global-state.md) and `feedback_compute_needs_explicit_params.md`).

Project examples:
- None currently. Project routes all compute work through `AddUnsafePass` (see below for the reason).

## AddUnsafePass

`RenderGraph.cs:1467-1516`. Use when you need full `CommandBuffer` access — mixed compute + copy, manual render-target binding for raster sub-work, or any sequence that doesn't fit the raster/compute split cleanly.

Restrictions:
- The render graph compiler serializes all native render passes around the unsafe pass — no merging.
- Limited validation: "The user is responsible to ensure that all dependencies are correctly declared." (`RenderGraph.cs:1452`).
- Future RG compiler versions may generate sub-optimal command streams for unsafe passes.
- "When using a unsafe pass the graph will also not automatically set up graphics state like rendertargets. The pass should do this itself using cmd.SetRenderTarget and related commands." (`RenderGraph.cs:1455-1456`).

Auto-applied:
- `AllowGlobalState(true)` — every unsafe pass automatically permits global-state mutation. `RenderGraph.cs:1505: renderPass.AllowGlobalState(true);`.

Required builder calls:
- `SetRenderFunc<PassData>(BaseRenderFunc<PassData, UnsafeGraphContext>)`.
- All `UseTexture` / `UseBuffer` declarations are still mandatory for scheduling.

Render func gets the full `CommandBuffer` via `CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd)`:
```csharp
builder.SetRenderFunc(static (BakeData d, UnsafeGraphContext ctx) => {
  var cmd = CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd);
  cmd.SetComputeVectorParam(d.PopulateCS, ID_Resolution, resVec);
  cmd.DispatchCompute(d.PopulateCS, d.PopulateKernel, gx, gy, d.ResZ);
});
```
(Pattern from `Packages/is.zori.atmospherics/Runtime/VolumetricFog/VolumetricFogPass.cs:1323-1326`.)

Project examples — most compute work is here:
- `Packages/is.zori.atmospherics/Runtime/VolumetricFog/VolumetricFogPass.cs:1039` — populate + integrate kernels in a single unsafe pass (so the two compute dispatches share a barrier-free range).
- `Packages/is.zori.atmospherics/Runtime/RealtimeGI/RealtimeGIPass.cs:852` — clipmap voxelization compute.
- `Packages/is.zori.atmospherics/Runtime/PhysicalSky/PhysicalSkyPass.cs:345` — sky LUT computes.
- `Packages/is.zori.atmospherics/Runtime/VolumetricFog/DistantFogPass.cs:289` — distant fog 3D-LUT bake.
- `Packages/is.zori.atmospherics/Runtime/VolumetricClouds/VolumetricCloudsPass.cs:810` — post-process compute.
- `Packages/is.zori.atmospherics/Runtime/DistantShadows/AtmosphericsScreenSpaceShadowsPass.cs:306,369` — compose + upsample (use `Blitter.BlitTexture` + extra `cmd.SetGlobal*` so they're unsafe).
- `Packages/is.zori.heightfields/Heightfields/Runtime/HeightfieldRenderFeature.cs:521,1142,1231` — HiZ downsample, BVH reset, height capture.
- `Packages/is.zori.heightfields/VirtualTextures/Runtime/RWVTFulfillerDispatch.cs:94` — RWVT page fulfillment.

URP precedent for unsafe-instead-of-compute:
- URP `RendererFeatures/ScreenSpaceShadows.cs:208-214` documents the rationale: "UUM-85291: Using UnsafePass to not allow this pass to merge with other passes as it can cause issues when using Deferred Lighting by breaking up the Draw GBuffer and Deferred Lighting passes ... For now, using an UnsafePass ensures that this pass won't be merged as a fix is found for the other underlying issues."

## Picking a pass type

Decision rule:
1. Pure rasterization to one or more attachments? → `AddRasterRenderPass`. Tightest validation, eligible for native-render-pass merging.
2. Single compute dispatch, no extra `cmd.SetGlobal*` outside what RG handles? → `AddComputePass`. Cleaner contract; future-proof against compiler-vs-unsafe divergence.
3. Mixed compute + raster sub-blits, manual `cmd.SetRenderTarget`, multiple compute dispatches that share state, or any need to call `cmd.SetGlobalKeyword` / `cmd.EnableKeyword` / `cmd.SetGlobalMatrixArray` / `cmd.SetGlobalTexture` from the render func? → `AddUnsafePass`.

The project leans heavily on (3) because the compute kernels read URP shadow globals (matrix arrays, vectors) that don't auto-route through RG's compute-context, and because some passes do `Blitter.BlitTexture` + `cmd.SetGlobalVector(MainLightShadowParams, ...)` keyword flips (`AtmosphericsScreenSpaceShadowsPass.cs:306-355`) that would be illegal on a `RasterCommandBuffer`.

## The deprecated AddRenderPass

`RenderGraph.cs:1528-1566`. `[Obsolete("AddRenderPass() is deprecated, use AddRasterRenderPass/AddComputePass/AddUnsafePass() instead.")]`. The legacy variant returns a `RenderGraphBuilder` (different from `IBaseRenderGraphBuilder`) — do not use, and rip it out if you find it.
