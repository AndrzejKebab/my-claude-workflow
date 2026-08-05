---
name: unity-teardown-unloads-runner-scene
description: "A UnityTearDown that unloads every scene unloads the PlayMode runner's own scene when a test loaded none — the run hangs forever with no result and no log line"
metadata: 
  node_type: memory
  type: project
  originSessionId: a9e768c7-eb1d-490d-aa8c-e4b31bc70e01
  modified: 2026-07-22T01:27:52.769Z
---

A `[UnityTearDown]` that unloads *every* loaded scene will unload the **PlayMode runner's own
scene** when the test it follows loaded no scene of its own. The run then hangs forever: no result,
no failure, no log line. Cost when it bit: four lost Unity runs (2026-07-22), made much harder to
diagnose because [[unity-run-liveness-ps-aux-lies]] hid the still-live processes.

**Why:** the runner lives in a scene like everything else; "unload all" has no way to know which one
is the harness.

**How to apply:** a teardown unloads only scenes the fixture itself loaded (track them), never a
blanket sweep. `DemoSceneFrozenSurfaceTests` in `is.zori.miniheightfields` carries the unsafe shape
and survives only because every one of its tests happens to load a scene — a latent hang for
whoever adds the first test that doesn't. Related: [[single-editor-test-runs]].
