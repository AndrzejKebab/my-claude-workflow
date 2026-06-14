# Sampling URP cascade shadows from a compute pass

The exact recipe for the project's bug: a compute kernel needs to read URP's main-light cascade shadow map and arrive at the same attenuation value a forward-lit fragment shader would compute. Source: URP `Shadows.hlsl` 629 lines, `MainLightShadowCasterPass.cs`, project's `ZoriVolumetricFogPopulate.compute`.

---

## The chain in `Shadows.hlsl`

URP's shadow path layered top-down:

| Function | Source | What it does |
| --- | --- | --- |
| `MainLightRealtimeShadow(shadowCoord, shadowParams, samplingData)` | `Shadows.hlsl:372-383` | Top-level entry. Branches on `_MAIN_LIGHT_SHADOWS_SCREEN` to either screen-space tex sample or shadowmap sample. |
| `MainLightRealtimeShadow(shadowCoord)` | `Shadows.hlsl:385-392` | Convenience overload, fills in `shadowParams` and `samplingData` from globals. |
| `TransformWorldToShadowCoord(positionWS)` | `Shadows.hlsl:356-370` | Computes shadow-space coordinate. Uses `_MainLightWorldToShadow[cascadeIndex]` (cascade path) or `_MainLightWorldToShadow[0]` (no cascade). |
| `ComputeCascadeIndex(positionWS)` | `Shadows.hlsl:342-354` | Picks cascade by 4-sphere distance test using `_CascadeShadowSplitSpheres0..3` and `_CascadeShadowSplitSphereRadii`. |
| `SampleShadowmap(...)` | `Shadows.hlsl:306-340` | Branches by soft-shadow quality keyword to a filter routine. Calls `SAMPLE_TEXTURE2D_SHADOW` directly for hard shadows. |
| `SampleShadowmapFilteredLow/Medium/High` | `Shadows.hlsl:234-284` | PCF filters using `_MainLightShadowOffset0/1` and `_MainLightShadowmapSize`. Each tap is `SAMPLE_TEXTURE2D_SHADOW`. |
| `SampleScreenSpaceShadowmap(shadowCoord)` | `Shadows.hlsl:218-232` | Reads pre-computed screen-space shadow texture via `SAMPLE_TEXTURE2D` (implicit-LOD!). |
| `GetMainLightShadowFade(positionWS)` | `Shadows.hlsl:434-441` | Distance-based fade using `_MainLightShadowParams.z/w`. |
| `BEYOND_SHADOW_FAR(shadowCoord)` macro | `Shadows.hlsl:135` | `shadowCoord.z <= 0.0 \|\| shadowCoord.z >= 1.0`. |
| `GetMainLightShadowParams()` | `Shadows.hlsl:184-188` | Reads `_MainLightShadowParams`. |
| `GetMainLightShadowSamplingData()` | `Shadows.hlsl:152-162` | Builds `ShadowSamplingData` from `_MainLightShadowOffset0/1`, `_MainLightShadowmapSize`, `_MainLightShadowParams.y`. |

`_MAIN_LIGHT_SHADOWS_SCREEN` is the trap. Quoted from `Shadows.hlsl:378-381`:
```hlsl
#if defined(_MAIN_LIGHT_SHADOWS_SCREEN) && !defined(_SURFACE_TYPE_TRANSPARENT)
    return SampleScreenSpaceShadowmap(shadowCoord);
#else
    return SampleShadowmap(TEXTURE2D_ARGS(_MainLightShadowmapTexture, sampler_LinearClampCompare), shadowCoord, shadowSamplingData, shadowParams, false);
#endif
```

