---
name: Cloud block modes need deterministic occlusion gate; CB rides on kernel diversity
description: Block4×4/Block8×8 leak cloud color onto closer opaques because composite has no cloud-front-vs-hi-depth test. CB modes accidentally survive via 2×2-trace-block kernel diversity. Any cloud-pipeline refactor must keep the gate.
type: feedback
originSessionId: ff56ef13-cabc-4754-be05-15fed2bc9344
---
In `Packages/is.zori.atmospherics/Runtime/VolumetricClouds/Shaders/ZoriVolumetricCloudsInternal.shader` Pass 1 (`FragComposite`), there is now a `#if defined(_CLOUD_FULLRES_TEMPORAL) || defined(_CLOUD_EIGHTHRES_TEMPORAL)`-gated test that suppresses the upsampled cloud when its front (`cloudDistLinear`) is unambiguously behind the full-res opaque (`hiRayDist * 1.10`).

**Why:** the composite's `sceneSkyMatch`/`cloudSkyMatch`/`depthW` gates only relate **tap** to **hi** opaque depth — never **cloud-front** to **hi** opaque depth. Trace-block aliasing (one trace ray covers 16–64 full-res pixels with one scene-depth pick) broadcasts cloud color into intermediate texels whose own scene-depth records foreground opaque, and nothing in the existing kernel rejects the inconsistent pair. Block trace blocks are 4×4 in intermediate space, so the composite kernel sits *inside* one trace block; Block4×4 specifically takes a point-sample fast path with no kernel at all. CB modes' trace blocks are 2×2 in intermediate space, so their 4-tap bilateral straddles trace-block boundaries the majority of the time — kernel diversity dilutes the polluted side. CB's correctness is statistical, not deterministic.

**How to apply:**
- Any future change to `UpsampleCloud` or `FragComposite` that touches the kernel/upsample path must preserve this gate (or replace it with an equivalent per-full-res-pixel cloud-front-vs-opaque test).
- The gate must compare **ray-distance to ray-distance** — `cloudFrontDist` is along-ray; convert hi via `hiLinearEye / dot(rd, -camFwd)`. Comparing eye-z to ray-distance directly false-fires at FOV edges.
- The gate must run **after** alpha-weighted upsample (so legitimate cloud-in-front taps still composite at full softness) and run **before** AP/fog transport (so suppressed cloud doesn't waste fog/AP work).
- If switching to a deterministic per-tap occlusion test inside `UpsampleCloud`, retain it across all bilateral fallback levels — the existing `wSum < 1e-5` fallback chain drops `cloudSkyMatch` then `sceneSkyMatch`, but **must not** drop the cloud-front test, otherwise the leak returns through the second fallback.
- Soft cloud-over-opaque composition (low cloud over distant terrain) is preserved automatically: the inequality `cloudFront > hi*1.10` is false by a wide margin for any genuine cloud-in-front case.
