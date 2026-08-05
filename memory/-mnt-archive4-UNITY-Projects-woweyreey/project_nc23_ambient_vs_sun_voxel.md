---
name: NC23 voxelised cloud lighting — not pursued on this project
description: NC23 voxel sun/ambient LUT is unshippable on Steam Deck per 2026-04-24 directive. Classical Nubis 2017 / HZD 2015 cone-march + Patapom ambient is the cloud-lighting direction. Architectural notes on where NC23's 40% win actually came from retained as background context in case the constraint ever lifts.
type: project
originSessionId: 54fcb518-eed1-4c6d-a6e3-73f6941176ce
---

**Status (2026-04-24):** NC23 voxelised cloud lighting is **not pursued on this project**. The user declared it unshippable on Steam Deck. Current and future cloud lighting direction: classical Nubis 2017 / HZD 2015 cone-march (`sampleConeToLight`, 4–6 taps), dual-HG phase, Decima in-scatter probability, Patapom 2013 Ei-slab ambient. NC23 voxel sun-density LUT and NC23 voxel ambient LUT are out.

**Why:** The 40% NC23 headline win comes with a voxelisation cost (rasterising cloud density into a world-space 3D grid every frame) that does not pay back on Deck-class GPU + memory. The TA / reproject / upsample path is where the Deck-relevant wins now live.

**How to apply:** Never propose NC23 voxel sun or ambient LUT as a cloud-lighting direction, design option, or "future-optimisation" follow-up in this project. When canonical research is cited for cloud lighting, anchor to Nubis 2017, HZD 2015, Schneider HFW 2022, Frostbite 2016 — not NC23.

---

**Background — what the NC23 40% actually covered (retained for context only):**

NC23's "Voxel Cloud Lighting" grid (slide p.151) stores summed density values in multiple directions. Two consumers:

1. **Sun direction** (p.136): `ms_volume *= exp(-inSunLightSummedDensitySamples * Remap(sun_dot, ...))` — replaces the per-step sun cone-march. **This is where the 40% savings come from.** The cone-march is the biggest per-step cost in the cloud pipeline.
2. **Ambient direction** (p.144): `ambient_scattering = pow(1.0 - dimensional_profile, 0.5) * exp(-summed_ambient_density)` — multiplies Nubis's constant-ambient approximation by spatial extinction. Side benefit on p.151.

Our Patapom Ei-slab ambient already has a 1D extinction term, so the NC23 ambient overlay would only incrementally improve spatial variation — not a visible win. The whole-stack claim only materialised with the sun grid, which is what we are now declining on Deck cost grounds.
