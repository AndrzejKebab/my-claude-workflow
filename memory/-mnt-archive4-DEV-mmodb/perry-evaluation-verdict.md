---
name: perry-evaluation-verdict
description: Perry AOT evaluation concluded — not viable for TS compute acceleration; decision to write STDB modules in Rust
metadata: 
  node_type: memory
  type: project
  originSessionId: aea09554-06cb-4159-8ed3-3f85edd930fd
---

The Perry AOT evaluation is complete (2026-06-01). Three-way E2E benchmark (Rust vs Perry vs V8) on stock SpacetimeDB v2.0.1 proved Perry cannot accelerate TypeScript compute workloads — V8's TurboFan is within 6% of native Rust wasm on tight numeric loops; Perry's NaN-boxing architecture puts it 3.7x behind Rust. AssemblyScript was investigated as an alternative (produces Rust-quality wasm from TS syntax) but the ~17% gain over V8 is not worth the effort.

**Why:** Perry's architecture (NaN-boxing, conservative type analysis, separately-compiled runtime) inserts runtime type-check calls that LLVM cannot optimize away. V8's speculative JIT with deoptimization guards is fundamentally more efficient for numeric code.

**How to apply:** Write SpacetimeDB modules in Rust. The Rust wasm path is the Wasmtime performance ceiling (98KB module, mature SDK). The Perry fork at `_vendor/perry-fork` (branch `feat/target-spacetimedb`) is preserved but not the path forward. Summary at `docs/perry-aot-evaluation.md`; full investigation at `docs/orchestrate/perry-e2e-bench/`.
