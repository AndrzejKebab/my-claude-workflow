---
name: naadf-dual-position-gotcha
description: "NAADF voxel renderer ports — when debug symptoms are black/garbage/wrong-geometry, check dual-position (world-coord vs voxel-coord offset) handling FIRST. This was the Bevy port's very first point of failure."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a82faf67-b968-4b63-bbaf-45b2bc2b87c0
---

When debugging a NAADF voxel-renderer port (Unity, Bevy, future), and the symptom is **black output, garbage rendering, or visually-wrong geometry from a render that compiled clean and dispatched** — make dual-position handling **Hypothesis 1**, ahead of handedness, matrix order, NDC depth, ray-direction math, or any other defusal concern.

**Why:** The Bevy port of NAADF hit this as its **very first point of failure** (user-flagged, 2026-05-20, during the project_slow_fall Unity-kickoff `/delegate` orchestration). NAADF scenes are intentionally offset from world origin — in the Bevy reference, `demo_origin_v() = (2016, 0, 2016)`, and the default scene's camera is at `off+(86,42,90)` looking at `off+(32,16,32)`. Any assumption that voxel coordinates start at world `(0,0,0)` silently breaks: the ray origin is far from the voxel volume, the DDA marcher walks empty space until its step-cap kicks in, the kernel writes the background color (or zero) for every pixel. Code that compiles clean, dispatches successfully, and produces a non-trivial PNG-byte signature can still be visually broken in exactly this way. The Vulkan PSO + GPU-time log will not warn you.

**How to apply:** In NAADF port debug — diagnose-first dispatches, fix dispatches, gate failures whose symptom is render-shape-wrong (NOT kernel-didn't-dispatch failures, which present differently — missing PSO cache, null compute references, no dispatch markers in the log):

1. **CPU builder side:** confirm the procedural builder emits voxel coordinates in the **same coordinate space** the kernel expects to sample in. If the builder writes to voxel-local `[0..N)` indices but the kernel transforms world-space rays into voxel-space using a *different* origin, the ray-march hits nothing.
2. **Camera-matrix construction side:** the camera position is in world-space (`demo_origin + offset`), but the inverse-VP matrix uploaded to the kernel must produce rays whose origin can be translated into voxel-space cleanly. Either subtract the volume origin on the CPU before building the matrix, or pass the volume origin as a separate uniform and subtract in the kernel.
3. **HLSL traversal side:** verify the traversal kernel performs the world→voxel translation explicitly. A kernel that assumes `rayOrigin` is already in voxel-space, when in fact it's in world-space at `(2016, 0, 2016)`, will march off the end of every chunk and return zero.

The Bevy port's defusal of this lives somewhere in its CPU camera-matrix construction + WGSL traversal (cite from `bevy-naadf/src/` when you write the Unity defusal — verify with grep before quoting, per [[feedback-vigilance-preamble-for-cg-work]]). Related: [[naadf-getraydir-monogame-conventions]] covers the *other* four defusals (handedness, NDC, matrix order, view-translation-free); dual-position is the fifth and is the one most likely to silently produce the symptom that LOOKS like a handedness bug.
