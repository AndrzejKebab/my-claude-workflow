# Surface Cache GI (URP) — cache population, ray-traced update, and the heightfield-mesh integration gap

Source roots (`swordgal`, `com.unity.render-pipelines.{universal,core}` PackageCache — hash suffix is resolved per install, re-verify if it drifts):

- `Library/PackageCache/com.unity.render-pipelines.universal@a69739b4d5a0/Runtime/RendererFeatures/SurfaceCacheGIRendererFeature/{SurfaceCacheGIRendererFeature.cs,SurfaceCacheWorldAdapter.cs}`
- `Library/PackageCache/com.unity.render-pipelines.core@f9bd39fba82f/Runtime/Lighting/SurfaceCache/SurfaceCacheWorld.cs`
- `Library/PackageCache/com.unity.render-pipelines.core@f9bd39fba82f/Runtime/UnifiedRayTracing/Common/AccelStructAdapter.cs`
- `Library/PackageCache/com.unity.render-pipelines.core@f9bd39fba82f/Runtime/PathTracing/World.cs` (offline/editor path tracer world — cited only for contrast)

Gated behind `#if SURFACE_CACHE`. Requires ray tracing hardware or the compute fallback (`SystemInfo.supportsRayTracing`, `SurfaceCacheGIRendererFeature.cs:1019-1021`). Incompatible with Static Batching — the feature refuses to run and logs `k_StaticBatchingErrorMesssage` if Static Batching is enabled for the active build target (`SurfaceCacheGIRendererFeature.cs:99, 1014-1017, 1098-1101`).

## 1. What it is

One `SurfaceCacheGIRendererFeature` per renderer owns:

- a **`SurfaceCacheWorld`** (core RP) — the realtime ray-tracing scene: accel structure (`AccelStructAdapter` wrapping `IRayTracingAccelStruct` + `GeometryPool`), material pool, punctual/directional light lists, environment cubemap.
- a **`SurfaceCache`** (core RP, referenced but not read for this page) — the actual surface-patch cache: a cascaded voxel volume of "patches" holding irradiance + statistics, updated by ray-traced light estimation.
- a **`SurfaceCacheWorldAdapter`** (URP glue, `SurfaceCacheWorldAdapter.cs`) — keeps `SurfaceCacheWorld` in sync with the live scene using `UnityEngine.InternalBridge.ObjectDispatcher`.

Per-frame flow in `SurfaceCachePass.RecordRenderGraph` (`SurfaceCacheGIRendererFeature.cs:510-817`):

1. Volume-driven parameter resolve (`SurfaceCacheGIVolumeOverride`); reallocates the cache if resolution/cascade-count changed structurally (:535-551).
2. Flat-normal resolve pass (compute) from camera depth.
3. Patch-allocation pass (compute) — maps screen tiles to cache voxel cells, seeded by depth/flat-normal/motion-vectors (motion-vector seeding is disabled in Scene View: `UseMotionVectorPatchSeeding`, :109-112).
4. `_worldAdapter.Update(...)` (:678-688) — syncs MeshRenderers/Terrains/Lights/Materials/ambient into `SurfaceCacheWorld` (§2).
5. `UpdateWorld` unsafe pass — commits the accel structure build + material pool + env cubemap (:690-700, :819-827).
6. `_cache.RecordPatchUpdate(...)` — the actual ray-traced/estimated irradiance update per patch (opaque call into `SurfaceCache`, not in this file).
7. Screen-space lookup (:704-740) + spatial/temporal upsampling (:781-812) → `resourceData.irradianceTexture`, the texture lit shaders sample.

## 2. How the cache populates — world discovery

`SurfaceCacheWorldAdapter` is built on `UnityEngine.InternalBridge.ObjectDispatcher` (`SurfaceCacheWorldAdapter.cs:27-48`) — an internal Unity bridge giving cheap, incremental "what changed this frame" streams, keyed by `EntityId`. It enables tracking for exactly four types:

