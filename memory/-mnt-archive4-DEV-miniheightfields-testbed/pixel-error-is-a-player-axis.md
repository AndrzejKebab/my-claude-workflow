---
name: pixel-error-is-a-player-axis
description: "Terrain LOD is driven by a player-facing pixel-error quality scalar — baked artifacts must serve the whole range, and one-setting capture QA proves nothing"
metadata: 
  node_type: memory
  type: project
  originSessionId: a9e768c7-eb1d-490d-aa8c-e4b31bc70e01
  modified: 2026-07-22T09:46:59.163Z
---

Terrain LOD in this project is **not** authored to a fixed pixel error. The pixel error is a
**quality scalability parameter players set in graphics settings** (user, 2026-07-22, correcting an
assumption I had reasoned from).

**The real authored span, from the user (2026-07-22):** `E = 32` on Steam Deck, `E = 16` a good
desktop realtime level (what the demo scene authors, and what every wave-0 capture was taken at),
`E = 1` a plausible Cinematic. That is a **32× range** — the shipped `HeightfieldQuality` presets are
exemplary placeholders and are *finer* than what actually ships, so never anchor reasoning on them.

**And baking happens ONCE for all platforms** — one archive serves the entire range. Extends
[[editor-decides-player-executes]]: not just "no runtime re-bake", but no per-platform and no
per-quality bake either.

**Why it bites:** a baked artifact — the VT archive, a far-shadow layer, anything frozen — must serve
every quality level a player can select, from one file. Any design whose acceptability depends on
"texel ≈ screen pixel" therefore cannot hold, because that ratio is the player's to change. Chajdas's
no-filtering argument is conditioned on a *fixed* pixel-to-sample ratio and is for this reason
structurally not inheritable here (`chajdas-2015-streaming-terrain-shadows` §3.3).

**How to apply:**
- Prefer representations that degrade *continuously* with LOD (a filtered pre-threshold quantity
  whose edge is a level set) over ones that degrade into a *different artifact class* (thresholded
  bits, which turn blocky). See [[vt-composite-determinism]] for the sibling filtering concerns.
- **Pixel error is a required axis for capture QA and for any render gate** — a frame graded at one
  setting proves nothing about the others, which makes single-setting capture evidence the same
  vacuity trap as [[gate-must-exercise-worst-case-regime]].
- The distance at which the archive's finest baked mip can no longer supply the selected pixel error
  sets the required **bake floor** — and it moves with the player's setting, so it is a range, not a
  number.
