---
name: Blitter.BlitTexture does not update _BlitTexture_TexelSize — use SV_Position
description: URP Blitter sets _BlitTexture via MaterialPropertyBlock but never touches _BlitTexture_TexelSize. Reading `screenUV * _BlitTexture_TexelSize.zw` in a Blit fragment shader silently returns stale dimensions from a previous draw and produces mostly-black output.
type: feedback
originSessionId: 1baef162-42d5-4a70-98b2-2f510e96fa21
---
**Rule:** When writing a fragment shader that runs under `Blitter.BlitTexture` / `Blitter.BlitCameraTexture` and needs the destination pixel coordinate, read it from **`input.positionCS.xy`** (SV_Position), not from `screenUV * _BlitTexture_TexelSize.zw`.

**Why:** URP's `Blitter.BlitTexture` sets only two things on the draw:
- `_BlitTexture` (via MaterialPropertyBlock)
- `_BlitScaleBias` (via MaterialPropertyBlock)

It never updates the `_BlitTexture_TexelSize` uniform that Blit.hlsl declares at global scope. That uniform keeps whatever value the engine's last texture bind set — typically the camera color buffer's size. Your 32x32 LUT bake then computes pixel coords using (e.g.) 1920x1080, maps most fragments outside the valid index range, and the whole LUT comes out black with a thin strip of bright pixels along one edge. No compile error, no warning.

This bit jiaozi158's pattern in our project. Their shaders only read `_BlitTexture_TexelSize.zw` — works in their project (maybe because their blit destinations happen to be camera-sized or their _BlitTexture_TexelSize gets set somewhere else in HDRP-derived code), but **does not work when you're using URP's core Blitter with a fixed-size LUT**.

**How to apply:**
- In Blit fragment shaders, write `uint2 coord = uint2(input.positionCS.xy);` and pass it as a parameter to any helper — don't rely on `_BlitTexture_TexelSize`.
- The diagnostic signature is: "LUT texture shows black with a thin bright strip on one side". First thing to check when precomputed LUTs look wrong.
- If you genuinely need source texture dimensions inside a Blit fragment (e.g. for source sampling), bind them explicitly: pass them via `Material.SetVector` on the LUT material before the blit.
