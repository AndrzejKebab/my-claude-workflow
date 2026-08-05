---
name: stability-harness-is-load-bearing
description: "The CA + CA↔particle stability/conservation harness is the validity basis of the sim; never drop or reduce it — rebuild black-box, feature-gated"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d9a77483-d6d9-4212-bea0-9620f01f7ebe
---

A "gut tests to black-box" pass (commit `2e4b591` on `api-haus/particle-fix`) deleted ~5390 lines of
foundational Rust tests — `scheduler_harness.rs` (seam/stability oracles + scorecards), `world_test.rs`
(foundational CA behavior), `velocity_test.rs`, `weather_test.rs` — replacing them with ~1288 lines and
dropping most coverage. The user called this a serious regression.

**Why:** that harness — mass conservation under varied CA↔particle seam conditions, scheduler
seam-deviation oracles, foundational CA behavior — is the **validity basis for particle-medium
stability** and the lighthouse's scientific instrument ([[project-lighthouse-falling-sand]]). It must
never be deleted or substituted.

**How to apply — restore = REWRITE, not git-restore:**
- Rebuild the full coverage on the clean `Simulation` **black-box** surface: control signals in →
  real app tick → metrics out. Never drive sim-loop internals ("simulation hijacking"); never
  reimplement app logic in a test. ([[blackbox-test-harness]])
- **Extend the black-box control surface** with the isolation toggles each technique needs — e.g.
  fully disable particles for pure-CA tests (`pure_ca` fixture exists), disable weather, pin gravity,
  disable jitter. Feature-gates are APP CONFIG, not test reimplementations.
- **Extend the metrics harness** with runtime **interrogation/query** accessors so a test can assert
  on a snapshot of current app state and compute ad-hoc quasi-metrics.
- Implement metrics/interrogation as **true feature-gated metrics, compiled out in release** (a cargo
  feature, default-off; established pattern here alongside `move_once`/`dda`/`cohesion_pull`).
- Write **domain-split** stability-harness docs (particles, CA).
