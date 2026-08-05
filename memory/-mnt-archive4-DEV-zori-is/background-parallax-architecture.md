---
name: background-parallax-architecture
description: How the sky/cloud/mountain background follows the streaming camera (scene/parallax.rs)
metadata: 
  node_type: memory
  type: project
  originSessionId: 8e0f94f8-8982-4e2e-bfe3-b64b07659a93
---

Background layers (sky, clouds, mountains, stars) follow the streaming camera via `src/scene/parallax.rs` `ParallaxView`, built once per frame in `Scene::render_impl` from `ca.camera()` (world cells; `#[cfg(streaming)]`, else origin → identity, byte-identical static look).

Design split:
- **NEAR/MID layers (mountains, clouds)** TRANSLATE: a world-cell delta → `cell_px·factor(depth)` device px, **snapped with `round()`** exactly like the CA buffer's `ca_placement_panned` (`round(frac·cell)`) so NEAREST pixel-art never sub-pixel-crawls. `factor = mix(parallax.near, parallax.far, depth)`.
- **FAR layers (sky gradient, stars)** use NORMALIZED `altitude_norm` (0 sea level → 1 at `parallax.space_altitude`), not cell_px translation — zoom-independent. Sky: horizon drops (`u_horizon_shift`), zenith blends → `parallax.space_color`. Stars: daytime fade-in gate `max(night, altitude_norm·star_alt_gain)`.

Altitude = `parallax.sea_level − cam_y` (Y is world-down; up = positive). Clouds are a **world-anchored infinitely-tiled deck**: `cam_x` feeds the `fract` wrap phase over ONE shared span so the band stays contiguous and weather-saturated at ANY world X (never an origin-only patch); vertical = each sprite's world altitude projected to camera altitude → you fly up through the band.

Key tuning fact: clip vertical projection ≈ `2·Δcells·factor/gh` where `gh = css_height/4` (render-scale-stable, since both buffer height and `cell_px` carry `eff = dpr·render.scale`). So cloud band at clip ~0.5 needs `factor≈0.09` (`cloud_depth≈0.94`) with `cloud_altitude≈600`. All knobs live under the `"Parallax"` `params!` section. See [[world-streaming-indirection]], [[render-50pct-pixel-perfect]].
