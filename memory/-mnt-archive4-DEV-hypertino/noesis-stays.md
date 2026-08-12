---
name: noesis-stays
description: User ruled 2026-08-10 that the editor keeps NoesisGUI; the ImGui migration question is closed
metadata: 
  node_type: memory
  type: project
  originSessionId: 72c79887-6cfd-4c6b-ac09-d2d5adb5b8e7
  modified: 2026-08-10T13:15:24.169Z
---

The editor UI toolkit question is decided: **NoesisGUI stays**. The user ruled this on 2026-08-10
("nope, we decided that Noesis stays") when asked whether E2 live QA should wait for the toolkit call.

**Why:** a 2026-08-10 design conversation had costed a move to floating Dear ImGui inspector windows —
~5,100 lines of Noesis-coupled editor code, a 50 MB vendored commercial SDK, a shader bake pipeline,
six `docs/p1-simplifications.md` ceilings that exist only for Noesis, and the quarantined `vulkanInterop`
bridge. Commit `14caeb4` ("checkpoint before editor-UI direction change") and `66490e1` (the 2026-07-03
removal of the previous ImGui integration) are the artifacts that make this look reopenable. It is not.

**How to apply:** do not propose or cost an ImGui migration again. Editor UI work — play-mode chrome,
the component-first inspector ([[hypertino-continuation-state]]), the monkey MCP resolver over the
Noesis retained visual tree — proceeds on Noesis. UI acceptance is the user's live QA against the
Noesis shell, per [[gates-two-tier-doctrine]].
