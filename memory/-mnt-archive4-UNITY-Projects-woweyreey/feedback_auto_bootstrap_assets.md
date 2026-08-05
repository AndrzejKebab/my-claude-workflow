---
name: Auto-bootstrap internal SOs; CreateAssetMenu for artist-touched SOs
description: Hidden internal-only ScriptableObjects (manifests, config tables) use [InitializeOnLoad] bootstrap at a fixed Resources path. Public artist-touched SOs (materials, profiles, presets) MUST have [CreateAssetMenu] so artists can author variants.
type: feedback
originSessionId: b3380b00-ea07-47c6-9ad5-1d17f81e3edd
---
Two distinct ScriptableObject categories with opposite rules:

**Category A — Hidden / internal-only (manifests, config, canonical lookup tables).** Single-instance assets that infrastructure depends on existing at a known path. Artists do not author these and should not see them in the Create menu.

- **No `[CreateAssetMenu]`.**
- `[InitializeOnLoad]` editor bootstrap creates + auto-populates the asset at a fixed `Resources/...` path when missing.
- Examples: `ZoriAtmosphericsShipManifest` (variant whitelist for builds), heightfield bootstrap tables.

**Category B — Public artist-touched (materials, profiles, presets, maps).** Multi-instance assets that artists actively create variants of. The Create menu is the primary discovery + authoring surface.

- **`[CreateAssetMenu(menuName = "Zori/...")]` required.** No menu = artists can't make new ones without writing code, which they shouldn't have to.
- May ALSO ship `[InitializeOnLoad]` defaults at fixed Resources paths so the runtime has guaranteed-non-null fallback values and so artists have copy-from starting points. Bootstrap and menu coexist — the bootstrap creates the *defaults*, the menu lets artists make *variants*.
- Examples: `FogVolumeMaterial`, `FogMapAsset`, `Noise3DProfile`, `CloudPreset`, `FogPreset`.

**Why:** User explicitly rejected a plan that relied on a CreateAssetMenu flow for the atmospherics ship manifest (2026-04-18 — "i'll create it ONCE and then we'll remove the create asset menu, or the system should auto-create it and auto-populate it"). User then clarified (2026-05-03) that this rule applies *only* to internal SOs — anything artist-touched MUST have a proper Create menu. The two are not interchangeable: hiding an artist-facing SO from the menu blocks the authoring workflow; exposing an internal manifest in the menu invites duplicate orphan instances.

**How to apply:**
- New SO type → first ask "do artists ever create variants of this?" If yes, Category B. If no (single canonical instance only), Category A.
- Category A: `[InitializeOnLoad]` bootstrap that defers via `EditorApplication.delayCall`, checks `AssetDatabase.LoadAssetAtPath`, creates via `ScriptableObject.CreateInstance` + `AssetDatabase.CreateAsset` when missing. Bail out if `BuildPipeline.isBuildingPlayer`. Idempotent Populate so reloads don't cause phantom dirty states. Optional "Re-populate" button in CustomEditor.
- Category B: `[CreateAssetMenu(fileName = "...", menuName = "Zori/<Subsystem>/<TypeName>")]` on the SO type. Menu path stays under `Zori/` so the package's surface is namespaced. May additionally ship bootstrap defaults at `Resources/Atmospherics/Default-<TypeName>.asset` for runtime fallback + artist starting templates — not mutually exclusive.
