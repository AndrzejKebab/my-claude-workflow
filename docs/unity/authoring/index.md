# Authoring, serialization & package samples — file rules and the sample lifecycle

Local reference for the Unity rules that decide whether a scene, prefab, or SubScene can resolve a script reference at all, and for the package-sample workflow that delivers those assets to consumers. These are not API-signature facts — they are constraints on how source files map to the asset IDs Unity writes into YAML, and on where a sample compiles versus where it ships. Breaking the serialization rules produces a defect (a "missing script") that never shows at C# compile time and only surfaces when the asset is opened or imported; mishandling the sample lifecycle ships that same defect to a consumer.

This docset is `mara`-local: the rules are the engine's, but the cited evidence is `mara`'s own authoring code under `Assets/Samples/…` and the character-controller-2D / physics-2D packages, where the same defect recurred three times during one orchestration.

## Documents

- [`monobehaviour-files.md`](monobehaviour-files.md) — the one-class-per-file rule and why `fileID: 11500000` only binds the file-name-matching type; the corollary for programmatic (`-executeMethod`) scene and prefab builders; the symptom and the YAML-level confirmation procedure.
- [`package-samples.md`](package-samples.md) — the package-sample lifecycle: `Samples~/` is the tilde-ignored golden deliverable, the `Assets/Samples/…` import is the working copy; import-if-absent first, develop and prove in the import, then promote to `Samples~/` only past a required compile + manual-QA gate. Re-import/publish is additive (stale files linger), and publishing must preserve `.cs.meta` GUIDs or a consumer's import gets missing scripts (the serialization-rule companion).

## When to read this

| You are about to…                                                      | Read first |
|------------------------------------------------------------------------|------------|
| Add or rename a `MonoBehaviour` or `ScriptableObject`                  | [`monobehaviour-files.md`](monobehaviour-files.md) |
| Put a second serialized authoring type next to an existing one        | [`monobehaviour-files.md`](monobehaviour-files.md) |
| Build a scene / prefab / SubScene programmatically (`AddComponent<T>` + save) | [`monobehaviour-files.md`](monobehaviour-files.md) |
| Diagnose "The referenced script is missing" / "associated script can not be loaded" | [`monobehaviour-files.md`](monobehaviour-files.md) |
| Develop, test, or publish a package sample (`Samples~/` ↔ `Assets/Samples/…`) | [`package-samples.md`](package-samples.md) |

## What this docset deliberately does NOT cover

- Custom serialization (`ISerializationCallbackReceiver`, `[SerializeReference]` polymorphism, `FormerlySerializedAs`). The rule here is about script *identity* (which type a `m_Script` reference resolves to), not about how a type's fields serialize.
- Asset GUID assignment and `.meta` mechanics beyond the single `fileID: 11500000` fact the rule turns on. The full meta-file model is Unity-Manual territory.
- ECS baking flow (`Baker<T>`, `IComponentData` emission). Authoring `MonoBehaviour`s are subject to this rule; the ECS types their bakers emit are not, and that boundary is the rule's whole point — see `monobehaviour-files.md` § "What is and is not subject".
- The broader UPM model — `manifest.json` / `packages-lock.json` entries, `testables`, the `package.json` schema beyond its `samples[]` array, and the embedded-vs-registry distinction. `package-samples.md` covers only the sample's two homes (`Samples~/` delivery, `Assets/Samples/…` working copy) and the publish discipline that keeps GUIDs stable; the package-management surface is project-`CLAUDE.md` and Unity-Manual territory.
