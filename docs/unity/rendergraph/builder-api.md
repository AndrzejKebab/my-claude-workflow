# Builder API reference

Every method on `IBaseRenderGraphBuilder`, `IRenderAttachmentRenderGraphBuilder`, `IComputeRenderGraphBuilder`, `IRasterRenderGraphBuilder`, `IUnsafeRenderGraphBuilder`. Source: `Library/.../com.unity.render-pipelines.core/Runtime/RenderGraph/IRenderGraphBuilder.cs` (392 lines) and the implementation at `RenderGraphBuilders.cs` (607 lines).

The interface tree (from `IRenderGraphBuilder.cs:10-310`):

```
IBaseRenderGraphBuilder              // every builder; resource declarations + flags
├── IComputeRenderGraphBuilder       // adds SetRenderFunc<ComputeGraphContext>
└── IRenderAttachmentRenderGraphBuilder  // adds Set{Render,Input,RandomAccess}Attachment
    ├── IRasterRenderGraphBuilder    // adds SetRenderFunc<RasterGraphContext> + VRS + InputAttachment
    └── IUnsafeRenderGraphBuilder    // adds SetRenderFunc<UnsafeGraphContext>
```

Concrete impl is the single struct `RenderGraphBuilders` (`RenderGraphBuilders.cs:23` — implements all four interfaces; the `RenderGraph` instance reuses one cached `m_builderInstance` and re-`Setup`s it per pass at `RenderGraph.cs:1388,1443,1513`).

The builder is `IDisposable` — concrete pattern is `using var builder = renderGraph.AddRasterRenderPass<...>(...)`. `Dispose` is where the deferred work runs: `UseAllGlobalTextures` is expanded into per-global `UseTexture` calls, `setGlobalsList` entries flow into `m_RenderGraph.SetGlobal`, and the pass is finalised onto the graph (`RenderGraphBuilders.cs:120-163`).

---

## IBaseRenderGraphBuilder methods

Methods exposed on every builder (raster, compute, unsafe).

### `UseTexture(in TextureHandle, AccessFlags = Read)`

```csharp
void UseTexture(in TextureHandle input, AccessFlags flags = AccessFlags.Read);
```

`IRenderGraphBuilder.cs:17`. "Declare that this pass uses the input texture."

- Caller responsibility: pass every `TextureHandle` the render func reads or writes through this method (or one of the `SetRenderAttachment*` / `SetRandomAccessAttachment` / `UseGlobalTexture` siblings). The graph only schedules and lifetimes the textures it knows about.
- RG handles: lifetime tracking, version bumping (write flag promotes to a new version, see `RenderGraphBuilders.cs:218-261`), barrier insertion, scheduling.
- `flags`: `Read` (default) | `Write` | `ReadWrite` | `WriteAll` | `Discard` (combinable). `WriteAll` declares "I overwrite the whole resource" — gives RG a free pass on preserving existing content (faster). `Discard` says "I do not depend on prior content" (`RenderGraphBuilders.cs:222-225`).
- Cannot be called for the same handle that you also passed to `SetRenderAttachment*` on the same pass — the validator at `RenderGraphBuilders.cs:352-401` flags that as "alreadyUsed".

Project examples:
- A volumetric-fog pass declares the URP main-shadow atlas as a Read dependency so `MainLightShadowCasterPass` schedules before fog population compute.
- A cloud raymarch pass declares its shape, detail, and weather 3D textures as Read.
- A Hi-Z downsample reads the depth copy and declares its ping-pong mip textures ReadWrite.

### `UseGlobalTexture(int propertyId, AccessFlags = Read)`

```csharp
void UseGlobalTexture(int propertyId, AccessFlags flags = AccessFlags.Read);
```

`IRenderGraphBuilder.cs:26`. "Declare that this pass uses the texture assigned to the global texture slot. The actual texture referenced is indirectly specified here it depends on the value previous passes that were added to the graph set for the global texture slot. If no previous pass set a texture to the global slot an exception will be raised."

