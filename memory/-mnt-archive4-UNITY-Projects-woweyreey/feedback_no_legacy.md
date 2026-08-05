---
name: no-legacy-compat
description: Never maintain backward compatibility or legacy API support — just replace the old API cleanly
type: feedback
originSessionId: 9b250140-aa16-4cdf-9b21-8ab760fa85f4
---
Don't upkeep legacy or backward compatibility of any kind when reworking APIs.

**Why:** User prefers clean breaks over maintaining old code paths. Legacy overloads add complexity without value in this project.

**How to apply:** When redesigning an API, remove the old signatures entirely. Don't add "legacy overloads" or fallback paths. Update all call sites to the new API.

**Exception — intentional switches:** Dual/multi paths ARE allowed when the plan, handoff, or user explicitly calls for one of:
- An **artistic choice** toggle (e.g. projection mode, style variant) for A/B comparison by the artist
- A **quality tier** switch (low/med/high) trading fidelity for cost
- An **algorithm/method** switch motivated by performance (e.g. alt integrator for weaker GPUs)

These are not legacy — they are first-class product surface. Keep them behind a keyword/enum and treat both branches as supported. Do NOT invoke this exception on your own initiative; it activates ONLY when the spec/plan/user mentions the switch. When in doubt, collapse to one path and ask.
