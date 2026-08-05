---
name: Cloud disocclusion band — hemi-oct cloudmap fallback
description: Referenced-solution for the open cloud-TA disocclusion band problem — slow-updated hemi-octahedron cloudmap texture filled on history rejection for sky pixels
type: project
originSessionId: 9b2671d0-2f30-4f90-913a-a3c7be82d612
---
The cloud TA disocclusion band (documented in `docs/clouds-ta-problematic.md`) has a referenced solution: **a slow-updated hemi-octahedron cloudmap sampled on history rejection for pure-sky pixels.**

Source: WickedEngine `volumetricCloud_renderCS_capture.hlsl` + `volumetricCloud_reprojectCS.hlsl:23–30`. A ~64² hemi-oct texture is refreshed on a slow temporal cadence (every N frames) by a dedicated capture pass that runs the same cloud shader against a hemispherical projection. On disocclusion in the reproject pass, sky-facing pixels (opaque depth == far AND V.y > 0) sample this cloudmap instead of leaving a history hole or showing a raw trace-res block. Analogous to Nubis's cubemap fallback strategy.

**Why:** We've discussed the disocclusion band on fast camera rotation as an unsolved problem. WE ships a concrete answer at trivial cost (small second RT, periodic capture dispatch).

**How to apply:** When/if we take another pass on cloud TA disocclusion handling, prototype this before attempting alternatives — small surface area, high evidence of viability (shipping in WE master). Full cross-engine context in `docs/research/cbr-ta-upsampling-cross-engine.md` §5 and `docs/research/wickedengine-volumetrics.md` §6.
