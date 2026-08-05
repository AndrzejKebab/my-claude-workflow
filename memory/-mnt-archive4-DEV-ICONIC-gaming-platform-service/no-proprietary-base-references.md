---
name: no-proprietary-base-references
description: Never name or cite the prior proprietary reference codebases anywhere in the repo
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 41c63f81-da93-4526-a80b-78a7f65f59f9
---

Never reference the prior proprietary bases (`~/_dev/p7/*`, the "game-api" repo) in any code, doc,
comment, commit message, or file committed to this repo. They are private bases the user worked on before,
used **only as a point of reference between the user and me in conversation**.

**Why:** they're proprietary; leaking their names/paths into this repo is a disclosure problem.

**How to apply:** describe designs generically ("the reference implementation we discussed", "deferred-write
engine") without naming the source. When writing docs/`docs/framework.md`/comments, contain zero mention of
external/prior codebases. See [[game-framework-contract-shape]].
