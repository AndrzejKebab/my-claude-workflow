---
name: HeightfieldTerrainController has no FloatingOriginAnchor — content procedurally offset
description: Terrain content lives at (goPos + Origin) in Unity-world, not at goPos — any matrix using terrainTf.worldToLocalMatrix needs Translate(-Origin) compensation
type: feedback
originSessionId: 7a154c77-1447-4a0b-ba91-2e4664256689
---
`HeightfieldTerrainController` does NOT have a `FloatingOriginAnchor` and does NOT implement `IFloatingOriginHandler`. Its `transform.position` stays put across FO shifts. Its visible content is procedurally anchored at `(goPos + Origin.Current)` in Unity-world — see `HeightfieldTerrainController.cs:774`: `mul(invRS, -(Origin.Current + transform.position))`.

**Why:** Heightfield content is rendered relative to a content-frame anchor that includes Origin. The terrain stays visually still relative to a moving FO-anchored player. `terrainTf.worldToLocalMatrix` only knows about goPos, so any matrix built from it sees the wrong terrain anchor by `+Origin` after the first FO repositioning. Symptom: heightfield SM (and godrays sampling it) drifts toward camera's new Unity-world position (~0,0,0) on every FO shift — fixed 2026-05-05 in `HeightfieldShadowSource.cs:301-322`.

**How to apply:** When building any world↔terrain-content transform from `terrainTf.worldToLocalMatrix` / `localToWorldMatrix`, pre-translate by ±Origin:
```csharp
var worldToLocal = mul(terrainTf.worldToLocalMatrix, float4x4.Translate(-foOrigin));
var localToWorld = mul(float4x4.Translate(+foOrigin), terrainTf.localToWorldMatrix);
```
Consumers downstream of the corrected matrix continue to take Unity-world (camera.transform.position-style) inputs — the fix is contained at construction. Any new SM-like camera-anchored snap, fog box-test, or terrain-content transform that uses Unity's transform matrices is suspect — verify with `Origin.Current != 0` before trusting it.

Convention recap (`Origin.cs` is canonical): `Global = Local - Origin`. After shift: `Origin -= delta`, FO-anchored objects do `transform.position -= delta`.
