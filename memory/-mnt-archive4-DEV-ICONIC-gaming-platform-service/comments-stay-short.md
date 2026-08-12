---
name: comments-stay-short
description: Write one-line comments; do not add multi-paragraph docblocks explaining reasoning at call sites
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 212ed9de-fca3-4bbd-83e8-9e62f97fa560
  modified: 2026-08-11T16:33:46.523Z
---

Default to a **one-line** comment, or none. Do not write multi-paragraph docblocks justifying a
decision at the call site, and do not add a comment above a `throw` explaining why the code is the
code it is — the code name already says it.

**Why:** repeatedly asked to stop ("stop writing insane walls of comments everywhere, i literally
beg you"). The reasoning belongs in the design doc (`docs/errors.md` and friends), not smeared over
every call site, where it buries the code and goes stale.

**How to apply:** an enum member gets one line. A call site gets nothing unless the behaviour is
genuinely surprising. File-level `@file` docblocks are still wanted where the repo already uses
them — the objection is to walls *inside* functions and above ordinary statements. When tempted to
explain a trade-off, put it in the doc and link nothing.

Related: [[short-plain-commit-messages]], [[docs-state-the-rule-not-the-behaviour]].
