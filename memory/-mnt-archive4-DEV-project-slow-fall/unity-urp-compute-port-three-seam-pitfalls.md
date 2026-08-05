---
name: unity-urp-compute-port-three-seam-pitfalls
description: "When porting a custom compute-shader renderer into Unity URP RenderGraph (especially from Bevy / Vulkan / a non-Unity engine), three convention seams will stack-fail in sequence — each presenting as a variant of \"black or wrong PNG\". Surfaced during the NAADF Bevy→Unity port (project_slow_fall kickoff, 2026-05-20, four diagnose-first cycles)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a82faf67-b968-4b63-bbaf-45b2bc2b87c0
---

When you build a new Unity URP RenderGraph + compute pipeline (especially a port from another engine), three Unity-side convention seams **will** hit in sequence. Each presents differently as the prior is fixed. Front-load these in the architecture and you skip 3–4 diagnose-first cycles.

**Why this is memory and not in a skill file:** these are stable Unity/URP API behaviors (not methodology) — they don't have a natural skill-file home, but a future session opening a Unity compute-pipeline debug should hit them as Hypothesis 1/2/3 *before* deep-diving into shader math, matrix defusals, or buffer-binding correctness.

---

## Seam 1 — `[InitializeOnLoad]` + `EditorApplication.delayCall` is not synchronous under `-batchmode -quit -executeMethod`

**Symptom:** capture utility runs, writes PNG, no Unity errors, but a `ScriptableObject` manifest your pass depends on is null and the pass silently early-returns. The PNG is the camera's clear color.

**Why:** `EditorApplication.delayCall` is delivered on the next editor *idle* tick. Under `-batchmode -quit -executeMethod Foo.Bar`, Unity goes straight from asset-refresh into your executeMethod and then exits — the delayCall callback never runs. So a ship-manifest bootstrap that defers asset creation via `delayCall` will simply not have created the asset by the time your executeMethod fires.

**Fix:** extract the asset-creation/populate body into a `public static void EnsureXNow()` callable synchronously from the executeMethod path. Keep the `[InitializeOnLoad]` static ctor and its delayCall for editor-startup ergonomics (so opening the editor still triggers a populate), but the synchronous method is the load-bearing one. The capture-menu / executeMethod entrypoint must call `EnsureXNow()` *before* any `AssetDatabase.FindAssets` lookup that assumes the asset exists.

**Diagnostic signature in capture log:** look for `Vulkan PSO: Pipeline cache has not changed skipping save` with no PSO-creation lines for your kernel — the kernel was never dispatched because its compute reference was null.

---

## Seam 2 — URP forces `enableRandomWrite = false` on the camera color target

**Symptom:** Unity error during capture: `Compute shader (KernelName): Property (_YourUavName) at kernel index (0): Attempting to bind texture as UAV but the texture wasn't created with the UAV usage flag set!`

**Why:** `UniversalRenderPipeline.CreateRenderTextureDescriptor` (`UniversalRenderPipelineCore.cs:~1572` in URP 17.5) unconditionally clears the `enableRandomWrite` flag on the camera target descriptor. Whatever you pass in is overwritten to `false`. The camera color target is therefore NEVER usable as a UAV for a compute kernel, regardless of what you set on your `Camera.targetTexture` or how you request the render. Setting `requireRandomWrite` on the `Camera` does NOT propagate to the URP descriptor.

**Fix (architect's pre-anticipated fallback):** in the RenderGraph pass, allocate a *transient* UAV-enabled intermediate via your project's `CreateTransient` helper (or `renderGraph.CreateTexture` with a `TextureDesc { enableRandomWrite = true, ... }`), dispatch the compute kernel into THAT, then `renderGraph.AddBlitPass(intermediate, activeColorTexture, ...)` to composite into the camera target. The blit pass is the seam that bridges the UAV-enabled compute output into URP's non-UAV camera target.

**Cross-engine note:** Bevy / Vulkan / DX12 raw don't have this restriction because they own the swapchain target's flags. The forced-false in URP is a Unity-side scoping decision.

---

## Seam 3 — `RWTexture2D` (kernel-stored top-down) vs `Texture2D` CPU-readback (bottom-up): row-order mismatch flips PNG vertically

**Symptom:** PNG renders correctly *in content* (palette colors, geometry visible) but is Y-inverted — sky at the bottom, ground at the top. Quadrant means show the inversion clearly: top quadrants are the bottom-half content, bottom quadrants are the top-half content.

**Why:** When a compute kernel writes to `RWTexture2D<float4> _Tex; _Tex[id.xy] = color;` it uses Unity's compute-coordinate convention where `id.y = 0` is the **top** scanline. But `AsyncGPUReadback.Request(_Tex)` → `Texture2D.SetPixels` → `ImageConversion.EncodeToPNG` follows the OpenGL bottom-up convention where row 0 is the bottom of the image. The mismatch flips the image vertically during readback. Bevy avoids this seam by using a 1-D storage buffer + a fragment-shader readback path that controls row order explicitly; Unity's compute→PNG seam is row-order-asymmetric.

**Fix:** if your kernel's ray-direction helper has an NDC Y-flip (e.g. `float2 ndcXY = (screenPos * 2.0 - 1.0) * float2(1.0, -1.0);` — the standard Bevy-WGSL pattern), **remove the `* float2(1.0, -1.0)` factor**. The texture-readback flip will then "right" the image naturally. Net Y orientation: correct.

**Numerical verification:** in NumPy, replay the matrix chain + ray-direction helper for `pixel.y=0` and `pixel.y=255`. If both produce internally-consistent ray directions (e.g. `pixel.y=0` → `+Y` ray, `pixel.y=255` → `-Y` ray) yet the rendered PNG is upside-down, the bug is at the readback seam, NOT in the kernel math. The fix is the kernel-side compensation described above.

---

## Cross-seam guidance

These three seams stack: each one is invisible until the prior is fixed. The diagnose-first cycle COUNT this produces is high (4 in the NAADF kickoff: ship-manifest sync, UAV transient, Path B handedness, NDC Y-flip removal). If you anticipate them during architect-phase design, you avoid 3+ cycles of fix-and-rerun.

When designing a Unity URP compute-pipeline architecture, the checklist:
1. Is any `[InitializeOnLoad]`-dependent asset reachable synchronously from the executeMethod path?
2. Is your compute kernel's write target a transient RG-allocated intermediate (with `enableRandomWrite=true`) followed by a blit, NOT the camera target directly?
3. Does your ray-direction helper compensate for the readback row-flip (drop the NDC Y-flip if you have one)?

Related: [[naadf-dual-position-gotcha]] covers the *fourth* NAADF-port-specific convention seam (world-coord vs voxel-coord), which is separate from these three Unity-side framework seams.
