---
name: probe-code-belongs-in-package-test-tree
description: docs/orchestrate/**/scratch/ sits outside every Unity compilation root — probe oracles a later gate must inherit go in the package Tests tree instead
metadata: 
  node_type: memory
  type: project
  originSessionId: a9e768c7-eb1d-490d-aa8c-e4b31bc70e01
  modified: 2026-07-22T01:28:01.406Z
---

`docs/orchestrate/<topic>/scratch/` is outside **every** Unity project's compilation roots, so
nothing placed there can be compiled, referenced, or inherited by a later gate. A probe oracle
written into `scratch/` is dead on arrival for the implementation wave that was supposed to inherit
it.

**Why:** the "commit every ad-hoc script with the task's artifacts" rule is about *provenance*, and
in a Unity repo provenance and compilability are different placements.

**How to apply:** shared predicate/oracle/fixture code goes in `is.zori.miniheightfields/Tests/Common/`
(referenced by EditMode, PlayMode and PlayMode.URP, so any wave's gate can consume it); probe compute
shaders go in `Tests/Common/Resources/`; the gate itself goes in the assembly whose graph it needs
(demo-scene freeze work is `Tests/PlayMode.URP`). Only the *runner scripts* — batchmode iteration
loops, filtered invocations — stay under `scratch/`. Established by wave-0 P1 of chajdas-freeze
(2026-07-22). Related: [[durable-e2e-not-editor-qa]], [[single-editor-test-runs]].
