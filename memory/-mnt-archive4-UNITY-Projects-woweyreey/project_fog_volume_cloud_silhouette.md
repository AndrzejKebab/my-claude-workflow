---
name: Fog volume cloud-silhouette goal — distinct from current detail erosion
description: User's actual goal for "fog gets cloud-like detail" is a sharp cloud-like SILHOUETTE on fog volumes (Enshrouded sl.20 voxel-SDF style), not just 3D noise carved INSIDE the volume. Phase 1–3's detail erosion is the inside-the-fog feature; outside-silhouette is a separate prototype.
type: project
originSessionId: 59505920-41e9-4bb7-b01b-4b72d5493b44
---
2026-05-08 user feedback during Phase 4 review of `docs/cloud-fog-unification-plan.md`:

> "what we've implemented is carving detail noise inside fog - making the
> inside of the fog have the carved out 3d noise. this doesnt give fog
> volume itself appearance of the cloud as I was hoping for, but perhaps
> thats what the next phases could help us prototype - clouds-to-fog and
> then we could reuse clouds to make the fog appear to have the sharp
> cloudy outline, perhaps"

**The two distinct features:**

1. **Detail erosion *inside* fog** (what shipped in Phase 1–3): Layer B's
   per-step `sigmaT_fog = sigmaT_fog_lf * detailErosion(noise, amount)` —
   carves the volume's interior density into wisps. Works inside any
   `FogMaterialVolume`. Does NOT change the volume's outer surface — that
   stays whatever the analytic primitive (box/sphere) gives.

2. **Cloud-like outer silhouette** (the user's actual goal — NOT yet
   implemented): the volume's *boundary* should look like a cloud surface
   — soft, eroded, wispy edges where the analytic primitive currently has
   a hard transition. Reference: Enshrouded sl.20 — 1 m SDF, 128³ around
   camera, raymarched with detail erosion at the surface, not interior.

**Why:** The plan-as-shipped treats authored fog density as the source of
truth at the boundary (Layer A populate produces a smooth density field
gated by the analytic primitive's distance function). Layer B detail
erosion only multiplies INSIDE that field. So box/sphere volumes still
have geometric edges, just with wispy interior.

**How to apply:** When the user asks "why doesn't my FogMaterialVolume
look like a cloud?" — they mean the silhouette, not the interior. Don't
re-tune `fogDetailErosionAmount` or `fogDetailNoiseScale`; those affect
the inside. The fix is a different feature: either (a) push detail erosion
into the populate's boundary distance evaluation so the analytic SDF gets
modulated by noise before becoming density (cheap, looks like cloud-mesh),
or (b) replace analytic primitives with sparse-VT voxel-SDF authored
volumes per Enshrouded (V3 of the package per plan §4 — far out of scope
now). Option (a) is the prototype path the user gestured at. Probably
fits as a later phase or §3 follow-up after the unified compositor lands.

**Linked:** `docs/cloud-fog-unification-plan.md` §4 (V3 deferral),
`docs/research/volumetric-fog-in-enshrouded.md` slides 15–18, 20.
