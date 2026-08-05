---
name: entities-baking-transform-order
description: "Entities baking: default-group baking systems run BEFORE transform baking assigns Parent — post-hoc Parent stripping silently no-ops; use TransformUsageFlags.WorldSpace instead"
metadata: 
  node_type: memory
  type: project
  originSessionId: 719966c5-bc10-48c0-99a3-906aee4b9058
  modified: 2026-07-21T23:47:09.869Z
---

A `[WorldSystemFilter(WorldSystemFilterFlags.BakingSystem)]` system in the DEFAULT baking group
runs before `TransformBakingSystemGroup` assigns `Parent`/`LocalTransform` to baked entities. A
system that queries `WithAll<Parent>` to strip parenting therefore matches nothing and no-ops —
silently, forever.

**Why:** `CarWheelUnparentBakingSystem` (swordgal) was such a no-op since the day it was written.
Physics write-back stamps world poses into `LocalTransform`, so simulation and every
LocalTransform-reading gate stayed healthy while the renderer composed parent × world — every
wheel DREW metres away from its car. Only a spectator screenshot caught it; a probe comparing
`LocalTransform` values read 0 detached in the same run (2026-07-22).

**How to apply:**
- An entity whose pose is written in world space (physics-driven children, e.g. Box3D bodies)
  must bake with `TransformUsageFlags.Dynamic | TransformUsageFlags.WorldSpace` — transform
  baking then emits an unparented world-space root. Declaration-level; no ordering to lose.
- Perceptual probes must read the channel the symptom lives in: renderers read `LocalToWorld`,
  so attachment/pose gates on presentation compare `LocalToWorld`, never `LocalTransform`.
- `LinkedEntityGroup` (ghost despawn-as-unit) survives losing `Parent`; transform hierarchy and
  prefab membership are independent.

Related: [[netcode-6-inprocess-session-harness]].
