---
name: wasm-bindgen-js-module-duplicate-instance
description: A JS module imported by both a wasm-bindgen extern and app JS gets TWO Vite instances — module-level state desyncs; use a globalThis singleton
metadata: 
  node_type: memory
  type: reference
  originSessionId: 21a33eda-7a37-47f2-adfe-5c96353bd554
---

zori.is gotcha (cost a long debug): a JS file imported BOTH by a `#[wasm_bindgen(module = "/src/web/foo.js")]` extern (lands in gen/zori.js as an absolute import) AND by app JS (`./foo.js` from src/web) resolves to **two different module instances on the main thread under Vite** (the generated import specifier differs from the relative one). So any module-level `let state` is per-instance: app JS sets instance A, the Rust extern reads instance B (null) → the extern's calls silently no-op.

**Symptom seen:** OPFS chunk persistence dead — `streamIoSave/Load` hit `if (!ioWorker) return` because `initStreamIo` (boot.js) set instance `5dqjv` but the Rust extern called instance `quext`. Confirmed by logging `Math.random()` per module load (5 instances: 2 sim workers + io-worker + main-gen + boot).

**Fix:** put ALL mutable shared state on a `globalThis` singleton every instance references: `const S = (globalThis.__zoriStreamIoState ||= {...})`. Worker realms get their own (harmless — they don't use it). See `src/web/stream-io.js`.

**How to diagnose fast:** when a Rust→JS extern call appears to no-op, log a per-instance id at module top + in the setter + at the call site; mismatched ids = duplicate instances. Drive the repro with the e2e harness (`tests/streaming.spec.js` oracle: paint→pan→save→load→assert byte-identity) — its stats readout (`__zoriStreamIo.stats()`: saves/loads/hits) localizes the failing stage. [[benchmarks-in-app-e2e-on-device]]
