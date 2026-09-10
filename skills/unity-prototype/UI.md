# UI Prototype (Runtime Variants)

Generate **several radically different UI variants** for one screen/panel/HUD, cycled at runtime from a small floating switcher. The user flips between them in play mode with real (or realistic fake) data underneath, picks one — or steals pieces from each — then the rest gets deleted.

If the question is logic/state → [LOGIC.md](LOGIC.md). If it's about how a mechanic feels → [FEEL.md](FEEL.md).

## When this is the right shape

- "What should the colonist inspector / build menu / HUD look like?"
- "I want to see a few options for this screen before committing."
- "Try a different layout for the pause menu."

## Two sub-shapes — strongly prefer sub-shape A

UI is much easier to judge **inside the running game** — real camera, real density, real data churn. A variant floating in an empty test scene is a vacuum: everything looks fine in isolation.

### Sub-shape A — mounted in the real game (preferred)

The variants replace/overlay the screen being prototyped **in the actual game scene**, fed by the game's live data (read-only). Existing UI stack stays; only the prototyped panel swaps per variant. Use this whenever the game runs well enough to host it — including for a screen that doesn't exist yet but would live inside an existing flow.

### Sub-shape B — a dedicated harness scene (last resort)

Only when the game can't sensibly host the prototype (the screen is a whole new top-level flow, or the game is mid-refactor and won't run). Build `Assets/_Prototypes/<name>/<Name>.unity` with a **fake data source that mimics real density and churn** — 30 colonists with changing needs, not 3 static ones. Empty-state UI hides every real design problem.

The switcher is identical in both.

## Process

### 1. State the question and pick N

Default **3 variants**; cap at 5 — beyond that they stop being radically different and start being noise. One-line plan in a top-of-file comment: *"Three variants of the colonist inspector, cycled with [ ] in play mode, mounted over the live game."*

### 2. Generate radically different variants

Use whatever the project's UI stack is — **UI Toolkit** (one `VisualTreeAsset` + controller per variant) or **uGUI** (one prefab per variant). Each variant:

- Serves the screen's actual purpose with the actual data available.
- Is **structurally different** — different layout, information hierarchy, primary affordance. Not a recolor. Three slightly-tweaked panel stacks is wallpaper, not a prototype. If two drafts converge, redo one with an explicit constraint ("no vertical list; try radial / try bottom-docked").
- Uses placeholder styling consistent with the game's existing theme *only if one exists* — otherwise flat neutral styling, so the comparison is about structure.
- Exports a clear name: `VariantA_Tabbed`, `VariantB_Sidebar`, `VariantC_Radial`.

Game-UI-specific pressure to design against: does it survive **gameplay underneath** (occlusion, camera motion), **input mode** (mouse vs gamepad focus), and **data churn** (values updating every frame)?

### 3. Wire the switcher

One `PrototypeUISwitcher` component owns the variants:

- Instantiates/mounts exactly one variant at a time, all fed from the same read-only data adapter.
- **`[` / `]`** (and gamepad shoulder buttons if the game is pad-driven) cycle variants, wrapping. Don't intercept keys while a text field is focused.
- Remembers the last variant across play sessions via `SessionState`/`EditorPrefs` so reload doesn't reset the comparison.
- A small **floating pill** bottom-center: `◀  B — Sidebar  ▶`, clickable arrows, styled deliberately unlike the game (high-contrast, drop shadow) so it's obviously not part of the design under evaluation.
- Entire switcher wrapped in `#if UNITY_EDITOR || DEVELOPMENT_BUILD` so a stray merge can't ship it.

### 4. Read-only by construction

Variants render state; they never mutate it. Buttons that would mutate call a stub that logs. The question is "what should this look like", not "does the command pipeline work". (Exception: navigation-feel questions like "is this radial menu usable on pad" may wire selection — still to stubs.)

### 5. Hand it over

Give the menu path / play instructions and the cycle keys. The valuable feedback is usually **"header from B, list from C"** — that composite *is* the design.

### 6. Capture and clean up

Record the winner and why (commit/ADR/`NOTES.md`), plus any stolen pieces. Then rebuild the winning design properly in the real UI assembly — variant code was written under prototype constraints and is not production UI — and delete `Assets/_Prototypes/<name>/` including the switcher. Variant prefabs left in a repo rot fast and confuse the next reader.

## Anti-patterns

- **Variants differing only in color or copy.** Real variants disagree about structure.
- **A shared layout between variants.** A shared data adapter is required; a shared layout defeats the point.
- **Testing against empty or static data.** Colony-sim UI lives or dies on density and churn — fake both.
- **Judging in the Game view at one resolution.** Cycle through the target aspect ratios / reference resolutions before declaring a winner.
- **Promoting a variant prefab straight to production.** Rewrite it under real standards when folding it in.
