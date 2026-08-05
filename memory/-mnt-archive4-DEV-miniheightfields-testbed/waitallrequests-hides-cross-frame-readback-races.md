---
name: waitallrequests-hides-cross-frame-readback-races
description: "A red-first gate for an async-GPU-readback counter bug must fly WITHOUT the Settle helper's WaitAllRequests force-flush, or the cross-frame race collapses to same-frame and the bug vanishes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37b99127-dc19-48e5-9627-83d3704cd042
  modified: 2026-07-19T20:10:36.329Z
---

The PlayMode fixture's `Settle(frames)` helper calls `AsyncGPUReadback.WaitAllRequests()` every
frame. That force-completes every pending readback within the frame boundary, which collapses any
**cross-frame** async-readback race into a same-frame one — so a bug that only exists because two
readbacks sample different frames does not reproduce under `Settle` at all.

Concretely: the `HiZ Culled` counter went negative because `LastHiZCulled = phase1Culled(frame N) −
phase2Recovered(frame N+k)` chained two async readbacks that landed on different frames. The
existing settle-based occlusion test never caught it — `WaitAllRequests` made both readbacks
complete in the same frame, where `phase2Recovered ⊆ phase1Culled` holds and the difference is
always ≥ 0.

**How to gate an async-readback counter bug:** warm up with `Settle`, then fly the motion loop with
a plain `m_Camera.Render(); yield return null;` and NO `WaitAllRequests`, so the readback latency
spans real frames. Sample the counter every frame and assert the invariant (e.g. min ≥ 0) plus a
liveness bound (max > 0) so a fix that merely zeroes the counter fails. Pattern lives in
`OcclusionCullTests.HiZCulled_NeverNegative_UnderMotionAndCuts`.

**Why:** async readbacks progress on the engine's natural cadence between frames; force-completing
them each frame changes the timing the bug depends on.

**How to apply:** any e2e gate targeting a value produced by `AsyncGPUReadback` (HiZ Culled, future
GPU counters) must NOT use the force-flushed settle for its measurement window.

Related: process-global summed counters (`HiZ Culled` sums each camera×renderer binding's stale
`LastHiZCulled`) over-count under multi-camera / leaked-fixture state, so an *upper*-bound assertion
on such a counter is unsafe in a full PlayMode suite — see [[single-editor-test-runs]] on batchmode
state leakage. See also [[durable-e2e-not-editor-qa]].