`SampleScreenSpaceShadowmap` (`Shadows.hlsl:218-232`):
```hlsl
half SampleScreenSpaceShadowmap(float4 shadowCoord)
{
    shadowCoord.xy /= max(0.00001, shadowCoord.w);
    shadowCoord.xy = UnityStereoTransformScreenSpaceTex(shadowCoord.xy);
#if defined(UNITY_STEREO_INSTANCING_ENABLED) || defined(UNITY_STEREO_MULTIVIEW_ENABLED)
    half attenuation = SAMPLE_TEXTURE2D_ARRAY(_ScreenSpaceShadowmapTexture, sampler_PointClamp, shadowCoord.xy, unity_StereoEyeIndex).x;
#else
    half attenuation = half(SAMPLE_TEXTURE2D(_ScreenSpaceShadowmapTexture, sampler_PointClamp, shadowCoord.xy).x);
#endif
    return attenuation;
}
```

`SAMPLE_TEXTURE2D` expands to `texture.Sample(sampler, coord)` on Vulkan (`BuiltInPackages/com.unity.render-pipelines.core/ShaderLibrary/API/Vulkan.hlsl:97`):
```hlsl
#define PLATFORM_SAMPLE_TEXTURE2D(textureName, samplerName, coord2)  textureName.Sample(samplerName, coord2)
```

`Texture2D.Sample` is implicit-LOD — the GPU computes the LOD from screen-space derivatives, which exist only in the rasterizer. Vulkan compute pipelines reject implicit-LOD reads at validation: error `VUID-RuntimeSpirv-ImplicitLod`. On D3D12 it silently returns LOD 0 in some drivers, undefined in others.

Conversely `SAMPLE_TEXTURE2D_SHADOW` is explicit-LOD on every API target (`Vulkan.hlsl:131`):
```hlsl
#define SAMPLE_TEXTURE2D_SHADOW(textureName, samplerName, coord3)    textureName.SampleCmpLevelZero(samplerName, (coord3).xy, (coord3).z)
```

So **the cascade-shadowmap path is compute-safe** (it ends in `SampleCmpLevelZero`), and **the screen-space path is NOT** (it ends in implicit-LOD `Sample`). The fix is to bypass the screen-space branch on the compute side.

---

## URP-published globals consumed by the cascade path

Cross-referenced against `MainLightShadowCasterPass.cs:44-57,398-435`:

| HLSL declaration | C# publication | How RG sees it | Compute-visible on Vulkan? |
| --- | --- | --- | --- |
| `TEXTURE2D_SHADOW(_MainLightShadowmapTexture)` (`Shadows.hlsl:63`) | `builder.SetGlobalTextureAfterPass(shadowTexture, _MainLightShadowmapID)` (`MainLightShadowCasterPass.cs:505`) | RG-tracked global slot | yes, if consumer declares the dep (`UseGlobalTexture(_MainLightShadowmapID)` or `UseTexture(resourceData.mainShadowsTexture)`) |
| `SAMPLER_CMP(sampler_LinearClampCompare)` (`Shadows.hlsl:65`) | inline-encoded sampler — name pattern `Linear` + `Clamp` + `Compare` synthesises a `SamplerComparisonState` with linear filter, clamp address, comparison enabled. No C# bind. | invisible to RG (it's a sampler, not a texture) | yes — sampler is per-shader-module, no host bind needed. See [samplers.md](samplers.md). |
| `float4x4 _MainLightWorldToShadow[MAX_SHADOW_CASCADES + 1]` (`Shadows.hlsl:75`, 5 entries on URP defaults) | `cmd.SetGlobalMatrixArray(_WorldToShadow, m_MainLightShadowMatrices)` (`MainLightShadowCasterPass.cs:398`) | not RG-tracked (no `UseGlobalMatrixArray` exists) | yes — rides CommandBuffer ordering. Producer keeps order via `AllowGlobalStateModification(true)` at `MainLightShadowCasterPass.cs:502`. |
| `float4 _CascadeShadowSplitSpheres0/1/2/3` (`Shadows.hlsl:76-79`) | `cmd.SetGlobalVector(_CascadeShadowSplitSpheres0..3, ...)` (`MainLightShadowCasterPass.cs:404-411`) | not RG-tracked | yes — same path |
| `float4 _CascadeShadowSplitSphereRadii` (`Shadows.hlsl:80`) | `cmd.SetGlobalVector(_CascadeShadowSplitSphereRadii, ...)` (`MainLightShadowCasterPass.cs:412-416`) | not RG-tracked | yes — same path |
| `float4 _MainLightShadowOffset0/1` (`Shadows.hlsl:82-83`) | `cmd.SetGlobalVector(_ShadowOffset0/1, ...)` (`MainLightShadowCasterPass.cs:425-430`, only when `supportsSoftShadows`) | not RG-tracked | yes — same path |
| `float4 _MainLightShadowParams` (`Shadows.hlsl:84`) | `cmd.SetGlobalVector(_ShadowParams, new Vector4(strength, soft, fadeScale, fadeBias))` (`MainLightShadowCasterPass.cs:399-400`) | not RG-tracked | yes — same path |
| `float4 _MainLightShadowmapSize` (`Shadows.hlsl:85`) | `cmd.SetGlobalVector(_ShadowmapSize, new Vector4(invW, invH, W, H))` (`MainLightShadowCasterPass.cs:432-434`, only when `supportsSoftShadows`) | not RG-tracked | yes — same path |
| `_MAIN_LIGHT_SHADOWS` / `_MAIN_LIGHT_SHADOWS_CASCADE` keywords | `cmd.SetKeyword(ShaderGlobalKeywords.MainLightShadows, count == 1)` and `cmd.SetKeyword(ShaderGlobalKeywords.MainLightShadowCascades, count > 1)` (`MainLightShadowCasterPass.cs:365-366`) | not RG-tracked | yes — same path. Compute kernel must include the matching `#pragma multi_compile` to compile a variant with the keyword set. |

