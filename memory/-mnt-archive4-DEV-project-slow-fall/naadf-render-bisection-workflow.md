---
name: naadf-render-bisection-workflow
description: "When bisecting a NAADF render bug across compute-shader keyword variants (AADF vs dense-DDA, with/without debug ramps), drive via batchmode + programmatic keyword toggle, not editor inspector clicks."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6e7267f7-1ceb-4ad3-b8fa-56be2c23f0b7
---

When bisecting a NAADF render bug between compute-shader keyword variants (e.g. AADF traversal vs `NAADF_DEBUG_DENSE_DDA` fallback, with/without `NAADF_DEBUG_FIRST_HIT_DEPTH`, etc.), the workflow is:

1. Toggle keyword in code: `ComputeShader.EnableKeyword("X")` / `DisableKeyword("X")` or `cmd.EnableKeyword(localKeyword)` from the pass. Compute shader keywords are NOT toggleable via the Unity inspector.
2. Run the capture via `unity -batchmode -executeMethod <Zori.TestBed.Editor.Capture.X>` (no `-nographics`; needs `DISPLAY`).
3. Compare the resulting capture PNGs side by side. Two captures of the same scene with different keywords is the standard bisection.

**Why:** [[unity-urp-compute-port-three-seam-pitfalls]] documents three convention seams the Unity port hits. Bisecting which seam a render bug is on requires comparing variants — and the variants are gated by compute-shader keywords whose toggle surface is code-only. Suggesting "toggle the keyword in the inspector" wastes a round-trip.

**How to apply:** when proposing a debug bisection that involves a compute-shader `#pragma multi_compile` variant, the dispatch must include writing the code path that toggles the keyword and triggering the capture from batchmode — not "ask the user to toggle X in the inspector." Related to [[naadf-dual-position-gotcha]] which lists batchmode-driven captures as the verification surface for first-render correctness work.
