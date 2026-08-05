---
name: No per-instance tracking in composited shaders
description: Never propose findClosestInstance or per-instance data recovery in composited SDF shaders — use world-space data directly
type: feedback
---

Do not propose finding/tracking individual instances after composited ray march hit. Features like imperfections should use world-space hit position directly (e.g. planar mapping on hitPos), not attempt to recover per-instance local-space data.

**Why:** The composited shader blends all instances via smooth union — recovering a "closest instance" is architecturally wrong and adds unnecessary complexity.

**How to apply:** When porting features from per-object shaders to composited SDF shaders, adapt to use world-space data available at the hit point rather than trying to reconstruct per-instance data.
