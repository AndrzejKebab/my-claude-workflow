---
name: shadow-direct-trace-mode
description: "The heightfield shadow term IS the slab trace — boundary heights traced whole every frame on the box lattice; the temporal bake (2026-07-19) AND the per-screen-pixel interleaved trace (2026-07-20) are both REMOVED"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3aeabc29-801b-4bb7-b979-83fa928b85e4
  modified: 2026-07-20T00:31:31.415Z
---

The shadow term is the slab trace: per box texel, one walk stores the shadow volume's boundary
heights for the sun disc's edge tangents (`HFMaxMip_TraverseShadowHeights` →
`ShadowViewState.Slab`, RG on the box lattice, re-traced whole every frame, no history); every
receiver resolves from the pair at its own height (`HFSlabVisibility`). The surface snapshot
(flat R32F at 2× lattice, captured per frame) keeps the VT out of the walk. Two predecessors are
REMOVED: the temporal box bake (f1c6c87, 2026-07-19) and the per-screen-pixel interleaved trace
with depth-validated reprojection (2026-07-20) — the per-receiver horizon walk survives only as
the test probes' oracle. The shadow-path data now also feeds the occlusion cull's near tier
(window max + snapshot-floor min + validity mask; spec 03-virtual-texture/05-hiz-and-bvh.md §2b).

**Why:** the traced term beat the bake on every axis it amortised; the slab decoupled trace cost
from screen resolution (walks = shadowResolution², 3.85→1.54 ms on Deck at 256²).

**How to apply:** don't resurrect bake-era or interleave-era APIs or cite their spec sections
(03-shadows §4 is a removal stub). Gates: `HeightfieldShadowDirectTraceTests`,
`HeightfieldShadowSlabTests`, `HeightfieldShadowGoldenSweepTests`. Suite baseline: URP17.3 =
33 EditMode + 169 PlayMode (re-blessed 2026-07-20: two-tier cull-bound gates + phase-2 survival
gate; fixtures default to depth priming Forced — the shipped renderer config). URP17.0/17.5
rows still carry stale 179 and need re-blessing on their next full run.
Related: [[terrain-fixture-needs-depthonly]], [[pin-orthogonal-dimension-in-fixtures]].
