---
name: unity-prototype
description: Build a throwaway Unity prototype to answer one design question before committing to it. Routes between three branches — an editor-driven simulation harness for state/data-model questions, a graybox play-mode scene for mechanic/game-feel questions, or several radically different UI variants toggleable at runtime. Use when the user wants to prototype a gameplay system, sanity-check a data model or state machine, graybox a mechanic, mock up game UI, or says "prototype this", "graybox it", "let me play with it", "does this feel right", "try a few layouts".
---

# Unity Prototype

A prototype is **throwaway code that answers a question**. In a Unity project there are three kinds of question, and each demands a different artifact.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this logic / simulation / data model hold up?"** → [LOGIC.md](LOGIC.md). A pure C# core driven from an EditorWindow harness — no play mode, no scene, instant iteration.
- **"Does this mechanic feel good?"** → [FEEL.md](FEEL.md). A graybox scene: primitives, live-tunable numbers, restart hotkey, on-screen state overlay.
- **"What should this UI look like?"** → [UI.md](UI.md). Several radically different UI variants in one scene, cycled at runtime from a floating switcher.

Getting the branch wrong wastes the whole prototype. Rules of thumb when the user isn't reachable: a system/component/reducer under discussion → logic; anything involving input, movement, timing, camera, or "fun" → feel; a screen, HUD, panel, or menu → look. State the assumption in a comment at the top of the prototype.

## Rules that apply to all branches

1. **Throwaway from day one, clearly quarantined.** Everything lives under `Assets/_Prototypes/<name>/` with its own asmdef (`Proto.<Name>`). The asmdef references the minimum it needs; nothing in the real game may reference a `Proto.*` assembly — the dependency arrow only points inward. This keeps compiles fast and makes deletion a one-folder operation.
2. **One action to run.** Add a `MenuItem("Prototypes/<Name>")` that opens the harness window or loads the graybox scene and enters play mode. The user must never hunt for a scene file.
3. **Never ships.** Prototype scenes stay out of Build Settings. Any runtime code that could leak is wrapped in `#if UNITY_EDITOR || DEVELOPMENT_BUILD`. No `Resources/` folders inside `_Prototypes` (Unity ships those unconditionally).
4. **No persistence by default.** State lives in memory. No saving ScriptableObjects, no PlayerPrefs, no files — persistence is a thing a prototype *checks*, not something it depends on. If the question is explicitly about save data, write to a file named `PROTOTYPE_wipe_me.*`.
5. **Skip the polish.** No tests, no error handling beyond runnability, no object pooling, no addressables, no art. Primitives, `Debug` colors, default materials.
6. **Surface the state.** Every frame (feel/UI) or after every action (logic), render the full relevant state — an IMGUI/UI Toolkit debug overlay or the harness window. The user must see what changed without opening the Inspector.
7. **Respect the host project's paradigm.** If the game is ECS/DOTS, keep the prototype's core logic in Burst-compatible static functions over plain structs so the validated logic can later be lifted into an `ISystem` unchanged. If it's MonoBehaviour-land, plain C# classes are fine. Never make the *harness* code Burst/ECS — only the core.
8. **Delete or absorb when done.** Fold the validated logic/winning variant into the real game (rewritten under production standards), then delete `Assets/_Prototypes/<name>/` in the same commit.

## When done

The *answer* is the only thing worth keeping. Capture it durably — commit message, ADR, design doc, or a `NOTES.md` next to the prototype — together with the question it answered and the final tuned values (the numbers found in a feel prototype are half the answer). If the user is around, that capture is a quick conversation; if not, leave the `NOTES.md` placeholder so the verdict gets filled in before the folder is deleted.
