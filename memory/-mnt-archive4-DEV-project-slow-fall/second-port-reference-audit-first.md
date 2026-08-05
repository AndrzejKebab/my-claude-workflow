---
name: second-port-reference-audit-first
description: project_slow_fall is the SECOND port of NAADF; Bevy + MonoGame already addressed every architectural decision. Compound /delegate dispatches without an explicit reference-audit-first phase shipped the YCoCg-AABB blunder (May 2026). Use distributed mode OR a compound brief that mandates reference audit before any design.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 317cd490-7a89-4562-94a9-ea362e4827ac
---

For project_slow_fall (the Unity NAADF port at `/mnt/archive4/DEV/project_slow_fall`): when designing or refactoring any algorithmic component, the architect MUST read `/mnt/archive4/DEV/bevy-naadf/` (Bevy port) and `/mnt/archive4/DEV/NAADF/` (MonoGame reference) before proposing a shape. Every algorithmic choice in design docs / briefs must cite `file:line` from at least one reference.

**Why:** Verified May 2026. The Unity port's TAA was re-implemented in the URP single-history YCoCg-AABB lerp blend pattern instead of the NAADF sample-ring + per-sample [0,100] clamp + sum + divide-by-count pattern that both references ship and the paper specifies. Five diagnostic dispatches probed inside the wrong architecture before a comparative read of Bevy + MonoGame surfaced the rot. The user diagnosed the workflow failure: consolidated mode hid the architect inside a single agent run, the architect never had a clean "read references end-to-end first" phase, and pattern-matched the URP convention.

**How to apply:**
- When `/delegate` selects between consolidated and distributed for design work in this codebase, **prefer distributed** so the architect dispatch has a clean reference-audit deliverable on disk before implementation.
- If consolidated mode is unavoidable (user-selected, scope-fits), the brief MUST mandate a reference-audit phase BEFORE any design work, AND forbid URP/HDRP/Unity-tutorial pattern-match shapes ("if neither Bevy nor MonoGame does it, you don't either"), AND require `file:line` citation from references for every algorithmic choice.
- The CLAUDE.md "Porting discipline" section (`/mnt/archive4/DEV/project_slow_fall/CLAUDE.md`) carries the binding rule version — link to it in briefs.
- Related: [[unity-urp-compute-port-three-seam-pitfalls]] documents three Unity-specific seams already known to bite when porting; the YCoCg-AABB blunder is a fourth class (algorithmic shape divergence, not convention seam).
