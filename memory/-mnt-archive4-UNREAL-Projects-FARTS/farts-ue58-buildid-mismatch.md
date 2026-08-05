---
name: farts-ue58-buildid-mismatch
description: FARTS UE5.8 source build BuildId split; what's benign vs what actually breaks, and how to fix
metadata:
  node_type: memory
  type: project
  originSessionId: 9a0c2619-b51c-49ff-91d3-05ad12b1c06b
  modified: 2026-08-04T22:05:31.185Z
---

FARTS uses a **source build** of Unreal at `/mnt/archive4/UNREAL/UE_5.8.0` — **the directory name is historical, it holds 5.8.1-release** as of 2026-08-04. Project GUID `A74BB7C6-...`, and since the 5.7 install was retired it is the **only** entry in `~/.config/Epic/UnrealEngine/Install.ini`, so nothing prompts for a version. Editor target = `FARTSEditor Linux Development`.

**BuildId is per-target, and a split is normal.** An engine `make` stamps one id on the engine-wide modules; the subsequent `FARTSEditor` build stamps a different one on what it relinks, and `Engine/Binaries/Linux/UnrealEditor.modules` (the core) carries the *project build's* id. After the 5.8.1 update: core `d67a6241` with 284 modules, and 497 engine-plugin modules left on the make's `9c7e9b71`. Separate program targets (UnrealLightmass, ShaderCompileWorker, UnrealInsights, UnrealFrontend) legitimately carry their own ids. **Comparing every `.modules` file against one id reports "6 distinct BuildIds" and is pure noise** — I made exactly that mistake and had to redo the check.

**What actually matters:** every plugin in the *enabled closure* (`FARTS.uproject` plus transitive `.uplugin` deps — 34 declared → 118 resolved) must match core. UE skips any module whose BuildId ≠ core with no error beyond an eventual "module could not be found", so a stale plugin reads as one that simply never registered. The 497 stale ones are plugins FARTS doesn't enable — harmless until one gets enabled.

**Why a plain build doesn't fix it:** UBT checks source timestamps, not BuildId, so it reports "up to date" (no-op, only WriteMetadata) and never relinks stale modules.

**Tooling now in the repo** (don't rewrite it): `Scripts/check_buildids.py` does both the per-target and closure checks, exiting nonzero only when the closure is dirty; `Scripts/rebuild_project_581.sh` purges Binaries/Intermediate for the project, its plugins and the engine Marketplace plugins, rebuilds, then gates on it. Fix for a dirty closure = delete those Binaries/ + Intermediate/, rebuild `FARTSEditor` (relinks from existing .obj, restamps the id).

**Disabled (broken/heavy, not needed):** `Avalanche` + `MediaIOFramework` (GPUTextureTransfer fails on Linux — no NVIDIA SDK) and `MetaHumanGenerator`. MCP server = `ModelContextProtocol` plugin; actor/level ops come from the `EditorToolset` Python toolsets (`SceneTools`, `ActorTools`). Relates to [[prefer-tools-over-guessing]] and [[ue-engine-update-procedure]].
