---
name: terrain-fixture-needs-depthonly
description: "Any terrain-representative test shader must carry a DepthOnly pass — SSS/screen-space receivers reconstruct from prepass depth, and a fixture without the pass reads far-plane → lit, silently"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3aeabc29-801b-4bb7-b979-83fa928b85e4
  modified: 2026-07-19T13:00:22.696Z
---

A terrain fixture shader without a `DepthOnly` pass never enters the depth prepass (the package's
`DepthPrepassRecorder` draws by LightMode tag), so every screen-space shadow receiver on that terrain
reconstructs to the far plane and reads lit. `VTShadowOnlyTest` lacked it until 2026-07-19; scenes
with a stock mesh masked the hole because URP's own prepass drew the mesh.

**Why:** the failure is silent and scene-dependent — a gate can pass with a mesh receiver and fail
terrain-only, imitating a trace/compose bug (cost a multi-run bisect: MPB pool, azimuth, residency
theories all dead ends).

**How to apply:** when a new terrain fixture shader is authored, copy the DepthOnly pass from
`WhiteLitShadowFixture.shader` (displaced vertex + null fragment). When an SSS-term gate reads
all-lit on terrain pixels, check depth first: branch-code the trace/compose far-depth early-out and
read the intermediate target. Related: [[shadow-direct-trace-mode]].
