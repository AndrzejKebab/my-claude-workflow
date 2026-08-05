---
name: grz-weapon-mesh-extraction
description: Gruzzam weapons are baked into the character skeletal mesh; extract a standalone static mesh via GeometryScript
metadata: 
  node_type: memory
  type: project
  originSessionId: a6449e5c-3bc7-4367-95e1-b6f90823fdd5
---

The Gruzzam (Grz_HammerPack) weapons are NOT standalone assets — the hammer is baked into
`Grruzam_*Modeling_Hammer_include_Weapon` skeletal meshes as 3 material sections
(`03_-_Default33*`) skinned to a `Grruzam_Weapon_Hammer` bone; the `_Default` variant is the
body without it. To use one as a held weapon you must extract it.

`Scripts/extract_grz_hammer.py` does this: a GeometryScript commandlet —
`copy_mesh_from_skeletal_mesh` at ref pose → identify the body material id by triangle count
(largest section; copy reorders ids so the body is NOT always id 0) → `delete_triangles_by_material_id`
→ **express the hammer in hand_r-local space** → `create_new_static_mesh_asset_from_mesh` →
assign materials slot==id. Result: `/Game/_Project/Armaments/Meshes/SM_Grz_Hammer` (194 tris).
The **GeometryScripting** plugin is now enabled in FARTS.uproject for this.

CRITICAL for the grip (1b6b978b): do NOT bbox-center the extracted mesh — that floats it. The
example holds the hammer because it's skinned into the hand chain, so spawn a SkeletalMeshActor
with the source mesh, read `hand_r`'s component-space ref transform
(`comp.get_socket_transform("hand_r", RelativeTransformSpace.RTS_COMPONENT)`), and
`inverse_transform_mesh(dm, H)` so the grip sits at the origin in hand_r space. `AFartsHammerActor`
then attaches to the FARTS `hand_r` socket with an **identity** mesh transform (both are UE-Manny
`hand_r`, so it transfers). The melee damage zone is separate — keep it at the forward-reach
position the swing animation expects (`+X` on the hand), not at the visual head, or `hammer_hit`
fails. Visual grip check: `-game ... -FartsProbeArmaments -FartsGripShot` writes
Saved/Screenshots/LinuxEditor/grz_hammer_grip.png.

UE-python API gotchas that cost iterations: `IDs`→`_i_ds` in method names
(`get_num_triangle_i_ds`, `get_max_material_id`); count triangles per material via
`select_mesh_elements_by_material_id` + `get_mesh_selection_info` (the IndexList from
`get_triangles_by_material_id` won't convert to a python array); MCP `call_tool` arg key is
`arguments` (not `parameters`/`params`), with `toolset_name` + short `tool_name`.

Extracted meshes' materials reference the untracked Grz_HammerPack, so they render grey
without the pack. The hold transform lives on `AFartsHammerActor`'s Mesh component
(`FartsWeaponActors.cpp`). See [[farts-als-character-foundation]], [[farts-avatar-part-dynamics]].
