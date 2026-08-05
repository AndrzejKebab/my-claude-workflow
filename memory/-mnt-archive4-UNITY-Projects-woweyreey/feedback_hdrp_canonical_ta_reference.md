---
name: HDRP as canonical TA reference
description: Use HDRP 17 as the primary frame of reference for cloud temporal accumulation implementation
type: feedback
originSessionId: 7272181c-1552-4d43-a58e-5a7d6b5d82c3
---
HDRP 17 is the canonical reference for the cloud TA pipeline. Key files: `VolumetricCloudsTrace.compute`, `VolumetricClouds.compute` (reproject), `VolumetricCloudsDenoising.hlsl` (helpers). Always cross-check against HDRP before proposing approaches.

**Why:** User explicitly requested a solid frame of reference anchored to a shipping engine. HDRP 17 is Unity-native and closest to our URP implementation.

**How to apply:** When implementing or debugging cloud TA (checkerboard scheduling, reprojection, neighbourhood clamp, upsample), verify the approach matches HDRP 17's pattern from `docs/clouds-pre-nc23-lineage.md`. Cite specific HDRP functions/line references from the lineage doc.
