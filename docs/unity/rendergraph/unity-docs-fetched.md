# Unity 6.3 docs — curated extracts

Fetched 2026-05-04 via WebFetch from the Unity 6000.3 documentation portal and the URP / Core RP package portal. URLs that returned 404 against the 6.3 doc tree are noted; package-portal mirror URLs (`docs.unity3d.com/Packages/com.unity.render-pipelines.core@17.0/api/...`) are the working source for ScriptReference signatures and are the primary citation here.

---

## Fetch results summary

| URL | Status |
| --- | --- |
| `docs.unity3d.com/6000.3/Documentation/Manual/render-graph-system.html` | 404 (URL does not exist on 6.3 manual; the equivalent landing page lives under `Manual/urp/render-graph.html`) |
| `docs.unity3d.com/6000.3/Documentation/Manual/render-graph-introduction.html` | 404 |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph.html` | 200 (index page; mostly nav links) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-write-render-pass.html` | 200 (substantive content) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-textures.html` | 404 |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-frame-data.html` | 200 (index) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-compute-shader.html` | 200 (index) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-compute-shader-run.html` | 200 (substantive) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-pass-textures-between-passes.html` | 200 (index) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/accessing-frame-data.html` | 200 (substantive) |
| `docs.unity3d.com/6000.3/Documentation/Manual/urp/use-built-in-shader-methods-shadows.html` | 200 (substantive) |
| `docs.unity3d.com/6000.3/Documentation/ScriptReference/Rendering.RenderGraphModule.RenderGraph.html` | 404 |
| `docs.unity3d.com/6000.3/Documentation/ScriptReference/Rendering.RenderGraphModule.IBaseRenderGraphBuilder.html` | 404 |
| `docs.unity3d.com/6000.3/Documentation/ScriptReference/Rendering.RenderGraphModule.IComputeRenderGraphBuilder.html` | 404 |
| `docs.unity3d.com/6000.3/Documentation/ScriptReference/Rendering.RenderGraphModule.IRasterRenderGraphBuilder.html` | 404 |
| `docs.unity3d.com/Packages/com.unity.render-pipelines.core@17.0/api/UnityEngine.Rendering.RenderGraphModule.RenderGraph.html` | 200 (substantive — used as primary source for method signatures) |
| `docs.unity3d.com/Packages/com.unity.render-pipelines.core@17.0/api/UnityEngine.Rendering.RenderGraphModule.IBaseRenderGraphBuilder.html` | 200 (substantive) |

The 6.3 ScriptReference URLs the original brief listed do not resolve. The Core RP package-portal mirror (`@17.0` matches the project's URP 17.5.0 — Core RP's 17.0 is the correct major-version companion) is the working canonical source for the API signatures. All API quotes below are from that mirror, not the 6.3 portal.

---

## Manual: writing a render pass

Source: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-write-render-pass.html

### Core instructions

1. **Declare the Render Pass Class** — inherit from `ScriptableRenderPass`.

2. **Declare Resources (PassData)** — inner class holding render graph resource references and C# variables needed by the pass:
   ```csharp
   class PassData
   {
       public TextureHandle copySourceTexture;
   }
   ```

3. **Implement `RecordRenderGraph` method** — configures the pass during graph recording. Declares inputs/outputs but does not add command-buffer commands directly.

### Pass type

Raster render pass via `renderGraph.AddRasterRenderPass<PassData>()`. (Manual does not cover `AddComputePass` / `AddUnsafePass` choice — see [pass-types.md](pass-types.md).)

### Builder methods called

- `builder.UseTexture()` — declares read-only texture input
- `builder.SetRenderAttachment()` — declares color render target
- `builder.AllowPassCulling(false)` — prevents culling if unused
- `builder.SetRenderFunc()` — assigns the rendering function

### `SetRenderFunc` pattern

```csharp
builder.SetRenderFunc(static (PassData data, RasterGraphContext context)
    => ExecutePass(data, context));
```

Use static methods or static lambdas to avoid memory allocations.

### Render-func example

```csharp
static void ExecutePass(PassData data, RasterGraphContext context)
{
    Blitter.BlitTexture(context.cmd, data.copySourceTexture,
        new Vector4(1, 1, 0, 0), 0, false);
}
```

### Injection

Call `renderer.EnqueuePass()` within the `AddRenderPasses()` method of a Renderer Feature implementation.

---

## Manual: running a compute shader in render graph

Source: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-compute-shader-run.html

### Phases