---

## Builder declarations the receiver needs

The receiver is a compute pass (project: `AddUnsafePass` because the populate pass also issues `cmd.SetGlobal*` and dispatches multiple kernels — see [pass-types.md](pass-types.md)).

```csharp
// Inside RecordRenderGraph for the consumer:

using var builder = renderGraph.AddUnsafePass<BakeData>(s_LightingSampler.name, out var data, s_LightingSampler);

// 1. Texture read dep — pivots on the URP-provided shadow handle so RG schedules
//    MainLightShadowCasterPass before us.
var lightData = frameData.Get<UniversalLightData>();
var resourceData = frameData.Get<UniversalResourceData>();
var mainIdx = lightData.mainLightIndex;
data.MainLightActive = false;
if (mainIdx >= 0 && mainIdx < lightData.visibleLights.Length)
{
  var vl = lightData.visibleLights[mainIdx];
  if (vl.light != null && vl.light.shadows != LightShadows.None)
  {
    var mainShadow = resourceData.mainShadowsTexture;
    if (mainShadow.IsValid())
    {
      builder.UseTexture(mainShadow, AccessFlags.Read);
      data.MainLightActive = true;
    }
  }
}

// 2. AllowGlobalStateModification — auto-true on AddUnsafePass (RenderGraph.cs:1505).
//    For AddComputePass it would be needed manually only if THIS pass also issues
//    cmd.SetGlobal*; for read-only consumption of URP-published globals it is NOT
//    needed on the consumer.
builder.AllowGlobalStateModification(true);  // belt-and-suspenders for unsafe; auto-set anyway

// 3. AllowPassCulling(false) — prevent culling because the populate pass writes to
//    history textures whose dependency chain RG cannot fully see.
builder.AllowPassCulling(false);

// 4. Other texture deps for the kernel's own UAVs/SRVs:
builder.UseTexture(materialACurr, AccessFlags.ReadWrite);
// ... etc per kernel binding ...

builder.SetRenderFunc(static (BakeData d, UnsafeGraphContext ctx) => {
  var cmd = CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd);

  // 5. Variant compile — set the keyword on the compute shader so the
  //    `#pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE`
  //    selects the cascade variant. Mirror URP's keyword choice.
  CoreUtils.SetKeyword(d.PopulateCS, "_MAIN_LIGHT_SHADOWS_CASCADE", d.MainLightActive);
  CoreUtils.SetKeyword(d.PopulateCS, "_MAIN_LIGHT_SHADOWS", false);

  // 6. NO mirroring of the cascade matrix array / split spheres / shadow params
  //    is needed — URP issued them via cmd.SetGlobal* and the CommandBuffer is
  //    intact through to our DispatchCompute below. They are visible to compute.

  cmd.DispatchCompute(d.PopulateCS, d.PopulateKernel, gx, gy, d.ResZ);
});
```

What is **NOT** needed:
- `builder.UseAllGlobalTextures(true)` — adds noise. Only `_MainLightShadowmapTexture` matters and we already declared it.
- `cmd.SetComputeMatrixParam(populateCS, _MainLightWorldToShadow, ...)` — not for the URP shadow globals. They flow from URP's `cmd.SetGlobalMatrixArray`. Mirroring would only be necessary for globals that arrive via host-side `Shader.SetGlobal*` (see [global-state.md](global-state.md)).
- A keyword for `_MAIN_LIGHT_SHADOWS_SCREEN`. Don't compile that variant on the compute side; it leads to the implicit-LOD trap.

---

## Compute-side bypass of `MainLightRealtimeShadow`

Because `MainLightRealtimeShadow`'s `_MAIN_LIGHT_SHADOWS_SCREEN` branch uses `SAMPLE_TEXTURE2D` (implicit-LOD), do not call it from a compute kernel even if you also disable the screen-space keyword on the compute shader — the variant has to compile, and if any other consumer later flips `_MAIN_LIGHT_SHADOWS_SCREEN` global on for graphics, the compute variant compiled with that keyword would still trip the validator.

The project's pattern (`Packages/is.zori.atmospherics/Runtime/VolumetricFog/Shaders/ZoriVolumetricFogPopulate.compute:66-91`) is to write a local explicit-LOD-only helper:

```hlsl
half ZoriComputeSampleMainLightShadow(float3 wp)
{
#if defined(_MAIN_LIGHT_SHADOWS) || defined(_MAIN_LIGHT_SHADOWS_CASCADE)
  float4 shadowCoord = TransformWorldToShadowCoord(wp);

  // Explicit-LOD comparison sample. SAMPLE_TEXTURE2D_SHADOW expands to
  // `tex.SampleCmpLevelZero(sampler, uv, refZ)` on every API target.
  half attenuation = (half)SAMPLE_TEXTURE2D_SHADOW(
    _MainLightShadowmapTexture, sampler_LinearClampCompare, shadowCoord.xyz);

  // Apply shadow strength (URP `SampleShadowmap` line 335: LerpWhiteTo).
  half shadowStrength = (half)_MainLightShadowParams.x;
  attenuation = lerp(half(1.0), attenuation, shadowStrength);

  // Shadow fade toward 1.0 at the cascade far plane (Shadows.hlsl:434).
  half shadowFade = GetMainLightShadowFade(wp);

  // Out-of-frustum → fully lit (Shadows.hlsl:135 + 339).
  return BEYOND_SHADOW_FAR(shadowCoord)
    ? half(1.0)
    : lerp(attenuation, half(1.0), shadowFade);
#else
  return half(1.0);
#endif
}
```

The `#pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE` (no `_MAIN_LIGHT_SHADOWS_SCREEN` variant) at `ZoriVolumetricFogPopulate.compute:13` keeps the screen-space variant out of the variant table entirely.

