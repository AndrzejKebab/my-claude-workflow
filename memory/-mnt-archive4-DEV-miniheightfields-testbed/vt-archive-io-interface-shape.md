---
name: vt-archive-io-interface-shape
description: "The VT archive read interface must stay batchable, async-shaped and granular even while the PoC implementation is blocking"
metadata: 
  node_type: memory
  type: project
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T16:42:03.341Z
---

Ruling, 2026-07-20. Two halves, opposite directions:

**Packing/freezing may block.** It is a slow deliberate editor action (the Ableton freeze).
Blocking population and encoding is fine. Making it background like lightmap baking is
explicitly deferred, not required.

**Reading must be shaped for async from the start**, even though the PoC implementation
completes inline. The interface is to be *pipelineable, async, discernible, granular, and
above all parallelisable/batchable* — a sync implementation behind it is fine; a sync-shaped
*interface* is not, because the native plugin and the in-flight residency state both need to
slot in without a rewrite.

**Concretely that means:** submit N requests, get one handle, poll completion, resolve
per-request status — the `ReadCommandArray` shape (N `ReadCommand`s, one submit, one
`ReadHandle`, per-command `GetBytesRead(i)`). NOT one blocking call per tile per layer.
The same shape is what a Vulkan plugin would expose, so it survives the backend swap.

**Known debt as of this ruling:** `VTArchiveReader.ReadTile(key, layer, byte[], out failure)`
is scalar, blocking and per-layer — it violates this and needs reshaping to batch submit +
poll. Recorded rather than silently carried. See
`docs/todo/terrain-io-packing-streaming-findings.md`.

Related: [[vt-streaming-minimal-then-native-plugin]] — the plugin is Vulkan-first by user
preference, other backends later.
