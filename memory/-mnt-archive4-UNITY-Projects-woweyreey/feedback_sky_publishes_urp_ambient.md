---
name: Sky/atmosphere systems must publish to URP's standard ambient pipeline
description: Any sky system must write RenderSettings.ambientSkyColor/EquatorColor/GroundColor (and ultimately customReflectionTexture) every frame so surface shaders pick up atmospheric lighting through the normal SH / reflection probe path
type: feedback
originSessionId: 1baef162-42d5-4a70-98b2-2f510e96fa21
---
Any physically-based sky / atmosphere feature in this project must publish its output to URP's **standard ambient pipeline**, not just to its own private globals:

**Required (Phase 1):**
- `RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight`
- `RenderSettings.ambientSkyColor` — zenith/upward sky radiance
- `RenderSettings.ambientEquatorColor` — horizon sky radiance
- `RenderSettings.ambientGroundColor` — ground bounce

**Required (Phase 2+):**
- `RenderSettings.customReflectionTexture` — small cubemap convolved from the sky, driving the default reflection probe

Sky features *may additionally* publish their own extra globals (sky LUTs, transmittance, etc.) for consumers that want the full atmospheric coupling (e.g. volumetric clouds, volumetric fog). But those extras do **not** replace the standard ambient publication — they are on top of it.

**Why:** The user wants the rendering stack to stay compatible with anything that reads `RenderSettings.ambient*` or the default reflection probe — i.e. every stock URP Lit shader, particle system, decal. If the sky only publishes private globals, everything else in the scene still reacts to whatever Unity's default ambient was at play-start and ignores the atmosphere entirely. Reference behaviour is Enviro — it writes these every frame.

**How to apply:** In the ScriptableRendererFeature's `AddRenderPasses` (main thread), compute the three ambient colours from the current sun direction + sun color + atmosphere parameters and assign them to `RenderSettings`. The compute can be a simplified analytical model (not a full readback of the precomputed LUTs) so it stays cheap every frame; the reflection probe cubemap is the later, more expensive piece.
