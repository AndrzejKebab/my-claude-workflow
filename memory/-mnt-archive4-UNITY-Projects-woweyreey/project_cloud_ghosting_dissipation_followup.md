---
name: Block-mode cloud ghosting dissipation — Pass-1 write-gate landed (speculative)
description: 2026-05-07 — Pass-1 write-gate in FragReproject mirrors the composite-time occlusion gate. Reasoned-not-observed fix; user accepted because non-destructive. Safe to revert if it never earns its complexity in practice.
type: project
originSessionId: dc8e96a9-c690-442c-a9ff-00c6521a3e79
---
**Speculative — landed but not visually confirmed in practice.** User accepted it as a non-destructive precaution against a reasoned-about sub-frame ghost-flicker mechanism, not because the artefact was reproduced first. If future review finds no perceptible benefit, revert is safe — composite gate at L695 is the load-bearing protection.

**Resolution (2026-05-07):** Pass-1 write-gate landed in `ZoriVolumetricCloudsInternal.shader:FragReproject` (after debug-capture defaults, before `if (historyValid)`). Mirrors the composite-time occlusion gate (`FragComposite` L695-724): when `!cloudIsAtFar && !currSky && anchorDist > currSceneRayDist * 1.10`, returns `lighting=0`, `status=float4(0, currentSceneDeviceDepth, 0, 0)` early. Same `#if _CLOUD_FULLRES_TEMPORAL || _CLOUD_EIGHTHRES_TEMPORAL` scope as the composite gate.

**Why this works:** the composite gate suppressed *display* of leaked cloud on opaque-front pixels but Pass 1 still wrote the leak into `_CloudsHistoryLighting`. Sub-pixel scene-depth jitter near silhouettes flipped the 1.10 ratio frame-to-frame; on frames the composite gate didn't fire, the upsampled history flashed onto the opaque. Stopping the write at Pass 1 means there's no history to flash through.

**Why no noise reintroduction:** unlike the abandoned sun-trust system that collapsed `wHist` globally and wrote single-frame trace into history, this is per-pixel-geometry-selective and writes zero (not noisy fresh trace). Visible image on gated pixels is unchanged from today (composite gate already showed zero).

**Why no cloud-outline hardening over opaques:** gate fires only when cloud is *behind* opaque. Cloud-vs-sky and cloud-in-front-of-distant-terrain skip the gate. Boundary tracks the geometry silhouette, which was the cloud edge anyway.

**Block8×8 caveat:** intermediate runs at quarter-res; one scene-depth sample summarizes 4 composite pixels. Up to 4 px cloud erosion at silhouettes possible; bounded, static, far less objectionable than the ghost flash it replaced.

**CB modes intentionally excluded** by `#if BLOCK` — their composite kernel reaches a 2×2 trace neighbourhood with `BilateralCloudFallback` biasing away from sky-gap traces; Block modes have no spatial fallback diversity.

**HDRP-canon ghosting set is independent and unchanged.** Variance clip, motion-scaled k, motion-scaled wHist, soft cloud-depth rejection, edge fade all still apply on non-gated (visible-cloud) pixels in all four temporal modes.

See `docs/clouds-ta-problematic.md` "Block-mode Pass-1 write-gate" section for details.
