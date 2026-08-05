---
name: subagent-gpu-app-verification-loop
description: "Sub-agents can't verify a windowed GPU app by running it — WGSL errors surface only at runtime, one per run. Use a headless e2e render test."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2fb32083-ec99-43c8-a26a-d2dfbd3951f6
---

Do NOT have sub-agents verify a windowed GPU app (Bevy/wgpu) by running it. Two failure modes observed:

1. **Open-ended "prove it works"** — "confirm TAA accumulates", "read GPU buffer across frames", "verify temporal stability". Agent can't see framebuffer, GPU readback is fiddly → loops: tweak → build → run (window opens) → still can't tell → repeat. (Phase A-2 TAA Batch 2.)
2. **"Run exactly once" cap** — `cargo build`/`cargo test` compile Rust but NOT WGSL. Shaders are runtime assets — naga-oil + driver validate/compile at pipeline creation on first rendered frame. Every shader error (naga-oil naming, import-rewrite, scalar↔vec broadcast, bind-group mismatch) is invisible until live run; each run aborts on the *first* bad shader. Run-once wedges the agent; it (correctly) chose "run until clean" and re-ran ~10× × 1min. (Phase B Batch 3.)

**Why:** sub-agent verification must be deterministically observable from its tool outputs in bounded steps. A live windowed run is neither.

**How to apply:** verify via a **headless e2e integration render test** that runs as a single `cargo test` — boots the app windowless, runs render graph for fixed frames, reads back framebuffer, asserts pixels. Catches every shader-compile / naga-oil / pipeline / bind-group / validation error as one test failure with a real message. Scope sub-agent verification to `cargo build` + `cargo test`. Subjective visual confirmation = user at /delegate review gate. Harness design: `docs/orchestrate/naadf-bevy-port/e2e-render-test.md`. Related: [[naadf-getraydir-monogame-conventions]].
