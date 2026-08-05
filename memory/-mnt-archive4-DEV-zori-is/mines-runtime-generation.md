---
name: mines-runtime-generation
description: "Full Noita Mines biome generates per-chunk in the browser via the emscripten world-gen module seam (~134ms/chunk perf flag)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 972828aa-cf5a-4bb9-9c27-7f98f2a0daf6
---

The full Noita "Mines" biome generates per-chunk in the BROWSER. The generator `crates/formation/src/mines.rs::generate_chunk_mines(seed, cx, cy)` (wang caves + BitmapCaves + material distribution + set-pieces + veg + moss + shade, 512×512, byte-equal to the CLI `world --noita` `paint_noita` pipeline) lives INSIDE the emscripten `zori_noise` module — it links FastNoise2's C++, which can't link into the app's shared-memory wasm. Flow: `gen-worker.js` calls the module's `generate_world_chunk(seed,cx,cy)` C-ABI seam (`crates/zori_noise/src/native.rs`) → compact 2-byte `[material,shade]` cells → main-wasm `stream_repack_world_chunk` (`seeding.rs`) expands to the feature-derived `CELL_BYTES` store stride (dev=3, material@CH_MATERIAL/shade@CH_SHADE). The main app wasm links NO formation/FastNoise2 (symbol-scan verified); the old `formation-gen` feature is GONE. The generator is filesystem-free via `crates/formation/src/embed.rs` (`include_bytes!`/`include_str!` the defaults.json config + wang atlas + set-piece PNGs; embedded-first, disk-fallback so the native CLI is identical). `formation` + `zori_noise` share the `api-haus/fastnoise2` fork. Rebuild the module with `build-noise.sh` (needs emcc; emcc 4.0.23 works); committed at `public/noise/zori_noise.{js,wasm}`.

Streaming determinism (a chunk is identical regardless of neighbor residency): generated over a 1-macro (64px) halo, 512² centre cropped. Two load-bearing fixes: (1) wang herringbone re-addressed by pure hashes of ABSOLUTE lattice coords (`wang::generate_window`, corner mode) not a scan-order RNG at the region origin; (2) all noise sampled over a FIXED 64px global tile lattice (`mat_noise::gen_grid_global`) so a world pixel's coord is bit-identical across windows (FastNoise2 `fma` was last-ULP window-origin dependent). Verify with `formation stream-check` (also fs-free). Module material histogram (proof it's the composite, not the old socket world): VOID 52%, ROCK_WET 24%, MOSS 9%, EARTH 6%, STONE 5%, COAL 3%.

PERF FLAG: ~134ms/chunk (emcc -O3) — above the ~100ms streaming budget; off the CA critical path but a fast pan outruns it (~7-8 chunks/s per gen-worker → pop-in). Reduction candidates: cache the parsed wang tileset across chunks (likely the big cost — parsed per-chunk today), shrink the moss SDF, coarsen the halo. NOT yet optimized.

Render colours come from [[app-render-palette-vs-registry]]; a headless native preview of a Mines chunk through the real palette is `formation chunk-rg8` → the app's `ca_preview` bin ([[render-backend-first-class]]).
