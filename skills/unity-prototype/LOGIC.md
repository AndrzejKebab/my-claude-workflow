# Logic Prototype (Editor Harness)

A pure C# simulation core driven by hand from an **EditorWindow** — buttons dispatch actions, the window pretty-prints the full state after each one. No scene, no play mode, no domain reload between tweaks if the core is pure. Use this when the question is about **business logic, state transitions, or data shape** — the kind of thing that looks fine on a whiteboard but only breaks when pushed through real sequences.

## When this is the right shape

- "Does this job/needs/priority system handle the case where X happens mid-Y?"
- "Can this chunk/save/inventory data model actually represent...?"
- "I want to feel out the API of this system before writing the real `ISystem`."
- Anything where the user wants to **press buttons and watch state change**, and rendering/physics/input are irrelevant.

If the question is about how a mechanic *feels* in motion → [FEEL.md](FEEL.md). If it's about layout/looks → [UI.md](UI.md).

## Process

### 1. State the question

One paragraph in a comment at the top of the core file: what state model, what question. A logic prototype answering the wrong question is pure waste — make it checkable later.

### 2. Isolate the core in a portable, engine-free module

The core answers the question; the EditorWindow is disposable scaffolding. Keep the core:

- **Pure C# over plain data.** No `UnityEngine.Object` references, no `MonoBehaviour`, no `Debug.Log` for control flow, no time reads — the harness passes in ticks/deltas explicitly.
- **In the host project's future shape.** ECS project → static functions over blittable structs (`[BurstCompile]`-compatible, `NativeArray`/fixed buffers where the real system would use them) so the validated logic drops into an `ISystem` verbatim. OO project → a reducer `(State, Action) → State`, an explicit state machine, or a small pure-function set — whichever fits the question, not whichever is easiest to wire up.
- **Deterministic.** Seed any randomness from the harness so a surprising sequence can be replayed.

Nothing flows from harness into core except plain data.

### 3. Build the smallest EditorWindow that exposes the state

One file, `Proto<Name>Window.cs`, in an `Editor/` folder inside the prototype asmdef:

1. `MenuItem("Prototypes/<Name>")` opens it.
2. **Top: full current state**, pretty-printed and diff-friendly — one field per line, `EditorGUILayout.LabelField` with bold section headers, dim/gray for derived values. Foldouts for collections; never truncate silently.
3. **Bottom: action buttons**, one per dispatchable action, plus `Tick ×1 / ×10 / ×100` if the sim is time-stepped, plus **Reset** and **Reseed**.
4. Keep a small ring buffer of the last ~20 actions and render it as a history strip — "how did I get into this state" is usually the interesting question.
5. `Repaint()` after every dispatch.

IMGUI is fine here; don't reach for UI Toolkit unless the window itself needs to survive. The whole state should fit in one window without scrolling if possible.

### 4. If the sim is inherently time-driven

An `EditorApplication.update` loop stepping the core at a fixed dt (with a Play/Pause button in the window) beats entering play mode. Only fall back to a play-mode bootstrap scene if the question genuinely involves Unity's player loop, jobs scheduling, or subscene streaming — and then keep the same pure core, driven by a 20-line `MonoBehaviour`/`ISystem` shim.

### 5. Hand it over

Tell the user the menu path. They drive it; the interesting moments are "wait, that shouldn't be legal" or "huh, I assumed the priority would flip" — bugs in the *idea*, which is the point. Add actions on request; prototypes evolve.

### 6. Capture the answer

When done, the answer is the only keeper. Ask the user what it taught them, or leave `NOTES.md` beside the prototype for the verdict. The validated core can be lifted into the real assembly (rewritten to production standard — proper naming, tests, error handling); the window gets deleted with the folder.

## Anti-patterns

- **Don't enter play mode for a logic question.** Domain reload is the iteration killer; the EditorWindow avoids it entirely.
- **Don't add tests.** A prototype needing tests is no longer a prototype.
- **Don't reference real game assemblies from the core** unless the question is about integrating with them. Copy the two structs you need instead — divergence is fine, it's throwaway.
- **Don't blur core and harness.** If the core calls `EditorGUILayout` or `Debug.Log`, it's no longer liftable.
- **Don't simulate rendering.** If you're spawning GameObjects to visualize, you probably wanted [FEEL.md](FEEL.md).
