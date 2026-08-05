---
name: Shadow upsample must preserve sharp edges
description: When upsampling shadow/occlusion signals without TAA downstream, pick UE-style bilinear+nearest-depth (no bilinear across depth edges, no Catmull-Rom, no stochastic). Shadows are high-contrast near-binary signals — soft edges look wrong.
type: feedback
originSessionId: d0a4a271-7038-4597-bd97-a2f1165a3a76
---
When upsampling a low-res shadow/occlusion term (SSS compose, ambient occlusion, contact shadows, etc.) to full res:

- **Flat neighborhoods** → plain bilinear is fine.
- **Depth edges** → **nearest-depth pick** (UE-style). Sample 4 low-res depths around the full-res pixel, pick the shadow sample whose depth is closest to the full-res depth. No weighted blending, no bilateral smoothing.

**Do NOT** use:
- Catmull-Rom — banned per `feedback_catmull_rom_edge_halo.md` (negative lobes → dark halo).
- Stochastic (pixelmager-style) — requires TAA downstream to clean up the noise. Without TAA, shows as persistent dither on the shadow term.
- Bilateral Gaussian blending at depth edges — blurs the shadow silhouette.

**Why:** Shadows are high-contrast near-binary signals. Any soft blending across a depth discontinuity puts partial-shadow values on pixels that should be fully lit or fully shadowed — visibly wrong, looks like a halo or ghost around silhouettes.

**How to apply:** Any upsample that produces a shadow/occlusion output and does not feed TAA. The target reference is `docs/research/cbr-ta-upsampling-cross-engine.md:196-207` (UE's bilinear + nearest-depth 2-mode upsampler). Same reasoning applies to SSAO / screen-space contact shadow / cloud shadow projection terms.
