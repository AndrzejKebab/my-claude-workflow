# Samplers in compute kernels

Samplers in URP/Core HLSL come in two kinds:

1. **Inline-name-encoded samplers** declared in shared headers, synthesised by Unity from the name pattern. No C# bind. Always available once the header is included.
2. **Real samplers** declared in HLSL and bound from C# via `cmd.SetComputeTextureParam` / `material.SetTexture` (the texture's import settings drive the sampler) or via explicit `cmd.SetGlobalTexture` (with the sampler implied by the texture's import settings).

For most URP/Core HLSL the first kind dominates and is the path you should use.

---

## URP / Core inline samplers

### `Packages/.../com.unity.render-pipelines.core/ShaderLibrary/GlobalSamplers.hlsl`

Full file (`GlobalSamplers.hlsl:1-14`):
```hlsl
#ifndef UNITY_CORE_SAMPLERS_INCLUDED
#define UNITY_CORE_SAMPLERS_INCLUDED

// Common inline samplers.
// Separated into its own file for robust including from any other file.
// Helps with sharing samplers between intermediate and/or procedural textures (D3D11 has a active sampler limit of 16).
SAMPLER(sampler_PointClamp);
SAMPLER(sampler_LinearClamp);
SAMPLER(sampler_TrilinearClamp);
SAMPLER(sampler_PointRepeat);
SAMPLER(sampler_LinearRepeat);
SAMPLER(sampler_TrilinearRepeat);

#endif //UNITY_CORE_SAMPLERS_INCLUDED
```

These six are inline-encoded: Unity's shader compiler reads the name (`sampler` + filter + wrap), synthesises the corresponding `SamplerState`, and binds it without any C# call. The pattern is documented in Unity's shader sampler docs and held stable since URP 7.

Pulling from project memory `feedback_urp_sampler_linearclamp_collision.md`: redeclaring `sampler_LinearClamp` in a package header collides with URP's `GlobalSamplers.hlsl`. The collision symptom is `"Kernel at index (0) is invalid"` on Vulkan. Don't redeclare any of the six.

### `Shadows.hlsl:65`

```hlsl
SAMPLER_CMP(sampler_LinearClampCompare);
```

`SAMPLER_CMP` expands to `SamplerComparisonState samplerName` on every API target (verified in `Vulkan.hlsl:71`, `D3D11.hlsl:80`, `Metal.hlsl:71`, `Switch.hlsl:71`, `Switch2.hlsl:71`, `WebGPU.hlsl:69`, `GLCore.hlsl:78`). The name pattern `Linear` + `Clamp` + `Compare` synthesises a comparison sampler with linear filtering, clamp address, and `D3D12_FILTER_COMPARISON_MIN_MAG_LINEAR_MIP_POINT` semantics (or the Vulkan equivalent). No C# bind needed.

`sampler_LinearClampCompare` is **not** in `GlobalSamplers.hlsl` — it lives in `Shadows.hlsl` because it's tied to the shadow texture path. If you don't include `Shadows.hlsl` (transitively via `Lighting.hlsl`) you don't have it.

### `Packages/.../com.unity.render-pipelines.universal/ShaderLibrary/Shadows.deprecated.hlsl:7-8`

Aliases for the legacy per-texture-name sampler binding:
```hlsl
#define sampler_MainLightShadowmapTexture sampler_LinearClampCompare
#define sampler_AdditionalLightsShadowmapTexture sampler_LinearClampCompare
```

These re-export the same comparison sampler under the `sampler_<TextureName>` convention. The deprecated header exists because some shaders still reference `sampler_MainLightShadowmapTexture` — for new code prefer `sampler_LinearClampCompare`.

---

## How comparison samplers wire up

`SAMPLE_TEXTURE2D_SHADOW` macro definitions, identical across every API target:

| Platform | Definition (file:line) |
| --- | --- |
| D3D11 (D3D12 inherits) | `D3D11.hlsl:139` — `textureName.SampleCmpLevelZero(samplerName, (coord3).xy, (coord3).z)` |
| Vulkan | `Vulkan.hlsl:131` — `textureName.SampleCmpLevelZero(samplerName, (coord3).xy, (coord3).z)` |
| Metal | `Metal.hlsl:130` — `textureName.SampleCmpLevelZero(samplerName, (coord3).xy, (coord3).z)` |
| GLCore | `GLCore.hlsl:145` |
| GLES3 | `GLES3.hlsl:166` |
| WebGPU | `WebGPU.hlsl:128` |
| Switch / Switch2 | `Switch.hlsl:130` / `Switch2.hlsl:130` |

