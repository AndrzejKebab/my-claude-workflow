---
name: read-the-reference-implementation
description: "mhf is a port of Kühnert's method and the author maintains a live implementation (kurtkuehnert/bevy_terrain) — read it before inferring how a technique works from the paper's prose"
metadata: 
  node_type: memory
  type: project
  originSessionId: 539966d6-2869-4a80-adf2-cde6eaee6f34
  modified: 2026-07-20T09:44:28.952Z
---

The terrain is a port of Kühnert 2022, and the author keeps a working implementation at
<https://github.com/kurtkuehnert/bevy_terrain> (the thesis-era `terrain_renderer` is frozen;
prefer bevy_terrain). Load-bearing files: `src/shaders/functions.wgsl` (tile lookup, morph, LOD
blend), `src/shaders/attachments.wgsl` (sampling), `assets/shaders/planar.wgsl` (composition).

**Why:** the LOD-fringe blend was re-derived by inference through six wrong shader iterations
(2026-07-20) — each fixing the symptom the previous exposed — while the reference sat public.
The thing that settled it is two lines and is NOT deducible from the spec prose:
**derivatives filter WITHIN a tile; distance selects WHICH tile.** Our `VTLookup` selected the
tier by screen derivative, so tiers changed at tile-box edges where no weight computed from the
analytic ring could align — every reconciliation broke elsewhere.

**How to apply:** when a ported technique misbehaves and the fix is not obvious from the code at
HEAD, read the reference BEFORE the second speculative change. Its conventions are inverted
(`lod` counts up with detail where our `mip` counts down), so port the reasoning, never the
expressions. Recorded in the repo's AGENTS.md reference-material section.
