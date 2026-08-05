---
name: unity-run-liveness-ps-aux-lies
description: ps aux | grep Unity reported zero processes while four batchmode runs were live and contending — check lockfiles/pgrep instead
metadata: 
  node_type: memory
  type: project
  originSessionId: a9e768c7-eb1d-490d-aa8c-e4b31bc70e01
  modified: 2026-07-22T01:27:46.857Z
---

`ps aux | grep -i unity` is not a reliable liveness check for Unity batchmode runs in this testbed
(observed 2026-07-22: it reported **zero** processes while **four** runs were live and contending
for the same project). A run you believe is dead can still hold `Temp/UnityLockfile` and corrupt or
hang the next one.

**Why:** batchmode children get re-parented / renamed in ways the naive grep misses, and the grep
also loses to its own quoting in this shell.

**How to apply:** before assuming a project is free, check `Temp/UnityLockfile` presence and
`pgrep -f` against the project path, or the run's own log tail — never a bare `ps | grep`. This is
the check that gates [[single-editor-test-runs]] and the batchmode-vs-live-editor rule.
