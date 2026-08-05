---
name: shadergraph-custom-target-mechanics
description: "How mhf's custom ShaderGraph target works — asmref into URP editor asm, displayName ordering trap, additionalShaderID secondary shader, Dependency line"
metadata: 
  node_type: memory
  type: project
  originSessionId: 82f1c76b-2749-4fea-bb5f-a033284a0a98
---

The mhf VT Stamp target (`is.zori.miniheightfields/Editor/ShaderGraphTarget/`) subclasses ShaderGraph's internal `Target` by compiling into `Unity.RenderPipelines.Universal.Editor` via `.asmref` (GUID `c579267770062bf448e75eb160330b7f`) — the only sanctioned seam: SG's whole generation API is internal, `InternalsVisibleTo` whitelist only (byte-identical across SG 17.0.4/17.3.0/17.5.0; Target API drift is purely additive). Consequences and traps, all verified 2026-07-16:

- Code in that asmref subtree cannot reference package assemblies; contracts travel as strings (shader name, LightMode tag, uniform names).
- **GraphData sorts active targets alphabetically by `displayName`** and the first target's SubShader is what `Material.FindPass`/`passCount` resolve against. A target named before "Universal" silently steals the primary shader's active SubShader. mhf's target is named "VT Stamp" (V > U) for this; a generation gate (`StampTargetGenerationTests`) pins it.
- `SubShaderDescriptor.additionalShaderID = "Hidden/{Name}_X"` emits a standalone secondary shader; a primary-side SubShader carrying `shaderDependencies` emits the ShaderLab `Dependency` line (build inclusion + `Shader.Find` reachability). Import-order "dependency not found" warnings are benign — Unity's own URP terrain graph templates emit them.
- `ignoreCustomInterpolators` (default true) makes `CustomInterpolatorNode` reads inline to `float4(0,0,0,0)` — mhf's stamp pass exploits this: the shim (`HeightfieldsSG.hlsl`) substitutes a file-scope static set by the fulfiller-quad fragment (`HeightfieldStampShared.hlsl`).
- Don't include URP `CoreIncludes.CorePostgraph` in a minimal non-lit pass — its Varyings.hlsl needs lit fields (`invalid subscript 'sh'`); include `Editor/ShaderGraph/Includes/ShaderPass.hlsl` pregraph yourself so `#if SHADERPASS ==` comparisons don't collapse to undefined==undefined.
- Editing target C# does NOT reimport dependent .shadergraphs despite `AddAssetDependency(SourceDependency)` in batchmode runs — touch the graph file to force regeneration when iterating.

**Why:** these cost a full debug loop each; the codebase itself can't reveal them (they live in SG internals).
**How to apply:** extending the stamp target (MRT layouts, new pass sets) — reread this before touching SubShader/pass descriptors; keep the generation gate green as the drift detector.