- Caller responsibility: pass the `Shader.PropertyToID(...)` for a global the graph already knows about (because some prior pass called `SetGlobalTextureAfterPass(handle, sameId)`).
- RG handles: looks up the current handle bound to that slot in `RenderGraph.GetGlobal(propertyId)` (`RenderGraphBuilders.cs:328`) and inserts an implicit `UseTexture(h, flags)` for the receiving pass. If the slot is empty it throws (`RenderGraphBuilders.cs:337`).
- This is the **preferred** way to read a global texture published by a prior pass — gives RG accurate per-resource dependency tracking instead of pulling in everything via `UseAllGlobalTextures`.

Project examples (called via the `s_SSAOTextureID` slot in URP):
- `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/Decal/DBuffer/DBufferRenderPass.cs:287` — `builder.UseGlobalTexture(s_SSAOTextureID);` only when SSAO is valid.
- `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/Passes/FinalBlitPass.cs:293` — `builder.UseGlobalTexture(s_CameraDepthTextureID);`.

The project itself currently uses `UseAllGlobalTextures(true)` instead of named `UseGlobalTexture` everywhere — see `empirical-examples.md` for the inventory.

### `UseAllGlobalTextures(bool enable)`

```csharp
void UseAllGlobalTextures(bool enable);
```

`IRenderGraphBuilder.cs:39`. "Indicate that this pass will reference all textures in global texture slots known to the graph."

- Caller responsibility: enable when you can't statically know which globals the pass touches (e.g. a `DrawRendererList` pass executing arbitrary user shaders). The XML doc explicitly recommends `UseGlobalTexture` over this when feasible: "It is highly recommended ... to use UseTexture(globalTextureSlotId) with individual texture slots instead of UseAllGlobalTextures(true) to ensure the graph can maximally optimize resource use and lifetimes."
- RG handles: at builder `Dispose` it iterates `m_RenderGraph.AllGlobals()` and calls `UseTexture(t, Read)` on every valid handle (`RenderGraphBuilders.cs:131-140`). So this is **purely a textures-only mechanism** — matrix arrays, vectors, floats published via `cmd.SetGlobalMatrixArray` / `cmd.SetGlobalVector` are NOT covered. Compute uniforms travel through a different path (see [global-state.md](global-state.md)).
- Critical constraint: only declares dependencies on textures that some prior pass has registered through `SetGlobalTextureAfterPass`. Globals set host-side via `Shader.SetGlobalTexture` outside the graph are unknown to RG and unaffected.

Typical uses include cloud history textures, screen-space shadow intermediates,
cloud-shadow maps, and probe or hemispherical capture textures.

### `SetGlobalTextureAfterPass(in TextureHandle, int propertyId)`

```csharp
void SetGlobalTextureAfterPass(in TextureHandle input, int propertyId);
```

`IRenderGraphBuilder.cs:54`. "Make this pass set a global texture slot at the end of this pass. During this pass the global texture will still have its old value."

- Caller responsibility: typically also call `UseTexture(h, Write)` (or `SetRenderAttachment*`) on the same handle in the same pass, since you usually publish what you produced. Not a hard requirement — you can stamp a slot without writing to the texture.
- RG handles: appends `(handle, propertyId)` to `m_RenderPass.setGlobalsList` (`RenderGraphBuilders.cs:348`); on `Dispose` calls `m_RenderGraph.SetGlobal` so subsequent passes that call `UseGlobalTexture(propertyId)` see the new handle (`RenderGraphBuilders.cs:143-146`). The actual `cmd.SetGlobalTexture` is issued by the compiler at execute time after the pass body runs (`RenderGraph.cs:2761`).
- The slot timing is important: the IDs are valid for the **next** pass. Within the producing pass the slot still has its previous value.
- When `RENDER_GRAPH_CLEAR_GLOBALS` is defined, slots set this way are cleared at end of graph execution.

Project examples:
- Publish a final cloud-shadow map with `builder.SetGlobalTextureAfterPass(finalHandle, PropCloudShadowmap)`.
- Publish cloud lighting and depth outputs for a later reprojection pass.
- Publish an integrated fog texture for later composition.
- URP `MainLightShadowCasterPass.cs:505` — `builder.SetGlobalTextureAfterPass(shadowTexture, MainLightShadowConstantBuffer._MainLightShadowmapID);` — this is the publication point that lets receivers `UseGlobalTexture(_MainLightShadowmapID)`.

### `UseBuffer(in BufferHandle, AccessFlags = Read) → BufferHandle`

