---
name: V3 voxel field naturally resolves Det/Frx density mismatch
description: The current architectural mismatch where Fog Detail trace and integrate kernel both consume MaterialA at different resolutions (Det reads `MaterialA.a / dt_slab` per-step, Frx reads SLV Hillaire-baked) dissolves under V3 voxel field — both consumers read the same authoritative voxel atlas, no `MaterialA` round-trip for density. Captures the design intent so V3 work can avoid re-deriving it.
type: project
originSessionId: 59505920-41e9-4bb7-b01b-4b72d5493b44
---
2026-05-09 wrap-up of `cloud-fog-followup` orchestration. User correctly
identified that the right time to fix the Det/Frx density mismatch is
when V3 (sparse-VT voxel field) lands — at that point both density
consumers share the same source naturally.

**The current mismatch (deferred to V3):**

- Populate kernel writes per-froxel `σ_t × dt_slab` into MaterialA from
  analytical sources (FogMaterialVolume, FogMap, height fog, rain fog).
- Integrate kernel reads MaterialA, applies Hillaire `(1 - exp(-τ)) / τ`
  closed-form, accumulates SLV.
- Fog Detail trace reads MaterialA via `SampleFroxelSigmaT(t) = mA.a /
  dt_slab` at per-step linear stride, treats as raw σ_t per metre.
- Frx zone reads SLV (Hillaire-baked) via segment difference.
- Det zone reads trace LUT (raw-σ_t-then-trace-Hillaire).

Both zones ultimately want to render the same density field, but apply
different transformations. For smooth density (e.g. height fog) they
match approximately. For sharper variations they diverge — visible as
"slightly less dense than legacy" under unified compositor.

Path A (density LUT) was proposed as a band-aid: integrate writes a
separate `_VolumetricFog_DensityVolume` (raw σ_t per metre, slab-
averaged) so the trace reads pre-computed density without the divide.
NOT in published canon — Wronski/Bauer/Hillaire/Schneider all use ONE
integrator, not the Det+Frx split we have. User chose to defer.

**How V3 resolves it:**

In V3, density flows from a single sparse-VT voxel atlas (per-Schneider
sl.15-18: hi-res model → 16m voxel downsample → BC-compressed tile
atlas → world-space VT). Both consumers read this atlas:

- **Populate kernel:** samples voxel atlas at froxel center → writes
  per-froxel σ_t × dt_slab into MaterialA → integrate path unchanged.
- **Fog Detail trace:** samples voxel atlas DIRECTLY at per-step world
  position → no MaterialA round-trip for density. MaterialA still used
  for material params (phase G, albedo, ambient scale).

Both consumers read the same continuous density field at different
resolutions. No mismatch.

**Per-Enshrouded sl.42-43 trace inner loop (V3 target):**

```
while (t < tEnd):
  sdf = sample_voxel_sdf(camera + V*t)
  if sdf > 0:
    t += max(sdf, minStepLength)        // sphere-trace through empty
    continue
  density_base = sample_voxel_density(p)
  noise_type   = sample_voxel_noise_type(p)   // per-voxel Curly vs Alligator
  detail       = sample_detail_noise(p, noise_type)
  sigma_t      = max(0, density_base - detail × erosion_amount)
  // Lighting + Hillaire integration as today
  t += primaryStep
```

Sphere-tracing replaces uniform stepping → free traversal through clear
air. Density carries arbitrary 3D shape complexity, not just box/sphere.

**What stays vs what changes when V3 lands:**

Stays:
- Phase 4.5 oracle architecture (ambient/shadow/material oracles).
- Compositor zone layout (Det/Frx/Dst + cloud overlay).
- Hillaire integration form, cone-march detail-shadow (Issue #6),
  camera-proximity cloud fade (Issue #5), all Enshrouded-canonical
  lighting choices.

Changes:
- `SampleFogSigmaT` in `FogDetailCommon.hlsl` swaps from `mA.a /
  dt_slab` to direct voxel-atlas sample.
- New `is.zori.rwvt`-backed sparse-VT density storage.
- New GPU jump-flood SDF builder (Cuntz07) for camera-anchored near-
  field 128³ SDF.
- New authoring pipeline: hi-res model → voxel downsample → tile atlas.
- Populate kernel: voxel-atlas sample alongside (or replacing) the
  analytical evaluation — analytical primitives can coexist for simple
  cases.

Per-voxel noise-type (sl.27 / sl.52-53): artists paint per-region
noise (Curly-Alligator vs Alligator) and trace blends accordingly
during erosion. Impossible with analytical primitives.

**Linked:**
- `docs/cloud-fog-unification-plan.md` §4 (V3 deferral).
- `docs/orchestrate/cloud-fog-followup/00-reuse-audit.md` (Fog Detail
  density-source audit + Three-bug investigation).
- `docs/research/volumetric-fog-in-enshrouded.md` slides 15-18, 20,
  27, 42-43.
- `project_chunked_clipmap.md` — `is.zori.rwvt` sparse-VT canon.
- `project_fog_volume_cloud_silhouette.md` — Enshrouded-look feature.
- `project_cloud_altitude_lut_for_self_shadow.md` — also V3-deferred.

**When to revisit:** when V3 work begins. The density-mismatch fix is
a natural side-effect of switching the trace's density source from
`mA.a / dt_slab` to direct voxel sample. Don't pre-build the density
LUT in the meantime — it'd become dead code post-V3.

**2026-05-09 addendum — additional approximations V3 eliminates:**

User asked: "if we had a voxelised volume then we could sample the
density throughout the entire froxel ray and make an informed
consistent choice on the density?" Yes — and V3 also eliminates two
related approximations the current architecture forces:

1. **Froxel trilinear blur.** Populate evaluates analytic SDFs at
   froxel CENTRES. A 30 m sphere centred at 50 m fits in one froxel
   → that froxel gets full density, neighbours get zero. Trilinear
   smooths the boundary but the underlying signal is froxel-quantised.
   The volume's density is effectively "spread" across the froxel cell
   (~50 m × 50 m × ~10 m at near range), much larger than the sphere
   itself. From the trace's perspective, density looks dilute. User
   description: "fog volume informs overall density which then gets
   distributed onto the underlying depth — which is not what the
   froxel volume even suggests."

2. **Linear-proportion T_at_front approximation.** The cloud-overlay
   slot's `TransmittanceUpTo(cloud_front)` for `cloud_front <
   fogDetailEffective` linear-proportions the Det LUT's optical depth
   (`Tdet = exp(-odFull × t/fogDetailEffective)`). Assumes uniform
   extinction across Det's range. For a fog volume actually
   concentrated at one position, gives slightly too much extinction
   near the front and slightly too little near the volume's centre.
   This patch (commit `911ecc0`) fixes the cloud-bleeds-through-fog
   symptom but doesn't fix the underlying "density spread across
   froxel" issue.

V3 voxel atlas at e.g. 1 m resolution captures the sphere accurately.
Per-step trace samples voxel directly → density preserved at boundary,
no froxel blur. `T(cloud_front)` becomes the exact integral of voxel
densities along [0, cloud_front]. No linear-proportion needed. Both
approximations dissolve.

Patches landed pre-V3 (Path A category — `911ecc0` etc.) are stopgaps;
they should be deleted at V3 transition since per-step voxel sampling
makes them unnecessary. Mark with `// V3-removable:` comments in the
shader for easy bulk-removal.
