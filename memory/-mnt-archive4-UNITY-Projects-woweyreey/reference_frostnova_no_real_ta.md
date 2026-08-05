---
name: Frostnova has no real temporal upscaling
description: CIS-5650 Frostnova nubis2/3 repo is NOT a TA reference — reproject.comp is a passthrough, all jitter/pixelOffset is commented out
type: reference
originSessionId: 923618bb-612d-44a8-84e5-6ba48d88b5a6
---
`github.com/YueZhang1027/CIS5650-Final-Project-Frostnova` is a student project. Despite the README's "temporal upscaling 30-70% FPS" claim, the actual code:

- `src/shaders/reproject.comp` falls through to `imageLoad → imageStore` straight copy. The intersection + UV-back-projection is commented out.
- Every `// TODO: Jitter` and `// 1/16 of the pixels after reproject compute shader` line is dead code in `compute.comp`, `farCloud.comp`, `nearCloud.comp`, `computeNubisCubed.comp`.
- Their actual perf gain is: lightGrid precompute (256×256×32) + adaptive `sqrt(distance)*0.08` step + near/far raymarch split at 500 m. Not temporal.

**Why:** Avoid spending time looking up Frostnova for cloud TA / reprojection / jitter pattern learnings — there's nothing implemented to study. HDRP 17 + WE/HZD/Schneider PDFs remain the canonical refs.

**How to apply:** If asked to "reference Frostnova" for cloud temporal work, push back with this. Their cloud lighting + adaptive raymarch is real and worth reading; the temporal pipeline is not.