```csharp
BufferHandle UseBuffer(in BufferHandle input, AccessFlags flags = AccessFlags.Read);
```

`IRenderGraphBuilder.cs:62`. "Declare that this pass uses the input compute buffer."

- Caller responsibility: declare every `BufferHandle` (StructuredBuffer / ByteAddressBuffer / etc.) that the render func binds.
- RG handles: lifetime + version, same as textures. Returned handle should be ignored — the XML doc says "You should not use the returned value it will be removed in the future."
- For UAV buffers in raster/unsafe passes use `UseBufferRandomAccess` instead (declares it as a u-register slot).

Project examples:
- Structured buffers used by fog, cloud, particle, and voxel passes follow this pattern.

### `CreateTransientTexture(in TextureDesc) → TextureHandle`<br>`CreateTransientTexture(in TextureHandle) → TextureHandle`

```csharp
TextureHandle CreateTransientTexture(in TextureDesc desc);
TextureHandle CreateTransientTexture(in TextureHandle texture);
```

`IRenderGraphBuilder.cs:70,78`. "This texture will only be available for the current pass and will be assumed to be both written and read so users don't need to add explicit read/write declarations."

- Caller responsibility: just use it inside the pass; do not declare with `UseTexture`. Lifetime is bounded to the single pass.
- RG handles: pool allocation, scheduling, automatic Read+Write tracking (`RenderGraphBuilders.cs:204-216`).
- The `TextureHandle` overload copies the descriptor from another handle (handy for "scratch matching the camera target").

### `CreateTransientBuffer(in BufferDesc) → BufferHandle`<br>`CreateTransientBuffer(in BufferHandle) → BufferHandle`

`IRenderGraphBuilder.cs:86,94`. Same semantics as `CreateTransientTexture` for buffers.

### `UseRendererList(in RendererListHandle)`

```csharp
void UseRendererList(in RendererListHandle input);
```

`IRenderGraphBuilder.cs:100`. "This pass will read from this renderer list. RendererLists are always read-only in the graph so have no access flags."

- Caller responsibility: if your pass calls `cmd.DrawRendererList`, declare the list here (or `RenderGraph.CreateRendererList`/`CreateShadowRendererList`/`CreateSkyboxRendererList` for built-in flavours).
- RG handles: schedules culling/draw-call generation jobs into the frame; the list is only valid for the recording frame.

Project examples:
- URP `MainLightShadowCasterPass.cs:491` calls `builder.UseRendererList(passData.shadowRendererListsHandle[cascadeIndex]);` — one per cascade.

### `EnableAsyncCompute(bool value)`

```csharp
void EnableAsyncCompute(bool value);
```

`IRenderGraphBuilder.cs:106`. "Enable asynchronous compute for this pass."

- Caller responsibility: only meaningful for compute passes. Use sparingly — async compute requires a separate queue and barriers between graphics and compute work.
- RG handles: places the pass on the async queue if the platform supports it.

### `AllowPassCulling(bool value)`

```csharp
void AllowPassCulling(bool value);
```

`IRenderGraphBuilder.cs:115`. "By default all passes can be culled out if the render graph detects it's not actually used."

- Caller responsibility: pass `false` whenever the pass has side effects RG cannot observe — e.g. it publishes a global via a render-func `cmd.SetGlobal*` that the compiler doesn't track, or it writes to an imported persistent RT used by next-frame.
- RG handles: marks the pass as un-cullable. Note: `AllowGlobalStateModification(true)` already implies `AllowPassCulling(false)` (`RenderGraphBuilders.cs:64-77`).

This is common for passes that write history textures consumed next frame,
because the current graph cannot otherwise see the future-frame consumer.

### `AllowGlobalStateModification(bool value)`

```csharp
void AllowGlobalStateModification(bool value);
```

`IRenderGraphBuilder.cs:123`. "Allow commands in the command buffer to modify global state. This will introduce a render graph sync-point in the frame and cause all passes after this pass to never be reordered before this pass. This may have negative impact on performance and memory use if not used carefully so it is recommended to only allow this in specific use cases. This will also set AllowPassCulling to false."

