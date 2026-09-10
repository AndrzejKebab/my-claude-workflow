# Feel Prototype (Graybox Scene)

A throwaway play-mode scene built from primitives that answers **"is this mechanic any good?"** — movement, camera, combat timing, placement flow, pacing. Numbers are tunable *while playing*, restart is one key, and the relevant state is always on screen. The answer to a feel question is mostly a set of tuned values plus a yes/no.

## When this is the right shape

- "Does this dash/jump/recoil/build-placement feel right?"
- "Is a 0.4s wind-up readable or annoying?"
- "Should the camera lead the cursor or the pawn?"
- Anything where the user needs a controller/mouse in hand to judge.

If the question is answerable without motion or input → [LOGIC.md](LOGIC.md). If it's about layout/looks → [UI.md](UI.md).

## Process

### 1. State the question and the success test

Top-of-scene comment (on a `PrototypeInfo` component or in `NOTES.md`): the question, and how the user will judge it ("dash chains feel responsive at 60fps with 3 enemies"). Feel is subjective — pin down *what to pay attention to* so the session isn't just noodling.

### 2. Build the graybox

- **One scene**, `Assets/_Prototypes/<name>/<Name>.unity`, opened via `MenuItem("Prototypes/<Name>")` which loads it and enters play mode.
- **Primitives only.** Cubes, capsules, `Debug.DrawLine`, unlit flat colors for semantic meaning (red = threat, green = interactable). Zero art, zero real prefabs — borrowed art smuggles in borrowed behavior and drags iteration speed down.
- **Fake everything around the mechanic.** The mechanic under test gets real code; everything else is the dumbest stub that creates the right pressure (enemies = capsules moving toward the player, resources = spheres that vanish on click).
- **Minimal input path.** Read input in the simplest way the project allows; don't build an input abstraction.

### 3. Make every interesting number live-tunable

This is the heart of a feel prototype:

- Put all tunables in **one struct on one component** (or one `ScriptableObject` instance) — `[Range]` sliders, sensible min/max, grouped with `[Header]`s. Never scatter constants through the code.
- Sliders must apply **while playing** — read the values every frame, don't cache at `Awake`.
- Play-mode tweaks are lost on exit, so add a **Copy values** context-menu/button that dumps the current struct as text (JSON or C# initializer) to the console or clipboard. Tuned numbers are half the answer; losing them to play-mode exit is the classic waste.

### 4. Hotkeys: restart and scenario

- **R** — full reset of the mechanic's state without exiting play mode (respawn, clear cooldowns, reseed). Iteration cadence is try → R → try; exiting play mode each attempt kills the session.
- **1/2/3...** — jump to preset scenarios if the mechanic has setup cost (wave of 5 enemies, low-health state, night time).

### 5. On-screen state overlay

An IMGUI `OnGUI` panel in a corner, every frame: the tunable values currently in effect, the mechanic's key runtime state (velocity, cooldowns, state-machine phase, combo count), and the hotkey legend. The user should never need the Inspector to know what's happening. Wrap it in `#if UNITY_EDITOR || DEVELOPMENT_BUILD`.

### 6. ECS projects

Same shape, adjusted: the graybox scene bootstraps a **separate prototype world** (or a dedicated subscene) so the real game's systems don't run. The mechanic's core stays in Burst-compatible static functions (see [LOGIC.md](LOGIC.md) §2) called from one throwaway `ISystem` or even a plain `MonoBehaviour` shim — for a feel test, `MonoBehaviour` movement at prototype scale is fine and iterates faster; port to jobs only if the question *is* about scale.

### 7. Hand it over, then capture

Give the menu path and the hotkey list. Watch for "can you make the enemies faster" — that's the session working. When a verdict lands, record in `NOTES.md`/commit: the yes/no, **the final tuned values** (paste the Copy-values dump), and anything that surprised. Then rebuild the mechanic properly in the real game and delete the folder — graybox code is written under prototype constraints and must not be promoted as-is.

## Anti-patterns

- **Art in the graybox.** Even one nice model recalibrates everyone's judgment and slows iteration. Flat-shaded primitives only.
- **Tuning by recompiling.** If changing a number takes a domain reload, the prototype has failed at its one job.
- **Testing feel in a vacuum.** A dash feels great alone and terrible with three enemies. Stub in the cheapest possible pressure.
- **Building real systems around the mechanic.** No inventory, no save, no netcode — unless the question is literally "does this feel right *under 150ms latency*", in which case fake the latency, not the netcode.
- **Skipping the values dump.** A "yes it feels good" without the numbers means re-tuning from scratch in production.
