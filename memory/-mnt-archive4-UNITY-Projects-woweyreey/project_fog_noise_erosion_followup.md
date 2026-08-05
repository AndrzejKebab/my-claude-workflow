---
name: Fog Nubis-look erosion is profile-level + needs raymarch TA — long-term initiative, not a kernel patch
description: Per-volume noise erosion on FogVolume/FogVolumeMaterial was the wrong abstraction. The Nubis fluffy look is a profile-level rendering treatment that requires a separate raymarched fog pipeline with dedicated TA (like clouds), not bolt-ons to the existing froxel populate kernel.
type: project
originSessionId: c11e6dba-4be9-410f-a722-120ea6ace681
---
The `FogVolume` / `FogVolumeMaterial` per-instance noise fields (noiseProfile, noiseScale, noiseChannel, noiseAmplitude, windScrollMultiplier) were a wrong abstraction and have been removed from the system. The Nubis-look erosion belongs at the FogProfile level (i.e. `VolumetricFogSettings` / `FogPreset`) as an optional global toggle, not a per-volume material parameter. Reasoning (user, 2026-05-03):

**1. Architectural fit.** The Nubis fluffy look is a *rendering treatment* applied uniformly to fog, not a *per-material property*. It's "fog renders with Nubis erosion: yes/no" and "with which detail noise atlas," not "this hot spring uses Worley channel 2."

**2. Froxel fog can't carry the look.** The froxel populate kernel was designed for **coarse falloff only**. Even the existing slab structure has noisy jittery slabbing problems. Adding high-frequency noise erosion at froxel resolution aliases the noise into per-slab jitter — it does not produce fluffy wisps, it produces visible flickering slab boundaries.

**3. Clouds already implement the look properly.** The cloud raymarch (`ZoriDistantFogRaymarch.compute` + cloud trace shaders) does per-step noise sampling with a dedicated TA pipeline tuned for the high-frequency content. Replicating that for fog volumes means building an equivalent raymarch pass + TA, not patching the populate kernel.

**4. Curly-Alligator / Alligator noise variants** (Schneider Nubis Cubed 2023, used by Enshrouded fog) are not yet generators in `Noise3DProfile`. Currently the profile bakes Perlin / Worley FBM / PerlinWorleyDilation. Adding the two Alligator variants is its own follow-up; for the eventual Nubis fog implementation we'd use what `Noise3DProfile` ships and add the two new kernels later.

**How to apply when this initiative resumes:**

1. Add a `FogProfile.nubisErosionEnabled` bool toggle (and a `Noise3DProfile` reference + amplitude on the *profile*, not on volumes).
2. Stand up a new raymarch pass for fog volumes that mirrors the cloud raymarch architecture: per-pixel marching, per-step noise sampling, dedicated half-res reconstruction + TA history (matching clouds' TA stages).
3. Composite the raymarched fog with the existing froxel result (the froxel grid keeps owning the coarse atmospheric path; the raymarch owns the high-freq erosion).
4. Add the Alligator / Curly-Alligator kernels to `Noise3DProfile` so the fog raymarch has Enshrouded-canonical noise to work with.

**Reverted state (2026-05-03):** all per-volume noise infrastructure removed from populate kernel, FogVolumeMaterial, FogVolumeGpu, and VolumetricFogPass. EvalVolumeMarched sub-march helper removed. Froxel fog is back to single-sample analytical SDF coverage per volume — Bauer's coarse procedural baseline, no per-volume noise.
