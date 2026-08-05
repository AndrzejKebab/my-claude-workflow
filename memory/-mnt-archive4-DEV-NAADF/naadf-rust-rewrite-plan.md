---
name: naadf-rust-rewrite-plan
description: "Plan to rewrite NAADF as a Rust app with wgpu + wgpu_dlss, Vulkan + DX12 backends"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5c67887c-38f4-43eb-9ff8-621faa0882ac
---

The NAADF voxel GI engine (currently C#/MonoGame-Compute/DX11, Windows-only — see [[naadf-runs-on-linux-via-wine]]) is planned to be rewritten in **Rust with wgpu**, using the **`wgpu_dlss`** crate for DLSS Ray Reconstruction, targeting the **Vulkan + DX12** backends.

Decided direction (user was firm — don't re-litigate scope/API):
- **Keep** from the paper (Ulschmid et al., EUROGRAPHICS 2026, `/mnt/archive4/DEV/Kova/docs/research/ulschmid-2026-naadf-voxel-gi.md`): the NAADF data structure, ray traversal, and the compressed ReSTIR GI front-end (adaptive ray queue + lit/unlit split + 8×8 region resampling).
- **Replace** the reconstruction tail (the paper's long-term-memory 32-frame TAA + sparse bilateral denoiser) with **DLSS RR** — behind a trait, with the long-term TAA kept as the non-NVIDIA fallback and benchmark baseline.
- New work RR forces: a G-buffer materialization pass (expand packed `firstHitData` into flat depth/normal/roughness/albedo textures), a motion-vector pass (NAADF's stored virtual-path plane chain makes correct *specular* MVs computable — a genuine advantage), and a render-res ≠ output-res split (secondary trace dominates the frame, so render GI at reduced res + RR upscale).
- Shaders: compile the existing HLSL `.fx/.fxh` to SPIR-V (dxc) + DXIL — no WGSL port, since the browser/WebGPU target was dropped.
- Notes: `wgpu_dlss` only works on Vulkan/DX12 + NVIDIA RTX, pins to specific wgpu versions, ships the `nvngx_dlss` redistributable. The `cpt-max` MonoGame-Compute fork dependency disappears in the rewrite.

Possibly related to Kova (top-down voxel game) — its research notes map NAADF onto Kova's architecture — but the rewrite target (standalone vs Kova renderer) was not pinned down.
