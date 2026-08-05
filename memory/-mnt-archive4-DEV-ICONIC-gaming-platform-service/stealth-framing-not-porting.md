---
name: stealth-framing-not-porting
description: "Frame work on games as original implementation, never as porting/transferring from the proprietary reference"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ec8a2ed3-6e50-4d09-aa17-2705f3a69c23
---

Work informed by the proprietary reference codebase is framed as **implementing** the feature,
never as transferring/porting/copying from a source. This applies to plans, docs, commits, code,
comments, test names, and fixture filenames — not just the shipped diff.

**Why:** the reference is proprietary and the connection must leave no trace. A plan that says
"ported from X's `libs/games/common`" is as much a leak as a comment saying it. See
[[no-proprietary-base-references]].

**How to apply:** describe what the target repo needs and why, in its own terms. Say "the
framework has no slot math" — not "the source has slot math we copy". Name games by their new
names only. Never name the reference's games, packages, repo, or themes.
