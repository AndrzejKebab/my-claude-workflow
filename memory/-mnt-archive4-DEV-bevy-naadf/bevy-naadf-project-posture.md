---
name: bevy-naadf-project-posture
description: "bevy-naadf is a faithful port of the NAADF method from C#/MonoGame, then expands upon it with streaming + game-engine feature sets beyond C# scope"
metadata: 
  node_type: memory
  type: project
  originSessionId: 234d8e25-76c2-4b8b-a636-28823c3b2f54
---

`bevy-naadf` at `/mnt/archive4/DEV/bevy-naadf` is a **faithful port of the NAADF method** from C#/MonoGame at `/mnt/archive4/DEV/NAADF/NAADF/`, **and then expands upon it** with streaming + game-engine feature sets the C# codebase doesn't have.

The faithful-port-rule was sharpened on 2026-05-21 (binding user clarification) — it was never an absolute "match C# for everything"; it's "faithfully implement the NAADF method, then build beyond it."

**What stays faithful (C# is canonical reference):**
- The NAADF rendering method itself — three-layer AADFs, GPU producer chain (W0/W2/W3/W4/W5), Algorithm 1 construction, Phase-B GI design, ray traversal, all paper-derived algorithms.
- Bug-for-bug parity on the method's algorithms still matters where C# defined them.

**What expands beyond C# (first-class, no "approved divergence" framing needed):**
- Streaming functionality (residency window, GPU producer admission, snapshot resource, WRITE-path under streaming) — outside C# scope entirely. C# has no streaming.
- Game-engine direction per `voxel-canvas-arch/` ideation — VoxelCanvas component, brushes as ECS entities, plugin split, per-entity voxel volumes, eventually toroidal canvas + brush-likes replacing pagetable streaming.
- Bevy-idiomatic redesigns where the engine work calls for them (not as "improvements to C#" but as net-new engine surface).

**How to apply:**
- For algorithm correctness within the NAADF method: C# is the spec. Bug-for-bug match still applies when C# defined the algorithm.
- For streaming / game-engine surface: design freely. No need to justify divergence from C# (C# doesn't have it).
- When in doubt about which mode a task is in: ask "does C# do this?" — if yes, faithful port; if no, engine direction.
- Historical orchestrations (`naadf-bevy-port/`, `feature-completeness/`) were the faithful-port-of-method era; their "approved divergence" framing was scoped to the method itself, not to all future engine work.

**Port-as-is discipline (project `CLAUDE.md`) is SEPARATE from C# port-faithfulness:** porting `streaming-world`'s working streaming-WRITE-path solution from prior bevy-naadf branches is not "faithful to C#" (C# has no streaming) — it's "faithful to a known-working bevy-naadf design." Use prior bevy-naadf solutions as-is; treat C# as authoritative only for the algorithms it defined.

**What still applies project-wide:**
- Performance budgets (project `CLAUDE.md`) — 240+ FPS, ~1 GB total VRAM, no GiB-class per-frame readbacks.
- Mobile binding cap ([[mobile-256mib-binding-cap]]) — hardware constraint.
- Verification discipline (project `CLAUDE.md`) — e2e gates only.

Related: [[master-branch-identity]], [[mobile-256mib-binding-cap]], [[naadf-getraydir-monogame-conventions]].