- `MeshRenderer` — type tracking (add/remove/property change) + transform tracking (Global TRS).
- `Light` — same.
- `Material` — type tracking only (scene objects + assets).
- `Terrain` / `TerrainData` (if `ENABLE_TERRAIN_MODULE`) — same as MeshRenderer.

Nothing else is tracked. No `SkinnedMeshRenderer`, no arbitrary custom `Renderer` subclass, no `MeshFilter`-alone changes, and critically: **no procedural `Graphics.Draw*` / `cmd.Draw*Indirect` call of any kind** — those never touch a component the dispatcher watches.

### MeshRenderer path (`MeshRendererSet`, :244-482)

A renderer enters the world when `enabled && activeInHierarchy && MeshFilter.sharedMesh != null && vertexCount != 0`, it is not part of a static batch, and its `renderingLayerMask` passes the volume filter. First-seen → `SurfaceCacheWorld.AddInstance(mesh, materialHandles, masks, localToWorldMatrix)` (`SurfaceCacheWorld.cs:434-459`) → `AccelStructAdapter.AddInstance(Mesh, ...)` (`AccelStructAdapter.cs:144-164`) → `GeometryPool` pulls the mesh's **GPU** vertex/index buffers directly — `mesh.GetVertexBuffer(stream)` / `mesh.GetIndexBuffer()`, forced to `GraphicsBuffer.Target.Raw` (`GeometryPool.cs:731-762`) — and compute-copies them **once** into a shared consolidated pool buffer backing the BLAS/AABB build.

That one-shot copy matters: only three update paths exist afterward — `UpdateInstanceTransform`, `UpdateInstanceMask`, `UpdateInstanceMaterials` (`SurfaceCacheWorld.cs:487-506`). There is no "re-copy this instance's geometry" call. A mesh that mutates its own vertex buffer in place (same `Mesh` object, new positions written by a compute shader) is not re-ingested — the cache keeps ray-tracing the shape captured at registration time. Nor is a `MeshFilter.sharedMesh` reference swap tracked at all (only `MeshRenderer`/`Light`/`Material`/`Terrain`/`TerrainData` get `EnableTypeTracking` — not `MeshFilter`), so a chunk-swap pattern (assigning a new mesh to an existing `MeshFilter` to avoid GameObject churn) also goes unnoticed. The only proven refresh trigger is whatever the dispatcher's `MeshRenderer` type-tracking actually fires on — enable/disable and destroy/create go through a full remove+re-add (`Refresh`, :279-309).

**This paragraph is read from the code, not confirmed by an in-engine sabotage test.** Verify before depending on it: deform a registered mesh's vertex buffer in place, capture two GI-bounce frames, diff them (`/usr/bin/diff` or a perceptual metric — see this workflow's `diff` gotcha in the top-level `CLAUDE.md`), confirm whether the cache actually updates.

Materials need a compiled `"Meta"` shader pass (`FindPass("Meta") != -1`) or the fallback material silently substitutes, logging one error naming the offending material and renderer (`SurfaceCacheWorldAdapter.cs:454-471`). This is the same convention Unity's baked lightmapper has always used to extract GI-relevant surface data (albedo/emission).

### Terrain path (`TerrainSet`, :487-789)

Different from MeshRenderer: at add-time the terrain is **triangulated into a real mesh** (`TerrainToMesh.Convert`, called from `AccelStructAdapter.AddHeightmap`, :178-189) and registered exactly like a mesh instance. A `TerrainData` edit can't be patched in place, so it's handled as remove+re-add of the whole instance (`RebuildInstance`, :753-759), deferred ~30 ticks in editor to coalesce a sculpting stroke (`ProcessDeferredRebuilds`, :625-647) and applied immediately in a player build.

### The raw-heightfield path that exists but isn't wired here

