# Empirical examples — RenderGraph usage in URP 17.5 and project packages

Bucketed survey of every notable RG pass. For each: file:line, one-sentence description, builder methods used, dependency style.

The point is to give you a "closest existing pass" you can mirror declarations from when adding new code, and to show how URP itself wires up the patterns this project depends on.

---

## URP 17.5 — passes that publish global textures (producers)

Source root: `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/`.

| Pass | file:line | What it publishes | Builder methods |
| --- | --- | --- | --- |
| MainLightShadowCasterPass | `Passes/MainLightShadowCasterPass.cs:482` | `_MainLightShadowmapTexture` slot via `SetGlobalTextureAfterPass`; cascade matrix array + split spheres + shadow params + offsets via `cmd.SetGlobal*` inside render func | `AddRasterRenderPass`, `UseRendererList` (×cascades), `SetRenderAttachmentDepth`, `AllowGlobalStateModification(true)`, `SetGlobalTextureAfterPass`, `SetRenderFunc` |
| AdditionalLightsShadowCasterPass | `Passes/AdditionalLightsShadowCasterPass.cs:1045` | `_AdditionalLightsShadowmapTexture` | `AddRasterRenderPass`, `SetGlobalTextureAfterPass` |
| GBufferPass | `Passes/GBufferPass.cs:276` | `_CameraNormalsTexture`, `_CameraRenderingLayersTexture` | `AddRasterRenderPass`, `SetGlobalTextureAfterPass` (×2) |
| DepthNormalOnlyPass | `Passes/DepthNormalOnlyPass.cs:247-254` | `_CameraNormalsTexture`, `_CameraRenderingLayersTexture`, `_CameraDepthTexture` | `AddRasterRenderPass`, three `SetGlobalTextureAfterPass` |
| DepthOnlyPass | `Passes/DepthOnlyPass.cs:153` | `_CameraDepthTexture` | `AddRasterRenderPass`, `SetGlobalTextureAfterPass` |
| CopyDepthPass | `Passes/CopyDepthPass.cs:281,376,378` | `_CameraDepthTexture` | `AddRasterRenderPass`, `UseTexture(source, Read)`, `SetGlobalTextureAfterPass`, `AllowGlobalStateModification(true)` |
| CopyColorPass | `Passes/CopyColorPass.cs:234` | `_CameraOpaqueTexture` | `AddRasterRenderPass`, `SetGlobalTextureAfterPass` |
| MotionVectorRenderPass | `Passes/MotionVectorRenderPass.cs:239,241` | `_MotionVectorTexture`, `_MotionVectorDepthTexture` | `AddRasterRenderPass`, `UseAllGlobalTextures(true)` (line 219), `SetGlobalTextureAfterPass` (×2) |
| ScreenSpaceAmbientOcclusionPass | `Passes/ScreenSpaceAmbientOcclusionPass.cs:369,408` | `_SSAO_OcclusionTexture` | `AddUnsafePass` (Blit SSAO), `SetGlobalTextureAfterPass` |
| DrawScreenSpaceUIPass | `Passes/DrawScreenSpaceUIPass.cs:206` | `_OverlayUITexture` | `AddUnsafePass`, `UseAllGlobalTextures(true)`, `SetGlobalTextureAfterPass` |
| ScreenSpaceShadows (renderer feature) | `RendererFeatures/ScreenSpaceShadows.cs:214,217,220,223` | `_ScreenSpaceShadowmapTexture` (the `_MAIN_LIGHT_SHADOWS_SCREEN` opaque texture) | `AddUnsafePass`, `UseTexture(color, WriteAll)`, `AllowGlobalStateModification(true)`, `SetGlobalTextureAfterPass` |
| DBufferRenderPass | `Decal/DBuffer/DBufferRenderPass.cs:281,287,296,299` | `_DBufferTexture0/1/2` | `AddRasterRenderPass`, `UseTexture` (depth, normals, layers), `UseGlobalTexture(s_SSAOTextureID)`, `UseRendererList`, `SetGlobalTextureAfterPass` (×3), `AllowGlobalStateModification(true)` |

**Pattern**: producers always call `SetGlobalTextureAfterPass(handle, propertyId)` AND `AllowGlobalStateModification(true)` (the latter is mandatory if the render func issues additional `cmd.SetGlobal*`, optional if only the texture slot is published).

