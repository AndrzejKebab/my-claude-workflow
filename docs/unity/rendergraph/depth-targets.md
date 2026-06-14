# Depth target selection — three resources, two of them traps

URP's frame-data exposes three depth-related `TextureHandle`s on `UniversalResourceData`. They're not interchangeable — picking the wrong one silently breaks downstream sampling, or throws "color format used as depth attachment" at record time. This is the rule for writing a custom depth-prepass-style raster pass.

## The three handles

Source: `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/FrameData/UniversalResourceData.cs`.

| Field | line | What it is | Format |
| --- | --- | --- | --- |
| `activeDepthTexture` | 61 | The active depth render target the camera is currently rendering into. | Depth-stencil (D24/D32). |
| `cameraDepth` | 137 | Main offscreen camera depth target. "All passes can write to it depending on frame setup." | Depth-stencil. |
| `cameraDepthTexture` | 193 | "Contains the scene depth if the CopyDepth or Depth Prepass passes are executed." | **Configuration-dependent.** Depth in non-priming forward; **R32_SFloat** in priming/deferred (post-CopyDepth sampleable copy). |

`cameraDepthTexture` is the one bound to the global `_CameraDepthTexture` that lit shaders sample for screen-space effects.

## URP's prepass-target rule

`UniversalRendererRenderGraph.cs:1055-1060`:

```csharp
if (requiresPrepass)
{
    // If we're in deferred mode, prepasses always render directly to the depth attachment rather than the camera depth texture.
    // In non-deferred mode, we only render to the depth attachment directly when depth priming is enabled and we're starting with an empty depth buffer.
    bool renderToAttachment = (usesDeferredLighting || useDepthPriming);
    TextureHandle depthTarget = renderToAttachment ? resourceData.activeDepthTexture : resourceData.cameraDepthTexture;
    ...
}
```

So URP's prepass writes to one of two textures depending on `useDepthPriming || usesDeferredLighting`:

| Pipeline mode | `useDepthPriming` | URP prepass writes | `cameraDepthTexture` format | Sampleable depth in `_CameraDepthTexture` filled by |
| --- | --- | --- | --- | --- |
| Forward | off | `cameraDepthTexture` (depth-format) | depth-format | the prepass itself (in-place) |
| Forward | on | `activeDepthTexture` | R32_SFloat (color) | a separate `CopyDepthPass` |
| Deferred | (any) | `activeDepthTexture` | R32_SFloat (color) | a separate `CopyDepthPass` |

The "forward without priming" case is the only one in which `cameraDepthTexture` is itself a depth attachment — URP makes it dual-purpose to skip the copy.

## Picking the same target as URP from a custom feature

`useDepthPriming` is `internal` on `ScriptableRenderer` (`BuiltInPackages/com.unity.render-pipelines.universal/Runtime/ScriptableRenderer.cs:727`). External code can't read it. The way to recover URP's choice without reflection is to **detect by format**:

```csharp
var depth = resourceData.cameraDepthTexture;
if (depth.IsValid())
{
    var info = graph.GetRenderTargetInfo(depth);
    if (!GraphicsFormatUtility.IsDepthFormat(info.format))
        depth = resourceData.activeDepthTexture;
}
else
{
    depth = resourceData.activeDepthTexture;
}
builder.SetRenderAttachmentDepth(depth, AccessFlags.ReadWrite);
```

This lands custom prepass writes in whichever texture URP itself wrote scene casters into, so:
- `_CameraDepthTexture` (sampled by SSS, transparent depth-blend, fog, etc.) sees both URP scene casters and our content.
- No "color format used as depth attachment" exception — `R32_SFloat` cameraDepthTexture always falls through to `activeDepthTexture`.

## Why not just write `activeDepthTexture` always

In the **forward, no priming** case URP's prepass writes `cameraDepthTexture` (the depth-format one) and never touches `activeDepthTexture` at prepass time. Our writes to `activeDepthTexture` would land in a different physical texture from URP's scene-caster depth. `_CameraDepthTexture` global resolves to URP's `cameraDepthTexture`, so SSS / fog / forward-lit shaders that reconstruct world position from camera depth see scene casters but **not** our terrain — pixels reconstruct to far-plane garbage. Visual signature: object silhouettes appear as shadows under terrain (cascade WTS lookup at far-plane `wp` happens to project onto opaque-object atlas regions).

## Why not just write `cameraDepthTexture` always

In the **priming or deferred** case `cameraDepthTexture` is the post-CopyDepth `R32_SFloat` sampleable copy. RG (correctly) rejects it as a depth attachment:

```
InvalidOperationException: In pass 'X' when trying to use resource '_CameraDepthTexture' of
type Texture - SetRenderAttachmentDepth is called on a texture that has a color format
R32_SFloat. Use a texture with a depth format instead, or call SetRenderAttachment.
```

This regression is silent in any single test config — it only shows up when you toggle a feature that flips the priming heuristic.

## What `_CameraDepthTexture` resolves to

`MainLightShadowCasterPass.cs`-style `SetGlobalTextureAfterPass(handle, _CameraDepthTextureID)` runs from one of:
- the prepass itself (forward + non-priming) — the prepass IS the depth-format texture, and it publishes itself.
- `CopyDepthPass.Render` (`Passes/CopyDepthPass.cs:281,376,378`) when a separate copy is needed.

Either way the consumer pattern from a custom feature is:

```csharp
builder.UseGlobalTexture(_CameraDepthTextureID, AccessFlags.Read);
// OR
builder.UseAllGlobalTextures(true);
```

— see [`global-state.md`](global-state.md). The texture-handle lookup goes through the standard URP global slot whether the format is depth-format or R32_SFloat.

## Forbidden patterns

- ❌ `SetRenderAttachmentDepth(resourceData.cameraDepthTexture, ...)` without checking format. Throws when priming/deferred.
- ❌ Always writing `activeDepthTexture` in a custom prepass. Breaks `_CameraDepthTexture` content in forward-non-priming.
- ❌ Sampling depth from `activeDepthTexture` in a fragment/compute shader during the same frame's opaque rendering — read-during-write hazard. URP's `cameraDepthTexture` exists specifically to avoid this; route through it.
- ❌ Ignoring `cameraData.requiresDepthPrepass` / `renderPassInputs.requiresDepthTexture` when deciding whether to enqueue the pass. If URP isn't running a prepass at all, our standalone prepass becomes the only writer and downstream samplers may need different routing.
