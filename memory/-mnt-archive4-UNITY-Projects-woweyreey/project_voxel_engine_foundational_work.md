---
name: V3 voxel engine — foundational GPU library before atmospherics integration
description: V3 voxel field work begins with a foundational GPU library for voxel primitives — raymarching, sparse-VT sampling, sphere-tracing, jump-flood SDF — built in isolation with thorough test coverage. Atmospherics-side integration (fog density source swap, V3 of is.zori.atmospherics) follows AFTER the library is stable.
type: project
originSessionId: 59505920-41e9-4bb7-b01b-4b72d5493b44
---
2026-05-09 wrap-up direction:

> "we will begin the voxel engine exploration later. there will be
> preliminary work on preparing the voxel primitives first and building
> a gpu library for voxel raymarching with nice test coverage as
> foundational work for this, including raymarching, vt, sphere tracing
> primitives, etc."

**Sequencing:** Library FIRST, atmospherics integration SECOND.

**Foundational library scope (estimated):**

1. Voxel primitives — sample/store helpers, BC-compressed tile atlas
   wrappers, world-space addressing (FO-aware via existing
   `is.zori.heightfields` bridge pattern).
2. Sparse virtual texture (`is.zori.rwvt` extension or follow-on) —
   tile residency, streaming, eviction, allocation.
3. Sphere-tracing kernels — read SDF, advance by signed distance,
   handle inside/outside transitions cleanly.
4. Jump-flood SDF builder (Cuntz07 hierarchical 3D distance transform)
   — runtime camera-anchored 128³ near-field SDF generator.
5. Voxel raymarcher — generic loop that callers parameterise with a
   density evaluator, lighting evaluator, and output buffer shape.
6. Test coverage — unit tests for each primitive, integration tests
   for the raymarcher, golden-image tests for visual stability.

**What to AVOID during foundational phase:**

- Don't pre-integrate with `is.zori.atmospherics` yet. The library
  should be reusable for any voxel-density use case (fog, scenery,
  GI probes, AO fields, etc.).
- Don't pre-design specific authoring tools (model→voxel pipelines)
  before the runtime sampling primitives are stable.
- Don't prematurely couple to atmospherics-specific data structures
  (FogVolumeGpu, MaterialA, etc.) — keep the library agnostic.

**Atmospherics-side V3 integration (deferred until library lands):**

Three items resolve at once when V3 atmospherics integration begins:
1. Det/Frx density mismatch (`project_v3_voxel_field_resolves_density_mismatch.md`)
2. Source 2 self-shadow via cloud altitude LUT (`project_cloud_altitude_lut_for_self_shadow.md`)
3. Enshrouded-look outer silhouette (`project_fog_volume_cloud_silhouette.md`)

Plus authoring-side work: hi-res model → 16m voxel downsample → BC-
compressed tile atlas pipeline (per Schneider sl.15-18).

**Linked:**
- `project_chunked_clipmap.md` — `is.zori.rwvt` sparse-VT canon, the
  natural home for atlas streaming.
- `project_v3_voxel_field_resolves_density_mismatch.md` — atmospherics-
  side architectural transition.
- `docs/cloud-fog-unification-plan.md` §4 — V3 deferral.
- `docs/research/volumetric-fog-in-enshrouded.md` slides 15-18 (sparse-
  VT pipeline), 20 (1m SDF 128³), 42-43 (sphere-trace inner loop), 47
  (cloud density + erosion).

**When to revisit:** when the user signals "start the voxel engine
foundational work". The cloud-fog-followup orchestration leaves
analytic-primitive boundary noise + Phase 4.5 oracle architecture in
place; foundational library work is independent and parallel.
