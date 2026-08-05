---
name: Atmospheric compositor sources the sky — Unity skybox pass deprecated
description: Architectural decision (2026-05-09 wrap-up) — the unified atmospheric compositor takes ownership of sky-pixel composition. Unity's skybox pass is skipped on game cameras (Camera.clearFlags = SolidColor); the compositor samples physical sky for sky-pixels and composes with fog/cloud atmospherics. RenderSettings.skybox MATERIAL stays for IBL/reflection probe baking. Transparents integration deferred — known future cleanup.
type: project
originSessionId: 59505920-41e9-4bb7-b01b-4b72d5493b44
---
2026-05-09 user-confirmed direction:

> "ok, I agree. we'll tackle transparents integration in the future
> anyway."

(Following discussion of horizon-fog-volume composition issues that
revealed the sky-as-passive-background architecture has structural
limits.)

**The architectural shift:**

Currently:
1. URP renders opaques (writes depth)
2. URP skybox pass renders sky color where depth = far plane
3. Unified compositor stacks fog + clouds OVER existing camera color
4. Transparents render on top

After this change:
1. URP renders opaques (writes depth) — unchanged
2. **URP skybox pass SKIPPED via `Camera.clearFlags = SolidColor`**
3. Unified compositor's per-pixel branch: `if depth == farPlane → sample
   PhysicalSky for view direction → compose with fog/cloud → write to
   camera color`. Else: existing opaque-pixel path.
4. Transparents render on top — see fog-applied background (improvement
   for refractive materials)

**Why this is canonical:**

- HDRP volumetric sky + fog stacks identically.
- Schneider 2023 sl.49 (Enshrouded): "Finally we apply the full
  resolution fog texture from our ray marching pass by multiplying the
  combined scene irradiance and sky with the fog transmittance and
  adding the fog radiance." Same shape.
- Solves the fog-volume-vs-bright-skybox contrast issue that exposes
  froxel discretisation at the horizon (per
  `project_fog_volume_horizon_discontinuity_pre_existing.md`).
- One fewer URP pass (skybox).
- Sky becomes part of the atmospheric model, not stacked on top.

**What stays:**

- `RenderSettings.skybox` MATERIAL — kept for reflection probe baking
  + `unity_SpecCube0` IBL + `_GlossyEnvironmentColor`. Probes still
  bake from this material; the camera just doesn't render it.
- Existing `Runtime/PhysicalSky/` shader and pass — provides the sky
  source the compositor samples.
- Existing `_PhysicalSky_*` raster globals — sun/moon direction, color,
  atmosphere parameters. Compositor reads these for the sky-pixel
  branch.
- Editor scene view — keep skybox rendering for `Camera.cameraType !=
  CameraType.Game` (or accept black scene-view sky).

**Sky-pixel detection in compositor:**

Already exists per `feedback_skybox_farplane_history_fallback.md` —
the cloud TA pipeline distinguishes sky pixels via depth == far plane.
The atmospheric compositor extends this to compose the sky color
directly instead of just letting the skybox pass write it.

**Transparent integration — DEFERRED:**

Concerns to revisit:
- Transparent shaders with built-in `MixFog` would double-up the
  compositor's fog. Need per-shader audit + `_FOG_OFF` keyword
  enforcement, or coordinated fog evaluation via SLV oracle.
- Refractive transparents (glass) using `_CameraOpaqueTexture` will
  see fog-applied background — improvement, but visual A/B needed.
- `Camera.RenderToCubemap` real-time reflection probes — verify they
  include compositor's sky if used.
- User's call: "we'll tackle transparents integration in the future
  anyway" — accept transparent issues as known future work; ship the
  sky-composition change with documented caveat.

**Implementation scope (one orchestration phase):**

Files expected to touch:
- `Runtime/Core/AtmosphericCompositePass.cs` — set Camera.clearFlags or
  hook into URP to skip skybox pass for game cameras.
- `Runtime/Core/Shaders/ZoriAtmosphericComposite.shader` — sky-pixel
  branch in the compositor.
- `Runtime/PhysicalSky/*` — verify physical sky output is published as
  a raster global the compositor can sample (cubemap, sky-view LUT,
  or per-direction shader call).
- `Runtime/ZoriAtmosphericsFeature.cs` — toggle skybox-pass-skip per
  camera type.

**When to revisit transparents:** when a shipped scene shows visible
double-fog regression on transparent materials, or when the user
schedules a separate orchestration for transparent/atmospherics
unification.

**Linked:**
- `feedback_skybox_farplane_history_fallback.md` — sky-pixel detection
  canon already established for cloud TA.
- `project_fog_volume_horizon_discontinuity_pre_existing.md` — the
  composition issue that motivated this architectural shift.
- `docs/cloud-fog-unification-plan.md` — natural Phase 7 / extension
  topic.
- Schneider 2023 sl.49 — canon reference for fog × sky composition.
