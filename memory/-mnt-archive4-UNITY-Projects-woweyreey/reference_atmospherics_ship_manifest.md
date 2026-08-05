---
name: Atmospherics ship manifest — package-scoped variant whitelist
description: ZoriAtmosphericsShipManifest ScriptableObject + IPreprocessShaders/IPreprocessComputeShaders hooks that whitelist the atmospherics package's own shader/compute variants at build time. Auto-bootstrapped, auto-populated from #pragma scan.
type: reference
originSessionId: b3380b00-ea07-47c6-9ad5-1d17f81e3edd
---
The atmospherics package ships a build-time variant whitelist for its own shaders and compute shaders. It exists because URP's default stripping can drop variants selected by runtime-toggled keywords on materials built via `CoreUtils.CreateEngineMaterial` — URP's stripper doesn't see those materials.

**Files**:
- `Packages/is.zori.atmospherics/Runtime/ZoriAtmosphericsShipManifest.cs` — ScriptableObject schema: `shaders[]`, `computeShaders[]`, `shaderVariants[]`, `computeVariants[]` (each a `(shader|compute, passName|kernelName, enabledKeywords[])` tuple).
- `Packages/is.zori.atmospherics/Runtime/Resources/ZoriAtmosphericsShipManifest.asset` — auto-created.
- `Packages/is.zori.atmospherics/Editor/Build/ShipManifestBootstrap.cs` — `[InitializeOnLoad]` creates the asset if missing and populates it.
- `Packages/is.zori.atmospherics/Editor/Build/ShipManifestPopulator.cs` — globs `Runtime/**/Resources/**/*.shader|*.compute`, parses `#pragma multi_compile` / `#pragma shader_feature` lines, emits the full cartesian product of declared tokens as deterministically-ordered manifest rows. Idempotent — no-op on a clean manifest.
- `Packages/is.zori.atmospherics/Editor/Build/ShipManifestPreprocessor.cs` — `IPreprocessShaders` + `IPreprocessComputeShaders`. For shaders owned by the manifest, strips variants whose (projected-into-package-vocabulary) enabled-keyword set doesn't match any manifest row. Foreign shaders pass through untouched. Emits per-shader kept/stripped counts in `IPostprocessBuildWithReport`.
- `Packages/is.zori.atmospherics/Editor/Build/ShipManifestEditor.cs` — `CustomEditor` with Re-populate + Validate buttons (Validate scans package `.cs` for runtime keyword literals and warns on any not covered).

**Scope — what it covers**: variants of atmospherics-owned shaders/computes under the package's Resources folders.
**Scope — what it does NOT cover**: foreign shaders (URP lit, MicroSplat, water). For those, Unity's own keyword-preservation machinery on the renderer-feature or pipeline-asset side is the right tool.

**How to extend**: add a new shader or compute under `Packages/is.zori.atmospherics/Runtime/**/Resources/**/`, author `#pragma multi_compile`/`#pragma shader_feature` lines. Bootstrap re-runs on the next editor load; Re-populate button forces immediate refresh. No manual manifest editing expected.
