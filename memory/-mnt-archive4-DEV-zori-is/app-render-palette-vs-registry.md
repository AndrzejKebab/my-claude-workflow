---
name: app-render-palette-vs-registry
description: "The live app render palette is procedural — derived from the registry base colours by a Python/OKLab tool, not hand-authored"
metadata: 
  node_type: memory
  type: project
  originSessionId: 972828aa-cf5a-4bb9-9c27-7f98f2a0daf6
---

The streaming renderer's material colours are PROCEDURAL, derived from the single registry base colour per material (`materials::MATERIAL_COLORS`) — nothing hand-typed in Rust or the shader. See `docs/world-gen/PALETTE.md`.

Each material is a 256-step colour ramp indexed by the cell shade byte. DEFAULT is `hue_lock: true` (in `palette.yaml`): constant hue+chroma per material, only LIGHTNESS varies across a lifted band (`spread_up`>`spread_dn` since Noita bases are dark; `rock_wet`/`stone` lifted further). This is REQUIRED for readability — the shade byte is per-cell spatial noise, so a hue-DRIFTING ramp renders solid material bodies as unreadable chromatic confetti (the bug that broke the Mines look). An Aurora hue-family mode (`hue_lock: false` + `tools/palette/aurora.json`, pulls the base's hue family from Aurora and rides its drift) exists but is OFF for exactly that reason. Pipeline: `crates/materials` base RGB → `cargo run -p materials --bin registry_json` + `aurora.json` → `tools/palette/build_palette.py` reads `tools/palette/palette.yaml` (global hue_tol/spread/chroma_mul + per-material overrides) → emits `src/scene/palette.bin` (raw linear-RGBA f32, row=material, 256 cols=shade) + `src/scene/palette_gen.rs` (dims + `PALETTE_EMISSIVE_MASK`, `include_bytes!`s the .bin) + `palette.gen.json` mirror + `preview.svg`. `scene/ca.rs build_palette` parses the .bin → 256×COUNT RGBA32F texture; `ca.frag` does ONE `texelFetch(u_palette, ivec2(shade, mat))` — the shade byte indexes the curve directly. Emitter rows flagged by `PALETTE_EMISSIVE_MASK` (u32 bitmask, ≤32 materials), not magnitude.

Retune: edit `palette.yaml`, rerun the tool, commit the regenerated `palette_gen.rs`. Adding a material to the registry + rerunning is all that's needed to give it a colour. Colours are NO LONGER live-tunable from the dev panel (the ~48 `ca_*_light/dark/emissive/alpha` World params were deleted, along with their defaults.json keys). JFA emitter tints (`scene/jfa.rs`) read `materials::color(id)` directly (registry base), not the palette.

Reaching a material in-app:
- Paint brush caps at 16 (GLASS): `input/mod.rs` `clamp(1,16)` + `world/mod.rs` `intk(1,16)`.
- The full Noita Mines biome generates per-chunk in the browser via the emscripten module's `generate_world_chunk` seam — see [[mines-runtime-generation]]. Headless preview of a Mines chunk through this exact palette: `formation chunk-rg8` → `ca_preview` ([[render-backend-first-class]]).
