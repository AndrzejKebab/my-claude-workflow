---
name: Pass 1 history sample is bilinear, never Catmull-Rom (canon §6.2)
description: Cloud TA Pass 1 history reprojection MUST use bilinear with linear-clamp sampler — Catmull-Rom is forbidden by canon §6.2. Distinct from the Pass 2 rule with separate reasoning.
type: feedback
originSessionId: 8178fcec-4e8a-4bdf-a212-3f0af31f5657
---
The Pass 1 history reprojection step (`SAMPLE_TEXTURE2D(_PrevAccumulationTexture, sampler_linear_clamp, prevUV)`) **must** use bilinear filtering, never Catmull-Rom. Documented in `docs/clouds-pre-nc23-lineage.md` §6.2: *"All three shipping engines use bilinear with a linear-clamp sampler. None use Catmull-Rom for cloud history."*

**Why** (separate reasons from Pass 2 rule):
1. Catmull-Rom's negative outer lobes multiply clamped border texels and produce a persistent dark halo at the cloud buffer edge — visible every frame regardless of camera state.
2. Karis 2014 (slide 17) recommends Catmull-Rom for TAA of *sharp* geometry; cloud radiance is smooth, so the sharpening benefit does not apply. The kernel pays the edge-halo cost for zero benefit.

**How to apply:**
- Pass 1 history sample is bilinear, period. If a future session proposes Catmull-Rom for "anti-blur under motion," reject it — that's not the right knob.
- The canonical anti-blur fix is §9.2 motion-scaled history dilution (`feedback_motion_scaled_history_dilution.md`), not a sharper kernel.
- Pass 2 upsample is separately constrained to bilinear-or-nearest-depth (`feedback_catmull_rom_edge_halo.md`) for different reasons (silhouette halos at half→full upscale).

References: HDRP 17 `VolumetricClouds.compute:88` (`s_linear_clamp_sampler`), UE 5.7 `VolumetricRenderTarget.usf` (linear sampler), WE `volumetricCloud_reprojectCS.hlsl` (`sampler_linear_clamp`). All three converge.
