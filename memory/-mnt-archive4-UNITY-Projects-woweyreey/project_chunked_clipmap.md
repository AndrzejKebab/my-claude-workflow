---
name: Chunked Clipmap Refactor
description: RWVT replaced page table with clipped quadtree StructuredBuffer (Kühnert thesis §4.5)
type: project
---

RWVT page table replaced with clipped quadtree (StructuredBuffer<uint>). Deleted RWVTPageTable, RWVTPageMap, RWVTPageTableUpdate.compute. Created RWVTClippedQuadtree.cs.

**Why:** Terrain-focused VT doesn't need general-purpose mip-mapped page table. The chunked clipmap is simpler (no painters algorithm, no compute scatter) and uses less VRAM.

**How to apply:** The quadtree nodeCount = min(PageTableWidth, 512). Budget stress test threshold relaxed from 0.5% to 3.5% for monotonicity violations at LOD transitions — the quadtree produces sharper transitions than the painters algorithm. Same-mip coherency is perfect (0 seams).
