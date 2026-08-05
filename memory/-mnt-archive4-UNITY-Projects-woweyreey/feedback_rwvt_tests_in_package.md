---
name: RWVT tests must live in the package
description: All RWVT tests go in Packages/com.api-haus.rwvt/Tests/ — package must be testable independently of any project
type: feedback
---

RWVT tests must live in `Packages/com.api-haus.rwvt/Tests/PlayMode/`, never in project-level `Assets/_Project/TerrainVis/Tests/`.

**Why:** The package must be testable regardless of which Unity project it's in. Project-level code that needs to be referenced must be copied into the package's test assemblies/shaders.

**How to apply:** When writing new RWVT tests, always place them under `Packages/com.api-haus.rwvt/Tests/`. If the test needs project-level utilities (e.g. TerrainVis helpers), copy and customize them for the package test context.
