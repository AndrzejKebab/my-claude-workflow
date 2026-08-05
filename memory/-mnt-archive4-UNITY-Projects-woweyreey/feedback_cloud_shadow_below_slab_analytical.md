---
name: Cloud shadow below-slab uses bake-integrated optical depth, not analytical
description: Cloud SM is RG16F at fixed 768²/6 mips; G stores integrated optical depth -log(transmittance), receiver applies Beer-Lambert exp(-G) for below-slab attenuation
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
Cloud shadowmap is **R16G16_SFloat fixed 768²/6 mips** (Bauer 2019 RDR2 canonical resolution + tier-flat baseline). Two channels:

- **R = ESM depth** — transmittance-weighted distance from slab top to effective occluder (Annen08, Bauer slide 35). Drives sharp in-slab shadow edges via `saturate(exp(_CloudShadow_EsmConstant * (esmDepth - clampedReceiver) * rcpSlab))`.
- **G = integrated optical depth** = `-log(max(transmittance_final, 1e-6))` — total Beer-Lambert exponent through the column, accumulated by the bake march.

Below-slab attenuation: `belowSlabT = exp(-opticalDepth)`. Smooth crossover from in-slab ESM to below-slab Beer-Lambert at the slab floor via `smoothstep(0.9, 1.0, receiverDepth/maxSlabDepth)`.

**Why:** First Phase 1 attempt tried to drop G entirely and derive below-slab attenuation analytically via `_CloudShadow_GradientIntegral` (CloudHeightGradient closed-form integral × ESM depth × _CloudShadow_OpticalScale). That **inverted the polarity** — clear sky read as fully shadowed because ESM depth is a *position* (large under clear sky), not an *optical-depth measurement* (zero under clear sky). The bake already integrates the column extinction; the only correct encoding stores that integral directly.

The pre-Phase-1 G-channel encoded slab-exit transmittance (`exp(-tau)`); the post-fix G encodes the exponent itself (`tau`). Same memory footprint, different content — mathematically equivalent for the receiver since `exp(-tau)` is the Beer-Lambert step at sample time. Storing `tau` is more numerically friendly under blur (linear blend on the exponent has the same approximation level as linear blend on the transmittance, but stays bounded under heavy cloud).

**How to apply:**
- Format **must be RG16F**, never R16F. Allocations in `CloudShadowSource.AllocFlat()` and `AllocMipped()`.
- Receiver-side: `belowSlabT = exp(-opticalDepth)` where `opticalDepth = stored.g`. Never re-derive from ESM depth.
- Bake clamps `transmittance` floor to `1e-6` before `-log` to avoid INF; early-out at `transmittance < 0.001` caps τ near 6.9 (well within R16F).
- Resolution + mip count fixed at 768/6 across all tiers (no `[QualityLocked]` on these — both removed from `CloudShadowFalloff` and `DistantShadowQualitySpec`).
- Other cloud shadow knobs (march steps, blur radius, temporal alpha, ESM constant, mip LOD bias) stay tier-driven.
- **Per-consumer optical boost:** `_CloudShadow_OpticalBoost` global defaults to 1.0 each frame (graphics passes use canonical). Fog populate + distant-fog raymarch override per-dispatch from `CloudShadowFalloff.opticalBoostFog` (runtime-clamped `max(1, ...)`). Receiver: `belowSlabT = exp(-opticalDepth * _CloudShadow_OpticalBoost)` — only multiplies the below-slab Beer-Lambert path; ESM in-slab compare untouched. Lets fog amplify cloud shadows independently of the ground/SSS calibration. Typical `opticalBoostFog = 200` when ground `opticalScale = 6e-06`. ESM in-slab compare sharpness stays owned by `_CloudShadow_EsmConstant`.
- `_CloudShadow_GradientIntegral` global is currently orphaned (CPU still publishes it; no consumer reads it). Cleanup deferred — when ready, remove `ComputeGradientIntegral` helper in `CloudShadowSource`, the `_GradientIntegral` PropID + `SetGlobalFloat`/`SetComputeFloatParam` publishes in `CloudShadowSource.cs`, `PhysicalSkyPrecomputation.cs`, `DistantFogPass.cs`, `VolumetricFogPass.cs`, and the HLSL declaration in `DistantShadowCommon.hlsl`.

**Upgrade path (deferred — stratified clouds only):** This encoding is effectively a **1-node AVSM** (Salvi 2010, `docs/research/salvi-2010-adaptive-volumetric-shadow-maps.md`) — one (depth, transmittance) sample per XZ texel, sufficient when the cloud raymarch produces a single continuous slab and all receivers are below it. If production ever wants stratified geometry (cumulus base + clear gap + cirrus tops, or cloud-on-cloud self-shadowing across separate layers), AVSM-4 to AVSM-8 stores the full piecewise-linear transmittance curve with constant memory: budget scales as `nodes × (resolution²) × bytes_per_node` so AVSM-4 ≈ 6 MiB and AVSM-8 ≈ 12 MiB at 768² (vs ~3 MiB today). Consumers walk the curve to evaluate `T(z)` at any receiver depth. Bake side gains a streaming insert+compress loop (Salvi §3.2 — area-under-curve simplification, removes the node-pair with smallest L1 deviation). Defer until layered clouds are an actual goal — current single-slab does not benefit.
