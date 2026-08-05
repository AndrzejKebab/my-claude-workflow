---
name: feedback-ssot-vs-agentic-divergence
description: "Porting C# NAADF — if Bevy has N>1 divergent hard-coded versions of a singular C# constant, refactor to SSoT, don't patch one site."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1b90ad0-1c04-4ed5-a406-7a39e6d62fc0
---

Porting a constant (scene size, world extent, voxel dims, etc.) from C# NAADF to Bevy — if Bevy has **N>1 divergent hard-coded values** where C# has **a singular constant**, fix = **refactor to SSoT**, NOT a patch to the currently-observable site.

**Why:** agentic dev with limited context tends to re-hardcode constants in N places (each agent rediscovers locally), drifting values. C#'s SSoT is the correct shape. [[bevy-naadf-faithful-port-rule]] = match C#'s structure, not just its value at one site.

**How to apply:** Bevy-vs-C# audit MUST enumerate every Bevy constant in the relevant path, not just the load-bearing one. Deliverable states explicitly "single canonical chain" or "N divergent — refactor required". Applied for `oasis-vox-instance-count` /delegate (2026-05-19) — world-size constants verified as single chain; divergence was asset-level.
