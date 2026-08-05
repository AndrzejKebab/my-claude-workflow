---
name: reverse-z-clip-convention
description: "hypertino renders reverse-Z / [0,1] clip depth; any render composited into a scene pass must match or it gets clipped/invisible"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8e855018-86eb-4b88-9a40-bee5d862e61c
---

hypertino renders **reverse-Z with a ZERO_TO_ONE ([0,1]) clip-space depth** convention: Vulkan uses `GLM_FORCE_DEPTH_ZERO_TO_ONE` + reverse-Z + `GreaterOrEqual` depth; GL/WebGL2 sets `EXT_clip_control GL_ZERO_TO_ONE`. Any secondary or third-party render path composited into a scene pass gets near-clipped / mis-projected if it doesn't match this convention — and the symptom is silent (geometry simply doesn't draw), so it reads as "nothing rendered" rather than "wrong depth".

**Why:** bitten twice in the asset-pipeline-usd / Noesis work. (1) Native editor blue-screen — `apps/editor/editorcamera.cpp` built its projection without `GLM_FORCE_DEPTH_ZERO_TO_ONE`, so glm emitted an OpenGL [-1,1]-Z matrix against the reverse-Z pipeline → far plane maps to NDC z=-1, Vulkan clips, nothing drawn. (2) Web Noesis panel invisible — the scene's `EXT_clip_control ZERO_TO_ONE` near-clipped NoesisGUI's `z=-1` UI geometry; fixed by resetting clip space to `NEGATIVE_ONE_TO_ONE` + `UPPER_LEFT` at the GL Noesis device per render and restoring the scene convention before present.

**How to apply:** when integrating any new render into a scene pass (a UI lib like Noesis, an overlay, third-party draws), reconcile the reverse-Z / ZERO_TO_ONE clip convention FIRST — either author to match it, or locally reset+restore clip control around the foreign draws. Check this before deep-debugging an invisible overlay / non-drawing geometry.

**Emscripten guard gotcha (bitten a 3rd time):** guard clip-control / optional-extension calls on the GL EXTENSION STRING (what the GL backend + web_bench do), NOT on `emscripten_webgl_get_proc_address("glClipControlEXT")` — that proc thunk is ALWAYS non-null on emscripten, so a proc-pointer guard silently passes and calls into a null `GLctx.extClipControl`, crashing every frame on WebGL2 contexts without `EXT_clip_control` (Firefox/GTX-980). Also: don't let a `UPPER_LEFT` clip-control reset double as a UI Y-flip — when the reset becomes a no-op on the absent path the UI renders upside-down; flip Y in the UI's own projection instead.
