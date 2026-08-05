---
name: Compute shadow sampling — direct + globals via AllowGlobal*
description: Sampling URP main-light shadowmap from compute requires reading URP's Shadows.hlsl directly and replicating an explicit-LOD path; bind via AllowGlobalStateOnPass / EnableShaderKeyword on the RenderGraph builder, not via Shader.GetGlobal* + SetComputeTextureParam.
type: feedback
originSessionId: aa89e226-0d88-418f-99f4-79fbcf4355e7
---
When sampling URP main-light cascade shadows from a compute kernel:

1. **Read URP `Shadows.hlsl` directly** and extract the actual sampling chain — don't trust `MainLightRealtimeShadow` to work in compute (its branches end in implicit-LOD `Texture2D.Sample`, which Vulkan compute rejects). Write a compute-safe local helper that mirrors the math but calls `SampleCmpLevelZero` (or the URP explicit-LOD macro) on the comparison sampler. The helper has to handle: `TransformWorldToShadowCoord` math, the comparison sample, `GetMainLightShadowFade`, and `BEYOND_SHADOW_FAR` boundary check — all pure math except the sample, which is the part Vulkan compute needs explicit-LOD for.

2. **Don't bind shadow texture/matrices via `Shader.GetGlobalTexture` + `SetComputeTextureParam`** — that's host-side, reads stale state at record time, and is "barbaric" (user's word). The canonical way: rely on URP's globals being available to the compute pass by configuring the RenderGraph builder properly — `AllowGlobalStateModification` / `AllowPassCulling` / `EnableShaderKeyword` calls, plus `builder.UseTexture` on the URP-owned shadowmap handle from `UniversalResourceData.mainShadowsTexture`. URP's `MainLightShadowCasterPass` already issues `cmd.SetGlobal*` for matrices/params/sizes during execute — those reach compute when the pass allows global reads.

**Why:** `Shader.GetGlobal*` is host-side; reads what was last set on the C# side, which is whatever URP set last frame. URP's authoritative globals are pushed via CommandBuffer during execute. Compute kernels see those globals automatically when the RenderGraph pass declares `AllowGlobalStateOnPass(true)` or equivalent. No manual forwarding needed.

**How to apply:** When adding shadow sampling (or any URP-resource sampling) to a custom compute pass: (a) read URP's actual HLSL to map the sample chain, (b) write an explicit-LOD compute-safe variant of the receiver function, (c) configure the RenderGraph builder to allow URP globals through, (d) declare `builder.UseTexture` for the shadowmap handle for proper RenderGraph dependency tracking. Never `Shader.GetGlobalTexture` + `SetComputeTextureParam` for URP-owned RTs.
