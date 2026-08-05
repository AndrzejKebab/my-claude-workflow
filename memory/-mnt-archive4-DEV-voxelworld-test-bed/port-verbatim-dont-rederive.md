---
name: port-verbatim-dont-rederive
description: "When porting from the bevy_voxel_world reference, copy it verbatim — re-deriving \"the intent\" is what produces the overengineering the user rejects"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 109615a6-bc32-4e53-9db6-8d07cc0b337a
  modified: 2026-07-27T12:01:08.464Z
---

When the task is "port the Voxel Plugin approach", read the reference and copy it — do not
re-derive the mechanism from its documented intent. Every defect in the 2026-07-27 streaming
session came from a place where the port had been "improved": an analytic emptiness proof 420
lines against the reference's ~50, a per-executor replication of the whole stamp store where the
reference shares one immutable structure, invented backpressure that read `max_subdivisions: 0` as
a cap when it means unlimited.

The user's words, twice: *"then maybe dont deviate from voxel plugin, ok?"* and later, in caps,
that the entire approach was overengineered and to rewrite it like Voxel Plugin.

**Why:** the reference is a working system with its own gates and comments; a re-derivation is an
untested reimplementation wearing the same name. Deviations do not announce themselves — they show
up days later as voids on screen.

**How to apply:** before writing a mechanism, open the reference file and read it. If ours has a
concept the reference lacks (a proof engine, a verify mode, a per-thread replica, a counter
taxonomy), that is the bug, not the feature. Cite reference `file:line` in the comment for anything
non-obvious. Reference lives at `/mnt/archive4/DEV/voxel_world/bevy_voxel_world`, crate
`crates/voxel_plugin/src`. See [[calibrate-instruments-before-trusting]].
