# Global state and how it reaches custom passes

The single most error-prone area of RenderGraph in URP. This document covers:

1. The two kinds of "global" — host-side `Shader.SetGlobal*` vs CommandBuffer-issued `cmd.SetGlobal*`.
2. What `UseGlobalTexture` / `UseAllGlobalTextures` / `AllowGlobalStateModification` actually do (each is commonly misused).
3. The propagation rules between producer and consumer passes.
4. The exact list of globals issued by URP `MainLightShadowCasterPass` — these are the ones the project's compute fog/cloud passes need to consume.

---

## The two kinds of "global"

### Host-side: `Shader.SetGlobalTexture` / `Shader.SetGlobalMatrix` / etc.

Set on the `Shader` class — global to the application, not bound to any CommandBuffer.

- Reaches **graphics shaders** (vertex/fragment) reliably across DX/Vulkan/Metal — they are baked into the constant buffer at draw time.
- Reaches **compute shaders** unreliably:
  - On DX12 / Metal, host-side globals are typically visible in compute.
  - On Vulkan, host-side globals are NOT reliably visible in compute. The kernel reads them as zero. This is a well-known recurring trap; see project memory `feedback_compute_needs_explicit_params.md` and `feedback_physical_sky_compute_bindings.md`. The fix is always: capture the value at C# pass-record time and re-bind per dispatch via `cmd.SetComputeVectorParam` / `SetComputeFloatParam` / `SetComputeMatrixParam`.

The render graph does not see, schedule against, or lifetime-track host-side globals. They are invisible to the compiler.

### CommandBuffer-issued: `cmd.SetGlobalTexture` / `cmd.SetGlobalMatrixArray` / `cmd.SetGlobalVector` / etc.

Issued from inside a render func or a `ScriptableRenderPass.Execute`. Recorded into the CommandBuffer and replayed in pass order.

- Reaches both graphics and compute shaders, including on Vulkan, IF the CommandBuffer's bind survives until the consumer's dispatch is recorded.
- The render graph **only preserves the order across passes** when the producing pass calls `AllowGlobalStateModification(true)`. Without that, RG may reorder passes — a graphics pass that sets a global keyword could run after the compute pass that depended on it.

The render graph also tracks `cmd.SetGlobalTexture` only for textures explicitly published via `SetGlobalTextureAfterPass(handle, propertyId)` — the actual `cmd.SetGlobalTexture` is then issued automatically by the RG compiler (`RenderGraph.cs:2761`). For raw `cmd.SetGlobalTexture` calls inside a render func, RG sees nothing — same as for matrix arrays / vectors.

---

## What each builder method actually does

### `UseGlobalTexture(int propertyId, AccessFlags = Read)` — read dependency on a known slot

The receiving pass declares "I read whatever texture is currently bound to global slot `propertyId`". RG looks up `m_RenderGraph.GetGlobal(propertyId)` (`RenderGraphBuilders.cs:328`), finds the producing handle, and inserts an implicit `UseTexture(h, flags)` so the producer schedules first.

Throws if no prior pass has called `SetGlobalTextureAfterPass(_, propertyId)` on the slot — see `RenderGraphBuilders.cs:333-338`.

This is the targeted, RG-friendly way. Use it whenever you statically know which globals you read.

### `UseAllGlobalTextures(bool enable)` — read dependency on every known global texture

At builder `Dispose` time, iterates every published global slot and calls `UseTexture(t, Read)` on it (`RenderGraphBuilders.cs:131-140`).

- Only covers **textures** published via `SetGlobalTextureAfterPass`. Matrix arrays, vectors, floats, keywords are NOT covered.
- Only covers globals that some prior pass has actually published in this graph. Globals set host-side via `Shader.SetGlobal*` outside the graph are invisible.
- Use when your pass is opaque to RG ("DrawRendererList of arbitrary user shaders") or as a coarse net during bring-up. The XML doc explicitly says to prefer `UseGlobalTexture` per-slot.

### `AllowGlobalStateModification(bool value)` — for the producing pass

