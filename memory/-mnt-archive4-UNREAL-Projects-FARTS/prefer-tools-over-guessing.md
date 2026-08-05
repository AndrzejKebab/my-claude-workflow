---
name: prefer-tools-over-guessing
description: "When editor/tool access exists, inspect real state instead of speculating"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9a0c2619-b51c-49ff-91d3-05ad12b1c06b
---

When I have access to the live system (e.g. the Unreal MCP bridge, Bash, repo), the user wants me to **inspect actual state, not guess**. Pushed back hard when I listed speculative causes for "why can't I delete the landscape" while an MCP connection to the editor was available.

**Why:** Guessing wastes the user's time when ground truth is one tool call away; they find speculative lists annoying.

**How to apply:** Before explaining *why* something behaves a certain way, query it — list actors, read the log, check the file. Only fall back to reasoning when the tools genuinely can't answer (e.g. the needed toolset isn't loaded). See [[farts-ue58-buildid-mismatch]].
