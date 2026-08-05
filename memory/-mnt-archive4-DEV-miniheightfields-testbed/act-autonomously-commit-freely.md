---
name: act-autonomously-commit-freely
description: Do not ask for confirmation to continue in-scope work; commit whenever it makes sense rather than waiting to be told
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T16:26:00.888Z
---

Standing instruction, 2026-07-20: **stop asking for confirmation** before continuing work
that is already within the agreed scope, and **make commits when you see fit** rather than
waiting for an explicit "commit it".

**Why:** the back-and-forth costs more than it protects. Once scope is agreed, checkpointing
after each green gate is what the user wants; asking "shall I continue?" at every natural
seam is friction, not diligence.

**How to apply:**
- Finish the agreed deliverable end to end. Report at the end, not at every seam.
- Commit each coherent green increment (compile clean + relevant gate passing), so the
  working state is always recoverable.
- This relaxes the global CLAUDE.md default of committing only on request — it does NOT
  relax anything else. Still never push, merge, or take outward-facing/irreversible action
  off a question, and still answer readiness questions only after actually running the suite.
- Still surface genuine forks where the answer changes what gets built — but decide routine
  ones and say what was decided.
