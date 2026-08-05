---
name: wasm-defers-never-shapes-io
description: WebGL/wasm support defers to the far end of the roadmap; the IO read path keeps a minimal backend seam but ships exactly one backend
metadata: 
  node_type: memory
  type: project
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T16:06:17.235Z
---

Ruling, 2026-07-20 (refined same session): **wasm support defers to the far end of the
roadmap**, made conditional on whether low-level IO reaches WebGL.

**The condition resolved unexpectedly — record the fact, not the guess.** `AsyncReadManager`
IS compiled into the shipped WebGL player (full binding set registered in
`WebGLSupport_UnityPlayer.CoreModule_Dynamic.a`; `LocalFileSystemWebGL` with positional reads
present; no `#if UNITY_WEBGL` guard in any provisioned package). Wasm is **not** blocked by
API availability. Two open performance questions instead: the WebGL backend shows
`AsyncReadManagerSimple::SyncReadRequest`/`PumpRequests`, suggesting main-thread-pumped rather
than truly async; and StreamingAssets lives in MEMFS, so the whole archive sits in wasm linear
memory — heap size, not IO throughput, is likely the binding constraint. Both are measurable,
neither is a wall. The deferral stands as scheduling, not feasibility.

But the read path still carries a **minimal backend seam** — enough that a future native/Rust
instrumentation (io_uring, DirectStorage-class) or an Emscripten-driven backend drops in
without a rewrite. One backend ships; the seam exists for architecture, not for parity.

Scope of the seam is the **operation**, not the archive model: issue ranged read → poll →
bytes land in native memory. That shape is common to `AsyncReadManager`, a Rust plugin, and
Emscripten fetch, so it is safe to fix early. Handle lifetime and archive *mounting* are NOT
in the seam — abstracting those encodes Unity's `VirtualFileSystem` model and would be wrong
for a backend that does not share it.

**Why:** an interface designed against one implementation is usually the wrong interface;
an interface designed against the shape of the operation survives. Deferring wasm is about
not paying for a second backend now, not about refusing structure.

**How to apply:** do not propose WebGL fallbacks or a shipped second backend. Do keep the
archive format range-addressable (offset table + payload blob) and the read call behind one
narrow seam. Watch the Burst constraint: reads issued from Burst jobs cannot go through
virtual dispatch, so the seam is compile-time (generic constraint / asmdef selection), not a
runtime-polymorphic `interface` in the hot path. Relates to [[terrain-io-packing-streaming]].
