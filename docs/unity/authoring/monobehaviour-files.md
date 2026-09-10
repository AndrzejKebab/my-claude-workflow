# One `MonoBehaviour` per file, named after its class — the `fileID: 11500000` rule

The recurring "The referenced script is missing" / "associated script can not be loaded" defect comes from a single Unity serialization rule that has no C#-compile-time signal: Unity grants the canonical script `fileID: 11500000` only to the type whose name matches its `.cs` file, so any other serialized type sharing that file is unreferenceable from a scene, prefab, or SubScene. This page states the rule, the corollary for programmatic asset builders, and the YAML-level confirmation procedure.

## The rule

A `.cs` file holds exactly one `MonoBehaviour` or `ScriptableObject`, and the file is named exactly after that class. Unity's asset importer assigns the canonical script identity `fileID: 11500000` to the single type whose name matches the file name; that `{fileID: 11500000, guid: <the .cs's .meta guid>}` pair is the reference a scene, prefab, or SubScene writes to point at the script. A second `MonoBehaviour`/`ScriptableObject` in the same file gets no stable `fileID: 11500000` — there is one canonical slot per file and the file-name-matching type already holds it — so any asset that references the second type cannot resolve it and the component renders as a missing script.

The failure is invisible to the C# compiler. The file compiles, the type exists, and an editor that already has the type loaded into a live domain can even appear to work; the break surfaces only when the asset is re-imported or opened against the serialized `m_Script` reference, which is why it reaches a scene or SubScene undetected and recurs.

### What is and is not subject

The rule binds only the two serialized engine base types whose references go through the `fileID: 11500000` script slot:

- **Subject:** `MonoBehaviour`, `ScriptableObject`.
- **Not subject:** plain ECS and plain-CLR types — `IComponentData`, `IBufferElementData`, `ISystem`, `Baker<T>`, static classes, structs, enums, interfaces. These are never referenced through a `m_Script` slot, so several of them may legally share one file with each other and with one file-named authoring type.

This boundary is the whole point in an ECS authoring file: the `IComponentData` a baker emits, the `Baker<T>` itself, the `ISystem` that consumes the component, and tag structs can all sit beside the one authoring `MonoBehaviour` the file is named for — but a *second* authoring `MonoBehaviour` may not.

For example, a file named `CharacterAuthoring.cs` may contain a plain
`IComponentData` struct and `CharacterAuthoring : MonoBehaviour`, but another
serialized class such as `PlatformAuthoring : MonoBehaviour` belongs in its own
`PlatformAuthoring.cs` file. Splitting serialized classes this way gives each
one its own `.cs.meta` GUID and canonical script identity.

## Corollary for programmatic scene / prefab builders

An editor builder that authors assets via `gameObject.AddComponent<T>()` and saves with `EditorSceneManager.SaveScene` (or `PrefabUtility.SaveAsPrefabAsset`) gets a correct `{fileID, guid}` written for free — but only when `T` lives in its own correctly-named file. Unity resolves `T` to its canonical script asset and serializes the `fileID: 11500000` reference itself; the builder never spells the reference out.

Do not post-process the saved asset to repair MonoBehaviour references — inlining `MonoScript` stubs, hardcoding `fileID: 11500000`, or rewriting `m_Script` lines in the YAML. That hand-rolls an identity Unity owns, and it reintroduces the exact missing-script defect the moment a guid moves, a class is renamed, or a second type is added to the file. The robust approach is the negative one: keep one class per correctly-named file, let `AddComponent<T>` and the importer write the reference, and write no reference-repair pass at all.

Use `AddComponent<T>()` followed by `EditorSceneManager.SaveScene(...)` or
`PrefabUtility.SaveAsPrefabAsset(...)` and let Unity serialize the reference.
That produces resolvable references when each serialized type is in its own
correctly named file.

## Symptom and confirmation

The symptom is "The referenced script is missing on `<GameObject>`" in the Console, or "The associated script can not be loaded" on the component in the Inspector, when a scene / prefab / SubScene is opened or re-imported.

Confirm it at the YAML level rather than guessing:

1. In the `.unity` / `.prefab` text, find the offending component's `m_Script: {fileID: <…>, guid: <…>, type: 3}` line.
2. A valid authoring reference is `{fileID: 11500000, guid: <the target .cs.meta guid>, type: 3}`.
3. Read the target `.cs.meta` and check its `guid` against the reference's guid, and check that the `.cs` file is named after the referenced class. A guid that points at a multi-class file where the referenced type is *not* the file-named one, or a builder-written `fileID` that is not `11500000`, is the cause.

The fix is structural, not a YAML edit: move the offending type into its own file named after it, let Unity reimport so the new `.cs.meta` guid and `fileID: 11500000` are assigned, and re-add or re-resolve the component (re-running a programmatic builder writes the corrected reference automatically).

## Source citations

| Fact | How to verify it in this project |
|------|----------------------------------|
| Canonical script identity | Inspect an imported `.unity` or `.prefab` `m_Script` reference and its target `.cs.meta` file. |
| Multi-`MonoBehaviour` failure | Create a disposable prefab that references a second serialized class in the same file, then re-import it. |
| Per-class split | Move that class to a correctly named file and confirm the prefab resolves after re-import. |
| Programmatic authoring | Save an asset built with `AddComponent<T>()` and inspect the resulting `m_Script` reference. |

## Unity 6000.7 alpha caveat: scenes may forgive, prefabs may not

On `6000.7.0a1` the failure mode diverges between container types for a MonoBehaviour
living in a file not named after it:

- **Scenes** serialize the component with a non-canonical local `m_Script: {fileID: <hash>}`
  plus `m_EditorClassIdentifier: <Assembly>::<Namespace>.<Class>` — and this **resolves**:
  the component loads and its Baker runs during subscene import.
- **Prefabs** write `m_Script: {fileID: 0}` (the `m_EditorClassIdentifier` is present but
  ignored) — the component is a missing script and its Baker silently never runs. A ghost
  prefab baked this way simply lacks the components, with no warning anywhere.

So a scene-based smoke test can pass while every prefab embedding the same authoring type
is broken. The rule stands unchanged: one MonoBehaviour per file, file named after the
class — the alpha only makes the violation harder to notice.
