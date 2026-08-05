---
name: RealtimeGIPass clipmap is linear, not exponential
description: APV-style pass uses uniform entry sizes across all cascades; reach = (2N-1) * bpa * brickSize, not exponential 3^c
type: project
originSessionId: d20f25bf-2bc7-497b-95a4-98e20892991c
---
`Packages/is.zori.atmospherics/Runtime/GI/RealtimeGIPass.cs` implements a linear clipmap despite comments referencing APV's "pow(3, subdiv)" convention.

Every entry has the same physical size `entryDim = bricksPerAxis * brickSize` (finest-cascade value). Total grid extent = `(2 * cascadeCount - 1) * entryDim`. Outer cascades vary **probe density inside each entry** via `BricksPerAxisAtSubdiv` (bpa collapses to 1 after first cascade, so outer cascades have 1 brick × 4 probes per axis = sparser within the same physical space) — they do **not** extend spatial reach.

**Why:** The APV-native references in the pass header describe the probe-spacing semantics within entries, not the spatial clipmap layout. The code shows only one `entryDim` uploaded to the compute (`_SkyProbeEntryDim`), and the SkyProbe dispatch is `entriesPerAxis²` threads — no per-cascade spatial scaling. `halfGrid = entriesPerAxis * entryDim * 0.5f` confirms linear extent.

**How to apply:** When reasoning about GI coverage vs `cascadeCount`/`bricksPerAxis`/`brickSize`, use `reach = (2N-1) * bpa * brickSize`. Hard ceiling at `bpa=27, cascades=12` is `23 * 27 * brickSize ≈ 621 * brickSize` — so Cinematic-density probes (brickSize=1.5m) cap at ~931m reach; reaching multi-km requires coarser probes or a geometry refactor. Do NOT use exponential `3^cascade` in derivation formulas; that was a misreading of the header comment that cost a round-trip with the user on 2026-04-18.