1. Set up the render pass to use a compute shader
2. Add an output buffer
3. Pass in and execute the compute shader
4. Get the output data from the output buffer

### Builder pattern

Use `AddComputePass` with `ComputeGraphContext`:
```csharp
using (var builder = renderGraph.AddComputePass("MyComputePass", out PassData data))
{
    builder.SetRenderFunc(static (PassData data, ComputeGraphContext context) => ExecutePass(data, context));
}
```

### Buffer declaration

```csharp
class PassData
{
    public BufferHandle output;
    public ComputeShader computeShader;
}

public GraphicsBuffer outputBuffer;

// Constructor initialization
outputBuffer = new GraphicsBuffer(GraphicsBuffer.Target.Structured, 5, sizeof(int));
```

### Execution APIs

- `renderGraph.ImportBuffer(outputBuffer)` — convert buffers to handles
- `builder.UseBuffer(passData.output, AccessFlags.Write)` — buffer setup
- `SetComputeBufferParam` — attach buffers to the shader
- `DispatchCompute` — execute with thread group dimensions
- `GraphicsBuffer.GetData` — retrieve results after execution completes

---

## Manual: accessing frame data

Source: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/accessing-frame-data.html

Frame data is accessed through the `ContextContainer` parameter of `RecordRenderGraph`:

1. **Retrieve `UniversalResourceData`**: get the frame's textures via `ContextContainer.Get<UniversalResourceData>()`.
2. **Access texture handles**: e.g. `resourceData.activeColorTexture`, `resourceData.activeDepthTexture`, `resourceData.mainShadowsTexture` (the latter not explicitly listed on the page; verified via URP source `MainLightShadowCasterPass.cs:474-505` and `UniversalResourceData.cs`).

Other context-container types relevant to RG:
- `UniversalCameraData` (camera + viewport state, includes `historyManager` for prev-frame access)
- `UniversalLightData` (`mainLightIndex`, `visibleLights`)
- `UniversalShadowData` (`mainLightShadowsEnabled`, `mainLightShadowCascadesCount`, `supportsMainLightShadows`, `supportsSoftShadows`)
- `UniversalRenderingData`

Texture handle validity: only "the current render graph in the current frame". For multi-frame, use `UniversalCameraData.historyManager` and the camera-history-type API.

`ConfigureInput` API can ensure URP generates required textures (e.g. depth, normals).

---

## Manual: pass textures between render graph passes

Source: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-pass-textures-between-passes.html (index)

Three approaches:

1. **Frame Data**: make a texture available to later render passes in the same frame via the `ContextContainer` slots populated by URP.
2. **Global Textures**: make a texture available to all shaders and render passes via `SetGlobalTextureAfterPass(handle, propertyId)`. Consumed via `UseGlobalTexture(propertyId)` — this is the RG-tracked global slot mechanism.
3. **Imported Textures**: access a texture created outside the render graph system, across multiple frames — `renderGraph.ImportTexture(rtHandle)`.

(Page is index-only; the linked sub-pages contain code that mirrors the patterns documented in [global-state.md](global-state.md) and [empirical-examples.md](empirical-examples.md).)

---

## Manual: URP shadow sampling

Source: https://docs.unity3d.com/6000.3/Documentation/Manual/urp/use-built-in-shader-methods-shadows.html

### Required include

`"Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"` within `HLSLPROGRAM`. Imports `Shadows.hlsl` and `RealtimeLights.hlsl`.

### Required pragmas

For main light shadows:
```
#pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
```

For additional lights:
```
#pragma multi_compile _ _ADDITIONAL_LIGHT_SHADOWS
```

### HLSL methods exposed

| Method | Signature |
| --- | --- |
| `GetShadowCoord` | `float4 GetShadowCoord(VertexPositionInputs vertexInputs)` |
| `TransformWorldToShadowCoord` | `float4 TransformWorldToShadowCoord(float3 positionInWorldSpace)` |
| `GetMainLight` | `Light GetMainLight(float4 shadowCoordinates)` |
| `ComputeCascadeIndex` | `half ComputeCascadeIndex(float3 positionInWorldSpace)` |
| `MainLightRealtimeShadow` | `half MainLightRealtimeShadow(float4 shadowCoordinates)` |
| `AdditionalLightRealtimeShadow` | `half AdditionalLightRealtimeShadow(int lightIndex, float3 positionInWorldSpace)` |
| `GetMainLightShadowFade` | `half GetMainLightShadowFade(float3 positionInWorldSpace)` |
| `GetAdditionalLightShadowFade` | `half GetAdditionalLightShadowFade(float3 positionInWorldSpace)` |
| `ApplyShadowBias` | `float3 ApplyShadowBias(float3 positionInWorldSpace, float3 normalWS, float3 lightDirection)` |

