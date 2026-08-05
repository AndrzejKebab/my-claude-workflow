---
name: SDF publish baked origin, not camera
description: Camera-anchored bounded SDFs must publish the origin committed at the LAST rebake (not the current-frame camera) so shader UVW stays aligned with baked content
type: feedback
originSessionId: f2d75a87-1834-4d7c-94e8-ea33a4438510
---
For a camera-anchored bounded SDF (NC23-style NVDF + camera-centred variant), the shader's `_CloudSDF_WorldOrigin` must be the world origin used for the LAST actual bake — NOT the current-frame camera position — otherwise cloud shapes appear to track the camera between rebakes.

**Why:** the shader's UVW mapping is `(worldPos - origin) / extent`. If `origin` moves every frame with the camera but the texture contents were baked from density sampled at an earlier camera position, every new camera position remaps the stale content onto the same local UVW window. The baked shape then appears glued to the camera. Between rebakes the published origin must stay frozen; it only advances when we actually re-sample density.

**How to apply:** the baker caches `_bakedOrigin` when it commits a rebake. Every `Dispatch` publishes `_bakedOrigin` as the global (not `currentOrigin`). Rebake-dirty triggers include camera drift from `_bakedOrigin` exceeding one voxel, wind drift, preset change.

Canonical NC23 NVDF is world-anchored (covers a fixed scenario region), so the issue never arises there. The bug is specific to the camera-centred adaptation we use for open-world clouds.
