---
name: render-50pct-pixel-perfect
description: zori.is renders at 50% scale; CA/particle pixel buffer is integer-cell pixel-perfect — smooth controls must respect this
metadata: 
  node_type: memory
  type: reference
  originSessionId: 21a33eda-7a37-47f2-adfe-5c96353bd554
---

zori.is ALWAYS renders the CA/particle pixel buffer at reduced resolution and keeps it pixel-perfect on all displays. Chain (confirmed in `docs/orchestrate/world-streaming/05-render-and-controls.md`):

- Canvas backing store = `css · dpr · render.scale`; `render.scale = 0.5`, `render.ca_cell_px = 4` (defaults.json). `Scene.dpr` actually holds `dpr·scale`, not raw DPR (`src/lib.rs` resize).
- `cell_px p = round(ca_cell_px · dpr · scale)` — INTEGER device px per cell (2 at defaults); the grid cell count is scale-invariant (`css/ca_cell_px`).
- CA grid is an `RG8UI` NEAREST texture; particles overwrite texels in the same texture; `SafeArea::ca_placement` (`src/safe_area.rs`) magnifies texel→device px via a `gw*p` draw viewport pinned to the safe-rect floor; `ca.frag` does the single Y-flip + `texelFetch`; browser upscales backing→CSS by `1/(dpr·scale)`.
- Input inverts the IDENTICAL `ca_placement` map (`src/input/mod.rs` paint_at) — the one shared forward/inverse mapping any control code must reuse, or input and render drift.

**Implication for smooth controls:** pixel-perfect ⇒ `p` stays integer. Smooth pan = whole-DEVICE-pixel texture offset (a fractional-cell camera offset rendered as `round(frac·p)` device px via a `u_cell_offset` uniform in placement + ca.frag + particle.vert). Smooth zoom = fractional magnification DURING the gesture, snapping to an integer `p` level at rest. Smallest pixel-perfect step under NEAREST at scale 0.5 is one backing device px (~2 CSS px). Related: [[world-streaming-indirection]].
