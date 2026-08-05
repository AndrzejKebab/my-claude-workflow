---
name: URP Render Graph design principles
description: Comprehensive rules for render graph passes — transient vs external resources, pass enqueue, TextureHandle lifecycle, resource sharing between passes
type: feedback
---

## Resource types

**Transient (render graph managed):**
- Created via `renderGraph.CreateTexture(TextureDesc)` or `renderGraph.CreateBuffer(BufferDesc)`
- Returns `TextureHandle` / `BufferHandle` — declarative graph node IDs, NOT actual GPU resources
- Lifetime managed by render graph — allocated before first use, freed after last use
- Zero cost if the pass is culled

**External (user managed):**
- `RenderTexture`, `GraphicsBuffer` — real GPU resources with manual lifetime
- Must be **imported** to use in render graph: `renderGraph.ImportTexture(RTHandles.Alloc(rt))`
- Import converts external resource → `TextureHandle` for graph declaration
- Use external only when data must persist across frames (readback buffers, history textures)

## TextureHandle lifecycle

**Outside render func (RecordRenderGraph):**
- `TextureHandle` is a lightweight declarative node ID
- Used for graph topology: `builder.UseTexture(handle, AccessFlags.Read/Write)`
- Can be stored on pass fields, passed between passes during recording
- **Cannot** be resolved to actual texture — `(RTHandle)handle` will fail or return null

**Inside render func (SetRenderFunc lambda):**
- `RenderGraphResourceRegistry.current` is active
- `TextureHandle` has implicit operators: `→ RTHandle`, `→ RenderTexture`, `→ RenderTargetIdentifier`, `→ Texture`
- Cast explicitly: `(RTHandle)data.MyHandle` to pass to CommandBuffer/Blitter APIs
- This is the ONLY place where the actual GPU resource exists

## Pass recording rules

**Deterministic enqueue:**
- ALWAYS enqueue all passes unconditionally in `AddRenderPasses`
- Never branch on runtime state (data available, readback pending, etc.) at enqueue time
- Handle "nothing to do" inside `RecordRenderGraph` with early return
- Reason: Frame Debugger requires stable pass lists frame-to-frame

**Resource declaration:**
- Every texture/buffer a pass reads or writes MUST be declared via `builder.UseTexture/UseBuffer`
- `AccessFlags.Read` — pass reads the resource
- `AccessFlags.Write` — pass writes (previous contents undefined)
- `AccessFlags.ReadWrite` — pass reads and writes
- Render graph uses these declarations to determine execution order and resource lifetimes

## Sharing transient resources between passes — ContextContainer

The canonical URP pattern uses `ContextContainer frameData` with custom `ContextItem` subclasses:

```csharp
// 1. Define a ContextItem to carry TextureHandles between passes
class MyFeatureData : ContextItem
{
  public TextureHandle hiZMip0;
  public override void Reset() { hiZMip0 = TextureHandle.nullHandle; }
}

// 2. Producer pass: create texture, store in ContextContainer
public override void RecordRenderGraph(RenderGraph rg, ContextContainer frameData)
{
  var data = frameData.GetOrCreate<MyFeatureData>();
  data.hiZMip0 = rg.CreateTexture(desc);
  // ... use it in this pass
}

// 3. Consumer pass: read from ContextContainer
public override void RecordRenderGraph(RenderGraph rg, ContextContainer frameData)
{
  var data = frameData.Get<MyFeatureData>();
  if (data.hiZMip0.IsValid())
    builder.UseTexture(data.hiZMip0, AccessFlags.Read);
}
```

**Key rules:**
- Only ONE instance of each ContextItem type per frame
- `GetOrCreate<T>()` to create, `Get<T>()` to read (throws if not created)
- `Reset()` clears all handles to `TextureHandle.nullHandle` at frame end
- `RecordRenderGraph` is called in `renderPassEvent` order — later passes can read handles written by earlier passes
- This is how `UniversalResourceData` works (cameraDepthTexture, activeColorTexture, etc.)

**Anti-patterns:**
- Don't store TextureHandle on pass class fields across frames — they're per-frame graph nodes
- Don't pass TextureHandle during `AddRenderPasses` — runs before any RecordRenderGraph
- Don't hold references to producing passes just to read their fields — use ContextContainer

## Compute in render graph

Use `AddUnsafePass<T>()` for compute dispatches:
- `UnsafeGraphContext ctx` provides `ctx.cmd` (UnsafeCommandBuffer)
- Get native CommandBuffer: `CommandBufferHelpers.GetNativeCommandBuffer(ctx.cmd)`
- Bind textures: `nativeCmd.SetComputeTextureParam(cs, kernel, prop, (RTHandle)data.Handle)`
- Bind buffers: `nativeCmd.SetComputeBufferParam(cs, kernel, prop, data.Buffer)` (external GraphicsBuffer)
- Dispatch: `nativeCmd.DispatchCompute(cs, kernel, gx, gy, gz)`

**Depth textures** cannot bind as compute SRV. Copy first via `Blitter.BlitTexture` into an RFloat color texture, then bind the copy.

## Raster passes

Use `AddRasterRenderPass<T>()` for draw calls:
- `builder.SetRenderAttachment(colorTarget, 0, AccessFlags.ReadWrite)` — sets render target
- `builder.SetRenderAttachmentDepth(depthTarget, AccessFlags.Read)` — optional depth
- Inside lambda: `ctx.cmd.DrawMesh(mesh, matrix, material, submesh, pass)` — RasterCommandBuffer
- `Blitter.BlitTexture(ctx.cmd, source, scaleBias, material, pass)` — fullscreen blit

## Blitter API

`Blitter.BlitTexture` overloads:
- `(RasterCommandBuffer, RTHandle, Vector4 scaleBias, float mip, bool bilinear)` — simple copy
- `(UnsafeCommandBuffer, RTHandle, Vector4 scaleBias, Material, int pass)` — custom material
- `(CommandBuffer, RTHandle, Vector4 scaleBias, Material, int pass)` — native cmd
- Always needs `Blitter.Initialize()` called once (URP does this automatically)

## AsyncGPUReadback in render graph

- Request readback from external `GraphicsBuffer` (not transient — must persist until callback fires)
- One-in-flight guard: `if (!pending) { pending = true; AsyncGPUReadback.Request(buffer, callback); }`
- Callback fires on main thread next frame — copy data into persistent NativeArrays there
- Transient resources are freed after the pass — never readback from transient
