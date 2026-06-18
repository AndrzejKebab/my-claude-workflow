# Texture resources — creation APIs and lifetimes

The companion to [global-state.md](global-state.md). That document covers how to *publish* a texture as a global and how the binding reaches a consumer pass; this one covers *which kind of texture you are allowed to publish*, and why publishing the wrong kind crashes the frame. The two are read together: the publish mechanism (`SetGlobalTextureAfterPass`) only works for a resource whose lifetime outlives the producing pass, and only one of the three creation APIs gives you that.

The single bug this page exists to prevent: a transient texture published as a global. A transient is valid only inside the pass that creates it; a global binding propagates to later passes; RenderGraph rejects the cross-pass use and throws every frame. The taxonomy below states which API produces a publishable resource and which does not.

Source for this page: core RenderPipelines package `com.unity.render-pipelines.core@20646981ef08`, package version `17.6.0`, under `Library/PackageCache/.../Runtime/RenderGraph/`. URP cross-references are `com.unity.render-pipelines.universal@2f8ca6fea95b`. File:line citations are relative to those package roots. Version drift is real — the shared-texture finding below is a removal that happened in this version line, so a future engine may differ; re-verify against the engine a given project actually runs.

---

## The three creation APIs and their lifetimes

There are three ways to get a texture into a render graph, distinguished by lifetime. All three eventually call the same registry method `RenderGraphResourceRegistry.CreateTexture(in TextureDesc desc, int transientPassIndex = -1)` (`RenderGraphResourceRegistry.cs:816`) for created textures, or `ImportTexture` for imported ones — the lifetime difference is entirely in whether `transientPassIndex` is set and whether the resource is pooled.

### `CreateTransientTexture(in TextureDesc)` — single-pass scratch

`IRenderGraphBuilder.cs:70` (also the `in TextureHandle` descriptor-copy overload at `IRenderGraphBuilder.cs:78`). This is a **builder** method — called on the `using var builder` inside a single pass, not on the `RenderGraph` instance.

The texture is valid ONLY inside the pass that creates it. The implementation at `RenderGraphBuilders.cs:165-170` calls `m_Resources.CreateTexture(desc, m_RenderPass.index)` — note the pass index is passed as `transientPassIndex`, stamping the resource with the owning pass — and then `UseTransientResource(result.handle)`. The XML doc states the read/write contract: "This texture will only be available for the current pass and will be assumed to be both written and read so users don't need to add explicit read/write declarations" (`IRenderGraphBuilder.cs:65-66`). You do not `UseTexture` it; the transient mechanism declares the read+write itself (`RenderGraphBuilders.cs:281-283`: "Transient resources are always considered written and read in the render graph pass where they are used").

Use it for intermediate scratch a pass needs and discards within itself — a temporary the next pass never sees.

### `RenderGraph.CreateTexture(in TextureDesc)` — graph/frame-scoped, pooled and aliased

`RenderGraph.cs:682` (plus descriptor-copy overloads at `RenderGraph.cs:697,714`). This is a method on the **`RenderGraph` instance**, called before building a pass, not on the builder.

