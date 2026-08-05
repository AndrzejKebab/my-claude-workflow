---
name: shared-tree-sequencing
description: Never run a package-mutating implementer in parallel with editor-launching observation workstreams — all six Unity projects compile the same submodule; directory locks are not partitioning
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4781d14e-196e-4ff9-9fcb-0f1d90b87ea1
---

User: "17.5/17.0 validator hits problems that implementor agent creating, why would you allow them to work in parallel." The orchestrator had partitioned agents by Unity project directory (17.3 vs 17.5/17.0), but all six projects compile the shared `is.zori.miniheightfields` submodule + testbed — an editor-freeze observer read the extent implementer's mid-edit CS0117 as breakage in its own lane; both had to be stood down and checkpointed.

**Why:** Locks must partition shared mutable state, not directories. In this repo every project references the same package tree, so "you own 17.3, you own 17.5" is no isolation at all for compilation-dependent observation.

**How to apply:** Sequence tree-mutating workstreams and compile-dependent observers (editor launches, startup QA, perf captures, suite runs); never parallel. Law recorded in the delegate skill (§Structural-decay guards, shared-mutable-tree sequencing). Related: [[single-editor-test-runs]].
