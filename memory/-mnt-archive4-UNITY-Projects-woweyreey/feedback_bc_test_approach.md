---
name: BC encoder tests use PSNR + cross-slot mean-colour isolation, not SSIM
description: For runtime BC encode/decode validation, the canonical approach is per-channel PSNR (≥35 dB floor) on a HW-decode roundtrip plus mean-colour cross-slot checks for sub-rect bugs. SSIM is overkill for "did the encoder produce correct block bits".
type: feedback
originSessionId: 86e0a47d-8436-4c93-8163-753a8131b65b
---
For BC encoder testing in this project, use:

1. **Per-pathway PSNR roundtrip:** known pattern → SetPixels → encode → Graphics.Blit through HW BC decoder → AsyncGPUReadback → channel-aware MSE → 20·log10(1/√MSE). Floor 35 dB (Ka Chen slide 49 "no visible compression error"; aras-p reports ~39 dB at q=0.8 so 4 dB headroom).

2. **Multi-slot pool isolation:** solid colours per slot → assert mean decoded colour matches its source within 0.05 per channel AND L1-distance > 0.5 from every other slot's source. Catches sub-rect CopyTexture bugs where every slot lands the same blocks (off-by-row, off-by-column).

**Why not SSIM:** PSNR is what aras-p / AMD Compressonator publish RMSE numbers in (apples-to-apples). BC artifacts are mostly per-block quantization noise where PSNR is well-behaved; SSIM matters more for perceptual edge-blocking which isn't what the encoder gate is about.

**How to apply:** when adding a new BC pathway test, drive it through the same `RWVTBcHarness.Encode + DecodeSlotToRgba8 + PsnrDb` pattern. User approved this approach 2026-04-28.
