# Voxel World Project Memory

## Project Structure
- Unity project: `/mnt/archive4/DEV/voxel_world/voxels_unity_project`
- Package: `Packages/com.midori.voxel-world/`
- Runtime asmdef: `com.midori.voxel-world.runtime`
- Tests: EditMode in `Tests/`, PlayMode in `Tests/PlayMode/`
- Native lib: `Runtime/Plugins/x86_64/libvoxel_unity.so` (Rust FFI)

## Architecture (v0.3.0 → ECS Rendering)
- **Pure ECS rendering** using `Unity.Entities.Graphics` (no GameObjects)
- `EntitiesGraphicsSystem` manages mesh/material registration (`BatchMeshID`/`BatchMaterialID`)
- Prototype entity pattern: create once per material, `ECB.Instantiate` for each chunk
- Prototypes need `Prefab` tag (excluded from queries, stripped on Instantiate)
- `ICleanupComponentData` NOT copied by `Instantiate` — use `ecb.AddComponent` not `SetComponent`

## Key Unity ECS Patterns
- **No structural changes during iteration**: collect entities in NativeList first, then modify
- `SystemAPI.Query<>` foreach holds an implicit iteration lock — even `EntityManager.CreateEntity()` inside it fails
- `RequireAnyForUpdate` needed when system must run for BOTH active entities AND cleanup
- Assembly name for entities.graphics: `Unity.Entities.Graphics` (NOT `Unity.Rendering.EntitiesGraphics`)
- `BatchMeshID`/`BatchMaterialID` are in `UnityEngine.Rendering`; `EntitiesGraphicsSystem`/`MaterialMeshInfo`/`RenderMeshUtility` are in `Unity.Rendering`

## Testing
- PlayMode tests use default World (not custom) for proper system group scheduling
- `-nographics` flag prevents `EntitiesGraphicsSystem` from working — use graphics-enabled batch mode for PlayMode tests
- PlayMode test asmdef needs: `UnityEngine.TestRunner`, `UnityEditor.TestRunner` references
- Test fixture creates native world directly (bypasses SdfSceneBuildSystem baking)
- `InternalsVisibleTo` in `AssemblyInfo.cs` for test access to system internals

## FFI Details
- `voxel_world_update()` returns `FfiPresentationBatch` with transition groups
- World IDs are int handles from Rust side
- `FfiChunkKey`: grid_x/y/z + lod byte (16 bytes)