- This flag is for **the pass writing globals**. It does NOT itself "let the pass read globals set by previous passes" — that misconception is the project's main RG bug. The pass itself doesn't need this enabled to read existing globals; it needs `UseGlobalTexture`/`UseAllGlobalTextures` and a scheduled-before-me dependency on the producer.
- What it actually does: turns off pass-reordering across this pass and disables culling. So `cmd.SetGlobalTexture` / `cmd.SetGlobalMatrixArray` / `cmd.EnableKeyword` issued in the render func will not be moved relative to surrounding passes, and downstream passes can rely on the global being set.
- Caller responsibility: enable when your render func mutates global state (keywords, global vectors/matrices, global textures via raw `cmd.SetGlobalTexture` rather than `SetGlobalTextureAfterPass`).
- The unsafe pass type forces this to true (`RenderGraph.cs:1505: renderPass.AllowGlobalState(true);`) — every `AddUnsafePass` already opts in.

Project examples:
- Use it only where a pass intentionally reads shader globals that cannot be declared individually.
- URP `MainLightShadowCasterPass.cs:502` — needed because the render func issues `SetGlobalMatrixArray(_MainLightWorldToShadow, ...)` and `SetGlobalVector(_CascadeShadowSplitSpheres0..3, ...)` etc.
- URP `CopyDepthPass.cs:378` — needed because the render func sets `_CameraDepthTexture` global.
- URP `RendererFeatures/ScreenSpaceShadows.cs:220` — the post-blit keyword flip needs it.

### `EnableFoveatedRasterization(bool value)`

```csharp
void EnableFoveatedRasterization(bool value);
```

`IRenderGraphBuilder.cs:129`. "Enable foveated rendering for this pass."

- The user request mentioned `EnableFoveatedRasterizationDuringPass`; the actual method name is `EnableFoveatedRasterization`. Verified across URP source: every URP pass calls `builder.EnableFoveatedRasterization(...)` — see `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/Passes/DrawSkyboxPass.cs:160`, `MotionVectorRenderPass.cs:224`, `FinalBlitPass.cs:309`, `DrawObjectsPass.cs:346,522`, `DepthOnlyPass.cs:158`, `RenderObjectsPass.cs:321`, `XROcclusionMeshPass.cs:85`, `PostProcessPassRenderGraph.cs:2220,2522`.
- Caller responsibility: XR only; gate on `cameraData.xr.supportsFoveatedRendering && passSupportsFoveation`. Project does not target XR — leave default.

### `GenerateDebugData(bool value)`

```csharp
void GenerateDebugData(bool value);
```

`IRenderGraphBuilder.cs:135`. "Generates debugging data for this pass, intended for visualization in the RenderGraph Viewer."

- Caller responsibility: enable for passes you want to inspect in the RG viewer; debug builds only.
- The Unity-doc page for `IBaseRenderGraphBuilder` does not list this method publicly (see [unity-docs-fetched.md](unity-docs-fetched.md)) — it's exposed in source but not in the public API portal.

---

## IRenderAttachmentRenderGraphBuilder methods

Inherited by `IRasterRenderGraphBuilder` and `IUnsafeRenderGraphBuilder`. Source: `IRenderGraphBuilder.cs:141-276`.

### `SetRenderAttachment(TextureHandle, int index, AccessFlags = Write)` (+ overload with mip/slice)

```csharp
void SetRenderAttachment(TextureHandle tex, int index, AccessFlags flags = AccessFlags.Write);
void SetRenderAttachment(TextureHandle tex, int index, AccessFlags flags, int mipLevel, int depthSlice);
```

`IRenderGraphBuilder.cs:163,195`. "Use the texture as a rendertarget attachment."

- Caller responsibility: one call per MRT slot. Write to `SV_Target{index}` in the shader. Do NOT also `UseTexture` the same handle (validator throws).
- The default `Write` flag preserves prior content (read-modify-write); pass `WriteAll` if you overwrite the full target — gives RG more freedom and skips the load.
- Reading via `Read` flag means rasterization stage will read the buffer (blending, z-test). Not for shader sampling — for that use `SetInputAttachment` (raster only) or a separate `UseTexture` declaration on a different handle.

Project examples:
- A cloud-shadow blur chain typically declares one render-target attachment per pass.
- URP `MainLightShadowCasterPass.cs:495` — `builder.SetRenderAttachmentDepth(shadowTexture, AccessFlags.Write);` is the depth variant.

