---
name: cloud-depth uses HDRP projective inverse-z encoding
description: Cloud-trace depth stored as EncodeInfiniteDepth(saturate(near/depth)) in [0,1] R16_SFloat — sky sentinel = encoded 0, decoded distance hard-capped at 35km
type: feedback
originSessionId: 8178fcec-4e8a-4bdf-a212-3f0af31f5657
---
Cloud trace depth (`_CloudsTraceDepth` R-channel + status texture `.z` channel for accumulated `finalCloudDepth`) MUST be stored in **HDRP-style projective inverse-z encoding**, not raw linear metres. Sky sentinel = encoded `0`, near = encoded `1`.

```hlsl
// From com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl:1288-1297
float EncodeInfiniteDepth(float depth, float near) { return saturate(near / depth); }
float DecodeInfiniteDepth(float z, float near)     { return near / max(z, FLT_EPS); }
```

**Constants** (defined in `ZoriVolumetricClouds.shader` HLSLPROGRAM blocks of Pass 0/1/2):
- `CLOUD_DEVICE_NEAR = 100.0` — near-plane analogue for the projective encode.
- `CLOUD_DEVICE_FAR = 35000.0` — hard cap at decode time. Bounds visible cloud layer; independent of camera far-plane.
- `CLOUD_SKY_THRESHOLD = 1e-3` — sky-detection threshold; encoded-zero with epsilon guard.

**Encoding/decoding boundaries:**
- **Encode at** `Pass 0` MRT write: `o.depth = EncodeInfiniteDepth(cloudFrontDist, CLOUD_DEVICE_NEAR)` — raymarch core stays in linear-metre space (`cloudFrontDist = 1e10` for no-hit, `traveled` for hit).
- **Decode at** Pass 2 entry boundary (right after `UpsampleCloud`): `cloudDistLinear = min(DecodeInfiniteDepth(cloudDist, CLOUD_DEVICE_NEAR), CLOUD_DEVICE_FAR)` — fog/AP consumers need physical metres.
- **Decode in** Pass 1 depth-trust ratio: physical-metre subtraction is the meaningful quantity for history modulation.
- **Decode in** Pass 1 `anchorDist` reconstruction (for `worldPos = ro + rd * anchorDist`).

**Sky-detection comparisons** are all `<= CLOUD_SKY_THRESHOLD` (encoded ≈ 0), never `>= farPlane * 0.999`.

**Why:** R16_SFloat overflows above 65504, so storing raw linear distances against a `_ProjectionParams.z` of 100k+ silently produces `+Inf` in the texture. Comparisons "happened to work" by IEEE Inf semantics but the round-trip was unreliable — the SkyTapCount and CloudDepth debug overlays appeared pure black on sky pixels, evidence the encoded depth wasn't surviving Pass 1→Pass 2. Projective inverse-z in `[0, 1]` is exact representable in half-float, sky pixels stay at exact 0, near pixels get fine quantization (perceptually uniform), and there is no overflow path. Independence from `_ProjectionParams.z` means cameras with 600k far-planes Just Work.

**How to apply:** when adding any new cloud-depth touchpoint:
- Reading from trace-depth or status `.z` → value is encoded; decode if you need physical metres.
- Writing to either → encode if you have physical metres.
- Sky test → `<= CLOUD_SKY_THRESHOLD`, not far-plane comparison.
- Weighted blends (`finalCloudDepth = lerp(...)`) stay in encoded space — averaging encoded values keeps sky pixels stable at 0 and history convergence monotonic. HDRP does the same.

Untouched (deliberately): `_CloudShadowmap` (DistantShadows ESM, separate system), scene-depth status `.y` channel (`UNITY_RAW_FAR_CLIP_VALUE`-encoded, native Unity).
