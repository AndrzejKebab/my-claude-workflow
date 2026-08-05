---
name: Fog volume components are split per Bauer's two-volume axes
description: FogMaterialVolume (Bauer canonical material contributor) + FogMap (texture-shape with painting tooling) — two separate MonoBehaviours, distinct concerns. FogShadowVolume was deleted 2026-05-04 — Bauer slide 43 shadow volume is unconditional cascade+cloudSM+terrainSM, no per-volume override exists in the canonical model.
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
After 2026-05-04 cleanup, fog authoring is split across two MonoBehaviours that map to Bauer 2019 RDR2's material-volume data model (slides 22-23, 20):

- **`FogMaterialVolume`** (renamed from `FogVolume` — `[MovedFrom]` migration) — Bauer's canonical artist-placed fog contributor (slide 22-23, 45). Sphere/Box shape, Additive/Alpha/Particle blend modes, writes to **Material Volume A+B** only (σ_s/σ_t + phase/emissive/ambient/droplet). Material Volume is composed in blend order Additive→Alpha→Particle on top of procedural baseline.

- **`FogMap`** — Bauer slide 20 vertical-profile box with Texture2D RGB encoding (R=startAlt, G=falloffDistance, B=peak σ_t). Stays separate from FogMaterialVolume because painting tooling will live here. Material contributor — same Material A+B target as FogMaterialVolume, just sourced from a per-XZ texture profile.

**Shadow volume is unconditional, not per-volume.** Bauer slide 43 Shadow Volume is a global per-froxel R16F composited from cascade + cloud SM + terrain SM. The fog populate compute (`ZoriVolumetricFogPopulate.compute::ComputeShadowVisibility`) samples all three sources unconditionally for every froxel — there is no per-volume shadow override in the canonical model and the project no longer ships one. The 2026-05-03 `FogShadowVolume` MonoBehaviour + `FogShadowVolumeGpu` wire format + `_ShadowVolumes` StructuredBuffer + `ApplyShadowVolumeOverrides()` HLSL helper were all deleted on 2026-05-04 once the unconditional cascade tap proved sufficient.

**Key design invariants:**
- Components are **orthogonal axes**, NOT enum values on a shared component. A material BlendMode (Additive/Alpha/Particle) is for material composition. Don't conflate.
- `FogVolumeMaterial` ScriptableObject and `FogVolumeGpu` GPU struct stayed named (shared infrastructure, not coupled to one component class).
- A future `FogScatteredLightVolume` (writes directly to Scattered Light Volume bypassing material × shadow × phase) is theoretically possible per the same axis logic but **deferred until concrete art use case demands it** — has stylized non-physical implications.

**Per-dispatch cascade keyword on populate:** `_MAIN_LIGHT_SHADOWS_CASCADE` is required for the unconditional cascade tap inside `ComputeShadowVisibility` (Bauer slide 43 — the third shadow source alongside cloud SM and HF SM). Keyword stays on populate kernel only — does not propagate to Integrate or other kernels.
