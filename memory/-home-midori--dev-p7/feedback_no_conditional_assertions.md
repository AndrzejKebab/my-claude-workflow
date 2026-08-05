---
name: No conditional assertions in tests
description: Never wrap expect() in if branches — assertions must run unconditionally; use marker-driven flow instead
type: feedback
---

Never write conditional assertions (expect inside if branches). All assertions must run unconditionally.

**Why:** Conditional assertions hide failures and make tests unreliable. The e2e harness was reworked to avoid this pattern entirely.

**How to apply:** Drive test flow with response markers (e.g. `hasNextOutcomes`, `hasUnselectedOutcomes`) rather than game config flags. Assertions run at fixed points in the flow, not behind conditionals.
