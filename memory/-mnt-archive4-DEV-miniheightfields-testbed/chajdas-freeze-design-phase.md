---
name: chajdas-freeze-design-phase
description: Chajdas shadow/BVH freeze-bake tech design is complete and reviewed; wave-0 probes gate all integration
metadata: 
  node_type: memory
  type: project
  originSessionId: eac2ed69-bd2f-4105-b2bd-b96b15c2f044
  modified: 2026-07-22T00:16:17.867Z
---

The chajdas-freeze orchestration (packing-streaming branch, 2026-07-22) produced a tech design
hardened through two fresh-eyes review rounds, final at rev 4:
`docs/orchestrate/chajdas-freeze/05-design.md`. Freeze-time derive stage (archive→archive,
reads frozen bytes) bakes TWO co-indexed VT layers into zvra v4: `_Bounds` (per-texel R16G16
min/max per tile per frozen mip — a USER-VETOED shape correction: never a fixed per-terrain
grid; pinned basemap root + streamed finer tiles + parent-walk = bounds-lead-payload) and
`_FarShadow` (per-LOD per-sun-step binary bits, R32G32_UInt words). The frozen near trace
marches `_Bounds.g` directly (unification — per-frame occluder build ~0; window is
procedural-only); single cull model with full-slab fallback; far term morph-matched-blends
between mips (D34); sliding pyramid + drain apparatus + dual cull tiers removed. The recurring
conservatism class all three review rounds hit: bounds must cover the renderer's reconstruction
support in every dimension it interpolates — space (bilinear dilation) and mip (finalize fold).
Spec with all user amendments: `docs/orchestrate/chajdas-freeze/00-spec.md`.

**Wave 0 gates everything:** four probes on the real harness (P1 bake-vs-CPU-horizon oracle, P2
near-trace cost with 1.0 ms kill criterion, P3 seam+popping capture→user-eye, P4 step
placement) — standalone-sandbox PoC explicitly rejected as scheduling. Probe gates seed each
wave's battery gate red-first.

Key settled decisions: light-path provider seam (`time ↦ sun direction`; zori atmospherics
Celestial at `/mnt/archive4/UNITY/Projects/zori_test_bed/is.zori.atmospherics/Runtime/Celestial/`
is the production provider; resolved step table in archive metadata is the provider-agnostic
staleness record); time-of-day is runtime-free, lat/lon/date are bake inputs (re-freeze —
product distinction owed to Documentation~ at implementation); bake is PoC-grade and may
re-evaluate procedural content; Chajdas compression deferred to refactor box.

Continuation is fully staged: paste-ready wave-0 dispatch briefs at
`docs/orchestrate/chajdas-freeze/07-wave0-briefs.md` (DAG P1∥P2 → P3 → P4; P3 has a hard
user-QA stop), session handoff + kickoff line at `08-handoff.md`, refactor-box entries
propagated. The user runs implementation sessions on Opus orchestrators from the handoff.
Design final at rev 5 (adds the freeze control panel §6.3 with exact live pricing, D35/D36 —
36 decisions total). The user approved the relayed design state 2026-07-22 ("everything looks
proper to me") — waves proceed without a further punch pass; surface a decision only when new
information contradicts it. An Opus continuation session was launched via Orca in the
packing-streaming worktree with the /delegate kickoff from `08-handoff.md`. See [[freeze-is-all-or-nothing]],
[[editor-decides-player-executes]].
