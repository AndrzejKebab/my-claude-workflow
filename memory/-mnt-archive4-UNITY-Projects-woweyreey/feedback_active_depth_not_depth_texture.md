---
name: URP depth handle selection
description: cameraDepthTexture vs activeDepthTexture vs cameraDepth — picking the right one is config-dependent (forward vs deferred, useDepthPriming on/off); see docs/unity/rendergraph/depth-targets.md for the canon
type: feedback
originSessionId: 16ae2408-78b8-4291-ab7e-f423f44c3618
---
**Rule:** there is no single "always use X" answer for URP depth handles. Picking the wrong one silently breaks `_CameraDepthTexture` consumers (SSS / fog / forward-lit reconstruction) or throws "color format used as depth attachment" depending on URP config. The canonical reference is `docs/unity/rendergraph/depth-targets.md`.

**Why:** URP exposes three handles on `UniversalResourceData`:
- `activeDepthTexture` — the active depth render target.
- `cameraDepth` — the main offscreen depth target.
- `cameraDepthTexture` — config-dependent: depth-format in forward+no-priming (dual-purpose with the prepass write target), R32_SFloat sampleable copy in priming/deferred (post-CopyDepth).

URP's own prepass-target rule (`UniversalRendererRenderGraph.cs:1055-1060`): writes `cameraDepthTexture` if `!(useDepthPriming || usesDeferredLighting)`, else `activeDepthTexture`. `useDepthPriming` is `internal` — external code can't read it; format-detect instead.

**How to apply:**

For a custom **raster prepass** that writes depth (mirroring URP's prepass): format-detect to land in whichever physical texture URP chose:
```csharp
var depth = resourceData.cameraDepthTexture;
if (depth.IsValid())
{
  var info = graph.GetRenderTargetInfo(depth);
  if (!GraphicsFormatUtility.IsDepthFormat(info.format))
    depth = resourceData.activeDepthTexture;
}
else
  depth = resourceData.activeDepthTexture;
builder.SetRenderAttachmentDepth(depth, AccessFlags.ReadWrite);
```
Reference site: `Packages/is.zori.heightfields/Heightfields/Runtime/HeightfieldRenderFeature.cs:2042-2052`.

For a **compute pass that samples depth between prepass and opaques** (e.g. HiZ build): same format-detect — route through `_CameraDepthTexture` global is **wrong** here because in priming/deferred it isn't filled until `CopyDepthPass` runs after opaques.

For a **compute pass that samples depth after opaques** (consumers like SSAO): `builder.UseGlobalTexture(_CameraDepthTextureID, AccessFlags.Read)` or `UseAllGlobalTextures(true)` — by then `_CameraDepthTexture` is populated regardless of mode.

**Forbidden:** sampling `activeDepthTexture` from a fragment/compute shader *during* the same frame's opaque rendering — read-during-write hazard. URP's `cameraDepthTexture` exists specifically to avoid this. The format-detect rule above only works because our HiZ build is scheduled *between* prepass and opaques — not during opaques.

**Always toggle URP forward/deferred and `useDepthPriming` to verify** any custom depth pass — the bug is silent in any single config and only appears when the priming heuristic flips.
