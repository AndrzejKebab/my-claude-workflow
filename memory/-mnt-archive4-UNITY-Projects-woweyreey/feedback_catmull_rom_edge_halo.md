---
name: Never Catmull-Rom for cloud history — use bilinear + nearest-depth upsample (canon §11)
description: Canon §11.2 — cloud Pass 2 upsample is bilinear when the 2×2 half-res cloud-depth range is < 1 km, nearest-depth otherwise. Catmull-Rom was shipped pre-canon with an edge-halo fallback; both the kernel and the fallback are removed under canon.
type: feedback
originSessionId: 726c4158-973f-4d34-8c33-a1c331c299e5
---
The cloud Pass 2 upsample/composite **never uses Catmull-Rom**. Canon §11.2 (HDRP, UE, WE converge on this): sample the full-res output from the 2×2 nearest half-res history texels with bilinear reconstruction if their cloud-depth range is coherent (< 1 km), or nearest-depth otherwise (pick the half-res tap whose cloud-front is closest to scene depth, avoiding bleed across silhouettes). No bicubic, no Karis TAA upsample trick, no negative lobes.

**Why:**
- Catmull-Rom's negative outer lobes produce a ~1-2 source-texel-wide dark halo at buffer edges (`sampler_LinearClamp` pulls the boundary texel into negative-weight taps). The prior workaround — edge-fallback to bilinear — worked but meant shipping two codepaths for zero artistic gain over bilinear.
- Bilinear + nearest-depth matches what HDRP / UE / WE ship and is simpler. Depth-coherent pixels get a smooth bilinear; silhouette pixels get a point-sample from the best-matching half-res tap, which is the correct "no-bleed" choice.
- The sharpening Catmull-Rom offered over bilinear is below perceptibility at the Pass 2 ratio (2× upsample from half-res to full); the mitigation it required (edge guard) adds complexity without corresponding benefit.

**How to apply:**
- In FragUpsample: sample 4 half-res taps at `base + (0,0)/(1,0)/(0,1)/(1,1)`, compute `dMin`, `dMax`. If `dMax - dMin < 1000.0` → `SAMPLE_TEXTURE2D(_CloudsIntermediateLighting, sampler_LinearClamp, uv)`; else pick the tap with `abs(tapCloudDist - sceneRayDist)` minimum.
- Occlusion discard (canon §11.3): if `dMin > sceneRayDist + 1.0` for a non-sky output pixel, emit `float4(0, 0, 0, 0)` — under `Blend One OneMinusSrcAlpha` this is a composite no-op.
- Do NOT re-introduce `SampleCatmullRomCloudsLighting` on the argument that "the sharpening hides the half-res grid" — at 2× upsample the grid isn't visible with straight bilinear, and the edge-halo fallback is dead weight.

Note: the shared 3D Catmull-Rom helper in `FroxelTemporalCommon.hlsl` (fog populate) is a separate topic — its temporal-supersampling use-case is distinct from Pass 2 upsample. This rule applies to cloud Pass 2 specifically.

Supersedes the pre-2026-04-24 "Catmull-Rom needs edge fallback" rule — the whole kernel is gone for clouds.
