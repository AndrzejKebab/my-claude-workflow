---
name: Physically-based scattering LUTs need R16F_SFloat (half) or higher, not B10G11R11
description: B10G11R11_UFloatPack32 cannot represent the tiny values produced by Earth-scale Rayleigh/Mie integrals — the green-channel min positive is ~6e-5, the blue channel's is ~1.2e-4, and scattering radiance ends up below both. LUTs blacken silently with no compile error
type: feedback
originSessionId: 1baef162-42d5-4a70-98b2-2f510e96fa21
---
**Rule:** Physically-based scattering / atmosphere / volumetric LUTs in this project use **`GraphicsFormat.R16G16B16A16_SFloat`** (half-float, min positive ~6e-8, signed). Do not use `B10G11R11_UFloatPack32` for these — even though HDRP defaults to it, it silently fails for URP-scale sun/light inputs.

**Why:** Earth Rayleigh scattering coefficients are ~5e-6/m, multiplied by an 8 km air scale height (~0.04), phase function (~0.08), and transmittance (~0.9), then summed over 16–64 ray samples — final LUT cell values land around 1e-5 to 1e-4. The B channel of `B10G11R11_UFloatPack32` cannot represent values below ~1.2e-4 (its smallest normal positive is 2^-14 ≈ 6.1e-5 for the 11-bit mantissa; the 10-bit blue is worse), so every cell rounds to zero and the whole precompute pipeline (MultiScattering → InScatter → SkyView → sky draw) blackens silently. HDRP compensates by feeding in physically-scaled sun luminance (thousands of lumens) which shifts the values up; URP uses `Light.finalColor` which is ~(1,1,1) and never reaches that range.

**How to apply:** When porting HDRP / HDRP-derived precomputed-atmosphere code to URP, swap `s_ColorFormat` for `R16G16B16A16_SFloat` on every LUT allocation. If you ever need to compare with HDRP results bit-for-bit, keep a flag to toggle back to `B10G11R11`, but default to half-float. Test it by screenshotting one LUT early — "black with a thin bright strip" is the diagnostic signature of this bug.
