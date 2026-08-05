---
name: Fog material volumes — Bauer/Drobot z-bin canon (32-cap structural)
description: Canonical fog material volume structure is Drobot 2017 z-binning (Bauer 2019 RDR2 slide 44). The 32-volume cap is structural — single-uint tile bitmask. Drives the FogMaterialVolume cluster-grid rewrite.
type: project
originSessionId: 11a36976-71c3-49cf-80d6-21ddc4880efe
---
Bauer 2019 slide 44 explicitly: **"Up to 32 fog volumes stored in cluster grid · Z-Binning [Drobot17]"**. The 32 cap is the bit-width of one `uint` tile-bitmask word (Drobot Flat Bit Array, slide 15) intersected with a 1D Z-bin LUT (Drobot slide 29: `ZBIN[i] = (max << 16) | min`).

**Why:** Brute-force per-froxel iteration over fog volumes (the "before" picture in Drobot slides 8/16/18) costs `O(N · froxels)`; for our 1.38M-froxel medium tier that becomes the populate compute's dominant cost as `N` grows. RDR2 ships exactly this acceleration; our research canon (`feedback_research_canonical_anchor.md`) requires we follow it without "adapted" variants.

**How to apply:**
- Single unified `FogVolumeGpu[≤32]` StructuredBuffer (no per-blend-bucket buffers — blend mode encoded in `shapeBlendIntensity.y`, three accumulators run inside the inner loop, blended Add→Alpha→Particle at exit per Bauer slide 45).
- CPU: frustum-cull, sort by min-Z (camera distance), drop farthest beyond index 31 with `Debug.LogWarning`, build `uint[tileCount]` tile bitmask + `uint[zBinCount]` Z-bin LUT.
- GPU: `mask = tileMask & BitFieldMask(maxIdx-minIdx+1, minIdx)`; Drobot slide 17 entity-level scalarisation: `mergedMask = WaveReadFirstLane(WaveAllBitOr(mask)); while (mergedMask) { idx = firstbitlow(mergedMask); ... }`.
- Z-bin width follows the populate's quadratic slice→world-Z mapping (one bin per froxel Z slice — eliminates a quantisation step).

**Caveat:** The earlier research-md export only kept speaker notes and dropped the slide bullets, masking the 32-cap structural fact. The corrected `docs/research/bauer-2019-rdr2-atmospherics.md` slide 44 has the bullets back. Always cross-check that bullets + speaker notes are both present before reasoning from research markdown.

**Out of scope on the same change:** local-light z-binning (URP forward+ already covers in-scattering lights), Drobot rasteriser-based culling (overkill for ≤32 analytical SDFs), `WaveCompactValue` atomic-contention pruning (rasteriser-only).