Disables culling AND prevents the RG compiler from reordering this pass relative to surrounding passes (`IRenderGraphBuilder.cs:118-120,123` — "introduce a render graph sync-point"; `RenderGraphBuilders.cs:64-77`).

- The flag belongs on the pass that **mutates** global state via `cmd.SetGlobal*` / `cmd.EnableKeyword`. Without it, the modifying calls might reorder ahead of consumers.
- Common misconception (and the project's current bug): enabling this on the consumer pass to "let it read URP globals". That's not what it does. The consumer needs `UseGlobalTexture` / `UseAllGlobalTextures` (for textures) plus a scheduled-before-me read dep on the producer's output.
- Unsafe passes get `AllowGlobalState(true)` automatically (`RenderGraph.cs:1505`).

---

## Producer → consumer propagation rules

Pass A publishes a global; pass B reads it. What guarantees the binding survives the trip?

### Texture globals

Producer (pass A):
```csharp
using (var builder = renderGraph.AddRasterRenderPass<...>(...)) {
  // ... write to handle ...
  builder.SetGlobalTextureAfterPass(handle, _MyTexID);
}
```
RG records the (handle, _MyTexID) pair. After pass A executes, the compiler emits `cmd.SetGlobalTexture(_MyTexID, handle)`.

Consumer (pass B):
```csharp
// Option A — preferred, named:
builder.UseGlobalTexture(_MyTexID, AccessFlags.Read);
// Option B — coarse:
builder.UseAllGlobalTextures(true);
```
This both creates the read dep (so RG schedules B after A) and gives B a copy of the binding.

If pass A also issues a raw `cmd.SetGlobalTexture(_OtherID, otherHandle)` from inside its render func (not via `SetGlobalTextureAfterPass`), then pass A must call `AllowGlobalStateModification(true)` AND pass B has no RG-tracked way to see it. B can declare `UseAllGlobalTextures(true)` and the binding will exist on the CommandBuffer (because RG kept ordering), but RG itself doesn't know about it.

### Non-texture globals (matrix arrays, vectors, floats, keywords)

There is no `UseGlobalMatrix` / `UseGlobalVector` / `UseGlobalKeyword`. RG cannot create a per-property dep on these. The flow is:

Producer issues `cmd.SetGlobalMatrixArray(_MainLightWorldToShadow, m_MainLightShadowMatrices)` from inside its render func. To prevent RG reordering it past the consumer, producer calls `AllowGlobalStateModification(true)`.

Consumer must:
1. Declare a separate read dep on **some texture** the producer also writes — that's how RG schedules B after A. (`UseTexture(mainShadowsTexture, Read)` is the standard pattern; the texture is the natural pivot).
2. **Not** redeclare or override the matrix array on the CommandBuffer between producer and consumer (no rebind, no clear).
3. For graphics passes (raster pass with vertex/fragment shaders) on any platform: the matrix array is now visible.
4. For **compute** passes on Vulkan: a matrix array set via `cmd.SetGlobalMatrixArray` is visible to compute kernels, **provided** the compute dispatch is recorded into the same CommandBuffer downstream of that call. For example, URP's `MainLightShadowCasterPass` publishes cascade globals and a later fog-population pass declares the shadow atlas as Read, causing its dispatch to be recorded after those bindings.

The split: **textures** and **`cmd.SetGlobalMatrixArray`/`cmd.SetGlobalVector`** ride the CommandBuffer. **`Shader.SetGlobalMatrixArray` / `Shader.SetGlobalVector`** does NOT — those are host-side and invisible to Vulkan compute (project memory `feedback_compute_needs_explicit_params.md`).

For URP's main-light shadows the `cmd.SetGlobal*` route is what you want, and it is what URP itself uses. So you do NOT need to mirror the cascade matrix array per-dispatch — declaring the right RG dep is enough. (Confirmed at `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/Passes/MainLightShadowCasterPass.cs:398-435` — every cascade global is set via `cmd.SetGlobal*` from inside the render func.)

What you do need to mirror per-dispatch is anything published only via host-side `Shader.SetGlobal*`, such as custom sky-light vectors or terrain falloff parameters.

---

## URP MainLightShadowCasterPass — exact published globals

Source: `BuiltInPackages/com.unity.render-pipelines.universal/Runtime/Passes/MainLightShadowCasterPass.cs:44-57,398-435`.

### Property IDs (cached at file scope)
```csharp
public static readonly int _WorldToShadow                  = Shader.PropertyToID("_MainLightWorldToShadow");
public static readonly int _ShadowParams                   = Shader.PropertyToID("_MainLightShadowParams");
public static readonly int _CascadeShadowSplitSpheres0     = Shader.PropertyToID("_CascadeShadowSplitSpheres0");
public static readonly int _CascadeShadowSplitSpheres1     = Shader.PropertyToID("_CascadeShadowSplitSpheres1");
public static readonly int _CascadeShadowSplitSpheres2     = Shader.PropertyToID("_CascadeShadowSplitSpheres2");
public static readonly int _CascadeShadowSplitSpheres3     = Shader.PropertyToID("_CascadeShadowSplitSpheres3");
public static readonly int _CascadeShadowSplitSphereRadii  = Shader.PropertyToID("_CascadeShadowSplitSphereRadii");
public static readonly int _ShadowOffset0                  = Shader.PropertyToID("_MainLightShadowOffset0");
public static readonly int _ShadowOffset1                  = Shader.PropertyToID("_MainLightShadowOffset1");
public static readonly int _ShadowmapSize                  = Shader.PropertyToID("_MainLightShadowmapSize");
public static readonly int _MainLightShadowmapID           = Shader.PropertyToID("_MainLightShadowmapTexture");
```

### Texture global (published via SetGlobalTextureAfterPass, RG-tracked)

`MainLightShadowCasterPass.cs:505`:
```csharp
if (shadowTexture.IsValid())
  builder.SetGlobalTextureAfterPass(shadowTexture, MainLightShadowConstantBuffer._MainLightShadowmapID);
```

So `_MainLightShadowmapTexture` is the **only** shadow global RG knows about by name. Everything else below rides the CommandBuffer ordering.

### Matrix and vector globals (issued via cmd.SetGlobal* inside render func)

`MainLightShadowCasterPass.cs:398-435`:
```csharp
cmd.SetGlobalMatrixArray(MainLightShadowConstantBuffer._WorldToShadow, m_MainLightShadowMatrices);
cmd.SetGlobalVector(MainLightShadowConstantBuffer._ShadowParams,
    new Vector4(light.shadowStrength, softShadowsProp, shadowFadeScale, shadowFadeBias));

if (m_ShadowCasterCascadesCount > 1)
{
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._CascadeShadowSplitSpheres0, m_CascadeSplitDistances[0]);
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._CascadeShadowSplitSpheres1, m_CascadeSplitDistances[1]);
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._CascadeShadowSplitSpheres2, m_CascadeSplitDistances[2]);
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._CascadeShadowSplitSpheres3, m_CascadeSplitDistances[3]);
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._CascadeShadowSplitSphereRadii, new Vector4(
        m_CascadeSplitDistances[0].w * m_CascadeSplitDistances[0].w,
        m_CascadeSplitDistances[1].w * m_CascadeSplitDistances[1].w,
        m_CascadeSplitDistances[2].w * m_CascadeSplitDistances[2].w,
        m_CascadeSplitDistances[3].w * m_CascadeSplitDistances[3].w));
}

if (shadowData.supportsSoftShadows)
{
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._ShadowOffset0, ...);
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._ShadowOffset1, ...);
    cmd.SetGlobalVector(MainLightShadowConstantBuffer._ShadowmapSize, new Vector4(invShadowAtlasWidth,
        invShadowAtlasHeight, m_RenderTargetWidth, m_RenderTargetHeight));
}
```

The pass body is a `RasterCommandBuffer` (the cast happens at `MainLightShadowCasterPass.cs:507-509`), and **all of these `cmd.SetGlobal*` calls are recorded into the same CommandBuffer that the rest of the frame uses**. URP itself enables `builder.AllowGlobalStateModification(true)` at line 502 to keep the order safe.

### Keyword globals

`MainLightShadowCasterPass.cs:365-367`:
```csharp
cmd.SetKeyword(ShaderGlobalKeywords.MainLightShadows, data.shadowData.mainLightShadowCascadesCount == 1);
cmd.SetKeyword(ShaderGlobalKeywords.MainLightShadowCascades, data.shadowData.mainLightShadowCascadesCount > 1);
ShadowUtils.SetSoftShadowQualityShaderKeywords(cmd, data.shadowData);
```

`_MAIN_LIGHT_SHADOWS` / `_MAIN_LIGHT_SHADOWS_CASCADE` are set via `cmd.SetKeyword` — same CommandBuffer ordering rules apply. Same for `_SHADOWS_SOFT*` quality keywords.

### Sampler

`sampler_LinearClampCompare` is declared inline in `Shadows.hlsl:65` as a `SAMPLER_CMP(sampler_LinearClampCompare)`. Unity's sampler-name-encoding heuristic synthesises the sampler state from the name pattern (`Linear` + `Clamp` + `Compare` → linear filter, clamp address, comparison sampler). No C#-side bind is needed — see [samplers.md](samplers.md).

---

## Sets the trap for the cascade-shadow-from-compute bug

For a compute pass that wants to call `SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, ...)` and apply the cascade transform `_MainLightWorldToShadow[cascadeIndex]`, the receiver must:

1. **Texture dep**: `builder.UseTexture(resourceData.mainShadowsTexture, AccessFlags.Read)` — pivots on the URP-provided handle so RG schedules `MainLightShadowCasterPass` first. (Equivalent: `builder.UseGlobalTexture(_MainLightShadowmapID, AccessFlags.Read)` after URP's pass has published it.)
2. **State preservation**: `builder.AllowGlobalStateModification(true)` is auto-enabled because all project compute work goes through `AddUnsafePass` (`RenderGraph.cs:1505`). For a real `AddComputePass` you would need this manually — but it would belong on the producer or on this pass only if it ALSO issues `cmd.SetGlobal*`. The cleaner statement: the **producer** (URP main-shadow pass) needs `AllowGlobalStateModification(true)` for its own outgoing matrix arrays / vectors — and URP does that at `MainLightShadowCasterPass.cs:502`. The consumer doesn't need to.
3. **Variant compilation**: enable `_MAIN_LIGHT_SHADOWS_CASCADE` (or `_MAIN_LIGHT_SHADOWS`) on the compute kernel. URP issues the keyword globally via `cmd.SetKeyword`; for a multi-kernel compute shader you usually mirror with `CoreUtils.SetKeyword(_populateCS, kw, on)` ahead of dispatch.
4. **Avoid the screen-space branch**: `Shadows.hlsl` can short-circuit to `SampleScreenSpaceShadowmap` when `_MAIN_LIGHT_SHADOWS_SCREEN` is on, and that branch uses implicit-LOD `Texture2D.Sample` — illegal in compute on Vulkan. A compute-specific helper should bypass `MainLightRealtimeShadow` and call an explicit-LOD shadow comparison such as `SAMPLE_TEXTURE2D_SHADOW`/`SampleCmpLevelZero` directly. See [shadow-sampling-from-compute.md](shadow-sampling-from-compute.md).

The `_CascadeShadowSplitSpheres0..3`, `_CascadeShadowSplitSphereRadii`, `_MainLightShadowParams`, `_MainLightShadowOffset0/1`, `_MainLightShadowmapSize`, `_MainLightWorldToShadow[5]` globals all flow via the CommandBuffer because URP issues them with `cmd.SetGlobalVector`/`cmd.SetGlobalMatrixArray`. They reach Vulkan compute provided steps 1 and 2 hold. There is no `UseGlobalMatrixArray` to declare per-name; the texture dep + ordering is enough.

What does NOT work: depending solely on `Shader.GetGlobalMatrix(...)` host-side reads at record time. Those would be stale in multi-camera graphs and aren't visible to Vulkan compute even when they are fresh (`feedback_compute_needs_explicit_params.md`).
