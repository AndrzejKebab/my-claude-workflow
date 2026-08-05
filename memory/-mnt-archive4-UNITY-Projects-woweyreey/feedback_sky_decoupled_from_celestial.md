---
name: Sky/atmosphere features stay decoupled from CelestialTimeSystem
description: Sky, fog, and atmosphere render features must read sun state from the URP frame context (UniversalLightData), never by referencing or subscribing to CelestialTimeSystem
type: feedback
originSessionId: 1baef162-42d5-4a70-98b2-2f510e96fa21
---
Sky / atmosphere / fog render features must source sun direction, colour, and intensity from the SRP frame context (`frameData.Get<UniversalLightData>().visibleLights[mainLightIndex]`) — not by referencing `CelestialTimeSystem`, subscribing to `OnTimeTick`, or holding any scene component reference.

**Why:** The user wants the rendering stack to stay *ultimately uncoupled* from the celestial system. Celestial controls the sky only *indirectly and declaratively* by moving the scene's main directional light; anything that reads "the sun" should read it from the render context like any other URP feature. This preserves the ability to swap celestial for any other sun driver (time slider, cinematic animation, cutscene, test harness) without touching the sky package, and it matches the existing `feedback_no_scene_refs_in_features` rule. `VolumetricCloudsPass.ApplyRaymarchGlobals` already does this correctly.

**How to apply:** When planning or implementing any atmosphere/sky/fog render feature, refuse to `using` the celestial namespace or take a serialized light reference on the feature. Read the main light index and the visible light struct out of `UniversalLightData` inside `RecordRenderGraph`. If a parameter-dirty flag is needed, base it on profile (ScriptableObject) changes only, not on celestial events.