The texture is scoped to the whole graph (the frame's recording) and usable across multiple passes within that graph. It is freed at end of graph execution. The registry allocates it through the texture pool (`AddNewRenderGraphResource(out TextureResource texResource)` defaults `pooledResource: true` at `RenderGraphResourceRegistry.cs:153,163`; the pool is a `TexturePool` set up at `RenderGraphResourceRegistry.cs:314`), so its backing memory is reused and can be intra-frame aliased with other graph resources whose lifetimes do not overlap (`EnableIntraFrameMemoryAliasing`, `RenderGraphResourceRegistry.cs:340-346`). Because `transientPassIndex` is left at its `-1` default (`RenderGraphResourceRegistry.cs:816`), the resource is NOT stamped to any single pass, and the transient-pass validation below never fires for it.

This is the kind of texture you produce in one pass, read in later passes, and publish as a global within the same frame. It is what `SetGlobalTextureAfterPass` expects.

### `RenderGraph.ImportTexture(RTHandle)` — external, caller-owned, persistent across frames

`RenderGraph.cs:576`, with overloads `ImportTexture(RTHandle, ImportResourceParams)` at `RenderGraph.cs:610` and `ImportTexture(RTHandle, RenderTargetInfo, ImportResourceParams)` at `RenderGraph.cs:633` (the last is for RTHandles wrapping a `RenderTargetIdentifier`, where the graph cannot derive the texture's properties and the caller must supply them). Also a method on the **`RenderGraph` instance**.

The texture is an external, caller-owned `RTHandle`; the graph wraps it in a handle for the duration of this graph but does not own, pool, alias, or free its memory. The caller manages the `RTHandle`'s lifecycle (allocation and release), so the underlying texture persists across frames — this is how history/accumulation buffers and LUTs enter the graph. The XML doc records the scheduling consequence: "Any pass writing to an imported texture will be considered having side effects and can't be automatically culled" (`RenderGraph.cs:568-569`). The `ImportResourceParams` overload lets the caller describe clear behaviour, which the doc notes "may be more efficient than manually clearing the texture using `cmd.Clear` on some hardware" (`RenderGraph.cs:608`).

Use it for anything whose contents must survive from one frame to the next, or anything owned and bound outside the graph.

### No `CreateSharedTexture` in this version

A persistent-across-frames texture that the render graph itself owns and pools — `CreateSharedTexture` — does **not** exist as a usable API in this package version. It is present only as a hard-removed stub: `Deprecated.cs:69-70` declares `[Obsolete("CreateSharedTexture() and shared texture workflow are deprecated, use ImportTexture() workflow instead.", true)]` with the error flag `true`, so any call fails to compile. The companion `RefreshSharedTextureDesc` and `ReleaseSharedTexture` are obsoleted the same way (`Deprecated.cs:83-84,93-94`). An internal registry implementation still exists (`RenderGraphResourceRegistry.cs:589` `internal TextureHandle CreateSharedTexture(...)`), but it is not reachable from outside the module. The deprecation message names the replacement: the across-frames use case is served by `ImportTexture` with a caller-managed `RTHandle`. (A grep of the whole package confirms no other public shared-texture or "create persistent" entry point; newer RenderGraph versions may reintroduce one, so re-check on a version bump.)

---

## The rule the bug broke: a transient must not cross passes, so it must not be published as a global

A transient texture is stamped with the index of the pass that created it (`transientPassIndex = m_RenderPass.index`, `RenderGraphBuilders.cs:167`). Every time a builder declares a use of any resource it runs `CheckResource` (`RenderGraphBuilders.cs:650`), which compares the resource's transient index against the current pass:

```csharp
if (transientIndex != -1 && transientIndex != m_RenderPass.index)
{
    var name = m_Resources.GetRenderGraphResourceName(res);
    throw new ArgumentException(
        $"In pass '{m_RenderPass.name}' when trying to use resource '{name}' of type {res.type} at index {res.index} - " +
        RenderGraph.RenderGraphExceptionMessages.UseTransientTextureInWrongPass(transientIndex));
}
```

(`RenderGraphBuilders.cs:664-670`.) The message body is at `RenderGraph.ExceptionMessages.cs:117-118`. The full runtime error a reader sees is:

> `In pass '<consumer pass name>' when trying to use resource '<name>' of type Texture at index <i> - This pass is using a transient resource from a different pass (pass index N). A transient resource should only be used in a single pass.`

Why publishing as a global triggers exactly this: `SetGlobalTextureAfterPass(handle, propertyId)` records the handle into a global slot that propagates to subsequent passes (see [global-state.md](global-state.md) — the compiler emits `cmd.SetGlobalTexture` after the producing pass, and a consumer reaches the binding by declaring `UseGlobalTexture(propertyId)` or `UseAllGlobalTextures(true)`). When the consumer declares that use, RenderGraph resolves the global slot to the transient handle and calls `CheckResource` for it from the *consumer's* pass — a different pass index than the one stamped on the transient — and the validation above throws. In a full pipeline the consumer is often a pass you did not write: URP's own overlay passes (Draw UIToolkit / uGUI Overlay) and `DrawObjects` passes pull in published globals, so a transient published as a global crashes the frame even when your own passes never touch it again.

A transient is correct only for scratch consumed inside its single pass. The moment a texture must be visible to any other pass — published as a global, or simply read by a later pass — it must be a graph-scoped `CreateTexture` (or an imported `RTHandle`), never a transient.

---

## Which to use when

Three resource lifetimes map to three decision cases.

- **Scratch needed and discarded within one pass** → `builder.CreateTransientTexture(desc)`. Pooled, single-pass, auto read+write, never published, never read by another pass.

- **Produced in one pass, read by later passes within the same frame, and/or published as a global** → `renderGraph.CreateTexture(desc)`. Graph-scoped, pooled, aliasable. This is the resource you pass to `SetGlobalTextureAfterPass`. URP's own `MainLightShadowCasterPass` is the canonical example: the shadowmap is created graph-scoped via `UniversalRenderer.CreateRenderGraphTexture` — which returns `renderGraph.CreateTexture(rgDesc)` (`UniversalRendererRenderGraph.cs:266`) — and then published with `builder.SetGlobalTextureAfterPass(shadowTexture, MainLightShadowConstantBuffer._MainLightShadowmapID)` (`MainLightShadowCasterPass.cs:423`). It is a non-transient resource precisely because every shadow-receiving pass downstream reads it through the global slot.

- **Must persist across frames (history / accumulation / temporal buffers), or owned and bound outside the graph (a LUT, an externally allocated render target)** → `renderGraph.ImportTexture(rtHandle)` with a caller-managed `RTHandle` whose allocation and release you own. The graph treats writes to it as side effects and will not cull the producing pass (`RenderGraph.cs:568-569`).

---

## Interaction with `Graphics.RenderMesh`-injected geometry

Geometry injected from `beginCameraRendering` via `Graphics.RenderMesh` is drawn by URP inside its own RenderGraph `DrawObjects` passes, not by a custom pass you author. Such a draw can read a texture you published as a global only when the global propagates to that draw's pass and the pass declares it reads globals — i.e. the consuming `DrawObjects` pass declares `UseGlobalTexture(propertyId)` or `UseAllGlobalTextures(true)` (the propagation mechanism is documented in [global-state.md](global-state.md); only textures published via `SetGlobalTextureAfterPass` are covered, and only graphics shaders read host-side `Shader.SetGlobal*` reliably).

The taxonomy consequence is direct: a `CreateTexture` (graph-scoped) published as a global is reachable by such injected draws, because the resource outlives the producing pass and the global binding can legally resolve to it in the consumer. A `CreateTransientTexture` is not reachable by them — it cannot be published as a global at all (the validation above throws), and even if its handle reached the consumer's pass the cross-pass `CheckResource` would reject it. If injected geometry needs to sample a texture your feature produced, that texture must be graph-scoped or imported.
