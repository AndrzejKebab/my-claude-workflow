# Surface Cache GI (URP) and GPU-driven geometry

This page records the integration constraints that matter when a URP Surface
Cache GI implementation must see procedural, voxel, or heightfield geometry.
Verify details against the Render Pipeline packages installed with the current
Unity Editor because this feature and its internal APIs can change.

Relevant source roots:

- `Library/PackageCache/com.unity.render-pipelines.universal@<version>/Runtime/RendererFeatures/SurfaceCacheGIRendererFeature/`
- `Library/PackageCache/com.unity.render-pipelines.core@<version>/Runtime/Lighting/SurfaceCache/`
- `Library/PackageCache/com.unity.render-pipelines.core@<version>/Runtime/UnifiedRayTracing/`

If the Render Pipeline packages are built into the Editor, inspect them under:

```text
F:\Unity Editors\<version>\Editor\Data\Resources\PackageManager\BuiltInPackages\
```

## What the feature owns

A Surface Cache GI renderer feature typically owns:

- A ray-tracing world and acceleration structure.
- A surface-patch cache containing irradiance and statistics.
- An adapter that synchronizes supported scene objects, materials, lights, and
  transforms into that world.

The broad per-frame flow is:

1. Resolve volume parameters and resize the cache when its structure changes.
2. Resolve camera-space depth and normal inputs.
3. Allocate or update visible surface patches.
4. Synchronize supported scene geometry, lights, and materials.
5. Build or update acceleration structures.
6. Trace or estimate lighting into the cache.
7. Resolve, spatially filter, and temporally filter the screen-space result.

## Geometry discovery boundary

Inspect the current implementation's world adapter or object dispatcher to see
which component types it tracks. A component-driven discovery path commonly
recognizes standard objects such as `MeshRenderer`, `Terrain`, `Light`, and
`Material`.

Procedural calls such as `Graphics.Draw*`, `CommandBuffer.Draw*Indirect`, and
custom GPU-driven renderer components are not automatically discoverable. A
draw command does not create a scene component for the world adapter to track.

This is the first question for a voxel renderer: does the GI system discover
the renderer's geometry representation at all?

## Geometry ingestion and updates

A discovered `MeshRenderer` may be ingested by copying its GPU vertex and index
buffers into an internal geometry pool. Confirm whether that copy happens only
when the instance is registered or whether the active Unity version provides a
geometry-refresh path.

Do not assume that either of these updates is detected:

- Mutating an existing mesh's vertex buffer in place from compute.
- Replacing `MeshFilter.sharedMesh` while retaining the same renderer.

Test the behavior in-engine. Change the geometry drastically, capture frames
before and after, and compare the GI, occlusion, and acceleration-structure
result. Re-registering or recreating the renderer may be necessary when baked
geometry changes.

## Vertex displacement is not stored geometry

A flat template mesh displaced in a vertex shader remains flat in systems that
only ingest the mesh's stored vertex buffer. Shader displacement and
tessellation do not automatically become acceleration-structure geometry.

For a GPU-driven voxel or heightfield renderer, the GI representation must
therefore use one of these approaches:

- Real displaced vertices written into a mesh buffer before ingestion.
- A supported procedural-geometry or heightfield ingestion API.
- A deliberately simplified proxy mesh.
- No Surface Cache participation, with another approximation for interaction.

## Material requirement

Surface-cache population commonly requires a valid `Meta` shader pass for
albedo and emission extraction. Verify the actual runtime material:

```csharp
bool hasMetaPass = material != null && material.FindPass("Meta") >= 0;
```

Do not infer this only from a Shader Graph filename or target. Check the
generated shader or query the material in the Editor.

## Integration checklist for a voxel renderer

1. **Discovery:** Is there a tracked `MeshRenderer`/`Terrain`, or only an
   indirect draw issued by a custom renderer feature?
2. **Geometry:** Does the registered buffer contain final world-space or
   object-space surface geometry, rather than a shader-displaced template?
3. **Refresh:** What exact event causes changed chunks to be re-ingested?
4. **Lifetime:** Who owns the proxy meshes and removes them when chunks unload?
5. **Material:** Does every GI-visible material have a working `Meta` pass?
6. **Filtering:** Do rendering-layer masks include the intended voxel chunks?
7. **Batching:** Is static batching disabled if the active implementation is
   incompatible with it?
8. **Platforms:** Is hardware ray tracing available, and is the compute fallback
   acceptable on every target platform?
9. **Budget:** What is the update cadence and geometry cost for dirty chunks?
10. **Verification:** Can a controlled geometry or emissive-material change be
    observed in the cache on the next expected update?

## Integration options

### GPU-authored proxy mesh

Create a coarse real `Mesh` with a `MeshFilter` and `MeshRenderer`. Allocate its
vertex/index layout on the CPU, then write displaced positions and normals into
the GPU buffers from compute. This avoids CPU geometry readback while exposing
a standard renderer the GI discovery path can see.

If ingestion copies geometry only at registration, modifying the buffer is not
enough: re-register or recreate the proxy after meaningful changes. Choose a
coarse cadence based on dirty chunks or LOD-root changes rather than rebuilding
every frame.

### Supported procedural or heightfield ingestion

Some Unity ray-tracing internals contain raw-heightfield or procedural geometry
paths used by offline baking. Confirm whether the realtime Surface Cache world
exposes and calls such a path in the installed version. If it does not, wiring
an internal API requires maintaining a version-specific Render Pipeline fork.

### Accept the gap

If proxy geometry or a package fork costs more than the visual benefit, keep
the voxel terrain out of Surface Cache GI and approximate the most visible
interaction with ambient occlusion, probes, bent normals, or another project-
appropriate solution.

## What this page does not cover

- Surface Cache's internal ray-estimation and filtering math.
- HDRP integration.
- Offline path tracing or Adaptive Probe Volume baking beyond comparison with
  the realtime discovery and ingestion paths.
