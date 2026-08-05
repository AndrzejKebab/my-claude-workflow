---
name: Compute shader uniforms must be bound explicitly via SetComputeXxxParam
description: Shader.SetGlobal* never binds to compute kernels — every uniform a compute reads must be bound directly via cmd.SetCompute*Param per dispatch. Universal API rule, not a Vulkan quirk. Includes textures.
type: feedback
originSessionId: f9ee5476-9802-4095-af11-ed96c82da3d7
---
**Rule:** Every uniform a compute kernel reads must be bound for that dispatch via `cmd.SetComputeFloatParam` / `SetComputeVectorParam` / `SetComputeMatrixParam` / `SetComputeIntParam` / `SetComputeTextureParam` / `SetComputeBufferParam` against the **specific compute shader instance**, every dispatch.

**`Shader.SetGlobal*` (Vector/Matrix/Texture/Float) NEVER binds to compute kernels.** Not on Vulkan, not on D3D, not anywhere. This is the API contract — `Shader.SetGlobal*` is a fragment/vertex broadcast that propagates only to raster pipeline stages. Compute is isolated by design. (Earlier framing of this as a "Vulkan compute reads SetGlobal as zero" quirk was misleading and led to wasted debug cycles. See `feedback_compute_bindings_universal_rule.md`.)

**Companion rule:** Always dispatch via `cmd.DispatchCompute(cs, kernel, ...)` — never `computeShader.Dispatch(...)`. Direct compute dispatch bypasses CommandBuffer state.

**How to apply:**
- Write a `BindComputeXxx(cmd, compute, profile, ...)` helper that calls `SetComputeFloat/VectorParam` for every uniform the compute kernel reads. Call it immediately before each `cmd.DispatchCompute`.
- Same applies to textures: `cmd.SetComputeTextureParam(cs, kernel, id, tex)` per dispatch — `Shader.SetGlobalTexture` does NOT cover compute.
- For graphics shaders (fragment/vertex) `Shader.SetGlobal*` works fine — that's its design.
- Symptom check: if compute LUTs / output come out black or "stuck at zero" with no compile errors, missing bindings is almost always the cause.

**Why:** Unity's `$Globals` implicit CBuffer is only bound to graphics pipelines. Compute kernels get their uniforms only from the explicit `cmd.SetCompute*Param` API. This is platform-agnostic — the same on every backend. Treating it as platform-specific is a category error.
