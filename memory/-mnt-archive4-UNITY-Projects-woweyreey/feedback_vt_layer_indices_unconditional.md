---
name: VT layer-index slots must be reserved unconditionally
description: HeightfieldTerrainController and any RWVT-layer layout that is consumed by mask-bit-position math must reserve every slot regardless of whether its fulfiller resolved
type: feedback
originSessionId: 93db64b0-41cc-403f-9177-995d6f21aeaa
---
RWVT physical-pool indexing in `StampCompositor.BindMRT` / `ClearTileRegions` / `GatherActiveLayers` uses `(mask & (1 << li))` — i.e. it assumes layer-index `li` equals the bit position of that layer's `RWVTLayerMask` enum value. The `BuildFulfillerArrays` Pre/Post split likewise depends on the hardcoded `LayerSplat0=2`, `LayerSplat1=3` constants. **Any conditional layer-slot reservation drifts every later slot by one and silently corrupts the mask→pool mapping.**

**Why:** ship-manifest resolution is timing-sensitive in player builds. `HeightfieldRenderFeature.Create` publishes `ZoriHeightfieldsResources.SharedManifest` only on URP's first-frame pipeline construction — strictly after the controller's `OnEnable`. Editors mask this with a `#if UNITY_EDITOR` AssetDatabase fallback, so the bug only shows up in standalone. Previous regression: NormalOS was conditional on `_normalCompute != null`; in builds it was null at OnEnable, layout collapsed to `[Height, Splat0, Splat1, BaseMap]`, splat stamps wrote into wrong pools, BaseMap fulfiller never ran (the post-partition `li > LayerSplat1=3` excluded BaseMap at li=3).

**How to apply:**
- Always reserve every layer slot whose index is referenced in `LayerHeight/NormalOS/Splat0/Splat1`-style constants or matched against an `RWVTLayerMask` bit, even if the fulfiller compute/material isn't yet resolved.
- A null fulfiller is fine — the layer just stays black until populated. Lazy-resolve the fulfiller in `Update` and `InvalidateLayer` once it appears.
- When auditing similar code: trace any `(1 << li)` / `1 << layerIndex` pattern. If the `li` it walks isn't guaranteed to equal the mask-bit position, that's the bug.
- Editor-only verification is not enough for VT layout changes — the manifest-timing divergence is invisible until standalone.
