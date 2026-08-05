---
name: feedback-primitives-then-analytical-invariants
description: "Streaming/residency/sliding-window — test primitives independently first, then composition, then e2e; system self-reports unfulfilled state analytically, not via screenshots"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e4081ed2-be75-401d-a246-bb2dcded1571
---

Data-structure-backed systems (sliding window, residency, slot maps, pool + indirection) — don't verify primarily via e2e or visual diffs. Build bottom-up:

1. **Primitive** — pool, mapping, sliding-window, slot-assignment policy. Each has unit tests for the data structure's invariants in isolation (free + bound = capacity, eviction set, admission set, lookup).
2. **Composition** — two primitives together (pool + indirection; window driver + slot-assignment).
3. **E2E** — only after 1+2 pass.

**Pre-existing failures on the SAME primitive being modified are BLOCKERS, not deferred.** Brushing as "out of scope" ignores the primitive-level signal.

System must KNOW its state analytically. "Are any slots in the camera window unfulfilled?" must be answerable by querying — counter methods, log lines, `debug_assert!`, `diagnostics()` surface — NOT a screenshot.

**Why:** streaming-world Phase 2.13 cold-start admission-race fix landed cross-world ACK + external decoded-chunk gate. Gate = separate read-back observability, not self-reporting. User: *"the case with unfulfilled slots in the middle must be catched analytically - the system must know if it HAS unfulfilled slots in the middle at startup, not via screenshots"*. Also: 9 pre-existing `windowed_slot_map` failures (free + bound ≠ capacity) brushed off as out-of-scope.

**How to apply:**
- Brief requires primitive tests pass FIRST, then composition, then e2e.
- Pre-existing failures on the same primitive = blockers.
- Add observability surface (counters, methods, startup logs, `debug_assert!`) so system answers "am I healthy?" without screenshots.
- E2E verifies INTEGRATION, not primitive correctness. Loose SSIM is worse.

Related: [[feedback-e2e-gates-must-fail-fast]], [[feedback-e2e-must-drive-actual-main]].
