---
name: Volumetric fog — shared AP LUT substrate
description: Planned volumetric fog in is.zori.atmospherics will sample the same Hillaire 2020 Aerial Perspective 3D LUT that clouds sample — build fog on top of that LUT, not as a standalone pass
type: project
originSessionId: d853b88c-2779-4a8d-af3e-5a4011ae9a66
---
Planned volumetric fog lives in `Packages/is.zori.atmospherics` alongside clouds and PBSky. The agreed direction (2026-04-13) is Hillaire 2020: a shared **Aerial Perspective 3D LUT** (32×32×32 froxel volume, camera-frustum-aligned, `R16G16B16A16_SFloat`, stores `(inScatter.rgb, transmittance.a)`) baked per frame by `PhysicalSkyPrecomputation`, published as `_AerialPerspectiveLUT` global. Clouds sample it in their composite at `cloudDist`; fog will sample it at scene depth (or per-froxel for participating media).

**Why:** HDRP and UE both converge on this technique. It's the physically correct way to get sky/opaque visual consistency for clouds, and it's the shared substrate fog needs anyway — building the LUT for clouds unblocks fog entirely. Composite-side alpha fudges were rejected in favor of upstream light transport.

**How to apply:** Do not design fog as an independent raymarch with its own atmosphere integration. Fog = "read the AP LUT, apply `source * ap.a + ap.rgb` to opaque scene radiance," plus any local density modulation. The integrator helper to reuse is `IntegrateAtmosphere(O, V, tStart, tEnd, ...)` — planned to live in `Resources/PhysicallyBasedSkyEvaluation.hlsl` (extracted from the current `EvaluateAtmosphericColor` in `ApiHausPhysicalSkyPrecomputation.shader` Pass 0). If reviewing fog proposals, reject any that reimplement atmospheric scattering or skip the shared LUT.
