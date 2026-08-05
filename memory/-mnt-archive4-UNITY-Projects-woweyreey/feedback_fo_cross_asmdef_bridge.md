---
name: FO event subscription across heightfields ↔ VT asmdefs uses an upstream bridge
description: Origin.Shifted lives in heightfields asmdef; VT asmdef can't subscribe directly (circular asmdef ref); bridge file in heightfields forwards to VT components
type: feedback
originSessionId: 7a154c77-1447-4a0b-ba91-2e4664256689
---
`Zori.Heightfields` asmdef references `Zori.Heightfields.VirtualTextures`. The reverse reference would create a circular dependency, so VT components cannot subscribe to `Zori.Heightfields.Origin.Shifted` directly. The pattern is: a bridge file in the heightfields asmdef subscribes to `Origin.Shifted` and forwards via a public method on the VT component (e.g. `RWVTCpuPageTableManager.OnOriginShifted(delta)`), iterated through `RWVTManager.ActiveHandles`.

**Why:** Asmdef-encapsulation rule (no cycles). Discovered 2026-05-05 fixing VT ring jumps on FO repos — `RWVTCpuPageTableManager.PrevCenterTile` needs pre-shifting on FO event but lives in the lower-level VT asmdef.

**How to apply:** When a heightfields-package event needs to drive state in the VT package, write a `[RuntimeInitializeOnLoadMethod(SubsystemRegistration)]` bridge in the heightfields asmdef that subscribes to the heightfields-side event and calls a public method on the VT component. The VT component exposes the necessary mutator; the bridge orchestrates. Same pattern applies to any future heightfields → VT signalling. `RWVTManager.ActiveHandles` (static `IReadOnlyList<RWVTHandle>`) is the canonical iterator for live VT instances; reuse it instead of adding parallel registries. Existing example: `Packages/is.zori.heightfields/Heightfields/Runtime/FloatingOriginVirtualTexturesBridge.cs`.
