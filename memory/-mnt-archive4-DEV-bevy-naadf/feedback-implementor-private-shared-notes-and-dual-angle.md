---
name: feedback-implementor-private-shared-notes-and-dual-angle
description: "Iterative GPU/wasm debugging — consecutive implementors share a private notes file the orchestrator only reads on WON; enumerate from BOTH 'why broken' AND 'why occasionally works' angles; cross-check against the device-capability divergence catalog."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b6b284c-a4b9-4e10-80eb-a670749962ae
---

When iterative consolidated-mode debugging spans multiple dispatches:

1. **Implementor-private shared notes.** Reserve `docs/orchestrate/<topic>/IMPLEMENTORS_SHARED.md`. Consecutive implementors read on entry, append on bail/win. Orchestrator does NOT read unless WON — keeps orchestrator context clean while implementors accumulate a full cross-dispatch reasoning trace. Brief: "read IMPLEMENTORS_SHARED.md if it exists, try things, bail or win."

2. **Dual-angle hypothesis enumeration for non-deterministic bugs.** "Usually broken, occasionally works" — enumerate from BOTH "why broken" AND "why occasionally works." Mechanism is often a CONJUNCTION (race resolving favorably under specific timing/resource conditions). The lucky case is data about what conditions DO let it converge.

3. **Cross-check against the device-capability divergence catalog.** `docs/orchestrate/wasm-chunk-aadf-nondeterminism/02-diagnostics-impl.md` lists 84 native (Vulkan) vs web (Dawn/Chrome WebGPU) divergences, 6 load-bearing. Every hypothesis: does it rest on a capability the snapshot shows as divergent? Yes → strong signal. Identical → weakened.

**How to apply:**
- Every iteration's brief: (a) reference IMPLEMENTORS_SHARED.md, (b) dual-angle requirement, (c) explicit pointer to `02-diagnostics-impl.md`'s 84-divergence table.
- Orchestrator MUST NOT read IMPLEMENTORS_SHARED.md after BAILED — only after WON.

Related: [[feedback-multiple-runs-rule-out-false-positives]], [[feedback-vigilance-preamble-for-cg-work]], [[feedback-subagent-research-only-compliance]].
