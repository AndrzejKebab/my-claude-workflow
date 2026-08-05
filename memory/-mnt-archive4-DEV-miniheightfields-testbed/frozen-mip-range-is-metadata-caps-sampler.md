---
name: frozen-mip-range-is-metadata-caps-sampler
description: A frozen VT archive records its exact mip range as metadata; the fringe/sampler is capped to that range so it never oversamples past the finest frozen mip; basemap/surface fade stays a consumer choice
metadata: 
  node_type: memory
  type: project
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T21:09:09.520Z
---

Ruling, 2026-07-21, on frozen VT sampling. Frozen mode is a **content-delivery mechanism**
carrying a selection of mips or all mips.

1. **The exact mip range is archive metadata.** finest and coarsest mip are recorded explicitly
   in the archive header, not inferred from the key table. This is the authoritative contract for
   what the archive provides.

2. **The sampler is capped to that range.** The LOD-fringe lookup (and any VT lookup in frozen
   mode) must clamp its query mip to the archive's range so it never asks for a tile finer than
   the finest frozen mip. Oversampling past the finest mip is the presumed cause of the white
   innermost ring — the fringe reaches into a tier the archive does not carry. Admission was
   already floored (`VTDescriptor.minMipLevel`); the **sampler** must be floored the same way,
   which admission alone does not do.

3. **Basemap / surface fade is entirely the consumer's choice.** Frozen mode must NOT force the
   basemap cache on (an earlier idea, rejected). Whether the near field composites splats or
   samples a cached surface is `basemapFadeStart`/`basemapFadeRange` on the controller — consumer
   policy, untouched by freezing.

**How to apply:** thread the archive's finest mip to the fringe shader as a uniform and clamp the
query there; record finest+coarsest in the header (format bump). Do not touch the fade. Confirm the
white ring resolves by test — the mechanism is presumed, not proven. Relates to
[[freeze-is-all-or-nothing]] and [[editor-decides-player-executes]].
