---
name: master-branch-identity
description: bevy-naadf master = faithful NAADF-method port + streaming + game-engine expansion (post-2026-05-21 clarification); PBR on separate ready branch; aggressive deletion of orphan / superseded code is encouraged
metadata: 
  node_type: memory
  type: project
  originSessionId: 234d8e25-76c2-4b8b-a636-28823c3b2f54
---

bevy-naadf master = (1) **faithful port of the NAADF method** from C# NAADF (`/mnt/archive4/DEV/NAADF/`), (2) **expansion beyond C# scope** with streaming + game-engine direction (voxel-canvas-arch). See [[bevy-naadf-project-posture]] for the full posture.

PBR raymarching work lives on a SEPARATE branch, already ready — master must NOT carry PBR scaffolding. Split is intentional: master is the NAADF-method + streaming + game-engine track; PBR compounds in its own branch.

**Why:** master is the canonical deliverable surface — the NAADF method implemented faithfully PLUS the streaming + game-engine features the project actually builds toward. Scaffolding from intermediate investigations or rejected design alternatives is rot.

**How to apply:**
- Aggressive deletion of investigation residuals, dead scaffolding, stalled-design artifacts = encouraged.
- Delete vs keep: ask "does this serve the NAADF-method faithfulness OR the streaming + game-engine direction?" If neither, delete.
- PBR code on master = suspect by default; belongs on PBR branch.
- "Matches C#" is a valid reason to keep code that implements the NAADF method (per [[bevy-naadf-project-posture]]). It is NOT a reason to keep dual-mode gates or non-streaming dead branches in code that has moved beyond C# scope.

Related: [[bevy-naadf-project-posture]], [[naadf-getraydir-monogame-conventions]].
