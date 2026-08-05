---
name: PhysicalSky uniforms need SetComputeVectorParam in fog compute kernels
description: _PhysicalSky_SunColor / SunDirection / MoonColor / MoonDirection read as zero on Vulkan compute via SetGlobalVector — must bind per-dispatch via SetComputeVectorParam on every fog/cloud/AP compute kernel that reads them
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
PhysicalSky publishes its sun/moon state via `Shader.SetGlobalVector` (e.g. `_PhysicalSky_SunColor`, `_PhysicalSky_SunDirection`, `_PhysicalSky_MoonColor`, `_PhysicalSky_MoonDirection`). This works for graphics passes (SSS, opaque compose) but **Vulkan compute kernels read SetGlobal* uniforms as zero** — same trap documented in `feedback_compute_needs_explicit_params.md`.

**Why this matters specifically for fog cloud shadows:** if the fog Integrate compute reads `_PhysicalSky_SunColor` as (0,0,0), then `sunRadiance = 0 × stuff = 0`, `directRadianceLocal = 0`, `directIn = directRadianceLocal × distantShadow × sigmaSdt = 0`. Cloud shadow has nothing to attenuate. The Shadow Volume can have a perfect cloud-shaped gradient and it produces zero visible effect because direct lighting itself is zero. Fog luminance comes purely from `ambientIn + emissiveIn + rainbowIn` — none of which depend on `distantShadow`. Symptom: cloud shadow on fog completely invisible while ground SSS works perfectly. Hours of misdirected investigation possible without this rule.

**How to apply:**
- Any compute kernel that reads a `_PhysicalSky_*` uniform needs explicit per-dispatch `cmd.SetComputeVectorParam(cs, ID_PhysicalSky_*, value)`. Grab via `Shader.GetGlobalVector(...)` at record time, store in the pass data struct, bind in the dispatch closure.
- Same for `SetComputeFloatParam` if the sky publishes scalars (e.g. `_PhysicalSky_SunVisibility`).
- All four compute consumers of `_PhysicalSky_*` in this package are now bound per-dispatch (audited 2026-05-03):
  - `ZoriVolumetricFogIntegrate.compute` — Sun + Moon Direction + Color, bound in `VolumetricFogPass.cs` Integrate dispatch.
  - `ZoriDistantFogRaymarch.compute` — Sun Direction + Color, bound in `DistantFogPass.cs`.
  - `ZoriCloudSkyViewLUT.compute` — Sun Direction + Color, bound in `VolumetricFogPass.cs` CSV LUT bake closure (after `CloudFogCouplingUniforms.ApplyCloudLightingFromMaterialToCompute`).
  - `ZoriAerialPerspectiveLUT.compute` — Sun Direction + Color, bound in `PhysicalSkyPrecomputation.cs` AP dispatch.
- HLSL files reading `_PhysicalSky_*` from raster passes (`PhysicallyBasedSkyEvaluation.hlsl`, `CloudsAmbientLUTCommon.hlsl`, `Clouds.hlsl`) are FINE — graphics passes read SetGlobalVector correctly. Only compute consumers need per-dispatch bindings.
- General rule: when adding ANY new compute consumer of `_PhysicalSky_*`, never rely on the global; always bind per-dispatch via `SetComputeVectorParam`. Symptoms of missing this binding range from invisible cloud shadows on fog (zero direct lighting) to camera-locked pixelated artifacts (CSV LUT sampling a paraboloid with sun direction = (0,0,0)).
