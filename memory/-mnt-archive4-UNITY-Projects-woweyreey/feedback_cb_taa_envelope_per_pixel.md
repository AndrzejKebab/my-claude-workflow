---
name: CB+TAA cloud variance envelope must be trace-sourced at half-res stride (Checkerboard modes only)
description: Canon §7.1 — for Checkerboard temporal modes (4 sub-positions, sparse trace cache), the 3×3 clip-envelope must be trace-sourced at half-res stride. Block 4×4 / Block 8×8 modes (16 sub-positions, full-res or 2× upsample) have been validated to work with history-sourced moments — don't migrate them blindly.
type: feedback
originSessionId: 726c4158-973f-4d34-8c33-a1c331c299e5
---
**Scope:** This canon applies to **Checkerboard2x2 / Checkerboard8x8** temporal modes — the 4-position patterns where each trace cell is shared by many intermediate pixels and history is the dominant signal in any local neighbourhood. **Block4x4 / Block8x8** (16-position Bayer) tolerate history-sourced moments because the 16-frame coverage gives enough sub-pixel diversity that the envelope drifts less, and the user has confirmed Block modes ship with history-sourced clip without ghost regression (2026-05-07 review).

In the CB+TAA volumetric cloud pipeline, Pass 1's 3×3 variance-clip envelope is computed from the **current-frame trace buffer at half-res stride** — i.e. for each intermediate pixel, iterate `(dx,dy) ∈ [-1,1]²` over intermediate-resolution neighbours and sample the trace texel covering each neighbour's block (`traceCoord = nbIntCoord / ratio`). This is canon §7.1 (HZD 2015 / Nubis 2017 / HDRP 6000.x / UE `VolumetricRenderTarget.usf`).

**Why:** adjacent intermediate pixels inside a ratio×ratio block share most of their trace-neighbourhood texels but differ by the centre — so envelopes are per-pixel (no block-coherent clamp pump) while the values come from the raymarched fresh samples, not from self-referencing history. History-sourced 3×3 (previous rule) was introduced to paper over the block-coherent artefact seen with trace-res stride (one trace texel step between neighbours); canon's half-res stride on the trace buffer eliminates both problems at once.

**How to apply:**
- In FragReproject's 3×3 moments loop, iterate intermediate-pixel offsets and sample `_CloudsTraceLighting` via `clamp(nbIntCoord / _CloudsIntermediateRatio, 0, traceMax)`. Never sample `_CloudsHistoryLighting` in this loop.
- Use straight AABB min/max (canon §7.2) — no stddev, no k-factor, no minimum-variance guard. The half-res stride naturally keeps the envelope lively on non-owner frames because neighbours are live trace values.
- Neighbour admission: canon §7.3 — exclude when `abs(nbCloudDepth - freshCloudDepth) / max(freshCloudDepth, 1) > 0.30`. No dual-bucket sky/geo gate.
- Clamp history via line-segment clip to the AABB (`ClipCloudsToRegion`, Karis 2014) — half history+fresh line, not box clip.
- Historic "trace-res stride" block artefact is gone under half-res stride; symptom to watch for now is the opposite — envelope too permissive, which manifests as ghosting rather than blocks.

Supersedes the pre-2026-04-24 rule that envelopes had to be history-sourced.
