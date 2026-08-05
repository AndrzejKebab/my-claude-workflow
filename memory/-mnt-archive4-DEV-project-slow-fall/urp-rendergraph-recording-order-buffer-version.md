---
name: urp-rendergraph-recording-order-buffer-version
description: "URP RenderGraph resolves a buffer/texture read to the version produced by the latest write RECORDED BEFORE the reader — not the topologically-correct writer. A pass that reads resource X must be recorded after every pass that writes X, or it silently reads a stale version. Bit the NAADF GI port twice in one session (project_slow_fall, 2026-05-22)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc04fa92-551c-4409-ba8f-d9b2957cdf73
---

When multiple `ScriptableRenderPass`es (or sub-passes within one) write the
same imported `BufferHandle` / `TextureHandle`, URP RenderGraph resolves a
*reader's* dependency to the **most recent write recorded before that reader
in EnqueuePass / RecordRenderGraph order** — NOT to whichever pass "logically"
produces the final value. If pass R reads X but is recorded before pass W
that writes the value R actually needs, R silently gets a stale X. No error,
no warning — just wrong pixels.

**Why this is memory, not a skill:** it is a stable URP RenderGraph
scheduling behavior. A future session debugging a multi-pass NAADF/URP
compute pipeline that renders black / stale should hit this as an early
hypothesis — *before* deep-diving shader math. Code-reading a single kernel
will not reveal it; the bug is in the cross-pass recording order.

**It bit the NAADF GI port twice in one session:**
1. The interim debug-blit was recorded inside `NaadfFirstHitPass.RecordRenderGraph`,
   which `ZoriNaadfFeature` enqueues *before* `NaadfGiPass`. The blit read
   `_NaadfFinalColor` — but the only writer recorded before it was H1 (pre-GI
   atmosphere seed); G6's GI write was recorded later. So the blit decoded a
   pre-GI buffer → black voxels. Cost a 2-diagnostic detour (07 code-reading
   found nothing; 08 GPU probes isolated it). Fix: move the blit into
   `NaadfGiPass`, recorded after G6.
2. Same class, caught proactively: H3 TaaPresent reads `_NaadfTaaSampleAccum`,
   which G7 writes. H3 was recorded in `NaadfFirstHitPass` before `NaadfGiPass`.
   B4 moved H3+H4 to the tail so the recording order is
   `H1→H2 → G1..G7 → H3→H4`.

**Diagnostic signature:** a real code change to a producer pass leaves the
output *byte-identical* (the reader never saw the change because it resolves
an earlier version). A byte-identical capture across a genuine producer edit
= strong evidence of a recording-order / stale-version read, not a no-op edit.

**Design rule:** when a resource is written by pass W and read by pass R,
verify W is recorded before R in the actual EnqueuePass + RecordRenderGraph
order. Same-pass multiple dispatches DO get automatic STORAGE_WRITE→READ
barriers (verified on Vulkan); the hazard is specifically *cross-pass*
recording order. The clean structural shape: whichever pass owns the late
stages of the frame owns the tail — for NAADF, `NaadfGiPass` owns
`G1..G7 → H3 → H4`, not `NaadfFirstHitPass`.

Related: [[unity-urp-compute-port-three-seam-pitfalls]] (the Unity-API
convention seams), [[naadf-dual-position-gotcha]] (world/voxel coord).
