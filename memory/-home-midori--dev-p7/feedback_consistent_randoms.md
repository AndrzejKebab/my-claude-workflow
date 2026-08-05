---
name: consistent randoms required
description: All integration tests that depend on RNG must use the file-backed consistent randoms harness, not just cheats
type: feedback
---

All tests that depend on RNG must use a deterministic harness — either `loadCheats()` YAML or `createConsistentRandoms()` file-backed capture.

**Why:** Tests that rely on luck/hope for specific RNG outcomes are flaky. Every test must have deterministic game outcomes.

**How to apply:** `loadCheats()` with YAML pre-recorded sequences is fine — it provides full determinism via `PlaybackSequence`. Use `createConsistentRandoms()` when cheats alone aren't sufficient (e.g., games where cheat YAMLs don't exist or don't cover the needed scenario). Both approaches are acceptable.
