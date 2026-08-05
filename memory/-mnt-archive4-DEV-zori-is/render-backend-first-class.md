---
name: render-backend-first-class
description: "Render layer runs on glow (backend-agnostic): browser=WebGL2, native=EGL surfaceless GLES3 for headless previews/validation"
metadata: 
  node_type: memory
  type: project
  originSessionId: 972828aa-cf5a-4bb9-9c27-7f98f2a0daf6
---

The render layer (`src/gl/*`, `src/scene/*`) is backend-agnostic via the **`glow`** crate (0.16) — one GL API that is WebGL2 on wasm and native GL off it. The BACKEND is just how the single `glow::Context` is obtained (`src/gl/backend.rs`):
- Browser (unchanged production/benchmark/consumer path): `lib.rs::start` makes the canvas `WebGl2RenderingContext` as before; `Scene::new` wraps it with `glow::Context::from_webgl2_context`, and retains the raw handle in a thread-local `WEB_CTX` for the few things glow can't do — `get_extension` (EXT_color_buffer_float), HtmlImage texture upload, `drawing_buffer_width/height`, and the GPU timer (`gl/timer.rs`, EXT_disjoint_timer_query, kept `cfg(wasm)`).
- Native (headless): `backend::headless()` → EGL surfaceless GLES3 (`EGL_PLATFORM_SURFACELESS_MESA`, `EGL_OPENGL_ES3_BIT`, `CONTEXT_MAJOR_VERSION=3`, `EGL_NO_SURFACE`) + `from_loader_function`. GLES3 (not desktop GL) so `#version 300 es` shaders compile verbatim = same as WebGL2. Native deps (`khronos-egl`, `image`) are under `[target.'cfg(not(target_arch="wasm32"))'.dependencies]`.

The app runs natively in a LIMITED SUBSET for headless render/preview/validation: `gl` + `world` + `scene::{adaptive,ca,clock,present,variant,palette_gen}` compile for both targets; the `Scene` orchestrator, background passes, and `app/ca(sim)/events/input/prof/weather/…` are `cfg(target_arch="wasm32")` (sim workers, benchmarks, control-server, SharedArrayBuffer stay browser-only). `CaPass` is sim-decoupled via `upload_cells`. Error type across gl/+scene/ is `String` (glow's), not `JsValue`.

Headless preview bin: `cargo run --bin ca_preview -- <out.png> [gw] [gh] [chunk.rg8]` (`src/render_native.rs`) renders a chunk's `[material,shade]` cells through the REAL `ca.frag` + `palette.bin` over EGL, JFA/reflect OFF (flat albedo), → PNG. This KILLS the preview↔app colour divergence (previews now use the exact app renderer). Pipe a real Mines chunk in: `formation chunk-rg8 --out x.rg8` → `ca_preview y.png 512 512 x.rg8`. Docs: `docs/rendering-backend.md`.

Gotchas: `packed` is a RESERVED keyword in GLSL ES 3.00 — WebGL2's translator tolerated it but native NVIDIA GLES rejects it; a local was renamed `cell_packed` in ca.frag. The web render path is NOT browser-verifiable headlessly — confidence rests on glow-over-WebGL2 emitting identical calls + the native render being correct; a human must eyeball the browser once.

The flat headless preview of the Mines exposed that the app's per-cell `hash_shade` (white noise) × the wide Aurora ramp reads as harsh speckle for solid rock (fine for granular sand). Tightening the ramp only darkens it — the real fix (if wanted) is a spatially-coherent shade in `fill_shade`, or judge it with the live JFA lighting first (the preview has lighting OFF). See [[app-render-palette-vs-registry]].
