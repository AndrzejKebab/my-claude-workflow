---
name: Cuntz & Kolb 2007 FHA vs JFA — algorithmic comparison reference
description: Canonical performance & accuracy comparison for hierarchical 3D DT (FHA) vs Jump Flooding (JFA) on the GPU; relevant when designing/tuning Phase 5 V3 voxel SDF atlas
type: reference
originSessionId: 66efccc6-8d37-4b06-8e0f-4c0b345eb74a
---
Two companion documents extracted in `docs/research/`:

- **`cuntz-kolb-2007-hierarchical-3d-distance-transform.md`** — Eurographics 2007 Short Papers (4 pp). Use this for the **JFA-vs-FHA comparison** (FPS plot + 3 sub-tables of error metrics). Hardware: GeForce 8800 GTS.
- **`cuntz-kolb-2007-tr-3d-distance-transform.md`** — University of Siegen Technical Report, May 15 2007 (9 pp). Use this for the **formal Property 1 error-bound proof** ($\epsilon_d \le \sqrt{3}\Delta$ in 3D, tightened to $\frac{\sqrt{3}}{2}\Delta$ for typical push-down via Remark 1), **MRT implementation details** (3D-as-stack-of-2D-slices, `GL_RGBA_FLOAT16_ATI`, **`minDistance` GLSL listing**), and the [KC05] reference for the 3D-as-2D-MRT technique. Hardware: GeForce 7600 GT. NO JFA comparison numbers.

Use when:
- Deciding whether to put a hierarchical pre-pass in front of `VolumetricsJFASeed.compute` / `VolumetricsJFARefine.compute` / `VolumetricsJFAResolve.compute`.
- Reasoning about the FHA-as-pre-pass / JFA-as-tail hybrid (EG paper Sec. 4.1 last paragraph: replacing the trailing $j$ FHA propagations with the last $j$ JFA steps trims $e_\text{voxel}$ by up to 1% on 64³).
- Picking between FHA and JFA based on seed density:
  - **Dense seeds** (full mesh sampling) → JFA wins on accuracy ($e_\text{voxel}\approx 0.1\%$ vs FHA's ≈5% even at `+16`).
  - **Sparse seeds** (≤130 keypoints) → FHA+2 is exact while JFA(+0) develops errors at 34/130 seeds.
- Bounding the per-step error formally → cite the **tech report Property 1** ($\sqrt{3}\Delta$ worst case in 3D, $\frac{\sqrt{3}}{2}\Delta$ typical push-down).
- Implementing the FHA pipeline → tech report §5 has the canonical layout (4 MRT textures × sub-regions, `minDistance` GLSL primitive used for both super-sampling and 3×3×3 propagation).

Key constants that survive across GPU generations (relative ratios, not absolute FPS): FHA ≈ 11× faster than JFA on a 128³ grid; FHA's dense-seed `e_max` floor is roughly 1 voxel without `+j` and ≈0.1 voxel at `+16`; JFA hits sub-voxel accuracy at `+1`. Tech-report-specific: hierarchy alone (no JFA) gives ≈10× speed-up vs non-hierarchical pure propagation (30 FPS vs 3 FPS on 64³, kp=1).

Storage: 3D voxel grids stored as **stacks of 2D textures**, one per hierarchy level, so pull-up can mask "still-$\pm M$" voxels cheaply. Tech report uses MRT with sub-region tiling to support up to 256³ on GL2-era hardware (the 2048-pixel 2D-texture limit divided by 8 sub-regions per axis).