The Manual page does not list global properties. The **definitive** list of globals consumed by the cascade shadow path is in URP source `Shadows.hlsl:63-85` and is reproduced verbatim in [shadow-sampling-from-compute.md](shadow-sampling-from-compute.md).

For compute the project does NOT include `_MAIN_LIGHT_SHADOWS_SCREEN` in its pragma — that variant uses implicit-LOD `SAMPLE_TEXTURE2D` and is invalid in compute on Vulkan. See [shadow-sampling-from-compute.md](shadow-sampling-from-compute.md).

---

## ScriptReference: `RenderGraph` (Core RP @17.0)

Source: https://docs.unity3d.com/Packages/com.unity.render-pipelines.core@17.0/api/UnityEngine.Rendering.RenderGraphModule.RenderGraph.html

### Pass creation (the three modern entry points)

```csharp
public IRasterRenderGraphBuilder AddRasterRenderPass<PassData>(string passName, out PassData passData)
public IRasterRenderGraphBuilder AddRasterRenderPass<PassData>(string passName, out PassData passData, ProfilingSampler sampler)

public IComputeRenderGraphBuilder AddComputePass<PassData>(string passName, out PassData passData)
public IComputeRenderGraphBuilder AddComputePass<PassData>(string passName, out PassData passData, ProfilingSampler sampler)

public IUnsafeRenderGraphBuilder AddUnsafePass<PassData>(string passName, out PassData passData)
public IUnsafeRenderGraphBuilder AddUnsafePass<PassData>(string passName, out PassData passData, ProfilingSampler sampler)
```

### Legacy pass creation (deprecated)

```csharp
public RenderGraphBuilder AddRenderPass<PassData>(string passName, out PassData passData)
public RenderGraphBuilder AddRenderPass<PassData>(string passName, out PassData passData, ProfilingSampler sampler)
```

### Texture management

```csharp
public TextureHandle CreateTexture(in TextureDesc desc)
public TextureHandle CreateTexture(TextureHandle texture)
public TextureHandle CreateTexture(TextureHandle texture, string name, bool clear = false)

public TextureHandle ImportTexture(RTHandle rt)
public TextureHandle ImportTexture(RTHandle rt, ImportResourceParams importParams)
public TextureHandle ImportTexture(RTHandle rt, RenderTargetInfo info, ImportResourceParams importParams = default)

public TextureHandle CreateSharedTexture(in TextureDesc desc, bool explicitRelease = false)
public void RefreshSharedTextureDesc(TextureHandle handle, in TextureDesc desc)
public void ReleaseSharedTexture(TextureHandle texture)

public void CreateTextureIfInvalid(in TextureDesc desc, ref TextureHandle texture)
public TextureDesc GetTextureDesc(TextureHandle texture)
public RenderTargetInfo GetRenderTargetInfo(TextureHandle texture)
```

### Buffer management

```csharp
public BufferHandle CreateBuffer(in BufferDesc desc)
public BufferHandle CreateBuffer(in BufferHandle graphicsBuffer)
public BufferHandle ImportBuffer(GraphicsBuffer graphicsBuffer, bool forceRelease = false)
public BufferDesc GetBufferDesc(in BufferHandle graphicsBuffer)
```

### Backbuffer

```csharp
public TextureHandle ImportBackbuffer(RenderTargetIdentifier rt)
public TextureHandle ImportBackbuffer(RenderTargetIdentifier rt, RenderTargetInfo info, ImportResourceParams importParams = default)
```

### Renderer lists

```csharp
public RendererListHandle CreateRendererList(in RendererListParams desc)
public RendererListHandle CreateRendererList(in RendererListDesc desc)
public RendererListHandle CreateGizmoRendererList(in Camera camera, in GizmoSubset gizmoSubset)
public RendererListHandle CreateShadowRendererList(ref ShadowDrawingSettings shadowDrawingSettings)
public RendererListHandle CreateSkyboxRendererList(in Camera camera)
public RendererListHandle CreateSkyboxRendererList(in Camera camera, Matrix4x4 projectionMatrix, Matrix4x4 viewMatrix)
public RendererListHandle CreateSkyboxRendererList(in Camera camera, Matrix4x4 projectionMatrixL, Matrix4x4 viewMatrixL, Matrix4x4 projectionMatrixR, Matrix4x4 viewMatrixR)
public RendererListHandle CreateUIOverlayRendererList(in Camera camera)
public RendererListHandle CreateUIOverlayRendererList(in Camera camera, in UISubset uiSubset)
public RendererListHandle CreateWireOverlayRendererList(in Camera camera)
```

