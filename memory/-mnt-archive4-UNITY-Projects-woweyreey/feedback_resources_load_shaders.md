---
name: Shader.Find via serialized manifest (not Resources.Load)
description: Pin shaders into builds via serialized Shader[] refs on a feature-owned manifest, then look up at runtime with Shader.Find — do not use Resources.Load or Resources/ folders for shaders
type: feedback
originSessionId: a20894bf-9345-4acc-887c-a1c238f13502
---
For the atmospherics package (and any package that adopts the same pattern): shaders are NOT placed in `Resources/` and are NOT loaded with `Resources.Load<Shader>`.

Instead:
1. A ScriptableObject manifest (`ZoriAtmosphericsShipManifest`) holds direct serialized `Shader[]` / `ComputeShader[]` references, auto-populated at edit-time via `AssetDatabase.LoadAssetAtPath` by scanning the package's runtime `.shader` / `.compute` files.
2. The manifest is a hidden serialized field on the `ScriptableRendererFeature` — so the URP renderer asset's serialization graph transitively pins every shader into the build when (and only when) the feature is used.
3. Runtime `Shader` lookup uses `Shader.Find("<ShaderLab name>")` — safe because the serialized refs have already forced inclusion.
4. Runtime `ComputeShader` lookup iterates `manifest.computeShaders` and matches by `computeShader.name` (ComputeShader has no `.Find`).

**Why this replaces the old `Resources.Load` rule:** `Resources/` forces unconditional build inclusion, defeating the opt-in property — if a package isn't added to any URP asset, its shaders should not ship. Serialized references on a feature-owned manifest give that opt-in while still guaranteeing `Shader.Find` resolves the names because Unity's serializer pulled the shaders in.

**How to apply:**
- New shader/compute/texture in the atmospherics package → live under the owning domain's `Shaders/` or `Textures/` folder (never `Resources/`). `ShipManifestPopulator` auto-adds it to the serialized array on the manifest.
- All runtime asset lookups go through `ZoriAtmosphericsResources`:
  - `ZoriAtmosphericsResources.Shader("<ShaderLab name>")` — wraps a manifest-scoped iteration (equivalent to `Shader.Find` but restricted to manifest-pinned shaders).
  - `ZoriAtmosphericsResources.ComputeShader("<asset filename>")` — manifest iteration matched by `computeShader.name`.
  - `ZoriAtmosphericsResources.Texture("<asset filename>")` — manifest iteration matched by `texture.name`.
- Consumer code must NEVER call `Shader.Find`, `Resources.Load`, or `AssetDatabase.Load*` directly — the helper is the single seam.
- Do NOT reintroduce `Resources/` for any package asset; do NOT reintroduce `Resources.Load`.
