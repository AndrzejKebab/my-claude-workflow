---
name: no-perrywasm-host-fork
description: "Rejected approach — never fork the SpacetimeDB host to load Perry's JS-host WASM"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 844b0b96-55ab-4654-b172-51d34859983f
---

For [[mmodb-project]], do NOT make the SpacetimeDB host load Perry-shaped WASM (a `PerryWasm` host type that supplies Perry's 211-function `rt` JS-runtime as Rust host functions). The user explicitly called this "a HACK, not architecturally sound."

**Why:** it forks the database core and reintroduces a JavaScript-runtime-equivalent inside the host (NaN-box object model + GC + a wasm↔host call on every string/object/array op), defeating the whole point of AOT compilation and coupling the DB to Perry's internals.

**How to apply:** the sound path is the inverse — make the **forked Perry** emit a *freestanding* WASM module that conforms to SpacetimeDB's existing stable, language-agnostic native ABI, so the **stock** host loads it like any Rust/C#/C++ module. Fork only Perry's codegen and the SpacetimeDB *TypeScript module* (one release option); never the SpacetimeDB core/host.
