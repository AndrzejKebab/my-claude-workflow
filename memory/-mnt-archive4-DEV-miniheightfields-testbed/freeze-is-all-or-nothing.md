---
name: freeze-is-all-or-nothing
description: "A frozen VT streams only archive tiles — never mixed with live compositing; coverage below the archive's finest mip is the page table's parent walk, not a hybrid fill"
metadata: 
  node_type: memory
  type: project
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T20:22:49.763Z
---

Ruling, 2026-07-20, on what "frozen" means for the VT archive.

**All or nothing.** A terrain is either fully frozen or fully live/procedural. The current
iteration treats the whole layer set as one implicit frozen **group**. Frozen tiles are the
only tiles that stream. Do NOT composite live content on top of a frozen substrate — that
mixes two concepts and complicates everything downstream.

**Coverage below the archive's finest mip is already solved and needs no new code.**
`BuildPageTableJob` (`VTCpuPageTableManager.cs`) walks `(x>>1, y>>1, lod+1)` until it finds a
loaded slot, so any sample finer than what is resident resolves to its coarsest available
ancestor. The system is meant to propagate the page table toward resident pages always — there
is always a tile to sample or a fallback.

**Therefore the defect to fix is admission, not filling.** A frozen VT that renders black is
admitting tiles the archive does not carry: they get allocated, marked resident, and the page
table points at slots nobody ever wrote. The fix is a **mip floor** — in frozen mode the
desired set must never request finer than the archive's finest mip — after which the existing
parent walk covers everything below it (blurry at close range, never black).

**How to apply:** do not build a hybrid/partition fill. Do not add per-tile "is it archived?"
branching to the composite path. Clamp selection to the archive's mip range and let the page
table do what it already does. Relates to [[editor-decides-player-executes]].
