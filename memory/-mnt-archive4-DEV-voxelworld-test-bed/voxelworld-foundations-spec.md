---
name: voxelworld-foundations-spec
description: "Locked foundational decisions for is.zori.voxelworld — spec at docs/specs/00-foundations.md, research journal at docs/orchestrate/voxelworld-foundations/"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7eed1011-870d-447c-b456-576e49cc31e3
  modified: 2026-07-24T05:03:35.952Z
---

On 2026-07-24 the user locked the foundational scope for `is.zori.voxelworld` via scoping Q&A;
binding spec suite: `docs/specs/00..09 + GLOSSARY.md + ROADMAP.md` (superproject
voxelworld_test_bed; 00 is the decision record/index, 01–09 are per-technology deep dives),
superseded only by later numbered specs. Terminology contract (GLOSSARY): brushes are ECS-side
and PRODUCE core-side stamps; scatter brush = 1 entity → N stamps; never say "instanced brush". Locked: C-style C++20 native core (FastSIMD-style dispatch, scalar +
pinned AVX2 only, strict-FP determinism); URP only (HDRP "future maybe"); 24 km² world @ 0.5 m
voxels; field = pure function of seed/graphs (L0) + movable/instanced brush ECS ghosts (L1) +
sparse carve field of 8³ bricks with dual add/sub u8 distances (L2); GigaVoxels-style CPU cache +
clipmap-ring residency; surfacenets with the five-invariant gapless LOD scheme (port from
voxel_world branch `feat/seamless-lod-harness`, NOT main); NFE replication = brush ghosts +
per-region `DynamicBuffer<CarveOp>` + hash-addressed baselines; object voxel volumes (variable
resolution, Bananza-style regeneration); digging AND painting at 60 Hz (paint = attribute-only
mesh update). FastNoise2 submodule lives at `com.api-haus.fastnoise2`.

**Why:** the user answered the four scoping forks explicitly (language, pipeline, replication
model — "brushes are entities", 24 km²) and added requirements mid-session; future sessions must
not relitigate these.

**How to apply:** treat the spec as binding when working in voxelworld_test_bed or
is.zori.voxelworld; audit load-bearing claims via the journal reports in
`docs/orchestrate/voxelworld-foundations/` (journals, not canon). SIMD surfacenets porting
reference: `~/_dev/_unity/voxelmission/.../SurfaceNets/NaiveSurfaceNets.cs`.

The suite passed an 18-round adversarial fresh-eyes convergence loop (2026-07-24, commits
`24861dc..c26e857`): ~8 blocker/critical + ~35 major findings found and fixed across rounds
1–16; rounds 17+18 both CLEAN at MAJOR+. Do not re-litigate mechanisms whose failure rationale
is pinned inline in the specs — the "why not X" sentences are load-bearing survivors of that
loop.
