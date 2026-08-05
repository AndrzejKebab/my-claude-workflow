---
name: VolumetricFogCommon globals must ALL bind via SetComputeVectorParam on every compute consumer
description: Plain file-scope HLSL globals in VolumetricFogCommon.hlsl read as zero on Vulkan compute via SetGlobal* — every populate/integrate/raymarch kernel needs explicit per-dispatch binding for every uniform it reads
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
`Packages/is.zori.atmospherics/Runtime/VolumetricFog/ShaderLibrary/VolumetricFogCommon.hlsl` declares all volumetric fog uniforms as **plain file-scope HLSL globals** (no named CBUFFER wrapper). Per project canon `feedback_compute_needs_explicit_params.md`, Vulkan compute reads these as **zero** unless explicitly bound via `SetComputeVectorParam` / `SetComputeFloatParam` per-dispatch.

**This was the root cause of an 11-stage debugging session** (2026-05-03) where every shadow-related fix produced zero visible effect in fog. `_VolumetricFog_AlbedoTint` was pushed via `Shader.SetGlobalVector` for the apply raster pass but NEVER bound on the populate compute kernel. Result: populate computed `albedoRgb = 0`, wrote `Material A.rgb = 0`, integrate's `directIn = directRadianceLocal × distantShadow × 0 = 0`. Every in-scatter contribution multiplied by zero. Transmittance worked (alpha channel), so fog still attenuated background — but had no in-scattering RGB. Looked like normal fog because background bled through; cloud shadows / cascade shadows / god rays / FogShadowVolume / opticalBoostFog all had no effect because they modulated a zero.

**Symptom signature when this bug class is present:**
- Fog visible, attenuates background correctly.
- ANY shadow-modulating feature (cloud, terrain, FogShadowVolume, god rays, opticalBoostFog) produces zero visible response.
- Stage-style diagnostic that writes a known gradient/value to ShadowVolume produces no visible variation in fog.
- Forcing IntegratedVolume to a constant color directly (bypassing math) DOES show on screen — proves apply pass is fine.

**How to apply going forward:**
- For every compute kernel host (`VolumetricFogPass.cs`, `DistantFogPass.cs`, plus any future kernel), audit which `_VolumetricFog_*` uniforms each `*.compute` reads. Cross-check against the `SetComputeVectorParam` / `SetComputeFloatParam` calls in the dispatch closure. Missing bindings = silent Vulkan-zero bug.
- Same applies to `_PhysicalSky_*`, `_CloudShadow_*`, `_DistantShadow*`, `_HF*` globals — same pattern, same trap. Already audited and bound (2026-05-03).
- `_VolumetricFog_MainLightShadowEnabled` flagged at line 67 of VolumetricFogCommon.hlsl as audit followup — verify integrate + DistantFogRaymarch bind it explicitly.

**Cleaner long-term cleanup (deferred):** wrap all `_VolumetricFog_*` globals in a named CBUFFER like `ShaderVariablesPhysicalSky.hlsl` does. Named CBUFFERs read SetGlobal* correctly on Vulkan compute. Eliminates this entire class of bug. Not done yet because it's a wider refactor and per-dispatch binding is the project canonical pattern. But worth doing if this trap bites again.

**Diagnostic recipe** for "fog feature does nothing" symptoms in the future:
1. Force `IntegratedVolume = (10, 0, 0, 0)` constant in integrate's per-slab write — confirms apply pass reaches screen.
2. Write a known gradient `id.x / res.x` to ShadowVolume in populate — confirms write/read indices match.
3. If 1 works but 2 produces no visible variation, check `Material A.rgb` is non-zero — likely a populate-side AlbedoTint or sigma_s sourcing bug.
4. Audit every `_VolumetricFog_*` uniform read by populate against `SetComputeVectorParam` calls in the dispatch closure.