`TransformWorldToShadowCoord`, `GetMainLightShadowFade`, and the `BEYOND_SHADOW_FAR` macro are pure-math URP helpers from `Shadows.hlsl:135,356,434` — no implicit-LOD anywhere in their bodies, safe to call from compute.

---

## Pragmatic checklist

For a compute pass that needs URP cascade shadows:

1. [ ] `#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"` (which transitively includes `Shadows.hlsl`). Required at top of compute file.
2. [ ] `#pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE` on the compute shader. **Do not include `_MAIN_LIGHT_SHADOWS_SCREEN`** as a variant.
3. [ ] Write a local helper that mirrors the cascade math but ends in `SAMPLE_TEXTURE2D_SHADOW` (which expands to `SampleCmpLevelZero`, explicit-LOD) — do not call `MainLightRealtimeShadow` directly.
4. [ ] In C#: `builder.UseTexture(resourceData.mainShadowsTexture, AccessFlags.Read)` to schedule after `MainLightShadowCasterPass`.
5. [ ] In C#: `CoreUtils.SetKeyword(myComputeShader, "_MAIN_LIGHT_SHADOWS_CASCADE", true)` for the multi-cascade case (or `_MAIN_LIGHT_SHADOWS` for single-cascade) before `cmd.DispatchCompute`. Mirror URP's cascade-count choice from `UniversalShadowData.mainLightShadowCascadesCount` — accessed via `frameData.Get<UniversalShadowData>()`.
6. [ ] Use `AddUnsafePass` (auto-permits global state modification) OR `AddComputePass` only if the pass does no `cmd.SetGlobal*` of its own.
7. [ ] Do NOT mirror the cascade matrix array / split spheres / shadow params via `cmd.SetComputeMatrixParam` / `SetComputeVectorParam`. URP issues them via `cmd.SetGlobal*` and they ride the CommandBuffer. Mirroring would over-couple, mask future URP changes, and break in multi-camera graphs because `Shader.GetGlobal*` reads stale values.
8. [ ] Do NOT use `Shader.GetGlobalTexture(_MainLightShadowmapID)` + `cmd.SetComputeTextureParam` to forward the shadow atlas — host-side reads are stale at record time. Rely on the URP global slot via `UseGlobalTexture` or `UseTexture(resourceData.mainShadowsTexture)`. (Project memory: `feedback_compute_shadow_sampling_canon.md`.)
9. [ ] Do NOT redeclare `sampler_LinearClampCompare` in your compute file — `Shadows.hlsl:65` already declares it. Redeclaration collides; project memory `feedback_urp_sampler_linearclamp_collision.md` covers the analogous `sampler_LinearClamp` case.

