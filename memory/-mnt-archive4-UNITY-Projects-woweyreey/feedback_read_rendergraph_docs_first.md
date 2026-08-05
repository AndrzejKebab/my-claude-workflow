---
name: Read docs/unity/rendergraph/ before any RG work
description: Project canon for RenderGraph patterns lives in docs/unity/rendergraph/ — read it before writing/modifying any RG passes, depth target selection, camera state restoration, or global texture publishing
type: feedback
originSessionId: 4a8b4ff4-6561-438a-bc2c-9c3487253d4a
---
Always read `docs/unity/rendergraph/` before writing or modifying RenderGraph code (raster/compute/unsafe passes, custom features touching `_CameraDepthTexture`, shadow atlases, camera matrices, global texture publishing).

**Why:** Multiple recent debugging sessions (2026-05-06: heightfield RG migration — depth-target choice, camera state isolation around shadow caster) rediscovered things already documented in `docs/unity/rendergraph/`. Speculative fixes without consulting the docs cost hours and produce regressions when toggling unrelated features (e.g. distant shadows on/off flips `useDepthPriming` and changes `cameraDepthTexture` format from depth-stencil to R32_SFloat).

**How to apply:** Before the first edit on any RG-touching task:
- Open `docs/unity/rendergraph/index.md` and pick the relevant doc.
- For depth-prepass-style passes: `depth-targets.md`.
- For passes that mutate camera matrices (cascade rendering, atlas blits): `camera-state-isolation.md`.
- For compute reading URP shadow globals: `shadow-sampling-from-compute.md`, `global-state.md`.
- For sampler binding / collisions: `samplers.md`.
- For pattern mirroring: `empirical-examples.md`.

The rule is also recorded in the project CLAUDE.md `## Unity API canon — docs/unity/` section, which is the single entry point for all four docsets (`rendergraph/`, `jobs/`, `burst/`, `entities/`).
