---
name: ue-headless-python-authoring
description: "How to author UE assets headlessly in FARTS when MCP isn't connected — python commandlet pattern + gotchas"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5964ff4e-2d93-496f-ac4e-a1d269a71074
---

For FARTS asset authoring without the editor's MCP bridge (e.g. after a restart, when `mcp__unreal/voxel` tools aren't registered), drive a one-shot Python commandlet:

`UnrealEditor-Cmd FARTS.uproject -run=pythonscript -script="/abs/path.py" -unattended -nop4 -nullrhi -nosplash -nosound -stdout`

Engine binary: `/mnt/archive4/UNREAL/UE_5.8.0/Engine/Binaries/Linux/UnrealEditor-Cmd`. Kill any running editor first (it holds asset locks). Boots, runs script, exits in seconds.

Gotchas (all hit and solved 2026-06-24):
- `unreal.log()` / `print()` do NOT reliably reach captured stdout in commandlet mode. Write results to an explicit file (`open(...).write(); flush()`) and read that.
- Use `unreal.load_asset(path)` (direct LoadObject), NOT `EditorAssetLibrary.load_asset` — the latter checks the asset registry, which doesn't have `/Engine` content scanned in a commandlet, so engine assets (e.g. `/Engine/EngineMaterials/DefaultNormal`) fail to load.
- `/Engine/EngineMaterials/DefaultNormal` is NOT a flat (0,0,1) normal — it's a ~2 MB checkerboard/test texture. Do NOT use it as a "neutral" normal default; sampling it yields a visible pattern. `DefaultNormal_Uncompressed` (~11 KB) is the small one. For a real flat default, point at an actual surface normal map instead.
- `set_material_instance_*_parameter_value` silently no-ops if the param name isn't on the parent — always verify by reading back the MI's `texture_parameter_values`/`scalar_parameter_values`/`vector_parameter_values` editor-property arrays.
- `UMaterial.get_editor_property("expressions")` is deprecated in 5.8 → use `get_expressions()`. `UObject` has no `has_editor_property` in Python — wrap property reads in try/except.
- Exit code 1 with "Failure - N error(s)" is usually the benign GameFeatureData asset-manager init errors, not your script. Check your own RESULT line.
- Pre-existing env noise: `Intermediate/Build/XmlConfigCache.bin` "Permission denied" (root-owned from a prior sudo build) — non-fatal, the commandlet still runs.

More gotchas (2026-06-24, ALS foundation session):
- `EditorAssetLibrary.duplicate_asset` / `load_blueprint_class` DO hit the asset registry, which is NOT scanned for `/Game` or plugin (`/ALS`) content in a fresh commandlet → they silently fail/return None. Run `unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(["/Game","/ALS"], True)` FIRST. (`load_asset` alone also needs this for `/ALS` plugin content.)
- Commandlet `EditorActorSubsystem.spawn_actor_from_class/object` does NOT persist into a saved level (actors vanish on reload; `save_current_level`/`save_dirty_packages` don't capture them). Place level actors in the LIVE editor via MCP `SceneTools.add_to_scene_from_class/asset` instead.
- UE5.8 `UInputMappingContext` stores key mappings in `default_key_mappings` (a single `InputMappingContextMappingData` object), NOT the legacy `mappings` array (which reads empty). Clone+remap of an IMC must go through that; simplest is to reference the source IMC + IAs directly.
- `USkeleton` has NO python reader for virtual bones (`get_editor_property("virtual_bones")` fails; no `get_virtual_bones`). It DOES expose `add_compatible_skeleton(other)`, `get_num_curve_meta_data()`, and `compatible_skeletons` property. ALS skeleton setup = `unreal.AlsSkeletonUtility.add_animation_curves/add_or_replace_slot/add_or_replace_virtual_bone` (from ALSEditor). To read a VB's source bone, use SkeletalMeshTools `get_bone_parent` on the "VB ..." bone (target not exposed).
- Headless `-RenderOffScreen` `StartPIE` HANGS the game thread (all MCP calls then time out) — do PIE QA headful, not headless. A periodic DDC maintenance scan (~2 min, 60k+ files) and first-load shader compilation also block the game thread → MCP calls time out until they finish; wait for CPU to settle.

Launch the persistent headless editor for MCP via `setsid nohup UnrealEditor FARTS.uproject [/Game/Map] -RenderOffScreen -nosplash -stdout -FullStdOutLogOutput -unattended & disown` (or the Bash tool's `run_in_background`). MCP on 127.0.0.1:8000; toolsets register ~10-15s after launch. `-RenderOffScreen` (GPU working as of 2026-06-24, Vulkan OK) is preferable to `-nullrhi` when any toolset may touch RHI. Related: [[farts-ue58-buildid-mismatch]], [[voxelmcp-plugin]], [[farts-als-character-foundation]].

**Scope limit (2026-08-05):** this applies to asset PROPERTIES only. Python has no node API — anim graphs, Control Rig graphs and Blueprint graphs cannot be authored headlessly, and the failure is a stub that loads and does nothing rather than an error. Those are MCP jobs. See [[canonical-road-not-code-workarounds]].