---

## URP 17.5 — passes that read URP globals (consumers)

| Pass | file:line | What it reads | How it declares the dep |
| --- | --- | --- | --- |
| FinalBlitPass | `Passes/FinalBlitPass.cs:293` | `_CameraDepthTexture` | `builder.UseGlobalTexture(s_CameraDepthTextureID)` |
| DBufferRenderPass | `Decal/DBuffer/DBufferRenderPass.cs:287` | `_SSAOFinalTexture` (when valid) | `builder.UseGlobalTexture(s_SSAOTextureID)` (named) — only path in URP source where `UseGlobalTexture` is used by name; everything else uses `UseAllGlobalTextures` |
| DrawObjectsPass | `Passes/DrawObjectsPass.cs:294` | arbitrary user shaders → unknown globals | `builder.UseAllGlobalTextures(true)` |
| MotionVectorRenderPass | `Passes/MotionVectorRenderPass.cs:219` | depth/normals/etc. for motion-vector compute | `UseAllGlobalTextures(true)` |
| DrawScreenSpaceUIPass | `Passes/DrawScreenSpaceUIPass.cs:196,244` | UI shaders | `UseAllGlobalTextures(true)` (×2) |
| MainLightShadowCasterPass (render attachment + shadow draws) | `Passes/MainLightShadowCasterPass.cs:482-505` | renderer lists (one per cascade) | `UseRendererList` (×cascades), `SetRenderAttachmentDepth`, `AllowGlobalStateModification(true)`, `SetGlobalTextureAfterPass(shadowTexture, _MainLightShadowmapID)` |

**Note**: the URP `MainLightShadowCasterPass` is both a producer (publishes `_MainLightShadowmapTexture`) and a consumer (uses `UseRendererList` to draw casters into the depth attachment).

---

## URP 17.5 — compute / unsafe passes

| Pass | file:line | Type | Purpose |
| --- | --- | --- | --- |
| ProbeVolumeDebugPass | `Passes/ProbeVolumeDebugPass.cs:82` | `AddComputePass` | APV debug compute writeback. The only `AddComputePass` in stock URP. |
| ScreenSpaceAmbientOcclusionPass.Blit | `Passes/ScreenSpaceAmbientOcclusionPass.cs:369` | `AddUnsafePass` | SSAO compose blit |
| PostProcessPassRenderGraph (multiple) | `Passes/PostProcessPassRenderGraph.cs:320,803,886,939,1066,1278,1681,1779,1922` | `AddUnsafePass` | Bloom (mip pyramid), Kawase blur, Dual blur, Gaussian DoF, Bokeh DoF, lens flare occlusion + render, screen-space lens flare |
| HDRDebugViewPass | `Passes/HDRDebugViewPass.cs:245` | `AddUnsafePass` | HDR CIExy debug blit |
| InvokeOnRenderObjectCallbackPass | `Passes/InvokeOnRenderObjectCallbackPass.cs:42` | `AddUnsafePass` | calls user `OnRenderObject` callbacks |
| CapturePass | `Passes/CapturePass.cs:59` | `AddUnsafePass` | screen capture |
| DrawScreenSpaceUIPass (offscreen + overlay) | `Passes/DrawScreenSpaceUIPass.cs:218,261` | `AddUnsafePass` (×2) | IMGUI / software cursor |
| ScreenSpaceShadows (renderer feature) | `RendererFeatures/ScreenSpaceShadows.cs:214` | `AddUnsafePass` | screen-space shadow blit (rationale at line 208-213: avoids merging with deferred lighting, see [pass-types.md](pass-types.md)) |

**Observation**: URP itself uses `AddUnsafePass` for almost every blit-with-side-effects pass, exactly mirroring the project's pattern. `AddComputePass` is rare in URP.

---

## Project: `Packages/is.zori.atmospherics/Runtime/`

### Compute / unsafe passes that read URP globals

