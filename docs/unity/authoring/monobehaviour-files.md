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

`mara` evidence — `Packages/is.zori.entities.charactercontroller2d/Samples~/SideScrollerCharacter/SideScrollerAuthoring.cs` packs five serialized types in one file: the `SideScrollerSampleConfig` struct (`IComponentData`, not subject) plus four `MonoBehaviour`s — `SideScrollerSampleConfigAuthoring`, `SideScrollerCharacterAuthoring`, `SideScrollerPushableAuthoring`, `SideScrollerMovingPlatformAuthoring`. Only the type matching the file name (none of them — the file is `SideScrollerAuthoring`, which names no class in it) can hold `fileID: 11500000`, so every scene referencing those four MonoBehaviours showed missing scripts. The fix, visible in the deployed copy under `Assets/Samples/Zori Entities Character Controller 2D/0.1.0/Side-Scroller Character/`, splits each `MonoBehaviour` into its own correctly-named file (`SideScrollerCharacterAuthoring.cs`, `SideScrollerPushableAuthoring.cs`, `SideScrollerMovingPlatformAuthoring.cs`, `SideScrollerCharacterTuning.cs`), each then carrying its own `.cs.meta` guid and a valid `fileID: 11500000`.

## Corollary for programmatic scene / prefab builders

An editor builder that authors assets via `gameObject.AddComponent<T>()` and saves with `EditorSceneManager.SaveScene` (or `PrefabUtility.SaveAsPrefabAsset`) gets a correct `{fileID, guid}` written for free — but only when `T` lives in its own correctly-named file. Unity resolves `T` to its canonical script asset and serializes the `fileID: 11500000` reference itself; the builder never spells the reference out.

Do not post-process the saved asset to repair MonoBehaviour references — inlining `MonoScript` stubs, hardcoding `fileID: 11500000`, or rewriting `m_Script` lines in the YAML. That hand-rolls an identity Unity owns, and it reintroduces the exact missing-script defect the moment a guid moves, a class is renamed, or a second type is added to the file. The robust approach is the negative one: keep one class per correctly-named file, let `AddComponent<T>` and the importer write the reference, and write no reference-repair pass at all.

`mara` evidence — `Assets/Samples/Zori Entities Character Controller 2D/0.1.0/Side-Scroller Character/Editor/SideScrollerSceneBuilder.cs` is the correct pattern: it calls `AddComponent<SideScrollerCharacterAuthoring>()`, `AddComponent<SideScrollerPushableAuthoring>()`, `AddComponent<SideScrollerMovingPlatformAuthoring>()` (and the substrate physics authoring), then `EditorSceneManager.SaveScene(...)`, with no YAML post-processing. It produces resolvable references precisely because each of those types is now a one-class file.

## Symptom and confirmation

The symptom is "The referenced script is missing on `<GameObject>`" in the Console, or "The associated script can not be loaded" on the component in the Inspector, when a scene / prefab / SubScene is opened or re-imported.

Confirm it at the YAML level rather than guessing:

1. In the `.unity` / `.prefab` text, find the offending component's `m_Script: {fileID: <…>, guid: <…>, type: 3}` line.
2. A valid authoring reference is `{fileID: 11500000, guid: <the target .cs.meta guid>, type: 3}`. In `mara`'s side-scroller scene, `Assets/Samples/…/Side-Scroller Character/Scenes/SideScrollerSample.unity` carries exactly that shape, e.g. `{fileID: 11500000, guid: 564ee9945f053b2d5b71affa1b9b0088, type: 3}`.
3. Read the target `.cs.meta` and check its `guid` against the reference's guid, and check that the `.cs` file is named after the referenced class. A guid that points at a multi-class file where the referenced type is *not* the file-named one, or a builder-written `fileID` that is not `11500000`, is the cause.

The fix is structural, not a YAML edit: move the offending type into its own file named after it, let Unity reimport so the new `.cs.meta` guid and `fileID: 11500000` are assigned, and re-add or re-resolve the component (re-running a programmatic builder writes the corrected reference automatically).

## Source citations

| Fact | Reference |
|------|-----------|
| `fileID: 11500000` is the canonical script slot, one per file | `Assets/Samples/…/Side-Scroller Character/Scenes/SideScrollerSample.unity` `m_Script` lines; per-class `.cs.meta` guids |
| Multi-`MonoBehaviour` file → missing scripts (the defect) | `Packages/is.zori.entities.charactercontroller2d/Samples~/SideScrollerCharacter/SideScrollerAuthoring.cs` (five serialized types) |
| Per-class split as the fix | `Assets/Samples/…/Side-Scroller Character/SideScroller{Character,Pushable,MovingPlatform}Authoring.cs`; Platformer `FrictionModifier2DAuthoring.cs` |
| `AddComponent<T>` + `SaveScene`, no YAML post-processing | `Assets/Samples/…/Side-Scroller Character/Editor/SideScrollerSceneBuilder.cs` |
