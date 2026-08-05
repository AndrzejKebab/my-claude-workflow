---
name: Cloud accumulation cap is 16 frames (canon §9) — not a tier knob
description: Canon §9 N/(N+1) accumulation capped at 16/17 ≈ 94 % — constant across all tiers and not user-tunable. The artistic knob is a single _TemporalBlendFactor scalar on top of the canonical factor (default 1.0).
type: feedback
originSessionId: 726c4158-973f-4d34-8c33-a1c331c299e5
---
Cloud reprojection uses canon §9's `accumulationFactor = prevN / (prevN + 1)` capped at `16/17 ≈ 0.941`, with `newN = min(prevN + 1, 16)`. This is a **constant of the pipeline shape**, not a tier knob. Tiers vary only `RayMarchSteps` and `SunTapCount`.

**Why:** 16-frame running mean matches cloud temporal coherence (clouds change slowly; 16 frames ≈ 0.27 s @ 60 Hz, well below the scale at which density animates). Shorter windows re-pump per-frame noise; longer windows accumulate stale history against real cloud motion. 16 is the value HDRP / UE / HZD all ship.

**How to apply:**
- In Pass 1 FragReproject: `float accumulationFactor = min(prevSampleCount / max(prevSampleCount + 1.0, 1.0), 16.0/17.0); accumulationFactor *= _TemporalBlendFactor; float newN = min(prevSampleCount + 1.0, 16.0);`
- In `CloudQualitySpec` / `CloudSettings`: no `accumulationFrames` field, no `_CloudAccumulationFramesMax` uniform. The artistic knob exposed to presets is `temporalBlendFactor` (0..1, default 1) — lerps the whole factor so artists can drain history faster for debug / freeze-frame work. Warmup for tests is a fixed 32 frames.
- Apply the same formula to every intermediate pixel every frame — no owner / non-owner split (canon drops the HDRP-style owner-only blend because the AABB clamp is strong enough to handle the variance).

Supersedes the pre-2026-04-24 rule that `accumulationFrames` was a per-tier settings knob pinned at 8.