### `SetRenderAttachmentDepth(TextureHandle, AccessFlags = Write)` (+ mip/slice overload)

```csharp
void SetRenderAttachmentDepth(TextureHandle tex, AccessFlags flags = AccessFlags.Write);
void SetRenderAttachmentDepth(TextureHandle tex, AccessFlags flags, int mipLevel, int depthSlice);
```

`IRenderGraphBuilder.cs:209,232`. Used as the Z-buffer. "Calling SetRenderAttachmentDepth twice on the same builder is an error." — at most one depth target per pass. `Read` means depth-test only (z-test); `Write` means ROP depth writes.

### `SetRandomAccessAttachment(TextureHandle, int index, AccessFlags = ReadWrite) → TextureHandle`

```csharp
TextureHandle SetRandomAccessAttachment(TextureHandle tex, int index, AccessFlags flags = AccessFlags.ReadWrite);
```

`IRenderGraphBuilder.cs:246`. UAV / "Storage Image" — `RWTexture2d<T>`, `RWTexture3d<T>` etc. accessed via `register(ux)`. The slot index shares space with render targets and input attachments (see `CommandBuffer.SetRandomWriteTarget`).

### `UseBufferRandomAccess(BufferHandle, int index, AccessFlags = Read) → BufferHandle` (+ counter overload)

```csharp
BufferHandle UseBufferRandomAccess(BufferHandle tex, int index, AccessFlags flags = AccessFlags.Read);
BufferHandle UseBufferRandomAccess(BufferHandle tex, int index, bool preserveCounterValue, AccessFlags flags = AccessFlags.Read);
```

`IRenderGraphBuilder.cs:260,275`. UAV buffers. `preserveCounterValue` controls whether the append/consume counter is reset between passes.

---

## IRasterRenderGraphBuilder additional methods

Source: `IRenderGraphBuilder.cs:317-391`.

### `SetInputAttachment(TextureHandle, int index, AccessFlags = Read)` (+ mip/slice overload)

`IRenderGraphBuilder.cs:334,356`. Tile-memory framebuffer fetch — `LOAD_FRAMEBUFFER_INPUT(idx)` / `LOAD_FRAMEBUFFER_INPUT_MS(idx, sampleIdx)`. Not all platforms support it; gate on `RenderGraphUtils.IsFramebufferFetchSupportedOnCurrentPlatform`.

### `SetShadingRateImageAttachment(in TextureHandle)`

`IRenderGraphBuilder.cs:362`. VRS texture attachment.

### `SetShadingRateFragmentSize(ShadingRateFragmentSize)`

`IRenderGraphBuilder.cs:368`. VRS rate.

### `SetShadingRateCombiner(ShadingRateCombinerStage stage, ShadingRateCombiner combiner)`

`IRenderGraphBuilder.cs:375`. VRS combiner rule.

### `SetExtendedFeatureFlags(ExtendedFeatureFlags)`

`IRenderGraphBuilder.cs:381`. Platform-specific optimisation hints.

### `SetRenderFunc<PassData>(BaseRenderFunc<PassData, RasterGraphContext>)`

```csharp
void SetRenderFunc<PassData>(BaseRenderFunc<PassData, RasterGraphContext> renderFunc) where PassData : class, new();
```

`IRenderGraphBuilder.cs:389`. Mandatory. The `RasterGraphContext` exposes `cmd` of type `RasterCommandBuffer` — restricted command buffer that disallows compute dispatch, render-target switches, etc.

---

## IComputeRenderGraphBuilder additional methods

Source: `IRenderGraphBuilder.cs:283-293`.

### `SetRenderFunc<PassData>(BaseRenderFunc<PassData, ComputeGraphContext>)`

```csharp
void SetRenderFunc<PassData>(BaseRenderFunc<PassData, ComputeGraphContext> renderFunc) where PassData : class, new();
```

`IRenderGraphBuilder.cs:291`. Mandatory. `ComputeGraphContext` exposes `cmd` of type `ComputeCommandBuffer` — only compute / copy commands.

Some compute work may still require `AddUnsafePass` when it uses command-buffer operations not exposed by the typed compute builder; see [pass-types.md](pass-types.md) for the trade-offs.