### Ray tracing

```csharp
public RayTracingAccelerationStructureHandle ImportRayTracingAccelerationStructure(in RayTracingAccelerationStructure accelStruct, string name = null)
```

### Lifecycle

```csharp
public void BeginRecording(in RenderGraphParameters parameters)
public void EndRecordingAndExecute()
public void BeginProfilingSampler(ProfilingSampler sampler, string file = "", int line = 0)
public void EndProfilingSampler(ProfilingSampler sampler, string file = "", int line = 0)
public void EndFrame()
public void Cleanup()
```

### Debug

```csharp
public void RegisterDebug(DebugUI.Panel panel = null)
public void UnRegisterDebug()
public static List<RenderGraph> GetRegisteredRenderGraphs()
```

### Properties

```csharp
public RenderGraphDefaultResources defaultResources { get; }
public static bool isRenderGraphViewerActive { get; }
public string name { get; }
public bool nativeRenderPassesEnabled { get; set; }
```

---

## ScriptReference: `IBaseRenderGraphBuilder` (Core RP @17.0)

Source: https://docs.unity3d.com/Packages/com.unity.render-pipelines.core@17.0/api/UnityEngine.Rendering.RenderGraphModule.IBaseRenderGraphBuilder.html

### `UseTexture`
```csharp
void UseTexture(in TextureHandle input, AccessFlags flags = AccessFlags.Read)
```
"Declare that this pass uses the input texture."

### `UseGlobalTexture`
```csharp
void UseGlobalTexture(int propertyId, AccessFlags flags = AccessFlags.Read)
```
"Declare that this pass uses the texture assigned to the global texture slot."

### `UseAllGlobalTextures`
```csharp
void UseAllGlobalTextures(bool enable)
```
"Indicate that this pass will reference all textures in global texture slots known to the graph."

### `SetGlobalTextureAfterPass`
```csharp
void SetGlobalTextureAfterPass(in TextureHandle input, int propertyId)
```
"Make this pass set a global texture slot at the end of this pass."

### `UseBuffer`
```csharp
BufferHandle UseBuffer(in BufferHandle input, AccessFlags flags = AccessFlags.Read)
```
"Declare that this pass uses the input compute buffer."

### `CreateTransientTexture`
```csharp
TextureHandle CreateTransientTexture(in TextureDesc desc)
TextureHandle CreateTransientTexture(in TextureHandle texture)
```
"Create a new Render Graph Texture resource. This texture will only be available for the current pass."

### `UseRendererList`
```csharp
void UseRendererList(in RendererListHandle input)
```
"This pass will read from this renderer list. RendererLists are always read-only."

### `EnableAsyncCompute`
```csharp
void EnableAsyncCompute(bool value)
```
"Enable asynchronous compute for this pass."

### `AllowPassCulling`
```csharp
void AllowPassCulling(bool value)
```
"Allow or not pass culling. By default all passes can be culled out if the render graph detects it's not used."

### `AllowGlobalStateModification`
```csharp
void AllowGlobalStateModification(bool value)
```
"Allow commands in the command buffer to modify global state."

### `EnableFoveatedRasterization`
```csharp
void EnableFoveatedRasterization(bool value)
```
"Enable foveated rendering for this pass."

### Note on `GenerateDebugData`

The `IBaseRenderGraphBuilder` documentation page in the Core RP @17.0 portal does not list a `GenerateDebugData` method. It IS present in the source (`IRenderGraphBuilder.cs:135` — verified via local read; included in [builder-api.md](builder-api.md)) but not in the public API portal. Treat as internal-but-callable; safe to use, but Unity may not consider it stable API.

---

## Cross-references

- API canon for the project: [builder-api.md](builder-api.md) (matches this fetched data plus the source-only `GenerateDebugData`).
- Method semantics: [global-state.md](global-state.md) (resolves the `UseGlobalTexture` vs `UseAllGlobalTextures` vs `AllowGlobalStateModification` confusion).
- Picking a pass type: [pass-types.md](pass-types.md).
- Working examples: [empirical-examples.md](empirical-examples.md).
