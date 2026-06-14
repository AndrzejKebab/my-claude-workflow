# Camera state isolation around state-mutating raster passes

A custom raster pass that calls `cmd.SetViewProjectionMatrices(...)` per slice (cascade rendering, atlas blits, off-axis renderers) leaks the last-set V/P/VP into every subsequent pass that records into the same frame's command buffer. The "last cascade's light view" then drives world-position reconstruction in SSS, lit shaders' `unity_MatrixInvVP` reads, post-FX, etc. Visual signature: opaque-object silhouettes appear as shadows on the ground; entire scene appears rendered from the light's perspective.

This document catalogs the problem, what `cmd.SetViewProjectionMatrices` does and does NOT update, and the canonical URP pattern for restoring camera state from a feature.

## What `cmd.SetViewProjectionMatrices(view, proj)` updates

Per the Unity scripting docs (`CommandBuffer.SetViewProjectionMatrices`):

> Note: Only the `unity_MatrixV`, `unity_MatrixVP`, `glstate_matrix_projection`, and `unity_CameraProjection` are updated. The matrices `unity_MatrixInvV`, `unity_CameraInvProjection`, `unity_MatrixInvVP`, and `unity_WorldToCamera` are not updated.

| Updated | NOT updated |
| --- | --- |
| `unity_MatrixV` | `unity_MatrixInvV` |
| `unity_MatrixVP` | `unity_MatrixInvVP` |
| `glstate_matrix_projection` | `unity_MatrixInvP` |
| `unity_CameraProjection` | `unity_CameraInvProjection` |
| | `unity_WorldToCamera` / `unity_CameraToWorld` |

So even calling `SetViewProjectionMatrices(camera.viewMatrix, camera.projectionMatrix)` after the cascade loop does NOT restore the inverses. They keep the *last cascade's* values. SSS reconstructs world position via `unity_MatrixInvVP` and the bug manifests there first.

## What `cmd.SetupCameraProperties(camera)` updates

`CommandBuffer.SetupCameraProperties(Camera)` (and its `RasterCommandBuffer` wrapper at `BuiltInPackages/com.unity.render-pipelines.core/Runtime/CommandBuffers/RasterCommandBuffer.cs:256`) sets the full camera state in one call:

- V, P, VP, all three inverses, glstate matrices.
- `unity_WorldToCamera`, `unity_CameraToWorld`.
- `_WorldSpaceCameraPos`, `_ProjectionParams`, `_ZBufferParams`, `_ScreenParams`, `_Time`.
- World clip planes (`unity_CameraWorldClipPlanes[6]`).

This is what URP itself uses to restore state after its own state-mutating passes.

## URP's pattern: wrap with sibling restore RG passes

`UniversalRendererRenderGraph.cs:1095-1106`:

```csharp
if (isDepthNormalPrepass)
{
    // ...
    if (resourceData.isActiveTargetBackBuffer)
    {
        SetupRenderGraphCameraProperties(renderGraph, depthTarget);
    }
    DepthNormalPrepassRender(renderGraph, renderPassInputs, depthTarget, batchLayerMask, setGlobalDepth, setGlobalTextures, !hasFullPrepass);
    // Restore camera properties for the rest of the render graph execution.
    if (resourceData.isActiveTargetBackBuffer)
    {
        SetupRenderGraphCameraProperties(renderGraph, resourceData.activeColorTexture.IsValid() ? resourceData.activeColorTexture : resourceData.activeDepthTexture);
    }
}
```

URP wraps a state-mutating pass (`DepthNormalPrepassRender`) with `SetupRenderGraphCameraProperties` *before* and *after*. Same wrapper around the main shadow caster at `UniversalRendererRenderGraph.cs:763`.

`ScriptableRenderer.SetupRenderGraphCameraProperties` (`BuiltInPackages/com.unity.render-pipelines.universal/Runtime/ScriptableRenderer.cs:990`):

