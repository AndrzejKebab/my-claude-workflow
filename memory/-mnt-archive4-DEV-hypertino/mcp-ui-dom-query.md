---
name: mcp-ui-dom-query
description: "hypertino MCP editor control must be a general DOM-style tree query over the whole UI, never per-panel interface blocks"
metadata: 
  node_type: memory
  type: project
  originSessionId: d02d85e1-7b9a-4d4f-9a5e-bf480f24a20d
---

Hypertino editor's MCP "monkey interface" (agent UI control) must be a **general DOM-style query engine** over the entire Noesis visual/logical tree: query any element by selector → handle → focus / click / input(text|key) / read(rect,value,state). The whole UI is one queryable DOM; individual panels (inspector, scene list, toolbar, viewport) are just data in that tree, never hand-implemented interface blocks.

**Why:** replaces X11-window + python XTEST scripting for agentic dev/verify; agents have no vision, so a tree-query dump IS how the agent "sees" the UI. Per-panel adapters are the anti-pattern the user rejected explicitly.

**How to apply:** design/brief around one traversal+selector+action+read engine; never scope "implement focus for the inspector, then click for the scene list." Substrate already live at HEAD: `NoesisView::feedKeyboard/feedPointer/FindName/HitTest/elementRect/focusedTextBox`, `InputState` key/text/pointer, per-frame feed site `shell.cpp:658-662`. Templated cells lack `x:Name` → query by type/hierarchy/index/DataContext, not names. Orchestration: [[hypertino-continuation-state]]. Related anti-reify pref: [[design-discussions-lay-out-space]].
