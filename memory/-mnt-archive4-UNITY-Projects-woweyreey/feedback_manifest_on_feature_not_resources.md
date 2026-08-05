---
name: Ship manifest lives on the render feature, never in Resources/
description: ZoriAtmosphericsShipManifest must be a hidden serialized field on ZoriAtmosphericsFeature, not loaded via Resources.Load, so the feature's presence in a URP asset gates what ships
type: feedback
originSessionId: a20894bf-9345-4acc-887c-a1c238f13502
---
The atmospherics ship manifest (`ZoriAtmosphericsShipManifest`) must be referenced as a `[SerializeField, HideInInspector]` field on the `ZoriAtmosphericsFeature` (ScriptableRendererFeature). It MUST NOT live under any `Resources/` folder and MUST NOT be loaded via `Resources.Load`.

**Why:** When the render feature is wired into a URP renderer asset, Unity's serialization graph pulls in the manifest asset and — via the manifest's `Shader[]`/`ComputeShader[]` fields — every shader/compute the package needs. That transitive reference is what guarantees shaders ship. Conversely, if the feature is NOT added to any URP asset, the entire package (manifest + every shader + every compute) can be left out of the build and never compiled. A `Resources/` asset forces inclusion unconditionally, which breaks the "opt-in via feature" guarantee.

**How to apply:**
- Package ScriptableObject assets that gate build inclusion go on the consuming component/feature as hidden serialized fields, not Resources/.
- Runtime lookup is reached via `ZoriAtmosphericsFeature`'s exposed manifest (e.g., static accessor set in `Create()`/`OnEnable`), not `Resources.Load`.
- Editor bootstrap (`[InitializeOnLoad]`) is still responsible for creating/populating the manifest .asset and wiring the reference onto the feature asset(s), but the runtime path never touches Resources.
- This supersedes `feedback_resources_load_shaders.md` for the atmospherics package shader pipeline.
