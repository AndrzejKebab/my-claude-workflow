---
name: VT border padding approach
description: VT seam issues must be solved via physical tile border padding in the atlas, not trilinear blending or oversampling
type: feedback
---

VT seam issues are solved by proper border padding in the physical tile atlas, NOT by trilinear blending or oversampling.

**Why:** Trilinear is bad for many reasons. The VT must work for both streaming-from-disk and render-into-VT use cases. Border padding enables natural bilinear hardware filtration — once the page table resolves into tiles that have proper padding, bilinear just works.

**How to apply:** When addressing VT tile boundary seams, the fix is always in the border fill/padding mechanism (RWVTBorderFill.compute), never in shader-level multi-sample blending. The Kühnert thesis (Chunked Clipmap, Section 4.5.4) is the reference for this approach. Layer blending from the thesis is NOT applicable to VT — it's specific to their rasterization-based terrain rendering.
