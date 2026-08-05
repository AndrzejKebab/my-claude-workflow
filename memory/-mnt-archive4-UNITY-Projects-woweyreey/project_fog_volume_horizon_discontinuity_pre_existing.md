---
name: Fog volumes lose ~50% density at horizon — pre-existing, physics-correct, requires V3 to fix properly
description: Fog volume sphere/box primitives appear "halved" or fade at the horizon line where the camera ray transitions from sky-bound (full traversal) to terrain-bound (clipped at opaque depth). Confirmed by user 2026-05-09 to predate the unified compositor — it's a fundamental property of the populate→integrate pipeline applying premult-alpha composition over varying backgrounds, NOT a Phase 4/4.5/5 regression.
type: project
originSessionId: 59505920-41e9-4bb7-b01b-4b72d5493b44
---
2026-05-09 user confirmation: "this predates the unified compositor".

**The visible symptom:** A fog volume centred near the camera's horizon
altitude shows full density in its upper half (against sky) and ~50%
density in its lower half (against terrain). Sharp discontinuity exactly
at the horizon line.

**Root cause (two compounding effects, both physics-correct):**

1. **Geometric clipping by scene depth.** Upper-half rays traverse the
   full sphere to skybox (~35 km, full optical depth integrated). Lower-
   half rays traverse partial sphere then hit terrain at e.g. 200 m
   (truncated traversal, less optical depth). Beer-Lambert correctly
   reports less density on the shorter-traversal pixels.

2. **Premult-alpha contrast against varying background.** The same fog
   `(L, T)` reads more "fog-like" against bright sky than against dark
   terrain. `out = scene × T_fog + L_fog`: when scene is bright,
   `L_fog` dominates; when scene is dark, scene × T_fog still bleeds
   the dark terrain through. Eye reads density relative to background.

**Same effect with height fog active (image #37):** the volume's
inscatter has the same character as height fog's inscatter (same sun,
same phase, similar albedo) so the volume blends INTO the height fog
rather than holding a distinct silhouette.

**Why this is NOT a recent-work regression:**
- Populate kernel + integrate kernel produce identical MaterialA / SLV
  values regardless of which compositor is active.
- Legacy fog Apply samples the SLV at scene depth, applying premult-
  alpha composition. Same phenomenon.
- Unified compositor's Det zone reads MaterialA via trace,
  Frx/Dst zones via SLV — different paths, same physics outcome.

**What WOULD fix it (three knobs):**

1. **Higher per-volume density** (artist tunes σ_t) → opacity dominates
   background bleed-through. Limit: very high density looks solid not
   wispy.
2. **Strongly-contrasting scatter tint** per volume → silhouette holds
   via colour difference even when optical depth is moderate. Limit:
   stylized look, not atmospherically realistic.
3. **Architectural option — "above-scene fog volume sprite mode"**:
   render the volume's contribution at full density regardless of scene
   depth, then over-blend. Volume always reads consistent across
   horizon. Costs: depth-correctness goes away (volume appears in front
   of terrain it should be behind), substantial new render path
   separate from populate/integrate pipeline. Treat as a future V2
   feature toggle, NOT default behaviour.

**V3 path naturally improves this:**
- Schneider sl.20 voxel-fog raymarch has dense authored σ_t
  (high opacity dominates bleed-through, knob 1 effectively).
- SDF-based shape is sharp enough that boundaries hold visually
  (per `project_fog_volume_cloud_silhouette.md`).
- No architectural override needed — the use case naturally fits
  the dense voxel medium pattern.

**When to revisit:** If a project artist needs "always-visible volume
sprite" semantics before V3 lands, implement knob 3 as an opt-in toggle
on `FogMaterialVolume`. Otherwise wait for V3 voxel field.

**Linked:**
- `project_fog_volume_cloud_silhouette.md` — Enshrouded silhouette feature.
- `project_v3_voxel_field_resolves_density_mismatch.md` — V3 transition.
- `project_voxel_engine_foundational_work.md` — V3 prep direction.
- `feedback_fog_volume_architecture.md` — current authoring split.
