---
name: Motion-scaled history dilution is the canonical cloud anti-blur (canon §9.2)
description: Cloud TA blur under camera motion is fixed by Karis 2014 slide 45 motion-scaled history dilution — halve effective accumulation window above ~5% screen reprojection shift. NOT by sharper history kernel.
type: feedback
originSessionId: 8178fcec-4e8a-4bdf-a212-3f0af31f5657
---
When the user reports cloud blur growing with camera motion, the canonical fix is motion-scaled history dilution (Karis 2014 slide 45), not a sharper history sample kernel. Cloud Pass 1 history sample stays bilinear (`feedback_pass1_history_sample_bilinear.md`).

```hlsl
float reprojectShiftPixels = length((prevUV - currUV) * _ScreenSize.xy) / _ScreenSize.x;
float motionFactor         = saturate(reprojectShiftPixels / 0.05);   // 0.05 ≈ 5% screen
accumulationFactor        *= 1.0 - _MotionHistoryDilution * motionFactor;
```

Defaults: `_MotionHistoryDilution = 0.5` (`docs/clouds-pre-nc23-lineage.md` §13.2 ghosting panel default). Range 0–1.

**Why:** the bilinear cascade per-frame in Pass 1 is the source of motion blur (each resample is an O(√N) box low-pass, blur grows with frames spent in motion). Sharpening kernels can't fix this — they only mask one resample, not the cascade. The canon fix is to **drain** the history faster under motion: halve the effective accumulation window when motion exceeds ~5% screen, paying a small amount of trace noise *during* the motion (perceptually masked by the motion itself) instead of carrying ghost-blur for ~16 frames after motion stops.

HDRP 17 composes the equivalent via `accumulationFactor *= _TemporalAccumulationFactor * validityFactor * _CloudHistoryInvalidation` at `VolumetricClouds.compute:150`. The `_TemporalAccumulationFactor` carries the motion dilution.

**How to apply:**
- Compose blend weight as `accumulationFactor × validityFactor × motionDilution × _CloudHistoryInvalidation` (HDRP 17 pattern — single product, multiply on top of N/(N+1) ramp).
- Expose `motionHistoryDilution` and `historySampleCap` (N_max) as consumer knobs per §13.2 ghosting panel.
- Sanity-check via the existing `ReprojectionShift` debug mode — magnitude there is the input to `motionFactor`.
