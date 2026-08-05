---
name: All visually-asserting tests must write PNGs to TestScreenshots/
description: Any PlayMode/integration test that asserts on rendered or readback pixel data must also save PNG outputs under TestScreenshots/ for manual verification, even when the test passes.
type: feedback
originSessionId: e01f77db-5567-4863-8e28-5bab02747b2b
---
All visually-asserting tests must save their captured framebuffers / readback data as PNGs under `TestScreenshots/` (project root). Applies to: surface-shader render readbacks, VT page-table layout visualisations, tile-pool snapshots, mesh-displacement readbacks, any production-pathway pixel comparisons. Save on PASS too — not just on fail/Inconclusive.

**Why:** when a test passes numerically the user often wants to eyeball the output to confirm the assertion actually represents what they care about visually. The session repeatedly hit "tests passed but the user's scene was broken" because the only diagnostic was a single numerical assertion. PNGs in `TestScreenshots/` close that gap — the user can open them after any test run, regardless of pass/fail status, and verify visually.

**How to apply:**
- Any new test that takes an `AsyncGPUReadback` of a render target → emit a PNG via `ProductionTestHarness.SavePng` (or equivalent) before the assertion.
- Tests that compare two states (pre/post, A/B, optimal/actual) → emit one PNG per state plus optionally a diff PNG.
- Naming: descriptive snake_case prefix mirroring the test method or scenario, e.g. `base_teleport_residentA.png`, `prod_three_stamps_repro.png`, `adaptive_uvquad_minimap_ring.png`. Stable across runs so file watchers / git diff workflows make sense.
- Saving location is `TestScreenshots/` at project root (`Application.dataPath/../TestScreenshots`). Already established as the convention by the package's existing harnesses.
- Do NOT delete or git-clean these files in CI — they're diagnostic artefacts (per existing memory `feedback_dont_delete_test_artifacts.md`).
- Tests that don't have a visual surface (pure-CPU jobs, allocator unit tests, asmdef checks) are exempt — the rule applies only when there's actual pixel data being asserted on.