`AccelStructAdapter` also exposes `AddTerrainInstance(short[] heightData, int resolution, float3 heightmapScale, byte[] holeData, int holeResolution, ...)` (`AccelStructAdapter.cs:340-388`) — genuinely procedural ingestion: no `Mesh` at all, just a tiled-AABB acceleration structure (`CreateTerrainAabbBuffer`, 8×8-cell tiles, `_terrainTileWidth`) plus a heightmap atlas texture (`Texture2DArray`, grown incrementally as terrains are added, :303-338) sampled by a custom analytic ray/heightfield intersection. This is the closest thing Unity ships to "feed a raw heightfield straight into ray tracing."

It is **not used by `SurfaceCacheWorld`/`SurfaceCacheGIRendererFeature`** — `TerrainSet.AddToWorld` goes through `TerrainToMesh.Convert` instead (mesh path, above). `AddTerrainInstance` is wired only into the **offline/editor** path tracer world (`Runtime/PathTracing/World.cs:578-607`, used by the Progressive Lightmapper) and Adaptive Probe Volume baking (`Editor/Lighting/ProbeVolume/ProbeGIBaking.{VirtualOffset,SkyOcclusion,RenderingLayers}.cs`). So the realtime GI cache this renderer feature drives has no supported raw-heightfield entry point today, even though Unity's own baked-GI stack has one.

## 3. Integration verdict: `is.zori.miniheightfields` / `HeightfieldMeshRenderer`

Current home: `/mnt/archive4/ORCA/miniheightfields_testbed/packing-streaming/is.zori.miniheightfields/` (supersedes a prior copy at `.../woweyreey/Packages/is.zori.heightfields/`; per the project owner the rendering approach carried over largely unchanged — what moved is the shader authoring path, now strictly ShaderGraph-based). `swordgal` itself does not have this package installed; these citations are cross-project.

Findings, most decisive first:

1. **`HeightfieldMeshRenderer` (`Runtime/Core/Terrain/HeightfieldMeshRenderer.cs`) is a plain `MonoBehaviour`** carrying LOD/quality parameters and a `WorldBounds` property documented as "Used for RenderMeshIndirect culling bounds" — no `MeshFilter`, no `MeshRenderer`, no `Terrain` component. `ObjectDispatcher` has nothing to track here at all.
2. **Actual triangles are issued by `cmd.DrawMeshInstancedIndirect`** inside the render feature's own RenderGraph passes (`Runtime/Core/Rendering/DrawCameraTerrains.cs`), against a GPU-built quadtree of patch tiles and an indirect-args buffer. A raw `cmd.Draw*` call is invisible to any component-based scene-graph walk — it isn't a `MeshRenderer`, so no amount of "does it have a valid mesh" checking will ever surface it.
3. **Even the mesh that does exist (`HeightfieldPatchMesh.cs`) wouldn't help.** It's a small, flat, undisplaced patch template (`new Mesh` + `SetIndices(..., MeshTopology.Triangles, 0)`) — the actual terrain shape comes from per-vertex displacement done in the vertex stage (procedural instancing sampling a height texture/StructuredBuffer at draw time), not stored in the mesh. `GeometryPool` only reads a mesh's *stored* vertex buffer — it never runs a vertex shader. This is a general Unity ray-tracing constraint (vertex/pixel-shader displacement and tessellation never reach a BLAS unless the displaced result is baked into its own buffer first), not something specific to Surface Cache.
4. **Meta-pass status of the production terrain material is unresolved — two prior guesses here were wrong, corrected for the record.** The terrain surface shader is `Runtime/Materials/Heightfields Terrain Shader.shadergraph`. Checked directly in the asset's own JSON (`grep` on `m_ActiveTargets`/`m_Type`, not a filename guess): this single ShaderGraph asset carries **two active targets** — `UnityEditor.Rendering.Universal.ShaderGraph.UniversalTarget` paired with `UniversalLitSubTarget` (standard URP Lit codegen — Forward/GBuffer/DepthOnly/ShadowCaster and, per that subtarget's default codegen, ordinarily a Meta pass), *and* `Zori.MiniHeightfields.ShaderGraph.HeightfieldStampTarget` riding along in the same asset, contributing only its extra "StampBasemap" SubShader for the offscreen procedural-stamp compositing draw — not the terrain's main rendering passes. So the Meta pass most likely exists (standard `UniversalLitSubTarget` behavior), but this is inferred from the subtarget type, not from opening the generated `.shader` and counting passes. **Verify with `material.FindPass("Meta") != -1` in-editor before relying on either verdict.**

