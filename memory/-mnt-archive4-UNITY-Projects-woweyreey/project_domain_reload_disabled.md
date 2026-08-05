---
name: Domain reload disabled
description: Unity project has domain reload disabled on entering play mode (EditorSettings.enterPlayModeOptions) since project creation
type: project
---

Domain reload is already disabled for play mode transitions in this project. Do not suggest enabling/disabling it as an optimization.

**Why:** User configured this from the start. EnterPlayMode/ExitPlayMode skips domain reload.

**How to apply:** When analyzing test performance, domain reload is NOT a bottleneck. Look elsewhere for slowness (VM lifecycle, frame waits, test runner overhead, world recreation).