```csharp
internal void SetupRenderGraphCameraProperties(RenderGraph renderGraph, TextureHandle target)
{
    using (var builder = renderGraph.AddRasterRenderPass<PassData>(Profiling.setupCamera.name, out var passData,
        Profiling.setupCamera))
    {
        passData.renderer = this;
        passData.cameraData = frameData.Get<UniversalCameraData>();
        passData.cameraTargetSizeCopy = new Vector2Int(passData.cameraData.cameraTargetDescriptor.width, passData.cameraData.cameraTargetDescriptor.height);
        passData.target = target;

        builder.AllowGlobalStateModification(true);

        builder.SetRenderFunc((PassData data, RasterGraphContext context) =>
        {
            // ...
            if (data.cameraData.renderType == CameraRenderType.Base)
            {
                context.cmd.SetupCameraProperties(data.cameraData.camera);
                data.renderer.SetPerCameraShaderVariables(context.cmd, data.cameraData, data.cameraTargetSizeCopy, yFlipped);
            }
            // ...
        });
    }
}
```

Two critical traits:

1. **No render attachments.** Just `AllowGlobalStateModification(true)`, which both prevents culling AND prevents RG from reordering the pass relative to surrounding passes (`global-state.md` / `IRenderGraphBuilder.cs:118-120`).
2. **Calls `SetupCameraProperties` on the rastercmd.** That's a graphics state-mutation command that the engine resolves into a full camera property bind.

## Why a SEPARATE pass — not just a call at the tail of the same render func

Calling `cmd.SetupCameraProperties` at the end of a state-mutating pass's render func appears to work (no compile error, no RG complaint), but the camera-state restore does NOT propagate to subsequent native render passes. Frame Debugger shows downstream passes still seeing the cascade's `unity_MatrixInvVP`. URP's pattern is empirical — wrapping with a separate RG pass is the form that actually re-establishes camera state for the next native RP.

When the wrapper pass has `AllowGlobalStateModification(true)`, RG inserts a sync point that flushes the wrapping render pass's commands and forces a restart for the following pass. That restart picks up the camera-property bind we just queued.

## Recipe for custom features

A feature pass that mutates V/P/VP per slice MUST be wrapped:

```csharp
public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
{
    renderer.EnqueuePass(_myStateMutatingPass);
    renderer.EnqueuePass(_myCameraRestorePass);   // sibling at SAME event, enqueued after
}

sealed class MyCameraRestorePass : ScriptableRenderPass
{
    public override void RecordRenderGraph(RenderGraph graph, ContextContainer frameData)
    {
        var cameraData = frameData.Get<UniversalCameraData>();
        using (var builder = graph.AddRasterRenderPass<PassData>("My.RestoreCameraProps", out var passData, _sampler))
        {
            builder.AllowGlobalStateModification(true);
            passData.Camera = cameraData.camera;
            builder.SetRenderFunc(static (PassData d, RasterGraphContext ctx) =>
            {
                ctx.cmd.SetupCameraProperties(d.Camera);
            });
        }
    }
}
```

Both passes share the same `renderPassEvent`. Enqueue order determines dispatch order within the event bucket.

## Forbidden patterns

- ❌ Manually setting `unity_MatrixV` / `unity_MatrixInvVP` / etc. with `cmd.SetGlobalMatrix`. The engine's camera-state model is bigger than the named matrices — projection params, z-buffer params, world clip planes, time, screen params all need to stay coherent. Trust `cmd.SetupCameraProperties`.
- ❌ Restoring at the *end of the same render func* that mutated state. The restore exists in the right command buffer but the next native RP doesn't see it. Use a separate RG pass.
- ❌ Restoring with `cmd.SetViewProjectionMatrices(camera.V, camera.P)`. Only updates V/VP/projection, leaves the inverses pinned to whatever the cascade loop set them to.
- ❌ Forgetting `AllowGlobalStateModification(true)` on the restore pass. RG culls attachment-less passes by default. The flag both disables culling AND fixes the pass's position in the graph.
