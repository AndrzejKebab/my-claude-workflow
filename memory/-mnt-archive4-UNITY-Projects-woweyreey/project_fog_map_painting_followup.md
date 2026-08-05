---
name: FogMap painting tool — follow-up
description: Build an in-editor texture-paint tool for the FogMap component that lets artists author RGB profile maps (start altitude / falloff / peak σ_t) directly without leaving Unity.
type: project
originSessionId: c11e6dba-4be9-410f-a722-120ea6ace681
---
The `FogMap` component (Bauer 2019 slide 20) ships at the populate-kernel level on branch `gcb` (atmospherics submodule), reading a Texture2D whose RGB channels encode a per-texel vertical density profile in box-local Y normalised space:

- **R** = start altitude [0, 1] from bottom face
- **G** = falloff distance (e⁻¹ per local-Y unit)
- **B** = peak σ_t (m⁻¹) at start altitude

**Why follow-up:** Authoring this RGB encoding in an external paint program (Photoshop / Substance) is awkward — each channel has a distinct physical meaning, so the artist can't preview the result without round-tripping through Unity. An in-editor brush tool that paints directly into the texture (one channel at a time, with a live volumetric preview) collapses that loop.

**How to apply:**
- Implement as a Unity editor brush overlay, similar to terrain painting. Brush size, hardness, channel selector (R/G/B).
- Live preview by rebinding the painted texture immediately so the artist sees the box's σ_t change as they paint.
- Per-channel value pickers anchored to the same physical scale as the runtime (Koschmieder-anchored σ_t for B, [0,1] normalised for R/G).
- Save as standard Texture2D `.png` / `.exr` so the asset is portable; user noted "we'll implement a painting feature" as a follow-up (2026-05-03).

User confirmed that respecting the RGB encoding is correct — the texture is Bauer's canonical encoding, not a per-texel sigma scalar. Painting is the UX gap, not the encoding choice.
