---
name: No scene object references in ScriptableRendererFeatures
description: Renderer features live in project assets — never serialize scene object references (Light, Camera, Transform, etc.); pull from SRP frame data instead
type: feedback
originSessionId: af2be8bc-0bba-4c00-a645-34e1fb23a601
---
A `ScriptableRendererFeature` is serialized on a URP renderer asset (project asset). It cannot hold a reference to any scene object — scene references don't survive across scene loads, and the asset inspector can't even pick them.

**Why:** Renderer asset ↔ scene lifetime mismatch. A serialized `Light _sunLight` field on a feature is always invalid.

**How to apply:**
- Never add `[SerializeField] Light/Camera/Transform/GameObject/MonoBehaviour` fields to a `ScriptableRendererFeature` or nested `ScriptableRenderPass`.
- To read the main directional light in a pass: `frameData.Get<UniversalLightData>()` inside `RecordRenderGraph`, then `lightData.mainLightIndex` → `lightData.visibleLights[mainLightIndex]` (a `VisibleLight`). Use `.localToWorldMatrix.GetColumn(2)` for forward / `.finalColor` for color.
- To read the active camera: `frameData.Get<UniversalCameraData>().camera` (fine inside a pass; not from the feature's inspector).
- Scene-driven parameters should flow through a script on a scene object that calls into the feature (e.g. setting a plain struct property) or via a runtime-assigned `ICloudSettingsProvider`-style interface — not through serialized references.
