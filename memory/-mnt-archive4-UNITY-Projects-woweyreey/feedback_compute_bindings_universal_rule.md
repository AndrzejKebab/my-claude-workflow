---
name: Compute shader binding universal rule
description: Shader.SetGlobal NEVER binds to compute shaders — not a Vulkan quirk. Always bind directly via CommandBuffer.SetCompute*Param + dispatch via cmd.DispatchCompute, never computeShader.Dispatch.
type: feedback
originSessionId: f9ee5476-9802-4095-af11-ed96c82da3d7
---
**Shader.SetGlobal* (Vector/Matrix/Texture/Float) was never designed and is never supposed to extend onto compute shaders. This is not a Vulkan quirk, not a "platform difference", not a "compute reads as zero on Vulkan" bug. This is the API contract on every platform.**

The only way a compute kernel sees a uniform is by being **directly bound** before dispatch. Two universal rules:

1. **Never use `computeShader.Dispatch(...)`. Always use a CommandBuffer**: `cmd.DispatchCompute(cs, kernel, ...)` (or `ComputeCommandBuffer.DispatchCompute`).
2. **Always bind every uniform the kernel reads via direct compute API**: `cmd.SetComputeVectorParam(cs, id, value)`, `cmd.SetComputeMatrixParam`, `cmd.SetComputeFloatParam`, `cmd.SetComputeIntParam`, `cmd.SetComputeTextureParam`, `cmd.SetComputeBufferParam`. Per-dispatch, every dispatch.

`Shader.SetGlobal*` is a fragment/vertex broadcast — it propagates only to raster pipeline stages. Compute is isolated by design. If a compute kernel needs `_FloatingOrigin`, `_WorldSpaceCameraPos`, `_WorldToCloudShadow`, anything else — bind it explicitly per dispatch. No exceptions.

**Why:** Treating this as a "Vulkan compute auto-bind quirk" leads to wasted debug cycles chasing platform-specific behavior, when the real fix is universal: always bind directly. Reinforced 2026-05-05 during the FloatingOrigin rework — multiple iterations diagnosed missing compute bindings as a "Vulkan gap" instead of recognizing it as a global API contract.

**How to apply:**
- When writing or reviewing compute shader dispatches: every uniform the kernel reads must have a matching `cmd.SetCompute*Param` call before `cmd.DispatchCompute`.
- When writing or reviewing C# code that calls `cs.Dispatch(...)`: that's a bug, replace with `cmd.DispatchCompute(...)`.
- When auditing FO/atmospherics/any-pipeline code for compute-side incoherence: don't grep for "Vulkan", grep for missing direct bindings.
- Memory entries previously framing this as "Vulkan compute reads SetGlobal as zero" should be corrected to "compute kernels never see SetGlobal — bind directly".
