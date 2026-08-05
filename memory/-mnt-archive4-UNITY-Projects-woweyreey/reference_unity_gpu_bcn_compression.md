---
name: Unity GPU BCn compression via CopyTexture reinterpret (Aras)
description: Reference for how to compute-shader-encode BC1/BC3/BC4/BC7 in Unity — CopyTexture with srcElement/dstElement form bypasses the "width must match" sanity check and reinterprets an R32G32_SInt / R32G32B32A32_SInt block-packed RT as a real BCn texture.
type: reference
originSessionId: 54fcb518-eed1-4c6d-a6e3-73f6941176ce
---
**Repo**: https://github.com/aras-p/UnityGPUTexCompression — MIT sub-components (AMD Compressonator, Microsoft Xbox ATG FastBlockCompress). Verified D3D11 / D3D12 / Vulkan / Metal. Perf: BC3 1280×720 in 0.01–3.1 ms depending on quality tier.

**The mechanism** (four steps):

1. Compute writes BCn **block bits** into a temp 2D RT:
   - BC1 / BC4: `GraphicsFormat.R32G32_SInt` (64 bits/block), dims = dst / 4 each axis.
   - BC3 / BC5 / BC6 / BC7: `GraphicsFormat.R32G32B32A32_SInt` (128 bits/block).
   - `enableRandomWrite = true`.
2. Destination is a real `Texture2D(..., TextureCreationFlags.DontInitializePixels | DontUploadUponCreate)` with `Apply(false, true)` — lives only on GPU.
3. `Graphics.CopyTexture(temp, 0, dst, 0)` — the **srcElement / dstElement form**. This overload skips the "src/dst dimensions must match" check the simple 2-arg form enforces; the GPU reinterprets the raw block bits as BCn.
4. Shader samples `dst` with hardware BCn decoding — free, native.

**Practical encoders to reuse** (live inside the repo under `GPUTexCompression/External/`):
- `AMD_Compressonator` — BC1/BC3 with a quality dial (0..1). Best quality at q=1 but slower (3 ms BC3 720p on 3080 Ti); q=0.8 is the sweet spot (0.01 ms, RMSE 2.82 on BC3).
- `FastBlockCompress` (Microsoft Xbox ATG) — BC1/BC3, fixed quality (~0.01 ms). Lower quality than AMD at q=0.8.

**Other options**: `Betsy` (darksylinc) is GLSL, would need port. ASTC encoders (niepp/astc_encoder, etnlgd/UnityAstcGpuEncoder) exist but are **2D only** and ASTC 3D volumetric formats have minimal GPU support (not on Deck RDNA2).

**For 3D textures**:
- Easiest: encode per-Z-slice into a BC1 / BC4 `Texture2DArray`. Shader samples with manual trilinear (two slice taps + Z lerp).
- Alternative: Unity's newer releases support `Texture3D` with BC format — runtime creation + `CopyTexture` with 3D element handling is viable but less-trodden; Deck/Vulkan verify before committing.

**How to apply**: whenever a live-baked texture (3D LUT, compressed SDF, animated noise cache, etc.) needs GPU compression, clone the encoder + the CopyTexture trick from Aras's repo. Don't write a new BCn encoder from scratch — the MIT code is production-ready and the Unity-integration step is ~50 lines.
