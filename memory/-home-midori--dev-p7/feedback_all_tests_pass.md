---
name: all-tests-pass
description: ALL integration tests must pass — no "pre-existing" excuse
type: feedback
---

ALL integration tests must pass before merging. Do not dismiss failures as "pre-existing."
**Why:** The user does not accept regressions or known failures as acceptable baseline. Every test must pass.
**How to apply:** When running integration tests, the acceptance criteria is 0 failures. If tests fail, investigate and fix them — even if they were failing before your changes.
