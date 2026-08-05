---
name: feedback-proceed-over-scoping-questions
description: "When the user has signaled a direction, proceed with analysis instead of gating on scoping questions"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5c67887c-38f4-43eb-9ff8-621faa0882ac
---

When asked to "explore the design space" or similar, the user rejected a 3-question AskUserQuestion prompt with "well it doesn't matter" and just stated the decision.

**Why:** They move fast and would rather react to a concrete synthesis than answer a battery of upfront scoping questions. A multi-question prompt felt like friction.

**How to apply:** Give the substantive analysis first. If decisions are genuinely needed, prefer making a reasoned default and stating it, or asking one sharp question — not stacking 2–4. They'll correct course if needed. Relates to [[naadf-rust-rewrite-plan]].
