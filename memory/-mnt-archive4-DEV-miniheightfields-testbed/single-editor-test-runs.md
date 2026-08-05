---
name: single-editor-test-runs
description: "Suite runs target ONE URP project, never all six, never HDRP (unimplemented)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4781d14e-196e-4ff9-9fcb-0f1d90b87ea1
---

User law (2026-07-14): don't enumerate every editor on every run — pick one URP project (prefer a
live editor, else URP17.3) and run tests there; HDRP is completely unimplemented, never run it;
cross-version issues are fixed later when encountered, not preempted by six-project sweeps.

**Why:** six-editor sweeps per gate burn hours for drift that a later dedicated pass catches
anyway; HDRP runs are meaningless against an asmdef-only stub.

**How to apply:** wave/suite gates = one URP project. All-six is reserved for release-grade checks
the user requests by name. Recorded in the repo at AGENTS.md §"One editor per run, not six".
