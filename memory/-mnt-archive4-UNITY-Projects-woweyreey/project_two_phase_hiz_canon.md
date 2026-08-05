---
name: Two-phase HiZ canonical reference
description: The two-phase HiZ occlusion culling pattern in Packages/is.zori.heightfields traces directly to Aaltonen-Haar SIGGRAPH 2015 pages 51-54 (NOT Wihlidal GDC 2016)
type: project
originSessionId: 16ae2408-78b8-4291-ab7e-f423f44c3618
---
The heightfield package's two-phase GPU-driven occlusion culling (`HeightfieldOcclusionCull.compute` + `HeightfieldPhase1CullPass` / `HeightfieldPhase2CullPass` + the mid-frame and end-of-frame `HiZPass` instances) implements the canonical pattern from:

**Haar & Aaltonen — *GPU-Driven Rendering Pipelines* — SIGGRAPH 2015 *Advances in Real-Time Rendering* course.**
Extract: `docs/research/aaltonen-haar-2015-gpu-driven.md`. The two-phase pseudocode + flowchart + Xbox-One @1080p benchmark (2.3 ms total) is on pages 51–54 of the deck. Cite this paper for the algorithm.

**Why:** I initially cited Wihlidal GDC 2016 as the canonical two-phase reference. After reading both PDFs, this was wrong: Wihlidal (`docs/research/wihlidal-2016-optimizing-graphics-pipeline.md`) is the canonical reference for **GCN-centric compute triangle/cluster culling** + **software occluder rasterising** ("Software Z" since BF3) — not the two-phase scheme. Wihlidal page 72 mentions "re-projecting your previous depth buffer and testing with that" only as a one-line aside fallback when no software rasteriser is available.

**How to apply:** when commenting / documenting the two-phase code, cite **Aaltonen-Haar 2015 pages 51–54** for the algorithm. Cite **Wihlidal 2016** for downstream work on per-triangle compute culling (test math, GCN HTILE encoding, async-compute scheduling) — relevant if/when we extend the pipeline to triangle-level cluster culling. UE5 Nanite (Karis 2021 SIGGRAPH) descends from Aaltonen-Haar at cluster grain.
