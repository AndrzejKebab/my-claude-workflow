---
name: URP sampler_LinearClamp redefinition collision in compute
description: Compute kernels that include URP's Shadows.hlsl / Lighting.hlsl / DeclareDepthTexture.hlsl pull GlobalSamplers.hlsl transitively, which already declares sampler_LinearClamp — don't re-declare it in package headers or the compute stage will fail with "redefinition of 'sampler_LinearClamp'"
type: feedback
originSessionId: fe53b8d3-8300-4287-8a07-a79c70ea9267
---
Don't re-declare `sampler_LinearClamp` (or the other `sampler_LinearRepeat`, `sampler_PointClamp`, etc. magic-name inline samplers) inside package HLSL headers that may be pulled into a compute shader which also includes URP's `Shadows.hlsl`, `Lighting.hlsl`, `DeclareDepthTexture.hlsl`, or `DeclareOpaqueTexture.hlsl`. Those URP headers transitively pull `GlobalSamplers.hlsl` which already declares the inline samplers, and the duplicate declaration surfaces as a Vulkan compile error `"redefinition of 'sampler_LinearClamp' at kernel X"` followed by the more generic `"Kernel at index (0) is invalid"`.

**Why:** We've hit this at least three times in the atmospherics fog pipeline. The first time was with `s_linear_clamp_sampler` vs `sampler_LinearClamp` — fixed by declaring our own. The second time we wrapped the declaration in `#ifdef SHADER_STAGE_COMPUTE` to avoid clashing with raster stages. But the moment a compute kernel pulls in `URP/ShaderLibrary/Shadows.hlsl` (for `MainLightRealtimeShadow`) or similar, the SHADER_STAGE_COMPUTE-guarded declaration clashes with URP's own `GlobalSamplers.hlsl` declaration which is always emitted.

**How to apply:**
- In shared package HLSL headers (e.g. `VolumetricFogCommon.hlsl`), do NOT declare `SAMPLER(sampler_LinearClamp)` unconditionally or under a generic `SHADER_STAGE_COMPUTE` guard.
- Instead, declare it only when the file is pulled into a compute kernel that does NOT also include URP's GlobalSamplers chain. In practice this is rare — most of our computes want URP helpers.
- Preferred pattern: when the compute kernel includes `Shadows.hlsl` / `Lighting.hlsl` / `DeclareDepthTexture.hlsl`, REMOVE the package-level `sampler_LinearClamp` declaration entirely and rely on GlobalSamplers.hlsl's declaration.
- If the kernel does NOT include a URP header that pulls GlobalSamplers, either include `Packages/com.unity.render-pipelines.core/ShaderLibrary/GlobalSamplers.hlsl` directly, or declare the sampler with a package-scoped name (`sampler_VolumetricFog_LinearClamp`) to avoid the collision.
- The error signature to recognize quickly: Unity console shows "redefinition of 'sampler_LinearClamp' at kernel X" immediately followed by "Kernel at index (0) is invalid" — that pair always means a sampler-name collision between package HLSL and URP GlobalSamplers.
