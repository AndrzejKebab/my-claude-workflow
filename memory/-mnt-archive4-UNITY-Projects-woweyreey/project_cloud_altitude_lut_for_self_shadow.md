---
name: Cloud altitude LUT — future fix for Source 2 self-shadowing
description: Source 2 cloud-density-as-fog (in Fog Detail trace) is currently self-shadowed by `_VolumetricFog_ShadowVolume` because that volume bakes cascade × heightfield × cloud SM. Inside the cloud altitude band the cloud SM contribution is wrong — you can't be shadowed by clouds at your own altitude. Solution: gate cloud SM contribution to ground-altitude-only via an altitude LUT or comparison.
type: project
originSessionId: 59505920-41e9-4bb7-b01b-4b72d5493b44
---
2026-05-09 user direction during cloud-fog-followup orchestration:

> "could be solved by cloud altitude LUT in the future, please make a
> memory about it"

**Context.** Phase 4.5 SLV-as-oracle architecture has the trace shader
sample `_VolumetricFog_ShadowVolume` (R16F, fused cascade × heightfield ×
cloud SM) for direct-light shadow. Source 2 of the Fog Detail trace adds
`sampleCloudDensity(p)` as in-cloud σ_t. When the camera is INSIDE a
cloud, the shadow oracle still includes cloud SM — so the cloud-density
medium is shadowed by the cloud's own opacity. Visual result: black
patches where the camera is fully inside cloud volume.

**Naive fix (rejected for now):** populate writes a second shadow volume
without cloud SM, trace samples the no-cloud-SM oracle for the
Source-2 component. Costs one extra Texture3D + one oracle helper.

**User's preferred fix (deferred):** **cloud altitude LUT.** Gate the
cloud SM contribution by altitude — sample point's altitude vs. the
cloud height band. Below the cloud bottom (`_CloudHeightMinMax.x`) the
cloud SM is real (clouds shadowing ground). Within the cloud band, cloud
SM contribution is structurally wrong — must be zeroed or replaced with
self-density-based extinction.

**Why this is more elegant.** Single shadow volume, single oracle, no
texture allocation. The altitude gate is mathematically correct: clouds
above you cast shadows on you; clouds at your altitude don't. The LUT
captures the smooth transition through the cloud base where partial
shadowing makes physical sense.

**Implementation sketch (when revisited):**

```hlsl
// Sample the existing fused shadow.
const float fusedShadow = SampleFogShadow(t, V, uv);

// Compute altitude factor in cloud band:
//   altitude = sample point world-space Y (or planet-relative).
//   below cloud bottom → 1.0 (cloud SM legit, ground shadows fine)
//   inside cloud band  → 0.0 (cloud SM is self-shadowing, kill it)
//   above cloud top    → 1.0 (clouds below you do not shadow you)
const float altitudeFactor = ComputeCloudShadowGate(p.y);

// Decompose fused shadow into cascade × HF (legit) and cloud SM (gated)
// either via a two-channel volume OR an analytical recovery if cloud SM
// can be reconstructed from cloud-density evaluator.
shadow = lerp(cascadeXHF, fusedShadow, altitudeFactor);
```

The `ComputeCloudShadowGate` could be an analytical smoothstep over the
cloud height band (cheapest), or a small 1D LUT if the gate needs to
match the cloud raymarcher's actual coverage profile (more accurate).

**When to revisit.** After Phases 5 / 6 ship and the unified compositor
is stable. The current black-patch artefact is a known regression
specific to camera-inside-cloud, which is also the case Phase 5's fade
ramp targets — so the visible window is small. Acceptable to ship Phase
5/6 with the artefact present; followup phase implements the altitude
LUT.

**Linked:**
- `docs/cloud-fog-unification-plan.md` §2.2 (Layer B Fog Detail Source 2),
  §11 Q6 (phase blend at boundary).
- `docs/orchestrate/cloud-fog-followup/00-reuse-audit.md` (Issue #1).
- `feedback_godrays_canonical.md` — direct stays per-step shadowed.
- `feedback_compute_shadow_sampling_canon.md` — URP shadow sampling
  pattern.
- `project_fog_volume_cloud_silhouette.md` — separate "fog should look
  like cloud" feature distinct from this self-shadow fix.
