---
name: Extract sun from UniversalLightData.visibleLights, never RenderSettings.sun
description: Render features that need the main directional light must read it from frameData.Get<UniversalLightData>().visibleLights[mainLightIndex] inside the pass, not from RenderSettings.sun or FindObjectsByType<Light>
type: feedback
originSessionId: 1baef162-42d5-4a70-98b2-2f510e96fa21
---
When a render feature needs the main directional light (sun direction, color, intensity):

**Correct:** inside the pass's `RecordRenderGraph` (main thread), read
```csharp
var lightData = frameData.Get<UniversalLightData>();
int mainIdx = lightData.mainLightIndex;
if (mainIdx >= 0 && mainIdx < lightData.visibleLights.Length)
{
    var vl = lightData.visibleLights[mainIdx];
    Vector4 fwd = vl.localToWorldMatrix.GetColumn(2);
    Vector3 sunDir = -(new Vector3(fwd.x, fwd.y, fwd.z)).normalized;
    Color sunColor = vl.finalColor;
}
```
This is how `VolumetricCloudsPass.ApplyRaymarchGlobals` does it and is the only correct path.

**Wrong:** `RenderSettings.sun`, `Object.FindObjectsByType<Light>()`, a serialized `Light` reference on the feature, a singleton/service lookup from a time-of-day system. All of these:
- Bypass URP's culling and light selection logic (you can get a light URP didn't pick as main)
- Violate the "no scene refs in ScriptableRendererFeatures" rule
- Don't respect URP's `finalColor` (which includes intensity * colorMultiplier * lightmap-bake state)
- Create a scene-object coupling that the pass is supposed to avoid

**Why:** The whole point of the render-feature → frame-context contract is that the pass sees exactly what the rest of URP sees. Bypassing it produces subtle divergence (ambient lighting out of sync with the actual main light, shadow cascades mismatched with the sky's sun direction, etc.) and breaks features like VR stereo and camera stacking that rely on per-camera light data.

**Where `RenderSettings.ambient*` and other main-thread-only APIs fit:** `RecordRenderGraph` is main-thread and runs every frame during graph build. Write `RenderSettings.ambientSkyColor` etc. from there, NOT from the render func (which may execute on a worker thread).
