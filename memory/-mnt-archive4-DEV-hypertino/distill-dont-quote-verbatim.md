---
name: distill-dont-quote-verbatim
description: "Never record user messages verbatim in steering/context docs — distill to clean directives; interpreting is Fable's job"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 069108a5-de18-445a-9999-df2891ddd754
---

Stated 2026-07-05 during spec-book orchestration: "why are you always recording my messages verbatim, its your job to relay them and remove any unclear context, you're fable its your job."

**Why:** raw quotes carry typos, thinking-out-loud, and ambiguity into documents agents treat as binding; the orchestrator's value is resolving that ambiguity before it propagates.

**How to apply:** steering blocks, context files, and briefs state the distilled directive (decision + scope + basis), never `> "..."` quote blocks or "(user, verbatim: ...)" inserts. If a phrasing is genuinely ambiguous, resolve it with the user first, then record the resolved form. Related: [[no-dualistic-prose]], [[design-discussions-lay-out-space]].