---

## Why "the kernel reads zero" — three failure modes ranked

1. **Keyword variant mismatch.** The compute shader was compiled with `_MAIN_LIGHT_SHADOWS_CASCADE` off; `TransformWorldToShadowCoord` falls through to `cascadeIndex = 0` and `_MainLightWorldToShadow[0]` (the first cascade only). Symptom: shadows are correct only inside cascade 0 region, hard pop at cascade boundary. Fix: `CoreUtils.SetKeyword(populateCS, "_MAIN_LIGHT_SHADOWS_CASCADE", true)` before dispatch when `mainLightShadowCascadesCount > 1`.
2. **Missing texture dep.** No `UseTexture(mainShadowsTexture, Read)` declared, so RG culls or reorders our pass before the shadow caster runs. Symptom: `_MainLightShadowmapTexture` reads as zero (cleared atlas) → `SampleCmpLevelZero` returns 1.0 → no shadow. Fix: declare the dep, as in step 4 above.
3. **Host-side mirroring instead of CB ordering.** Receiving pass mirrors `Shader.GetGlobalMatrix(_MainLightWorldToShadow)` host-side and pushes via `SetComputeMatrixParam`. Multi-camera graphs scramble this because `MainLightShadowCasterPass` runs once per camera and `Shader.SetGlobalMatrix` happens during execute, not record. Symptom: shadows snap between cameras / random misalignment. Fix: rely on the CommandBuffer-side `cmd.SetGlobalMatrixArray` URP already issues, do not mirror.

If the matrix arrays really do read zero on Vulkan compute despite a correct texture dep + correct keyword, the diagnosis is almost always (1) or (2). The CommandBuffer-side cascade globals reach Vulkan compute reliably — confirmed by the project's existing fog/cloud lighting (which works) using exactly this pattern.
