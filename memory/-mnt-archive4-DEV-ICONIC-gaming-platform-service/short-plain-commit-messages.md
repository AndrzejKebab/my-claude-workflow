---
name: short-plain-commit-messages
description: "Commit messages and prose must be short and plain — no essays, no literary framing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6b792717-3eb1-46f9-bd68-b2c56419e78d
  modified: 2026-08-10T21:13:45.955Z
---

Write commit messages short and plain. Header, then a few terse bullets if needed. No
multi-paragraph narrative, no rhetorical framing ("That column is the point", "the diff that
turns it green is the burndown"), no bolded declarations, no retelling the investigation.

**Why:** the user reacted strongly ("HUMAN LANGUAGE PLEASE", "CUT IT DOWN") to 15-line essay
commit messages. They read commits to know what changed, not to be persuaded.

**How to apply:** state what changed and, if non-obvious, why in one line. Bullets over prose.
The same applies to chat replies — cut length hard. Docs can be fuller, but the same instinct
holds. See [[docs-state-the-rule-not-the-behaviour]].
