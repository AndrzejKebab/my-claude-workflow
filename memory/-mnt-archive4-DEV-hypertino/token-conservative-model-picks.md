---
name: token-conservative-model-picks
description: "Be conservative with tokens; dispatch subagents on Sonnet 5 or Opus 4.8, not the session model"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e5a23195-b623-44b8-ab47-8a5be77843ae
---

User directive (2026-07-02): be conservative about token use; pick the best-fit model per dispatched task — Sonnet 5 or Opus 4.8. Do not let subagents inherit the (premium) session model.

**Why:** session model (Fable) is premium; orchestration fans out many agents, cost multiplies.

**How to apply:** on every Agent call set `model` explicitly — `opus` for design/review/hard debugging, `sonnet` for mechanical work (commits, audits, formatting, doc writes, straightforward implementation). Also brief agents to read only what the task needs, no broad exploration.