---

## IUnsafeRenderGraphBuilder additional methods

Source: `IRenderGraphBuilder.cs:300-310`.

### `SetRenderFunc<PassData>(BaseRenderFunc<PassData, UnsafeGraphContext>)`

```csharp
void SetRenderFunc<PassData>(BaseRenderFunc<PassData, UnsafeGraphContext> renderFunc) where PassData : class, new();
```

`IRenderGraphBuilder.cs:308`. Mandatory. `UnsafeGraphContext.cmd` is the **full** `CommandBuffer` (via `CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd)`). No graphics-state setup is automatic — you must `cmd.SetRenderTarget` / `cmd.SetGlobalFloat` / `cmd.DispatchCompute` yourself. RG validation is reduced.

The `RenderGraph.AddUnsafePass` constructor (`RenderGraph.cs:1505`) hardcodes `renderPass.AllowGlobalState(true);` — every unsafe pass auto-allows global state modification.

---

## RenderGraph methods (that produce builders)

Source: `RenderGraph.cs:1338-1516`.

### `AddRasterRenderPass<PassData>(string passName, out PassData passData) → IRasterRenderGraphBuilder`

`RenderGraph.cs:1350,1369`. Plus a `ProfilingSampler` overload. Caller-file/line params are auto-supplied.

### `AddComputePass<PassData>(string passName, out PassData passData) → IComputeRenderGraphBuilder`

`RenderGraph.cs:1405,1424`.

### `AddUnsafePass<PassData>(string passName, out PassData passData) → IUnsafeRenderGraphBuilder`

`RenderGraph.cs:1467,1493`.

### `AddRenderPass<PassData>(...)` — DEPRECATED

`RenderGraph.cs:1528-1566`. `[Obsolete("AddRenderPass() is deprecated, use AddRasterRenderPass/AddComputePass/AddUnsafePass() instead.")]`. Project should not use this; if you find it in third-party packages, treat as legacy.

---

## Resource methods on RenderGraph (not on builders)

These are called on the `RenderGraph` instance itself before building a pass.

| Method | Source | Use |
| ----- | ----- | ----- |
| `CreateTexture(in TextureDesc) → TextureHandle` | `RenderGraph.cs` | per-frame transient with explicit desc; lives across the frame, freed at end |
| `CreateTexture(TextureHandle, name, clear)` | | clone descriptor |
| `ImportTexture(RTHandle) → TextureHandle` | | import a persistent RTHandle (history textures, LUTs) |
| `ImportTexture(RTHandle, ImportResourceParams)` | | with import semantics (multi-frame valid, etc.) |
| `ImportTexture(RTHandle, RenderTargetInfo, ImportResourceParams)` | | with explicit format info |
| `CreateBuffer(in BufferDesc) → BufferHandle` | | new transient buffer |
| `ImportBuffer(GraphicsBuffer, forceRelease) → BufferHandle` | | import an externally-owned `GraphicsBuffer` |
| `CreateRendererList(in RendererListParams)` | | for `cmd.DrawRendererList` |
| `CreateShadowRendererList(ref ShadowDrawingSettings)` | | for shadow caster passes |
| `CreateSkyboxRendererList(in Camera)` | | for skybox draws |
| `defaultResources` (property) | | `RenderGraphDefaultResources` — `defaultShadowTexture`, etc. URP `MainLightShadowCasterPass.cs:499` uses `graph.defaultResources.defaultShadowTexture` for the empty-shadow case |

---

## AccessFlags reference

Bitfield (`UnityEngine.Rendering.RenderGraphModule.AccessFlags`) used across `UseTexture`, `UseBuffer`, `SetRenderAttachment*`, `UseBufferRandomAccess`:

| Flag | Meaning |
| ----- | ----- |
| `Read` | pass reads the resource — content must be preserved by predecessors |
| `Write` | pass writes (a region of) the resource — prior content preserved |
| `ReadWrite` | pass both reads and writes |
| `WriteAll` | pass overwrites the entire resource — prior content can be discarded |
| `Discard` | pass declares it does not depend on prior content |

Logic in `RenderGraphBuilders.cs:218-261`. `Discard` + `Read` reads "version 0" (the freshly-allocated resource without prior content).
