# Package samples — `Samples~/` delivers, `Assets/Samples/…` develops

A package sample has two homes, and they play opposite roles. `Samples~/<Name>/` inside the package is the *delivery* artifact — what a consumer imports — and Unity ignores it entirely during a normal project import. `Assets/Samples/<DisplayName>/<Version>/<SampleName>/` is the *working* copy — the only place the sample compiles, runs, and can be tested. The correct workflow develops in the Assets copy and publishes back to `Samples~/` when the sample is ready, and the recurring defects this project hit all came from doing it the other way: hand-authoring directly in `Samples~/`, compiling through a fragile temp-copy dance, and shipping `.meta` files whose GUIDs the sample's own scenes no longer matched.

## The two homes

The trailing `~` makes Unity ignore the folder. Anything under `Samples~/` is not compiled and no asset there is imported during a normal project import — the importer never walks a tilde-suffixed directory. You therefore cannot test, run, or even compile-check a sample in place in `Samples~/`; a script there has no assembly and a scene there has no import.

The Package Manager's Samples tab → Import copies one sample out of `Samples~/` into the consuming project's `Assets/Samples/<PackageDisplayName>/<Version>/<SampleName>/`, where it joins the normal asset graph: the scripts compile into the project's assemblies and the scenes/prefabs import. That imported copy is the working copy — edit it and test it there.

The path uses the package's `displayName` and the sample's `displayName` from `package.json`, not the `Samples~/` folder names. `mara` evidence — `Packages/is.zori.entities.charactercontroller2d/package.json` declares `displayName: "Zori Entities Character Controller 2D"` and a sample `{ displayName: "Side-Scroller Character", path: "Samples~/SideScrollerCharacter" }`, and importing it lands the working copy at `Assets/Samples/Zori Entities Character Controller 2D/0.1.0/Side-Scroller Character/` — the source folder `SideScrollerCharacter` does not appear in the imported path.

## The iteration workflow

`Samples~/` is the golden deliverable; the `Assets/` import is where the sample is actually built and proven. Develop in `Assets/`, and promote to `Samples~/` only after the sample passes the promotion gate below.

0. **If there is no `Assets/Samples/…` working copy, create one first.** A sample with no import has no assembly and no imported assets, so it cannot be edited or verified — the first move is always to get a working copy. Through the editor this is the Package Manager Samples tab → Import. When driving Unity headlessly (no UI), "import" by copying `Samples~/<SampleName>/` into `Assets/Samples/<DisplayName>/<Version>/<SampleName>/` with the `.meta` siblings, so the working copy carries the package's own GUIDs.
1. **Maintain the working version in `Assets/Samples/<DisplayName>/<Version>/<SampleName>/`.** Test it, edit it, and iterate there — this is the only copy with assemblies and imported assets, so it is the only copy a change to the package's own API can be verified against.
2. **Promote to `Samples~/<SampleName>/` only after the promotion gate passes**, by copying the working version over (see the publish procedure below).
3. **The `Assets/` working copy remains after publishing.** Publishing copies into `Samples~/`; it does not move or consume the working copy, so you keep testing and editing in `Assets/` across publish cycles.

Never hand-author directly in `Samples~/`. A file written there has no compile and no import, so its first feedback is a consumer's failed import — the slowest possible loop, and the one that shipped this project's missing-script defects. Editing `Samples~/` first and only then copying into a stale `Assets/` import is the same anti-pattern wearing a disguise: the copy Unity actually compiles is the stale one, so a package API change the `Samples~/` edit depended on still breaks the build until the import is synced. Edit the import, prove it, then promote.

## Promotion gate — compile and manual QA

A sample is the package's worked example; promoting an unverified one ships a defect that only surfaces on a consumer's import. Promotion to the golden `Samples~/` deliverable is therefore gated on two checks against the `Assets/` working copy, both required:

1. **Compile-gate green.** The project imports and every assembly the sample belongs to compiles with zero errors — the headless probe is the batchmode import (`-batchmode -quit`), confirmed by a zero count of `error CS` and `## Script Compilation Error` in the log, not by the process exit code alone. A sample whose working copy does not compile cannot be promoted.
2. **Manual QA pass.** The sample is opened and run, and it does what it demonstrates — its scene opens with no missing scripts, and its interaction behaves. The compile-gate proves the code builds; only running it proves the authored assets (scenes, prefabs, serialized references) still resolve and the demo works, which no compile catches.

Only after both pass does the working copy get copied over to `Samples~/`. Skipping the manual QA is how a green-compiling sample with a broken scene reference still ships.

## Re-import is not a clean sync

