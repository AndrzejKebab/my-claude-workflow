# SRP resource & feature-authoring attributes

A reference for the attribute/class vocabulary Unity's own URP features use to declare their shader/material/compute dependencies as first-class, versioned, categorized Editor assets, plus a couple of internal engine idioms worth recognizing when reading or writing this kind of code. Captured against `SurfaceCacheGIRendererFeature.cs` / `SurfaceCacheWorldAdapter.cs` / `SurfaceCacheWorld.cs` (see [`surface-cache-gi.md`](surface-cache-gi.md) for the feature these are pulled from) in this project's `Library/PackageCache/com.unity.render-pipelines.{universal,core}@*` — cross-check signatures against the installed version before copying blind (see the top-level index's version-drift note).

## `IRenderPipelineGraphicsSettings` + `[ResourcePath]` — versioned, path-resolved resource assets

A render feature that needs its own shaders/materials/compute shaders wraps them in a small `IRenderPipelineGraphicsSettings` implementation instead of exposing raw `[SerializeField]` fields on the feature itself:

```csharp
[Serializable]
[SupportedOnRenderPipeline]
[Categorization.CategoryInfo(Name = "R: Surface Cache URP Integration", Order = 1000), HideInInspector]
sealed class SurfaceCacheRenderPipelineResourceSet : IRenderPipelineResources
{
    [SerializeField, HideInInspector] int m_Version = 6;
    int IRenderPipelineGraphicsSettings.version => m_Version;

    [ResourcePath("Runtime/RendererFeatures/SurfaceCacheGIRendererFeature/PatchAllocation.compute")]
    public ComputeShader m_AllocationShader;
    public ComputeShader allocationShader
    {
        get => m_AllocationShader;
        set => this.SetValueAndNotify(ref m_AllocationShader, value, nameof(m_AllocationShader));
    }
}
```
(`SurfaceCacheGIRendererFeature.cs:19-82`)

- **`[ResourcePath("...")]`** binds a field to a package-relative asset path the Editor resolves at settings-creation time — the shader/material ships with the package and is located by path, instead of requiring a user to drag a reference into an inspector slot. Read/write through the property + `SetValueAndNotify` so Editor listeners (live-reload, undo) see the change.
- **`m_Version` / `IRenderPipelineGraphicsSettings.version`** — a manual schema version on the settings asset itself, bumped whenever the resource set's shape changes, so migration code elsewhere in the package can upgrade old serialized copies.
- Retrieved at runtime via `GraphicsSettings.GetRenderPipelineSettings<SurfaceCacheRenderPipelineResourceSet>()` (`SurfaceCacheGIRendererFeature.cs:1033`) — a global per-render-pipeline-asset registry, not a reference the feature itself carries.
- **`[SupportedOnRenderPipeline]`** gates the settings asset to only appear/apply under a matching `RenderPipelineAsset` type — an HDRP project never sees or serializes it.
- **`[Categorization.CategoryInfo(Name = "...", Order = ...)]` + `[HideInInspector]`** — groups this settings block under a named, ordered category in Project Settings → Graphics, while `[HideInInspector]` suppresses the default per-field Inspector (it's edited only through that categorized settings UI, not by drag-selecting the asset directly).

**When to reach for this**: any `ScriptableRendererFeature` that needs its own compute shaders / fallback materials, instead of `[SerializeField]` fields directly on the feature (which forces every scene/prefab referencing the feature to carry a serialized reference, and gives no versioning or categorization).

## `[DisallowMultipleRendererFeature("message")]`

```csharp
[DisallowMultipleRendererFeature("Surface Cache Global Illumination")]
public class SurfaceCacheGIRendererFeature : ScriptableRendererFeature
```
(`SurfaceCacheGIRendererFeature.cs:84-85`) — refuses a second instance of the feature on the same `ScriptableRenderer`, surfacing the given display name in the Editor's "already added" error. Use whenever a feature owns a full-frame singleton resource (here: one `SurfaceCacheWorld` / ray tracing accel structure) that can't meaningfully exist twice on one renderer.

## `Handle<T>` / `HandleSet<T>` — generic strongly-typed handles

```csharp
using InstanceHandle = Handle<SurfaceCacheWorld.Instance>;
using LightHandle = Handle<SurfaceCacheWorld.Light>;
using MaterialHandle = Handle<MaterialPool.MaterialDescriptor>;
```
(`SurfaceCacheWorld.cs:9-16`; aliases in `SurfaceCacheWorldAdapter.cs:6-8`) — a single generic `Handle<T>` type parameterized by a marker type gives compile-time-distinct handle types per resource kind, so an `InstanceHandle` can never be passed where a `LightHandle` is expected, even though both are structurally "an int-like id." `HandleSet<T>` is the paired free-list allocator (`Add()`, implicit remove-and-recycle) backing each resource collection (`SurfaceCacheWorld.cs:300-301`). Reach for this pattern whenever a system hands out opaque ids for more than one resource kind — a zero-runtime-cost way to stop id-kind mixups the compiler would otherwise wave through.

## `ObjectDispatcher` — incremental scene-object change tracking

`UnityEngine.InternalBridge.ObjectDispatcher` (`SurfaceCacheWorldAdapter.cs:9` — internal engine bridge; verify availability before depending on it outside a package that already uses it) gives a per-type opt-in change stream instead of a manual dirty-flag system or a per-frame `FindObjectsByType` scan:

```csharp
objDispatcher.EnableTypeTracking<MeshRenderer>(ObjectDispatcher.TypeTrackingFlags.SceneObjects);
objDispatcher.EnableTransformTracking<MeshRenderer>(ObjectDispatcher.TransformTrackingType.GlobalTRS);
...
var transformChanges = objDispatcher.GetTransformChangesAndClear<MeshRenderer>(ObjectDispatcher.TransformTrackingType.GlobalTRS, false);
using var typeChanges = objDispatcher.GetTypeChangesAndClear<MeshRenderer>(Allocator.Temp);
foreach (var component in typeChanges.changed) { /* added or structurally changed */ }
foreach (var entityId in typeChanges.destroyedID) { /* removed */ }
```
(`SurfaceCacheWorldAdapter.cs:39-48, 99-122`) — two independent streams per type: transform-only changes (cheap, position/rotation/scale) and type/component changes (added/changed/destroyed, keyed by `EntityId` — Unity's stable cross-frame object identity). `GetTypeChangesAndClear` / `GetTransformChangesAndClear` drain the stream, so each is consumed exactly once per frame. This is the mechanism GI/lighting systems use to stay in sync with a live scene without a full rescan. A global filter change that isn't itself per-object-tracked (e.g. a rendering-layer-mask change on a volume) is handled by explicitly falling back to a full `ReevaluateAll` pass (`SurfaceCacheWorldAdapter.cs:74-85`) — the one place a manual rescan is still needed. Note the corollary this pattern hides a footgun for: only the *types* you call `EnableTypeTracking<T>` on are watched — a sibling type one hop away (e.g. `MeshFilter`, next to the tracked `MeshRenderer`) gets no signal at all if its own reference changes.

## `ShaderIDs` static nested class — cached `Shader.PropertyToID`

```csharp
internal static class ShaderIDs
{
    public static readonly int _RingConfigBuffer = Shader.PropertyToID("_RingConfigBuffer");
    ...
}
```
(`SurfaceCacheGIRendererFeature.cs:114-167`) — every shader property name is hashed once into a `static readonly int` at type-init, not re-hashed every frame inside the render-graph pass body. Convention: name the nested class `ShaderIDs` (or `ShaderConstants`), keep it `internal static`, one field per property, grouped near the pass class that uses them.

## Pass-data class + `RecordRenderGraph` + static render-func — not repeated here

Already the canonical subject of [`pass-types.md`](pass-types.md) and [`builder-api.md`](builder-api.md) — Surface Cache GI is a large worked example of the pattern (five distinct pass-data classes, one per compute/unsafe pass, in `SurfaceCacheGIRendererFeature.cs:171-298`) but doesn't introduce anything beyond what those pages already document.

## Structural-change-triggers-reallocation, not resize-in-place

Worth naming as its own idiom, seen in this file: a resource-owning object that depends on a few structural parameters (here: `SurfaceCache`'s voxel resolution + cascade count) doesn't try to resize its internal buffers in place. Instead the owning pass stashes the inputs those buffers were built from (`_coreResources`) and, when `RecordRenderGraph` notices a structural parameter changed, disposes the whole resource and reconstructs it fresh (`SurfaceCacheGIRendererFeature.cs:535-551`). Simpler and safer than partial-resize logic, at the cost of a one-frame full reallocation on that (rare, authoring-time) parameter change.
