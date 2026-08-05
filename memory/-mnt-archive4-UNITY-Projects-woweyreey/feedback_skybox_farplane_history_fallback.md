---
name: skybox farPlane history fallback (canonical)
description: Cloud TA history reprojection MUST split on sky-vs-cloud at the farPlane and use direction-only motion when sky — HDRP 17 three-stage mechanism, codifies what HZD 2015 page 95 only sketched
type: feedback
originSessionId: 8178fcec-4e8a-4bdf-a212-3f0af31f5657
---
When reprojecting cloud TA history during camera motion, sky pixels (`cloudDepth >= farPlane`) MUST be handled differently from cloud pixels — three stages, all required:

1. **Direction-only motion vectors for sky pixels.** Pack `positionFlag` into `worldPos.w` (0 = sky, 1 = cloud) before the previous-VP multiply. With W=0 the translation column drops out, leaving camera-rotation-only reprojection. Per-pixel parallax reprojection on a sky pixel ghosts because the skybox has no fixed world-space anchor.
2. **Sky-only 3×3 neighbourhood for variance clip on sky pixels.** Gather only the neighbours that are also sky (`depth == UNITY_RAW_FAR_CLIP_VALUE`); require ≥5/9 sky samples or skip the clamp; `validityFactor *= skyRatio` to fade history when sky/cloud mix is messy.
3. **Sky/cloud-state gating on bilinear upsample taps.** Zero a tap's weight when its sky-state doesn't match the current pixel's sky-state — prevents sky↔cloud bleed at silhouettes under camera rotation.

**Why:** The Nubis-lineage PDFs themselves (Schneider 2015 HZD, Schneider 2017 Decima, Schneider 2022 HFW, Schneider 2023 NC23, Hogfeldt 2016, Vos contributions) only say "where we could not reproject, like the edge of the screen, we substitute the result from one of the low-res buffers" (`docs/research/horizon-zd-clouds.md:962-967`). The farPlane-aware refinement is the HDRP 17 codification of the same idea — explicit author comment in `VolumetricCloudsDenoising.hlsl:18`: *"Given that the sky is virtually a skybox, we cannot use the motion vector buffer."* Without these three stages, ghosting at sky-cloud silhouettes during camera rotation is unavoidable.

**How to apply:** When designing or reviewing cloud TA in `is.zori.atmospherics`, this is the load-bearing reference. Cite by path:
- Lineage canon: `docs/clouds-pre-nc23-lineage.md:432-453` (§6.1 motion vectors split)
- HDRP 17 motion vectors: `Runtime/Lighting/VolumetricClouds/VolumetricCloudsDenoising.hlsl:18-39` (`EvaluateCloudMotionVectors` with `positionFlag`)
- HDRP 17 sky-only AABB clip: `Runtime/Lighting/VolumetricClouds/VolumetricClouds.compute:96-132`
- HDRP 17 upsample sky-state gating: `Runtime/Lighting/VolumetricClouds/VolumetricClouds.compute:159-162`
- Original (sketch only): HZD SIGGRAPH 2015 page 95 — `docs/research/horizon-zd-clouds.md:962-967`

WickedEngine ships the same direction-only branch but gates it behind `#if 0` (`volumetricCloud_reprojectCS.hlsl:44-57`); UE 5.7 uses camera-only screen velocity for both branches and loses parallax on panning cameras (`VolumetricRenderTarget.usf:212`). HDRP 17 is the canonical implementation.
