---
name: benchmarks-in-app-e2e-on-device
description: "Perf claims must come from in-app e2e benchmarks runnable on iPhone/Android, never native microbenches"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 21a33eda-7a37-47f2-adfe-5c96353bd554
---

Any performance claim for zori.is must be measured through an **in-app e2e benchmark pathway** (control signal in → real app tick → metric out) that is **runnable on the target devices: iPhone and Android** — and also locally. A native `rustc -O` microbench is not acceptable as the project's benchmark: it measures the wrong target (desktop native, not wasm-on-device) and its numbers don't derive from the real code path.

**Why:** mobile wasm perf (LPDDR bandwidth shared with GPU compositor, `memory.copy` 1.5–2× native, thermal/core-migration jitter) is what decides feasibility, and desktop native numbers mislead. Aligns with the black-box harness rule [[blackbox-test-harness]].

**How to apply:** when a decision hinges on perf, build/extend an in-app benchmark behind the e2e harness and report device numbers; use native microbenches only as throwaway order-of-magnitude aids and then discard them (don't commit them as tools).
