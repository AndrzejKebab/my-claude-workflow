---
name: proceed-after-approach-chosen
description: "Once the user picks an approach, add the deps/tooling it needs and proceed — don't bounce back to ask"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cfb7b60e-359a-461b-8626-b1808634abb0
---

When the user has chosen an implementation approach (e.g. via AskUserQuestion),
do not come back with a follow-up question just because the approach has an
implied cost — a missing crate, a C++ build dep, a feature flag to add. Add what
the approach needs and proceed.

**Why:** On the texture-array baker task the user answered two architecture
questions, then I asked a third ("basis-universal isn't in the tree — still want
compression?"). They rejected it with "lets bring all the necessary stuff here"
— i.e. the deps a chosen approach requires are not a new decision, they're
execution.

**How to apply:** After an approach is chosen, investigate feasibility yourself,
pull in the required dependencies/tooling, and only return to the user if you
hit something that genuinely changes *what* you build (not *what it costs* to
build it). Surface costs/constraints in the final summary instead.
