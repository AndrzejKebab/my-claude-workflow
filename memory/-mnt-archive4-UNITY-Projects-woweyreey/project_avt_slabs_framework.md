---
name: AVT multi-instance VT (Wave 9+ direction)
description: Wave 9 makes RWVTHandle multi-instance-capable. Project stands up two instances called "Detail" and "Vista" — slab is project jargon, NOT a VT package primitive.
type: project
originSessionId: a5793cff-b875-40be-b755-7b0ae0f08b00
---
The AVT direction past Wave 8 is **multi-instance VT**: the package
already supports layers sharing a pagetable inside one instance; Wave 9
makes the engine support N concurrent `RWVTHandle` instances, each with
its own pagetable / parent VT / layer set / TPU configuration.

**"Slab" is project jargon, not a VT primitive.** The VT package gains
zero types named `Slab` / `RWVTSlab` / `IRWVTSlab` / `SlabConfig` /
`SlabRole` / etc. The terrain controller calls its two `RWVTHandle`
instances "Detail" and "Vista" because that's their role in the
project's terrain pipeline — those names live in
`HeightfieldTerrainController`, not in the VT package.

If `*Slab*` appears anywhere in
`Packages/is.zori.heightfields/VirtualTextures/`, that's wrong —
it's a `RWVTHandle` instance.

**Wave 9 actual VT-package work:**
- `_RWVT_BasemapAllocId` global → per-instance uniform.
- `RWVTAllocationPolicy.RingCounts` / `ActiveSearchRadius` static →
  per-instance data.
- `RWVTAllocationPolicy.AssignBucketsByRing` runs per instance.
- `RWVTManager` audit for single-instance assumptions.
- Each instance binds its own `_DetailVT_*` / `_VistaVT_*` shader
  binding group.

**Project-layer work:**
- `HeightfieldTerrainController` constructs two `RWVTHandle` instances
  (Detail at `DetailedTPU=1024`, Vista at `VistaTPU=3`) with
  hardcoded layer layouts: Detail owns albedo/normal/SM/height;
  Vista owns height/splat-mask/basemap.
- `Stamp.Contributions: List<(VTInstanceName, LayerName)>` —
  explicit per-(instance, layer) opt-in. No numeric "authored TPU"
  threshold.
- `StampCompositor` per-page queries take a `RWVTHandle` parameter,
  filter stamps by spatial overlap + contribution.
- Surfshader samples both instances, composes by per-layer
  contribution (no `coverage` lerp, no `DetailedDistance` constant,
  no presence branch).

**Slabs are uniform — no per-instance branches:**
- Same engine, allocation policy, gather, fulfiller, BC, LRU,
  indirection across all instances.
- Per-instance variation is **data only**: `RWVTDescriptor` fields
  (virtual extent → bucket ladder, layer set, world bounds).
- No cutoff in any instance — every visible sector gets *some*
  bucket from `[bucket-0 .. bucket-max]`. Detail's far sectors get
  bucket-0 (1K), not no-allocation. The "ring shape" is bucket-size
  variation, not presence/absence.
- "Low TPU at distance" emerges from each instance's max-bucket cap
  + `ddx/ddy` mip sampling. Not a knob, not a branch.

**Stop conditions:**
- `*Slab*` types in the VT package.
- `DetailVT` / `VistaVT` classes (both are `RWVTHandle` instances).
- Per-sector mip clamps inside one VT (staging/obscurrence dead end).
- `IRWVTSpatialCoverage` / `CameraRing` / `WorldGrid` / sliding
  window — spatial distribution is the Chen Ka world-anchored sector
  grid, identical across instances.
- Cutoff/max-distance knob on any instance.
- `DetailedDistance` / `coverage` checks in the surfshader.
- Numeric "authored TPU" on stamps; explicit per-(instance, layer)
  opt-in only.
- Layer shared between instances; layers are owned by exactly one.
- Generalising `HeightfieldTerrainController` speculatively
  (artist-defined layouts is a future wave).

**Wave order swapped 2026-04-28:** PageID feedback ships **first**
(Wave 9, single VT instance) — replaces `CanonicalGatherJob` with
demand-driven `(PageID, Mip)` derived from per-pixel `ddx/ddy` of
virtual UVs, written to a 1/8 × 1/8 RWBuffer in the G-buffer pass,
async-read on CPU, fed to `TileAllocAndAssignJob`. Multi-instance
ships **second** (Wave 10) and generalises PageID feedback to
per-instance buffers as a side effect of the multi-instance
plumbing — the mechanism is the same, just N copies of it.

Why swapped: PageID feedback is independent of N (single-instance
verification surface is simpler), and multi-instance benefits from
landing on a demand-driven gather (otherwise doubling instances
doubles the CPU enumeration cost).

Reference: `docs/avt-phase3-plus-plan.md` §Wave 9 (PageID) +
Wave 10 (multi-instance) + architecture invariants 10/11.
Established 2026-04-28 with user.
