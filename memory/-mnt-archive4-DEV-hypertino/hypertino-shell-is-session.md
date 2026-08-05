---
name: hypertino-shell-is-session
description: "hypertino editor has one UI, one selection; the shell IS the session; MCP is a view onto the single editor"
metadata: 
  node_type: memory
  type: project
  originSessionId: d02d85e1-7b9a-4d4f-9a5e-bf480f24a20d
---

Hypertino editor architecture (owner-stated, load-bearing):
- **One editor, one UI, one selection state.** There cannot be more than one selection origin.
- **The shell IS the session** — not two layers. Any code that looks like "shell selection vs session selection" as two separate states is a bug (accidental split) or a missing rebuild/notify, never an intended architecture.
- **MCP is a view/controller onto that one editor**, not separate state. An MCP tool that changes selection must reach the same single selection the UI reads.
- **Multi-object selection is a FUTURE feature** — single-entity selection today.

**Why:** corrects a wrong mental model I fell into — dressing a plain "the inspector doesn't refresh when MCP changes selection" bug up as a spec "one-origin violation" with imaginary multiple origins. There are no multiple origins to reconcile.

**How to apply:** when MCP-driving diverges from UI behavior, the defect is that the MCP path missed the one real state — don't theorize about unifying origins. The faithful monkey way to select = `ui.click` the hierarchy row (drives the real single selection), per [[mcp-ui-dom-query]]. Orchestration context: [[hypertino-continuation-state]].
