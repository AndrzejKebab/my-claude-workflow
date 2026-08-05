---
name: vtcontentview-gradient-oracles
description: "VTContentView/VTDebugSample point-loads with integer truncation — pure-sample oracles are exact, finite-difference oracles over the readback carry position-snap noise; widen the baseline"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82f1c76b-2749-4fea-bb5f-a033284a0a98
---

`VTDebugSample.compute` (behind `VTContentView.Sample`) resolves each view texel via `VTLookup`
at the mip derived from the view footprint, then **point-loads with integer truncation** —
`_PhysicalPool[int2(physicalUV * size)]`. Every readback sample is positionally snapped by up to
half a resident-mip texel.

- **Pure-sample comparisons stay exact**: a snapped texel still carries an exact value at a nearby
  point (normal-vs-closed-form graded 0.82° mean on the egg-carton).
- **Finite differences ACROSS readback samples eat the snap as gradient noise**: a ±1-view-texel
  central difference measured ~5.5° mean angular error, uniform, not tile-seam-correlated. Fix by
  widening the baseline (±4 view texels dropped it to 1.4°) or using a closed-form oracle for
  per-texel strictness ([[verification-representatives-protocol]]).
- The resident mip under a high headless top-down camera is coarse (screen-derived desired set),
  so the snap is meters, not centimeters — don't assume mip 0 in gates.

**How to apply:** when a gate derives gradients/slopes/curvature from a `VTContentView` readback,
either widen the difference baseline well past one resident texel or grade against a closed form;
never tighten such a tolerance below the measured snap floor. Example: `NormalLayerTests` in
is.zori.miniheightfields.
