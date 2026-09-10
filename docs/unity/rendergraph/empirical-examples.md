# Reusable RenderGraph pass patterns

These examples capture recurring URP RenderGraph shapes without depending on
a particular package or project layout. Treat every declared resource as part
of the scheduling contract: RenderGraph can only order, cull, and synchronize
work it can see.

## Compute pass reading URP globals

A compute pass that samples the main-light shadow atlas should import or obtain
the atlas handle and declare it as a Read dependency. If the kernel also relies
on global cascade matrices or vectors, allow the required global state and make
sure the shadow-producing pass remains upstream.

```csharp
using (var builder = renderGraph.AddComputePass<PassData>("Voxel Lighting", out var data))
{
    data.shadowAtlas = resourceData.mainShadowsTexture;
    builder.UseTexture(data.shadowAtlas, AccessFlags.Read);
    builder.UseTexture(data.output, AccessFlags.Write);
    builder.SetRenderFunc((PassData pass, ComputeGraphContext ctx) =>
    {
        // Bind pass-owned resources explicitly, then dispatch.
    });
}
```

Use an unsafe pass only when required command-buffer operations are unavailable
through `ComputeCommandBuffer`. Unsafe access is not a substitute for declaring
dependencies.

## Raster pass publishing a global texture

Declare the destination attachment, then publish its handle after the pass:

```csharp
using (var builder = renderGraph.AddRasterRenderPass<PassData>("Cloud Shadow", out var data))
{
    builder.SetRenderAttachment(output, 0, AccessFlags.Write);
    builder.SetGlobalTextureAfterPass(output, Shader.PropertyToID("_CloudShadowTexture"));
    builder.SetRenderFunc((PassData pass, RasterGraphContext ctx) =>
    {
        // Draw fullscreen or render geometry.
    });
}
```

Prefer passing `TextureHandle`s directly between passes. Publish a shader global
only when downstream code cannot receive the handle explicitly.

## Transient intermediate texture

A transient texture belongs to one pass and cannot escape it:

```csharp
var transient = builder.CreateTransientTexture(new TextureDesc(width, height)
{
    name = "Temporary Blur Target",
    colorFormat = GraphicsFormat.R16G16B16A16_SFloat,
    clearBuffer = false
});
```

Use transient resources for scratch storage local to a pass. Use regular graph
textures when another pass must consume the result.

## History texture imported into the graph

History survives across frames, so it is owned outside RenderGraph and imported
each frame:

```csharp
TextureHandle previous = renderGraph.ImportTexture(historyPrevious);
TextureHandle current  = renderGraph.ImportTexture(historyCurrent);

builder.UseTexture(previous, AccessFlags.Read);
builder.UseTexture(current, AccessFlags.Write);
builder.AllowPassCulling(false);
```

RenderGraph cannot see next frame's read, so a pass whose only observable result
is a history write may need `AllowPassCulling(false)`. Keep history isolated per
camera; see [`camera-state-isolation.md`](camera-state-isolation.md).

## Hi-Z depth pyramid

A typical Hi-Z chain has two stages:

1. Raster or copy pass: Read camera depth and Write mip 0 of a depth-copy texture.
2. Compute passes: Read the previous mip and Write the next mip, or ping-pong
   between explicitly declared ReadWrite textures.

Each dispatch must declare the exact handles and access modes it uses. A hidden
global depth read does not create a RenderGraph dependency.

## Resource-declaration audit

For every pass, verify:

- Every sampled texture or buffer is declared Read.
- Every UAV or render target is declared Write or ReadWrite as appropriate.
- Attachments use `SetRenderAttachment`/`SetRenderAttachmentDepth`.
- Imported persistent and history resources have an explicit external owner.
- Global state access is enabled only when the pass genuinely needs it.
- Pass culling is disabled only for side effects invisible to the current graph.
- Async compute is enabled only after resource dependencies are complete and
  the target platforms have been profiled.

See [`builder-api.md`](builder-api.md), [`pass-types.md`](pass-types.md), and
[`global-state.md`](global-state.md) for the detailed API rules.
