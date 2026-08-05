---
name: Compression routing is per-format, not a boolean opt-in
description: When adding GPU runtime texture compression (BCn / ASTC / etc.), route via the per-layer/per-resource graphics format — NOT a global `compressionEnabled` boolean.
type: feedback
originSessionId: 5d54216a-759a-4009-b5a2-db6b9153927e
---
When designing GPU compression integration (BCn via aras-p path,
ASTC via etnlgd encoder, future formats), do NOT add a top-level
descriptor boolean like `bcCompressionEnabled` that gates the whole
encode pipeline.

**Why:** the choice of graphics format already declares intent. A layer
configured with `RGBA_DXT5_UNorm` can ONLY be written via BC encode —
direct compute random-write to a BC texture isn't possible. So the
boolean is redundant: the format IS the opt-in. A boolean adds a hidden
failure mode (BC format + flag off = silently broken pool) and
complicates extension to more formats (would need
`astcCompressionEnabled`, `bc7CompressionEnabled`, …).

Original direction came up while implementing AVT Wave 6.5 (BC encoder
port). Handoff doc proposed `desc.bcCompressionEnabled = true` as a
Deck-profile kill-switch. Pivoted on user direction (2026-04-28) to:

- Per-layer routing: `IsBcFormat(layer.format) && !layer.skipBcCompression`.
- `skipBcCompression` is a per-layer override for the rare case where a
  layer's format is BC but the engineer wants to test the direct path
  (or skip compression for displacement / mask-blend layers where
  artefacts are visible).
- Future ASTC support adds an `IsAstcFormat()` branch in the same
  router; no new descriptor flag.

**How to apply:** when a future task asks you to add a `<scheme>Enabled`
boolean to a descriptor for a runtime compression scheme, push back —
infer from the resource's graphics format instead. The only legitimate
boolean is a per-resource OPT-OUT (skip flag).

**Reference paths:**
- `aras-p/UnityGPUTexCompression` — BC1/BC3 + AMD Compressonator helpers (BC4/BC5).
- `etnlgd/UnityAstcGpuEncoder` — ASTC GPU encoder.
- Project memory `reference_unity_gpu_bcn_compression.md` for the Unity
  CopyTexture-reinterpret mechanism.
