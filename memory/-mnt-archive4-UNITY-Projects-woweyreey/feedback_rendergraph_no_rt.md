---
name: RenderGraph no RenderTexture
description: Never use RenderTexture with RenderGraph — use renderGraph.CreateTexture/ImportTexture with TextureHandle
type: feedback
---

Never use `RenderTexture` or persistent RT objects with RenderGraph. Use `renderGraph.CreateTexture()` for transient resources and `renderGraph.ImportTexture()` only for externally-managed resources.
**Why:** RenderGraph manages resource lifetimes and aliasing. Manual RT management conflicts with this and causes crashes/errors.
**How to apply:** All textures in RenderGraph passes must be TextureHandle from CreateTexture or ImportTexture. Buffers use ImportBuffer from GraphicsBuffer.