Every target lowers to `SampleCmpLevelZero(sampler, uv, refZ)`. This is the explicit-LOD comparison sample — LOD is fixed at 0 (no derivatives needed), making it valid in compute pipelines on every platform. The HLSL signature:
```hlsl
float Texture2D::SampleCmpLevelZero(SamplerComparisonState s, float2 location, float compareValue);
```
returns `1.0` if `location.depth > compareValue` (lit) else `0.0` (shadowed); with linear filtering it returns the bilinear-blended PCF result of 4 taps at LOD 0.

The "compare" semantic is what lets the GPU's hardware PCF unit do percentage-closer filtering in one instruction.

---

## Rules for sampling from custom compute

### Always use the macros, never `Texture2D.Sample` directly

For platform-portable code use `SAMPLE_TEXTURE2D` / `SAMPLE_TEXTURE2D_LOD` / `SAMPLE_TEXTURE2D_SHADOW` etc. defined in `Packages/.../com.unity.render-pipelines.core/ShaderLibrary/API/<Platform>.hlsl`. The macros indirect through `PLATFORM_*` so a single macro produces the right intrinsic per target.

### Implicit-LOD vs explicit-LOD in compute

Compute pipelines have no rasterizer-derived screen-space derivatives. Implicit-LOD reads (`SAMPLE_TEXTURE2D` → `texture.Sample`) are invalid in compute on Vulkan (validation error `VUID-RuntimeSpirv-ImplicitLod`); on D3D12 they typically return LOD 0 in driver-undefined ways.

Always use explicit-LOD variants in compute:
- `SAMPLE_TEXTURE2D_LOD(tex, sampler, uv, lod)` — `texture.SampleLevel(sampler, uv, lod)`.
- `SAMPLE_TEXTURE2D_SHADOW(tex, sampler, coord3)` — `texture.SampleCmpLevelZero(sampler, uv, refZ)`. Already explicit-LOD.
- `LOAD_TEXTURE2D(tex, ipos)` — `texture.Load(int3(ipos, 0))`. No filtering, no sampler needed; closest analogue to a UAV `[]` read.

### When to use `SAMPLER` (graphics) vs separate compute-safe variant

Project memory `feedback_compute_shadow_sampling_canon.md` is the canonical guidance: when a URP graphics-side helper (e.g. `MainLightRealtimeShadow`) contains an implicit-LOD path, write your own compute-safe variant. Don't try to `#define`-hack URP into compute mode — too brittle across URP version bumps.

The project's pattern for cascade shadows is `ZoriComputeSampleMainLightShadow` in `Packages/is.zori.atmospherics/Runtime/VolumetricFog/Shaders/ZoriVolumetricFogPopulate.compute:66-91`. Mirror this when you need other URP helpers from compute.

### Don't redeclare the URP/Core inline samplers

Six globals from `GlobalSamplers.hlsl` plus `sampler_LinearClampCompare` from `Shadows.hlsl`. If you include URP shader headers (you almost always do), they are already declared. Redeclaring causes a sampler-name collision and Vulkan rejects the kernel with a generic "Kernel at index (0) is invalid" — the diagnostic is misleading; the real cause is sampler collision.

If your compute file needs a sampler not in this set (e.g. anisotropic, wrap+linear+clamp combinations not pre-declared), use `SAMPLER(my_unique_name)` and ensure the name doesn't pattern-match anything in URP/Core.

---

## Sampler index quick reference for compute

| Need | Use | Source |
| --- | --- | --- |
| Linear filter, clamp wrap | `sampler_LinearClamp` | `GlobalSamplers.hlsl:8` |
| Point filter, clamp wrap | `sampler_PointClamp` | `GlobalSamplers.hlsl:7` |
| Trilinear (mipmapped), clamp wrap | `sampler_TrilinearClamp` | `GlobalSamplers.hlsl:9` |
| Linear filter, repeat wrap | `sampler_LinearRepeat` | `GlobalSamplers.hlsl:11` |
| Point filter, repeat wrap | `sampler_PointRepeat` | `GlobalSamplers.hlsl:10` |
| Trilinear, repeat wrap | `sampler_TrilinearRepeat` | `GlobalSamplers.hlsl:12` |
| Comparison sample (PCF shadow) | `sampler_LinearClampCompare` | `Shadows.hlsl:65` |

Include `Packages/com.unity.render-pipelines.core/ShaderLibrary/GlobalSamplers.hlsl` for the first six (`Common.hlsl` already pulls it in transitively via `Macros.hlsl`).

Include `Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl` (which transitively includes `Shadows.hlsl`) for the comparison sampler.