Net: **Surface Cache GI is currently blind to the heightfield terrain regardless of finding 4** — findings 1-3 alone are sufficient (no `MeshRenderer`, no component-visible draw call, no stored displaced geometry). No shadow cast into the cache, no light bounce off it, no occlusion. Silently: no error, no warning, it simply never registers.

## 4. Options if GI interaction with the terrain is wanted

Ranked by how much of the existing architecture stays intact:

1. **GI-proxy mesh, GPU-authored, no CPU readback (recommended).** A coarse, real `MeshRenderer` + `MeshFilter` sibling whose `Mesh` is populated by a **compute bake** (not sampled at vertex-shader time — see finding 3), on a coarse cadence (LOD-root change, or every few seconds — not per-frame). This is fully compatible with `GeometryPool`'s ingestion path without any CPU round-trip: `GeometryPool` never touches `Mesh.vertices`/`Mesh.triangles` — it calls `mesh.GetVertexBuffer(stream)` / `mesh.GetIndexBuffer()` (real GPU `GraphicsBuffer` handles, forced to `GraphicsBuffer.Target.Raw`) and compute-copies them GPU→GPU into its own pool buffer (`GeometryPool.cs:731-762`). So the proxy mesh's recipe is the standard GPU-authored-mesh pattern: declare layout only on the CPU side (`Mesh.SetVertexBufferParams`/`SetIndexBufferParams`, or `Mesh.AllocateWritableMeshData`, with `vertexBufferTarget`/`indexBufferTarget` including `.Raw` set *before* those calls), then dispatch a compute shader that writes displaced positions/normals straight into `mesh.GetVertexBuffer(stream)` as an `RWStructuredBuffer` — zero float data ever crosses back to the CPU for registration. Use a Meta-pass-carrying material (confirm/adjust per finding 4).

   This doesn't remove the one-shot-ingest constraint from §2, though: `GeometryPool` copies geometry into its pool **once**, at `AddInstance` time, and there's no "refresh this instance's geometry" call. A periodically-regenerated/streamed proxy still needs an explicit remove+re-add each time its baked geometry changes meaningfully — also fully GPU-side (Remove+Add just re-pulls the buffer), but it re-registers a BLAS/AABB entry rather than patching one in place, so cadence still needs to be chosen deliberately, not driven every frame. Given the copy-on-register semantics, an in-place buffer mutation on an otherwise-unchanged `MeshRenderer`/`Mesh` reference is *not* picked up (neither is a `MeshFilter.sharedMesh` swap — see §2) — validate the remove/re-add refresh path by sabotage test (bake new geometry, diff two GI-bounce captures) before relying on it.
2. **Route through `AddTerrainInstance`.** Shape-matches what a heightfield already has (raw heightmap + scale), avoiding the proxy-mesh double-authoring problem — but means patching Unity's own package source (`Library/PackageCache/...`, not project-owned) to wire the realtime `SurfaceCacheWorld` to the procedural path only the offline baker uses today. An unversioned engine fork, defensible only as a deliberate, documented decision, never a quick patch.
3. **Accept the gap.** Mark the terrain GI-invisible and fake the interaction where it matters most (e.g. an ambient-occlusion or bent-normal hack for objects near the terrain) rather than fighting a closed realtime pipeline.

## What this page deliberately does NOT cover

- `SurfaceCache`'s internal patch-update math (ray estimation, temporal/spatial filtering coefficients) — opaque in this pass, lives in core RP's `SurfaceCache` type (not read for this page).
- HDRP's Surface Cache integration, if any — URP only, per this project.
- The offline path tracer / Adaptive Probe Volume baking pipeline in depth — cited only for contrast in §2.