Re-importing a sample — or copying a newer `Samples~/` version into the existing `Assets/` import — overwrites and adds files, but it does not delete files that a prior import left behind and the new version no longer contains. Stale files linger in the `Assets/` import, and a stale copy left in `Samples~/` from an earlier publish ships to consumers as cruft. Two implications follow:

- **For a clean test of a changed sample, delete the `Assets/` import folder first, then re-import.** Re-importing over a dirty folder leaves prior-version files in place and tests a mixture of old and new.
- **When publishing, delete from `Samples~/` any file no longer present in the working copy** before or as part of the copy. An additive copy that only overwrites and adds will leave a renamed or removed file behind in `Samples~/`, and it ships.

`mara` evidence — the working copy `Assets/Samples/Zori Entities Character Controller 2D/0.1.0/Side-Scroller Character/Tests/SideScrollerSampleJumpGate.cs` exists in the `Assets/` import but has no counterpart under `Packages/is.zori.entities.charactercontroller2d/Samples~/SideScrollerCharacter/`; the two trees are not auto-synced and a copy in either direction reconciles only the files it is told to touch.

## Publishing preserves `.meta` GUIDs

A published `Samples~/` copy must carry the same `.cs.meta` (and asset `.meta`) GUIDs as the working copy it came from. The sample's scenes, SubScenes, and prefabs reference their scripts by `{fileID: 11500000, guid: <the .cs.meta guid>}` — see [`monobehaviour-files.md`](monobehaviour-files.md) for why `fileID: 11500000` is the canonical script slot. If the published `.meta` GUIDs differ from the GUIDs those scenes were authored against, a consumer who imports the sample gets the exact recurring defect this project hit: every referencing component renders as a missing script, because the `m_Script` GUID in the scene resolves to nothing in the imported tree.

So publishing copies each file **including its `.meta` sibling**, preserving the GUID, and a sample's scene and the scripts it references carry over together — the scene's `{fileID, guid}` pairs only resolve if the script `.meta` GUIDs they name are the ones that shipped. This is the publishing-side companion to the one-`MonoBehaviour`-per-correctly-named-file rule in [`monobehaviour-files.md`](monobehaviour-files.md): that rule decides whether a single project's scene can resolve its scripts; this one decides whether a consumer's import can, and both turn on the `.meta` GUID being stable and matching the serialized reference.

`mara` evidence — `Packages/is.zori.entities.charactercontroller2d/Samples~/SideScrollerCharacter/SideScrollerAuthoring.cs.meta` and the working copy `Assets/Samples/Zori Entities Character Controller 2D/0.1.0/Side-Scroller Character/SideScrollerAuthoring.cs.meta` carry the identical GUID `a5211188af6643e48ebb75e71e876649`, so the side-scroller scene's `m_Script` references resolve identically whether opened in this project or imported by a consumer.

## Publish procedure

To publish the working copy at `Assets/Samples/<DisplayName>/<Version>/<SampleName>/` back to `Samples~/<SampleName>/`:

1. Copy every file from the working copy into `Samples~/<SampleName>/`, **including the `.meta` siblings**, so GUIDs are preserved.
2. Delete from `Samples~/<SampleName>/` any file (and its `.meta`) that no longer exists in the working copy, so a renamed or removed file does not ship as stale cruft.
3. Leave the `Assets/` working copy in place — it is the development home and survives the publish.

The result is a `Samples~/` tree that is file-for-file the working copy with matching GUIDs, which is the precondition for a consumer's import to resolve every scene script reference.

## Source citations

| Fact | Reference |
|------|-----------|
| `Samples~/` is tilde-ignored; the import lands under `Assets/Samples/<DisplayName>/<Version>/<SampleName>/` keyed by `displayName` | `Packages/is.zori.entities.charactercontroller2d/package.json` (`displayName`, `samples[].path`); imported tree `Assets/Samples/Zori Entities Character Controller 2D/0.1.0/Side-Scroller Character/` |
| Re-import / publish is additive, not a sync (stale files linger) | working-copy-only file `Assets/Samples/…/Side-Scroller Character/Tests/SideScrollerSampleJumpGate.cs` with no `Samples~/SideScrollerCharacter/` counterpart |
| Publishing preserves `.cs.meta` GUIDs | matching guid `a5211188af6643e48ebb75e71e876649` in `Samples~/SideScrollerCharacter/SideScrollerAuthoring.cs.meta` and the `Assets/` working-copy `.meta` |
| Why a GUID mismatch is a missing script | [`monobehaviour-files.md`](monobehaviour-files.md) (`fileID: 11500000` script slot) |