| Pass | file:line | Reads | Declarations | Notes |
| --- | --- | --- | --- | --- |
| `VolumetricFogPass.RecordBakePass` | `VolumetricFog/VolumetricFogPass.cs:1039,1143,1320` | `_MainLightShadowmapTexture` for cascade-shadow tap inside populate kernel | `AddUnsafePass`, `UseTexture(mainShadow, Read)` (line 1143), `UseTexture` (×many UAVs), `AllowGlobalStateModification(true)`, `AllowPassCulling(false)` | Compute populate + integrate, gated on `lightData.mainLightIndex >= 0` and `light.shadows != None`. Cascade matrices/spheres flow CB-side from URP. |
| `AtmosphericsScreenSpaceShadowsPass.RecordComposePass` | `DistantShadows/AtmosphericsScreenSpaceShadowsPass.cs:306,316,321,322,327` | URP shadow globals + low-res depth | `AddUnsafePass`, `UseTexture(target, WriteAll)`, `UseTexture(lowResDepth)`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)`, `SetGlobalTextureAfterPass(target, _ScreenSpaceShadowmapTexture)` | Project's own SSS implementation paralleling URP's. |
| `AtmosphericsScreenSpaceShadowsPass.RecordUpsamplePass` | `DistantShadows/AtmosphericsScreenSpaceShadowsPass.cs:369,380-384,386` | low-res shadow + depth | `AddUnsafePass`, three `UseTexture`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)`, `SetGlobalTextureAfterPass` | |
| `RealtimeGIPass.Record` | `RealtimeGI/RealtimeGIPass.cs:852,959,960` | URP main shadow + scene radiance globals | `AddUnsafePass`, `AllowGlobalStateModification(true)`, `AllowPassCulling(false)` | |
| `PhysicalSkyPass.Record` | `PhysicalSky/PhysicalSkyPass.cs:345,377,378` | sun/moon globals | `AddUnsafePass`, `AllowGlobalStateModification(true)`, `AllowPassCulling(false)` | |
| `DistantFogPass.Record` | `VolumetricFog/DistantFogPass.cs:289,353` | host-side fog uniforms | `AddUnsafePass`, `AllowGlobalStateModification(true)` | |

### Raster passes that publish globals

| Pass | file:line | Publishes | Builder methods |
| --- | --- | --- | --- |
| `CloudShadowSource.RecordBakePass` | `DistantShadows/CloudShadowSource.cs:612,656-663` | (intermediate) | `AddRasterRenderPass`, `SetRenderAttachment(rawHandle, 0)`, three `UseTexture`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)`, `AllowPassCulling(false)` |
| `CloudShadowSource.RecordTemporalPass` | `DistantShadows/CloudShadowSource.cs:713,725-730` | (intermediate) | similar; `UseTexture(rawHandle)`, `UseTexture(prevHandle)` |
| `CloudShadowSource.RecordBlurPass` | `DistantShadows/CloudShadowSource.cs:748,760-764` | (intermediate) | similar |
| `CloudShadowSource.RecordFinalBlur` | `DistantShadows/CloudShadowSource.cs:776,788-793` | `_CloudShadowmap` | `SetGlobalTextureAfterPass(finalHandle, PropCloudShadowmap)` |
| `CloudShadowSource.RecordMipGenPass` | `DistantShadows/CloudShadowSource.cs:806,812-815` | mip chain | `AddUnsafePass`, `UseTexture(finalHandle, ReadWrite)`, `AllowGlobalStateModification(true)` |
| `HeightfieldShadowSource.*` | `DistantShadows/Heightfields/HeightfieldShadowSource.cs:356-579` | per-source HF shadow texture | 5 raster passes (Bake/Temporal/BlurH/BlurV/Fold) + 1 unsafe MipGen, all with `AllowGlobalStateModification(true)`; `UseAllGlobalTextures(true)` on first (line 367) |
| `DistantShadowCompositor.*` | `DistantShadows/DistantShadowCompositor.cs:400,494,530,568,634,648-649` | distant-shadow merged texture | 4 blur raster passes + a compose pass; final compose at line 634 has `UseTexture(blurred)`, `UseTexture(cameraDepthTexture)`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)` |
| `VolumetricCloudsPass.RecordTracePass` | `VolumetricClouds/VolumetricCloudsPass.cs:522,537-590` | `_CloudsTraceLighting`, `_CloudsTraceDepth` | `AddRasterRenderPass`, `SetRenderAttachment` (×2 MRT), `UseTexture(activeDepth)`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)`, two `SetGlobalTextureAfterPass` |
| `VolumetricCloudsPass.RecordReprojectPass` | `VolumetricClouds/VolumetricCloudsPass.cs:682,726-727` | reprojected cloud frame | similar pattern |
| `VolumetricCloudsPass.RecordPostProcessPass` | `VolumetricClouds/VolumetricCloudsPass.cs:810,830-831` | (intermediate) | `AddRasterRenderPass`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)` |
| `VolumetricCloudsPass.RecordCompositePass` | `VolumetricClouds/VolumetricCloudsPass.cs:861,882-883` | final composited cloud color | similar |
| `CloudHemiOctCapturePass` | `VolumetricClouds/CloudHemiOctCapturePass.cs:199,229-231` | `_CloudHemiOctCapture` | `AddRasterRenderPass`, `SetRenderAttachment(captureHandle, 0)`, three 3D-tex `UseTexture`, `UseAllGlobalTextures(true)`, `AllowGlobalStateModification(true)`, `SetGlobalTextureAfterPass` |

