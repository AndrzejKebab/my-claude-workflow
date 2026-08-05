---
name: Terrain shadowmap is camera-anchored, not stretched-across-world
description: Bauer's 128² RG16F terrain SM covers a camera-anchored shadowbox extent; tier range 128–512 (Medium=256). G stores raw ray length (meters); softness derives consumer-side
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
The heightfield/terrain shadowmap (Bauer 2019 RDR2 slide 34) is **camera-anchored over a configurable shadowbox extent**, not stretched across the entire world. At our 100km world, a fixed-128² stretched globally would yield ~781m/texel — useless. Camera-anchored 128² over a typical 1500m shadowbox extent yields ~12m/texel, which is Bauer's intended fidelity.

**Why:** Bauer's slide doesn't explicitly say camera-anchored, but the only sane interpretation given his ~70km RDR2 playable area + the soft-shadow ray-length channel implies a bounded extent. Project test: HeightfieldTerrainScene visuals at 1536² (pre-rework) ≈ visuals at 256² (post-rework Medium tier) once raw-ray-length softening is in place — the resolution drop is hidden by softness widening.

**How to apply:**
- HF SM is **RG16F**, R = light-space depth of first occluder (1.0 = miss = lit), **G = raw ray length in world meters** (not pre-baked softness — Bauer canon).
- Softness derives consumer-side via `HeightfieldShadowSoftness(rayLen, _HFPenumbraScale)` in `DistantShadowCommon.hlsl`.
- `_HFPenumbraScale` is published as a `Shader.SetGlobalFloat` per frame from `HeightfieldShadowSettings.penumbraScale`. Compute consumers ALSO need `cmd.SetComputeFloatParam(_HFPenumbraScale, ...)` per `feedback_compute_needs_explicit_params.md`. Helper also reads `_DistantShadowDepthHalf` — same compute-binding requirement.
- Resolution tier range is **128 (Potato) / 192 (Low) / 256 (Medium) / 384 (High) / 512 (Cinematic)**. NOT 128–2048 — the old upper end was a misalignment from before Bauer canon was applied.
- Shadowbox extent (`DistantShadowSettings.extent`) stays artist/tier configurable independently of resolution.
- Fog populate samples HF at single midpoint per froxel (Bauer slide 43 — view-independent visibility), NOT a 4-tap slab march.
