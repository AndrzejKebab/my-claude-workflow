---
name: autonomy-parallel-no-main-merge
description: "User grants high autonomy (don't ask per-gate, act on good opportunities, fan out parallel subagents) but merging to main always needs explicit permission"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6ccd7c47-2aa3-46a6-a8e1-deb3ff13db36
---

On multi-step refactors/orchestrations the user wants high autonomy: "everything always, dont even ask me, if you see a good opportunity - go for it" and "use parallel subagents and merge" (merge = combine subagent outputs in isolated worktrees, not merge to main). The one hard gate: **never merge to main without explicit permission.**

**Why:** they trust the orchestrator to drive phases to completion and value speed via parallelism, but treat the main branch as the one irreversible boundary that stays under their control.

**How to apply:** skip the refactor/delegate per-phase confirmation pauses once they've said "go" — proceed architecture→implementation→merge-into-feature-branch autonomously. Fan out file-disjoint work to parallel subagents (isolation: worktree) and merge results into the feature branch yourself, running the gate after merge. Then STOP and report; the final merge to main is theirs. See [[handoff-not-supervised-dispatch]].