### Transient texture pattern

`AtmosphericsRenderGraph.CreateTransient` at `Core/AtmosphericsRenderGraph.cs:40-49` is the package-scoped wrapper:
```csharp
public static TextureHandle CreateTransient(
  RenderGraph rg,
  in RenderTextureDescriptor desc,
  string name,
  bool clear = false,
  FilterMode filter = FilterMode.Point
)
{
  return UniversalRenderer.CreateRenderGraphTexture(rg, desc, name, clear, filter);
}
```

`UniversalRenderer.CreateRenderGraphTexture` (`BuiltInPackages/.../Runtime/UniversalRendererRenderGraph.cs`) is URP's standard transient-texture helper — it picks the right format and registers the handle as graph-owned. The project never calls `renderGraph.CreateTexture(in TextureDesc)` directly; everything goes through this wrapper or `renderGraph.ImportTexture(rtHandle)` for persistent history textures.

History textures are imported per camera. Pattern from `VolumetricCloudsPass.cs` (and elsewhere): allocate `RTHandle` in feature `Create()` / per-camera `EnsureState`, release in `Dispose`, and inside `RecordRenderGraph` call `renderGraph.ImportTexture(_handle)` to lift it into a `TextureHandle`. The `RTHandle` is the lifetime; the `TextureHandle` is the per-frame graph reference.

---

## Project: `Packages/is.zori.heightfields/`

| Pass | file:line | Type | Purpose | Declarations |
| --- | --- | --- | --- | --- |
| `HeightfieldRenderFeature.HiZ Depth Copy` | `Heightfields/Runtime/HeightfieldRenderFeature.cs:475,482-484,489` | `AddRasterRenderPass` | copy depth into HiZ mip 0 | `SetRenderAttachment(depthCopy, 0, Write)`, `UseTexture(depthSource, Read)`, `AllowPassCulling(false)` |
| `HeightfieldRenderFeature.HiZ Downsample` | `Heightfields/Runtime/HeightfieldRenderFeature.cs:521,543-548` | `AddUnsafePass` | mip pyramid via compute | `UseTexture(depthCopy, Read)`, `UseTexture(mipA, ReadWrite)`, `UseTexture(mipB, ReadWrite)`, `AllowPassCulling(false)` |
| `HeightfieldRenderFeature.BVH Reset Regions` | `Heightfields/Runtime/HeightfieldRenderFeature.cs:1142,1163,1165` | `AddUnsafePass` | clear BVH region buffer | `AllowPassCulling(false)` |
| `HeightfieldRenderFeature.HeightCapture` | `Heightfields/Runtime/HeightfieldRenderFeature.cs:1231,1259,1261` | `AddUnsafePass` | capture height buffer | `AllowPassCulling(false)` |
| `HeightfieldTerrainController.Stamp` | `Heightfields/Runtime/HeightfieldTerrainController.cs:547` | `AddUnsafePass` | stamp height edits | per-handle `UseTexture` |
| `RWVTFulfillerDispatch` | `VirtualTextures/Runtime/RWVTFulfillerDispatch.cs:94,113,115,117,119` | `AddUnsafePass` | virtual-texture page fulfillment compute | `UseTexture(physicalTextures[i], ReadWrite)` (×slabs), `UseTexture(pageTableTexture, ReadWrite)`, `AllowPassCulling(false)` |

