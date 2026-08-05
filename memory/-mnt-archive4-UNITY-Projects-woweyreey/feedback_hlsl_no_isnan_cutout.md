---
name: HLSL isnan() is unreliable — use finite sentinels for cutouts
description: Vulkan SPIR-V compilers optimize isnan() away under fast-math. Use a large finite sentinel (e.g. 1e30) and > threshold checks instead
type: feedback
originSessionId: d77e5e84-01cd-4696-8fe1-10eff67f70e9
---
Never use NaN as a sentinel / cutout marker in HLSL compute or fragment shaders. The Vulkan SPIR-V backend (and D3D's /Gfa path) compiles under fast-math assumptions that treat NaN as "impossible", optimizing away `isnan(x)` checks entirely. A shader warning surfaces this:

> Shader warning in 'Foo': value cannot be NaN, isnan() may not be necessary. /Gis may force isnan() to be performed

When you see that warning, trust it — the check is gone. The downstream symptom is NaN values flowing into mesh buffers / framebuffers / readbacks, and once they reach Unity's mesh system they corrupt `Mesh.bounds` (`-nan` min/max), which then cascades into "Invalid worldAABB" spam from the scene culling pass every frame for every renderer.

**How to apply:** Use a finite sentinel that fits the storage format AND sits outside any plausible value range. For R16F buffers (max ≈ 65504) use something like `50000.0` with a threshold of `40000.0`. Do NOT use 1e30 — it overflows R16F to `+inf`, and `h > threshold` against `+inf` gets optimized away just like `isnan`. R32F tolerates 1e30 but the same fast-math concern applies to infinity checks, so a plain large-but-finite value is safer across formats. Propagate the same threshold to any downstream shader or C# code that reads the value.

**Why:** Encountered this in the stamp selection-proxy pipeline. The NaN-encode blit emitted NaN for "stamp did not contribute here", the meshing compute checked `if (isnan(h))` to degenerate quads, and Vulkan happily compiled the check away — NaN verts leaked into every proxy mesh, NaN'd their AABBs, and every frame's scene cull complained about invalid worldAABB. Fix was switching to `1e30f` sentinel + `h > 1e20` check. Same gotcha applies to `!isfinite(x)` for infinity — use explicit thresholds instead.
