---
name: vt-fill-contract-is-three-fields
description: "Any driver of the VT fill must publish pending + resident + dirty mask together; a partial publish inherits the last tick's leftovers"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5262e936-24af-4221-9c7b-4689d3fdfe79
  modified: 2026-07-21T11:42:12.768Z
---

The VT fill program is driven by THREE published fields on `VTHandle` — `PendingAssignments`/`PendingCount`, `ResidentAssignments`, and `DirtyLayerMask` — and consumers choose between the first two by reading the third (`dirty ? resident : pending`). Any driver that publishes only the pending batch inherits whatever mask and resident span the last `UpdateCpuPhase` left standing.

`BuildAllResidentAssignments` returns a manager-owned view "valid until the next call", so after an `InvalidateAll` that span still describes evicted tiles whose slots have been reassigned.

**Why:** this silently corrupted every archive bake (2026-07-21). `RecordNormalFill` and `RecordBasemapFill` choose either/or, so baked tiles got no normals and no surface cache while the previous tick's tiles were drawn into their slots; `RecordHeightPhase` composites pending AND resident, so geometry looked right while the surface was stitched from the wrong places — patchy grey, different every run because it depended on when Freeze was pressed.

**How to apply:** when writing anything that drives the fill outside the normal CPU tick (a bake, a capture, a test harness), publish a complete state and clear the pool and the published state together. Gated by `VTFreezeHermeticTests` (bare) and `VTFreezeHermeticLayerStackTests` (full stack) — both freeze the same terrain quiet vs one tick past an invalidation and require bit-identical archives. Related: [[vt-composite-determinism]], [[vt-archive-io-interface-shape]].