Heightfields makes minimal use of globals — it operates on imported persistent textures and dispatches compute over them. No `SetGlobalTextureAfterPass` calls in the package.

---

## Recurring patterns to copy from

### "Compute pass that reads URP main-light shadow"

Mirror `VolumetricFogPass.cs:1039-1147` exactly:
1. `AddUnsafePass` (auto-allows global state mod).
2. Gate the dep on `mainLightIndex >= 0 && light.shadows != None` (line 1132-1147).
3. `builder.UseTexture(resourceData.mainShadowsTexture, AccessFlags.Read)` (line 1143).
4. `CoreUtils.SetKeyword(populateCS, "_MAIN_LIGHT_SHADOWS_CASCADE", mainLightActive)` before dispatch.
5. Call a local explicit-LOD-only HLSL helper, NOT `MainLightRealtimeShadow`.

See [shadow-sampling-from-compute.md](shadow-sampling-from-compute.md) for the full recipe.

### "Raster pass that produces a global texture"

Mirror URP `CopyDepthPass.cs:281-378`:
1. `AddRasterRenderPass`.
2. `SetRenderAttachmentDepth(destination, Write)` (or `SetRenderAttachment(...)` for color).
3. `UseTexture(source, Read)`.
4. `SetGlobalTextureAfterPass(destination, propertyId)`.
5. `AllowGlobalStateModification(true)` (only needed if the render func also issues `cmd.SetGlobal*`; CopyDepth does for `_CameraDepthTexture` matrix updates).
6. `SetRenderFunc(static (data, ctx) => { ... })`.

### "Compute pass with multiple kernels sharing state"

Mirror `VolumetricFogPass.cs:1039-2000`:
1. `AddUnsafePass` (compute-pass type can't host raster sub-blits anyway, so unsafe is the natural fit).
2. Declare every UAV/SRV via `UseTexture`.
3. `AllowPassCulling(false)` if the pass writes to history.
4. In render func: `cmd.SetComputeVectorParam` / `SetComputeMatrixParam` per-kernel (Vulkan needs explicit per-dispatch binds for host-side globals — `feedback_compute_needs_explicit_params.md`).
5. `cmd.DispatchCompute(populateCS, populateKernel, gx, gy, gz)`.
6. Repeat 4-5 for second kernel, sharing PassData fields.

### "Per-camera history textures"

Allocate in feature `Create()` or per-camera `EnsureState`:
```csharp
ShadowUtils.ShadowRTReAllocateIfNeeded(ref _historyHandle, w, h, bits, name: "_MyHistory");
```
Inside `RecordRenderGraph`: `var th = renderGraph.ImportTexture(_historyHandle);` then declare with `UseTexture` like any transient.

Release in feature `Dispose`:
```csharp
_historyHandle?.Release();
```

---

## Forbidden patterns (project rules)

From project memory and `Packages/is.zori.atmospherics/Runtime/Core/AtmosphericsRenderGraph.cs:7-34`:

- ❌ `RTHandle` in `PassData` or as a render-func argument. RTHandle is allocation-only.
- ❌ `Shader.SetGlobalTexture` at record time. Use `SetGlobalTextureAfterPass`.
- ❌ `Shader.GetGlobalTexture` to forward a texture from one pass to another via `cmd.SetComputeTextureParam`. Use `UseGlobalTexture` / `UseTexture(resourceData.<slot>)` and let RG do the routing.
- ❌ `ScriptableRendererFeature` holding scene refs. Read from `frameData.Get<UniversalCameraData>()` etc. (`feedback_no_scene_refs_in_features.md`).
- ❌ `Resources.Load` for shaders. Serialised manifest (`feedback_resources_load_shaders.md`, `feedback_manifest_on_feature_not_resources.md`).
- ❌ `cameraDepthTexture` (the optional CopyDepth copy) when you mean `activeDepthTexture` (the actual depth target). See `feedback_active_depth_not_depth_texture.md`.
- ❌ Redeclaring `sampler_LinearClamp` / `sampler_LinearClampCompare` in package headers. Already declared by URP. (`feedback_urp_sampler_linearclamp_collision.md`)
