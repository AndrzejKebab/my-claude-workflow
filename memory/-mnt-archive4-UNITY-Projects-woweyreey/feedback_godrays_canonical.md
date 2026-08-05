---
name: God rays modulate ambient/sky scattering, not direct lighting
description: Bauer slide 62 god rays accumulate transmittance-weighted shadow along ray, modulate AMBIENT inscatter only — direct stays per-step shadowed to avoid double-attenuation
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
Bauer 2019 RDR2 slide 62 god rays / light shafts implemented in this project's volumetric fog (both Integrate slice march and DistantFogRaymarch). The algorithm is intentionally non-physical but visually compelling — Bauer himself notes "this is not physically correct but gives plausible results for very little added cost."

**Algorithm:**
1. During slice/raymarch, accumulate `shadowedArea += (1 - visibility) * sampleArea * accumT` and `totalArea += sampleArea * accumT` per step.
2. After ray terminates, `shadowedFraction = shadowedArea / totalArea`.
3. Modulate ONLY the ambient/sky scattering term: `ambientFinal *= saturate(1 - shadowedFraction * intensity)`.

**Critical invariant — direct vs ambient streams must be split.** Direct lighting (`directIn = directRadianceLocal × distantShadow × sigmaSdt`) is ALREADY per-step shadowed. Applying god-ray modulation to it would be double-attenuation. Bauer's wording is specifically "modulate the sky scattering term" — that's ambient/sky only.

**Implementation in this project:**
- `ZoriVolumetricFogIntegrate.compute` Z-loop tracks `accumInScatterDirect` and `accumInScatterAmbient` separately (Hillaire `(1-Tseg)/tau` factored as `hillaire`, `SintDirect = directIn + emissiveIn + rainbowIn`, `SintAmbient = ambientIn`). Per-slab modulation written to volume so hardware trilinear Z-lerp samples right value at any sub-slab depth.
- `ZoriDistantFogRaymarch.compute` similar — two parallel `IntegrateOverSegment` calls, post-loop modulation on ambient only.
- Knob: `VolumetricFogSettings.godRaysIntensity` (Range 0..4, default 0 → off). 1.0 = canonical Bauer, 2-4 = dramatic.
- Bound via `_VolumetricFog_GodRaysIntensity` global on Integrate + DistantFogRaymarch via `SetComputeFloatParam` (Vulkan compute trap).

**Math sanity at intensity=0:** `godRayMod = saturate(1 - 0) = 1`, ambient unattenuated, split-stream sum mathematically identical to pre-godrays single-stream accumulator. Existing assets with default `godRaysIntensity = 0` see zero behavior change.

**Where it shows strongest:** camera looking through cascade-shadowed regions toward lit horizon; cloud-shadow-edges on terrain; forest canopy cracks. Subtle when looking straight up or in open shadow-free scenes.

**Visibility source reused:** `distantShadow` per froxel (already composed from cloud SM + HF SM + FogShadowVolume override). No new shadowmap taps. Cost is two extra fp accumulators per slice.
